from enum import StrEnum
from dataclasses import dataclass, field
from broskill import SkillControl, ToolControl, Tool
from typing import Any
from pathlib import Path
import re

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
    SKILL_CALL:str = 'google.gemma-3-12b-it'
    TOOL_CALL:str = 'google.gemma-3-12b-it'
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
    executed_calls:list = field(metadata=dict(description="every {name, input} ToolUse has actually run this turn, used to detect a repeated request"), default_factory=list)
    usage:dict = field(metadata=dict(description="input/output token usage this session, nested state.usage[slot][model_id] -- slot is the LLMUse field name (e.g. 'SKILL_CALL', 'TOOL_CALL'), so usage is visible both per-role and per-model"), default_factory=dict)
    verbose:bool = field(metadata=dict(description="when True, flows/*.py's step-tracking trace() calls print to stdout; when False they're silent. Controls harness-level debug noise, separate from `debug` (the recorded LLM call log, always kept regardless of this flag)"), default=False)

    def flush_turn(self) -> None:
        """Resets everything that's only valid for the turn that just
        finished, so the same State can go into the next Harness.run() call
        without leaking this turn's tool results into the next turn's
        Answer prompt (the cause of a real hallucination: a stale
        tool_results from turn 1 got treated as if it answered turn 2's
        different question).

        Kept as-is (session-scoped, not per-turn): registered_skills,
        extension_skills, registered_tools, session_tools (no need to
        reload/re-register what's already loaded), messages/session_messages
        (conversation history), debug and usage (full-session audit trail
        and cost tracking), model_id/max_retries (session config).

        Flushed (per-turn only): tool_results and candidated_tools (this
        turn's tool activity), executed_calls (dedup bookkeeping scoped to
        one turn's retry loop -- carrying it over would make a legitimately
        repeated request in a later turn get silently skipped), error_message
        and return_to (mid-turn routing state), retry_count (a fresh retry
        budget per turn), question (should already be cleared by
        AskUserQuestion, reset here too for safety).
        """
        self.tool_results = []
        self.candidated_tools = []
        self.executed_calls = []
        self.error_message = ''
        self.return_to = None
        self.retry_count = 0
        self.question = ''


_QUESTION_STARTERS = (
    "what", "where", "when", "who", "whom", "whose", "why", "how", "which",
    "is", "are", "am", "was", "were", "do", "does", "did",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "have", "has", "had",
)


def looks_like_a_question(text: str) -> bool:
    """True only if the text's final sentence actually reads as a question
    -- starts with a WH-word or auxiliary verb -- not just any text that
    happens to end in '?'. A casual sentence ending in a rhetorical tag
    ("...you know?", "...right?") is a complete answer with a verbal tic,
    not a dropped clarifying question; treating it as one derails an
    otherwise-finished turn into an unwanted ask_user_question detour (a
    real failure observed with a 'bro-tone' persona system_prompt, whose
    sentences habitually trail off with a rhetorical '?')."""
    text = text.strip()
    if not text.endswith('?'):
        return False
    sentences = re.split(r'(?<=[.!?])\s+', text)
    last = (sentences[-1] if sentences else text).strip()
    # stop at an apostrophe -- "What's"/"Doesn't" would otherwise match as
    # one token ("what's") that never equals the bare starter word ("what")
    first_word = re.match(r"[A-Za-z]+", last)
    if not first_word:
        return False
    return first_word.group(0).lower() in _QUESTION_STARTERS


def trace(state: "State", *args) -> None:
    """Prints only when state.verbose is True -- lets every flows/*.py
    step-tracking print (__file__, which branch fired, caught errors) be
    switched on/off from one place, State, instead of being unconditional
    stdout noise or hand-toggled per file."""
    if state.verbose:
        print(*args)


def all_already_executed(candidated_tools: list, executed_calls: list) -> bool:
    """True if candidated_tools is non-empty and every entry already appears
    in executed_calls -- i.e. the model asked for nothing it doesn't already
    have. Used to skip straight to ANSWER instead of re-running (or re-asking
    the model to reconsider) something already done."""
    return bool(candidated_tools) and all(t in executed_calls for t in candidated_tools)


NO_RESULT_MARKERS = ("nothing matches pattern:", "no file matches pattern:")


def tool_results_are_empty(tool_results: list) -> bool:
    """True if every tool result is a known 'found nothing' message (e.g.
    list_directory's 'nothing matches pattern: ...', read_file's 'no file
    matches pattern: ...') rather than real content. A quiet no-match message
    sitting inline under '## Tool Use and Result' reads enough like content
    that a small model can still confabulate a plausible answer around it --
    this flags that case so it can be called out explicitly instead."""
    if not tool_results:
        return False
    contents = [content for entry in tool_results for content in entry.values()]
    return all(
        any(c.strip().startswith(marker) for marker in NO_RESULT_MARKERS)
        for c in contents
    )


def render_tool_results(tool_results: list) -> str:
    """Renders state.tool_results (a list of single-key {name: output} dicts)
    as readable text, one real block per result -- avoids dumping raw Python
    dict repr (values with escaped \\n, everything squashed onto one line)
    into a prompt, which makes real content easy to miss or misread."""
    return "\n".join(
        f"### {name}\n{content}"
        for entry in tool_results
        for name, content in entry.items()
    )


def record_usage(state: "State", slot: str, model_id: str, response: dict) -> None:
    """Accumulates one call's input/output tokens into state.usage[slot][model_id].
    slot is the LLMUse field name the call was made under (e.g. "SKILL_CALL",
    "TOOL_CALL", "ANSWER"), model_id is the actual model that served it -- nesting both
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