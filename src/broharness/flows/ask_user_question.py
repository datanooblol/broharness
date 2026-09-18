from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import UserMessage

class AskUserQuestion(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.SKILL_CALL}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            questions = state.messages[-1]['content'][0]['text']
            user_input = input(questions)
            state.messages.append(UserMessage(user_input))
            state.debug.append(UserMessage(user_input))
            self.set_next(state.return_to)
            state.return_to = None
            return state
        except Exception as e:
            state.error_message = str(e)
            state.return_to = Process.ASK_USER_QUESTION
            self.set_next(Process.FAIL_RECOVERY)
            return state
