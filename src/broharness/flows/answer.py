from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import SystemMessage, AIMessage
from broharness.toolblock import tool_to_yaml, load_skill_tool, ask_user_question_tool
from broharness.codeblock import parse_json_codeblock
import yaml

class Answer(BaseTask):
    possible_next = {Process.END}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            skill_prompt = "\n".join([f"{p}"  for s, p in state.registered_skills.items()])
            local_prompt = f"{self.system_prompt}\n{skill_prompt}"
            response = self.llm(messages=state.messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.XXX_CALL)
            state.messages.append(AIMessage(response['content'][0]['text']))
            state.debug.append(response)
            self.set_next(Process.END)
            state.return_to = None
            return state
        except Exception as e:
            state.error_message = str(e)
            self.set_next(Process.FAIL_RECOVERY)
            state.return_to = Process.ANSWER
            return state
