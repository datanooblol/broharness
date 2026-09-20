from broflow import BaseTask
from broharness.data_model import State, Process, trace
from broharness.llms.bedrock import UserMessage, AIMessage

FALLBACK_MESSAGE = "Sorry, I ran into a problem and couldn't complete this."

class FailRecovery(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.SKILL_CALL, Process.TOOL_USE, Process.ASK_USER_QUESTION, Process.ANSWER, Process.END}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        trace(state, __file__)
        if state.retry_count < state.max_retries:
            state.retry_count += 1
            self.set_next(state.return_to)
            state.return_to = None
            return state
        if state.return_to == Process.ANSWER:
            # Answer itself is what kept failing -- routing back to it again
            # would just repeat the same failure forever instead of escaping.
            state.messages.append(AIMessage(FALLBACK_MESSAGE))
            state.session_messages.append(AIMessage(FALLBACK_MESSAGE))
            state.return_to = None
            self.set_next(Process.END)
            return state
        self.set_next(Process.ANSWER)
        return state