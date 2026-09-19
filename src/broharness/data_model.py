from enum import StrEnum
from dataclasses import dataclass, field
from broskill import SkillControl, ToolControl, Tool
from typing import Any
from pathlib import Path

class Process(StrEnum):
    SKILL_CALL = 'skill_call'
    TOOL_CALL = 'tool_call'
    TOOL_USE = 'tool_use'
    ASK_USER_QUESTION = 'ask_user_question'
    FAIL_RECOVERY = 'fail_recovery'
    ANSWER = 'answer'
    END = 'end'

@dataclass
class LLMUse:
    XXX_CALL:str = 'google.gemma-3-12b-it'
    REASONING:str = 'google.gemma-3-12b-it'
    ANSWER:str = 'google.gemma-3-12b-it'

@dataclass
class State:
    root:Path = field(metadata=dict(description="a project root directory"))
    skill_dir:Path = field(metadata=dict(description="a directory contains skills"))
    messages:list = field(metadata=dict(description="original messages"))
    session_messages:list = field(metadata=dict(description="messages but it will be updated during a session"))
    skill_control:SkillControl = field(metadata=dict(description="a class with methods relating to skill management"))
    tool_control:ToolControl = field(metadata=dict(description="a class with methods relating to tool management"))
    tools:Any = field(metadata=dict(description="original executed tools"))
    session_tools:Any = field(metadata=dict(description="tools but it will be updated during a session"))
    system_prompt:str = field(metadata=dict(description="a system prompt applies in `Answer`"), default='')
    question:str = field(metadata=dict(description="a question for `AskUserQuestion`"), default='')
    registered_skills:dict[str, Any] = field(metadata=dict(description="loaded skills used only in a session"), default_factory=dict)
    extension_skills:dict[str, Any] = field(metadata=dict(description="loaded skill extensions used only in a session"), default_factory=dict)
    registered_tools:dict[str, Tool] = field(metadata=dict(description="loaded tools used only in a session"), default_factory=dict)
    candidated_tools:list = field(metadata=dict(description="tools extracted from `SkillCall` and `ToolCall`"), default_factory=list)
    tool_results:list = field(metadata=dict(description="results of `ToolUse`"), default_factory=list)
    error_message:str = field(metadata=dict(description="Error message fetched after `FAIL_RECOVERY`"), default='')
    return_to:Process|None = field(metadata=dict(description="Process control routing any stage to a specified process"), default=None)
    debug:list = field(metadata=dict(description="all requests and responses during a session"), default_factory=list)
    model_id:LLMUse = field(metadata=dict(description="model used in a specified process"), default_factory=LLMUse)
    retry_count:int = field(metadata=dict(description="track how many times `FAIL_RECOVERY` is striggered"), default=0)
    max_retries:int = field(metadata=dict(description="retry only n times with `FAIL_RECOVERY`"), default=3)
    executed_calls:list = field(metadata=dict(description="every {name, input} ToolUse has actually run this session, used to detect a repeated request"), default_factory=list)
    usage:dict = field(metadata=dict(description="input/output token usage this session, nested state.usage[slot][model_id] -- slot is the LLMUse field name (e.g. 'XXX_CALL'), so usage is visible both per-role and per-model"), default_factory=dict)


def all_already_executed(candidated_tools: list, executed_calls: list) -> bool:
    """True if candidated_tools is non-empty and every entry already appears
    in executed_calls -- i.e. the model asked for nothing it doesn't already
    have. Used to skip straight to ANSWER instead of re-running (or re-asking
    the model to reconsider) something already done."""
    return bool(candidated_tools) and all(t in executed_calls for t in candidated_tools)


def record_usage(state: "State", slot: str, model_id: str, response: dict) -> None:
    """Accumulates one call's input/output tokens into state.usage[slot][model_id].
    slot is the LLMUse field name the call was made under (e.g. "XXX_CALL",
    "ANSWER"), model_id is the actual model that served it -- nesting both
    means usage can be summed either way: per-role (which step costs the
    most) or per-model (real $ cost, if a role's model changes mid-session).
    """
    usage = response.get('usage')
    if not usage:
        return
    slot_entry = state.usage.setdefault(slot, {})
    entry = slot_entry.setdefault(model_id, {"input_tokens": 0, "output_tokens": 0, "call_count": 0})
    entry["input_tokens"] += usage.get("inputTokens", 0)
    entry["output_tokens"] += usage.get("outputTokens", 0)
    entry["call_count"] += 1