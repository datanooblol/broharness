from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import UserMessage, AIMessage

class AskUserQuestion(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.SKILL_CALL}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            user_answer = input(state.question)
            state.session_messages.append(AIMessage(state.question))
            state.session_messages.append(UserMessage(user_answer))
            # state.tool_results.append({'ask_user_question': user_answer})
            state.question = ''
            self.set_next(state.return_to)
            state.return_to = None
            return state
        except Exception as e:
            state.error_message = str(e)
            print(str(e))
            state.return_to = Process.ASK_USER_QUESTION
            self.set_next(Process.FAIL_RECOVERY)
            return state
