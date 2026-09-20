from broflow import TaskRegistry, Flow

from broharness.data_model import Process, State
from broharness.llms.bedrock import bedrock
from broharness.flows.skill_call import SkillCall
from broharness.flows.tool_call import ToolCall
from broharness.flows.tool_use import ToolUse
from broharness.flows.ask_user_question import AskUserQuestion
from broharness.flows.fail_recovery import FailRecovery
from broharness.flows.answer import Answer


class Harness:
    """Fixed orchestration only: skill_call -> tool_call -> tool_use ->
    answer, with ask_user_question and fail_recovery as shared side-routes
    every other task can fall into. This is exactly the wiring from
    notebooks/from_scratch.ipynb, built once here instead of by hand per
    notebook/script.

    Deliberately lean: Harness owns nothing about a run except the fixed
    TaskRegistry/Flow. State is built entirely outside Harness -- root,
    skill_dir, skill_control, tool_control, tools, session_tools,
    system_prompt, model_id, verbose all live on State, constructed the
    same way notebooks/from_scratch.ipynb does it. This keeps the two
    testable and controllable separately: swap what's in State without
    touching Harness, or reuse one Harness across many independently-built
    States.

        h = Harness()
        state = State(...)   # built directly, see from_scratch.ipynb
        state = h.run(state)
    """

    def __init__(self, llm=bedrock):
        self.llm = llm

        registry = TaskRegistry()
        registry.register(Process.SKILL_CALL, SkillCall(name='skill-call', llm=llm, system_prompt=''))
        registry.register(Process.TOOL_CALL, ToolCall(name='tool-call', llm=llm, system_prompt=''))
        registry.register(Process.TOOL_USE, ToolUse(name='tool-use', llm=llm, system_prompt=''))
        registry.register(Process.ASK_USER_QUESTION, AskUserQuestion(name='ask-user-question', llm=llm, system_prompt=''))
        registry.register(Process.FAIL_RECOVERY, FailRecovery(name='fail-recovery', llm=llm, system_prompt=''))
        registry.register(Process.ANSWER, Answer(name='answer', llm=llm))
        self.flow = Flow(registry)

    def run(self, state: State) -> State:
        """One turn: State in, State out. Doesn't touch messages or turn
        bookkeeping -- that's the caller's job (build the first State
        directly; for each turn after that, append the next user message
        and call state.flush_turn() before calling run() again)."""
        return self.flow.run(start=Process.SKILL_CALL, end=Process.END, state=state)
