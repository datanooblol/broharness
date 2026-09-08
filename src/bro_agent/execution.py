"""The generic plan -> act -> respond loop: execute one skill against one request."""
import json
import subprocess
import sys
from pathlib import Path

from brollm import extract_codeblocks
from broflow import BaseTask, TaskRegistry, Flow

from .llm import call_bedrock
from .skills import REPO_ROOT, load_skill, skill_dir


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def read_file(path: str) -> str:
    return _resolve(path).read_text(encoding="utf-8")


def grep_file(pattern: str, path: str) -> list[tuple[int, str]]:
    return [
        (i, line)
        for i, line in enumerate(_resolve(path).read_text(encoding="utf-8").splitlines(), start=1)
        if pattern in line
    ]


TOOLS = {"read_file": read_file, "grep_file": grep_file}


def run_script(directory: Path, script: str, args: list[str] | None = None) -> str:
    """Runs a script bundled inside a skill's own folder as a subprocess.

    Unlike TOOLS (in-process functions), a bundled script is never imported
    or read into the model's context -- it's executed for real and only its
    stdout/stderr comes back. Args are passed as a list (never shell=True).
    Runs with cwd=REPO_ROOT so path args follow the same repo-root-relative
    convention as read_file/grep_file.
    """
    script_path = directory / script
    if not script_path.is_file():
        raise FileNotFoundError(f"no such script in skill: {script_path}")
    result = subprocess.run(
        [sys.executable, str(script_path), *(args or [])],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    output = result.stdout
    if result.returncode != 0:
        output += f"\n[exit {result.returncode}]\n{result.stderr}"
    return output


def build_plan_prompt(instructions: str, user_request: str, directory: Path) -> str:
    tool_lines = [f"- {name}" for name in TOOLS]
    scripts = sorted(p.name for p in directory.glob("*.py"))
    if scripts:
        tool_lines.append(
            f"- run_script(script, args): runs one of this skill's bundled scripts "
            f"({', '.join(scripts)}); args is a list of command-line arguments"
        )
    tool_docs = "\n".join(tool_lines)
    return (
        f"{instructions}\n\n"
        f"Available tools:\n{tool_docs}\n\n"
        "Decide which tool call satisfies the user's request, if any.\n"
        "Reply with only a fenced json codeblock, either:\n"
        '```json\n{"tool": "grep_file", "args": {"pattern": "...", "path": "..."}}\n```\n'
        "or for a bundled script:\n"
        '```json\n{"tool": "run_script", "args": {"script": "count_words.py", "args": ["path/to/file"]}}\n```\n'
        "or, if no tool is needed:\n"
        '```json\n{"tool": null}\n```\n\n'
        f"User request: {user_request}"
    )


def _first_json_block(raw: str) -> dict:
    json_blocks = [b for b in extract_codeblocks(raw) if b.language == "json"]
    return json.loads(json_blocks[0].content)


class PlanTask(BaseTask):
    possible_next = {"act", "respond"}

    def __call__(self, state, **kwargs):
        prompt = build_plan_prompt(state["instructions"], state["user_request"], state["skill_dir"])
        call = _first_json_block(call_bedrock(prompt))
        state["tool"] = call.get("tool")
        state["args"] = call.get("args", {})
        self.set_next("act" if state["tool"] else "respond")
        return state


class ActTask(BaseTask):
    possible_next = {"respond"}

    def __call__(self, state, **kwargs):
        if state["tool"] == "run_script":
            state["tool_result"] = run_script(state["skill_dir"], **state["args"])
        else:
            state["tool_result"] = TOOLS[state["tool"]](**state["args"])
        self.set_next("respond")
        return state


class RespondTask(BaseTask):
    possible_next = {"end"}

    def __call__(self, state, **kwargs):
        prompt = f"{state['instructions']}\n\nUser request: {state['user_request']}\n"
        if state.get("tool"):
            prompt += f"Tool `{state['tool']}` returned: {state['tool_result']}\n\n"
        prompt += "Write the final answer to the user, following the skill's instructions."
        state["answer"] = call_bedrock(prompt)
        self.set_next("end")
        return state


_registry = TaskRegistry()
_registry.register("plan", PlanTask("plan"))
_registry.register("act", ActTask("act"))
_registry.register("respond", RespondTask("respond"))
skill_flow = Flow(_registry)


def execute_skill(skill_name: str, user_request: str, registry: dict) -> dict:
    state = {
        "instructions": load_skill(skill_name, registry),
        "user_request": user_request,
        "skill_dir": skill_dir(skill_name, registry),
    }
    skill_flow.run(start="plan", end="end", state=state)
    return state
