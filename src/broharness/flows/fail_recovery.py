from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import UserMessage

class FailRecovery(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.SKILL_CALL, Process.TOOL_USE, Process.ASK_USER_QUESTION}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        print(__file__)
        if state.retry_count < state.max_retries:
            state.retry_count += 1
            self.set_next(state.return_to)
            state.return_to = None
            return state
        self.set_next(Process.ANSWER)
        return state