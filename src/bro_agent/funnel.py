"""The funnel flow: stage-gated, multi-turn, persistent -- unlike execute_skill.

Each inbound customer message runs one plan -> act -> respond pass scoped to
whatever skill currently owns the lead's stage, then the model proposes a
next stage which gets clamped against TRANSITIONS before anything is
persisted. That clamp is the guardrail: a lead can never skip straight to
close_handoff no matter what the model (or the customer) suggests.
"""
import json
from pathlib import Path

from brollm import extract_codeblocks
from broflow import BaseTask, TaskRegistry, Flow

from .llm import call_bedrock
from .skills import discover_skills, load_skill, skill_dir as _skill_dir
from .execution import read_file
from .leads import DEFAULT_DB_PATH, get_lead, update_lead, create_handoff

TRANSITIONS = {
    "qualify": {"qualify", "nurture"},
    "nurture": {"nurture", "present_offer", "handle_objection"},
    "present_offer": {"present_offer", "handle_objection", "close_handoff"},
    "handle_objection": {"nurture", "present_offer", "handle_objection"},
    "close_handoff": {"close_handoff"},  # terminal
}

# Each skill only sees the tools relevant to its own job -- not a global
# registry -- so a stage's plan prompt never leaks tools that belong
# elsewhere (see README, "Scaling up: many skills, many tools").
FUNNEL_SKILL_TOOLS = {
    "qualify-lead": {"save_lead_field": "save_lead_field(field, value): records a qualifying detail about this lead"},
    "nurture-lead": {"read_file": "read_file(path): reads this skill's bundled product_info.md"},
    "present-offer": {"get_pricing": "get_pricing(plan): looks up the real price for a plan name"},
    "handle-objection": {},
    "close-handoff": {"create_handoff": "create_handoff(notes): creates a handoff task for a human rep"},
}


def skill_for_stage(stage: str, registry: dict) -> str:
    for name, info in registry.items():
        if info.get("stage") == stage:
            return name
    raise KeyError(f"no skill declares stage={stage}")


def _save_lead_field(lead_id: str, field: str, value: str, db_path: Path) -> str:
    update_lead(lead_id, fields={field: value}, path=db_path)
    return f"saved {field}={value!r} for lead {lead_id}"


def _get_pricing(directory: Path, plan: str) -> str:
    pricing = json.loads((directory / "pricing.json").read_text(encoding="utf-8"))
    if plan not in pricing:
        return f"no such plan '{plan}'. available plans: {', '.join(pricing)}"
    return f"{plan}: {pricing[plan]}"


def _create_handoff(lead_id: str, notes: str, db_path: Path) -> str:
    return create_handoff(lead_id, notes, path=db_path)


def _first_json_block(raw: str) -> dict:
    json_blocks = [b for b in extract_codeblocks(raw) if b.language == "json"]
    return json.loads(json_blocks[0].content)


def _known_fields(lead: dict) -> str:
    return ", ".join(f"{k}={v!r}" for k, v in lead["fields"].items()) or "(nothing yet)"


def _format_history(history: list[dict], limit: int = 8) -> str:
    if not history:
        return "(this is the first message)"
    return "\n".join(f"{turn['role']}: {turn['text']}" for turn in history[-limit:])


def build_funnel_plan_prompt(state: dict) -> str:
    tools = FUNNEL_SKILL_TOOLS.get(state["skill_name"], {})
    tool_docs = "\n".join(f"- {doc}" for doc in tools.values()) or "(no tools for this stage)"
    return (
        f"{state['instructions']}\n\n"
        f"Conversation so far:\n{_format_history(state['lead']['history'])}\n\n"
        f"What's already known about this lead: {_known_fields(state['lead'])}\n\n"
        f"Available tools:\n{tool_docs}\n\n"
        "Decide which tool call (if any) is needed before replying. Do not\n"
        "call a tool to save something already listed as known above.\n"
        "Reply with only a fenced json codeblock, either:\n"
        '```json\n{"tool": "save_lead_field", "args": {"field": "budget", "value": "500/mo"}}\n```\n'
        "or, if no tool is needed:\n"
        '```json\n{"tool": null}\n```\n\n'
        f"Customer message: {state['user_request']}"
    )


def build_funnel_respond_prompt(state: dict) -> str:
    allowed = sorted(TRANSITIONS[state["current_stage"]])
    prompt = (
        f"{state['instructions']}\n\n"
        f"Conversation so far:\n{_format_history(state['lead']['history'])}\n\n"
        f"What's already known about this lead: {_known_fields(state['lead'])}\n\n"
        f"Current funnel stage: {state['current_stage']}\n"
        f"Customer message: {state['user_request']}\n"
    )
    if state.get("tool"):
        prompt += f"Tool `{state['tool']}` returned: {state['tool_result']}\n\n"
    prompt += (
        "Write the reply to send the customer. Do not ask again for anything\n"
        "already listed as known above. Then decide the next funnel stage --\n"
        "advance as soon as this stage's own instructions say you have enough.\n"
        f"Allowed next stages from here: {allowed}\n"
        "Reply with only a fenced json codeblock:\n"
        '```json\n{"answer": "...", "next_stage": "..."}\n```'
    )
    return prompt


class FunnelPlanTask(BaseTask):
    possible_next = {"act", "respond"}

    def __call__(self, state, **kwargs):
        call = _first_json_block(call_bedrock(build_funnel_plan_prompt(state)))
        state["tool"] = call.get("tool")
        state["args"] = call.get("args", {})
        self.set_next("act" if state["tool"] else "respond")
        return state


class FunnelActTask(BaseTask):
    possible_next = {"respond"}

    def __call__(self, state, **kwargs):
        tool, args = state["tool"], state["args"]
        if tool == "read_file":
            state["tool_result"] = read_file(**args)
        elif tool == "save_lead_field":
            state["tool_result"] = _save_lead_field(state["lead_id"], db_path=state["db_path"], **args)
            # Reflect the write in-memory too, so the respond step later in
            # this same turn sees it -- not just future turns.
            state["lead"]["fields"][args["field"]] = args["value"]
        elif tool == "get_pricing":
            state["tool_result"] = _get_pricing(state["skill_dir"], **args)
        elif tool == "create_handoff":
            state["tool_result"] = _create_handoff(state["lead_id"], db_path=state["db_path"], **args)
        else:
            raise ValueError(f"unknown tool for this stage: {tool}")
        self.set_next("respond")
        return state


class FunnelRespondTask(BaseTask):
    possible_next = {"end"}

    def __call__(self, state, **kwargs):
        parsed = _first_json_block(call_bedrock(build_funnel_respond_prompt(state)))
        proposed = parsed.get("next_stage")
        allowed = TRANSITIONS[state["current_stage"]]
        # Guardrail: a proposed stage outside the allowed set (e.g. the model
        # or the customer trying to jump straight to close) is clamped back
        # to the current stage rather than trusted.
        state["next_stage"] = proposed if proposed in allowed else state["current_stage"]
        state["answer"] = parsed.get("answer", "")
        self.set_next("end")
        return state


_registry = TaskRegistry()
_registry.register("plan", FunnelPlanTask("plan"))
_registry.register("act", FunnelActTask("act"))
_registry.register("respond", FunnelRespondTask("respond"))
funnel_flow = Flow(_registry)


def handle_turn(lead_id: str, message: str, registry: dict = None, db_path: Path = DEFAULT_DB_PATH) -> str:
    """Processes one inbound customer message and returns the agent's reply.

    Loads the lead's current stage, runs one plan/act/respond pass scoped to
    that stage's skill, then persists the (guardrail-clamped) stage
    transition and the full turn into the lead's history.
    """
    if registry is None:
        registry = discover_skills()

    lead = get_lead(lead_id, path=db_path)
    current_stage = lead["stage"]
    skill_name = skill_for_stage(current_stage, registry)

    state = {
        "instructions": load_skill(skill_name, registry),
        "user_request": message,
        "skill_dir": _skill_dir(skill_name, registry),
        "skill_name": skill_name,
        "lead": lead,
        "lead_id": lead_id,
        "db_path": db_path,
        "current_stage": current_stage,
    }
    funnel_flow.run(start="plan", end="end", state=state)

    update_lead(
        lead_id,
        stage=state["next_stage"],
        append_history={"role": "customer", "text": message, "stage": current_stage},
        path=db_path,
    )
    update_lead(
        lead_id,
        append_history={"role": "agent", "text": state["answer"], "stage": state["next_stage"]},
        path=db_path,
    )
    return state["answer"]
