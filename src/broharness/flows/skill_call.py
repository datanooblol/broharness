from broflow import BaseTask
from broharness.data_model import State, Process, all_already_executed, record_usage
from broharness.llms.bedrock import SystemMessage, AIMessage
from broharness.toolblock import tool_to_yaml, load_skill_tool, ask_user_question_tool
from broharness.codeblock import parse_json_codeblock, NoCodeBlockError
import yaml

class SkillCall(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.ANSWER, Process.FAIL_RECOVERY, Process.ASK_USER_QUESTION}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt


    def __call__(self, state:State)->State:
        print(__file__)
        try:
            skill_prompt = state.skill_control.load_skill('skill-call')
            available_skills = [f"- {s.name}: {s.description}" for s in state.skill_control.list_skills() if s.name not in ['skill-call', 'tool-call']]
            available_skills = f"## Available Skills:\n{'\n'.join(available_skills)}"
            available_tools = [
                tool_to_yaml(t) 
                for t in state.registered_tools.values() if t.name in ['ask_user_question', 'load_skill_tool']
            ]
            available_tools = f"## Availale Tools:\n{yaml.dump(available_tools, sort_keys=False)}"
            local_prompt = f"{self.system_prompt}\n{skill_prompt}\n{available_skills}\n{available_tools}"
            if state.error_message:
                local_prompt = f"{local_prompt}\n## Error Message:\n{state.error_message}"
            state.error_message = ''
            response = self.llm(messages=state.session_messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.XXX_CALL)
            state.debug.append(response)
            record_usage(state, "XXX_CALL", state.model_id.XXX_CALL, response)
            candidated_tools = parse_json_codeblock(response['content'][0]['text']).get('tool_use', [])
            state.candidated_tools = candidated_tools
            if not candidated_tools:
                self.set_next(Process.ANSWER)
                return state
            if all_already_executed(candidated_tools, state.executed_calls):
                self.set_next(Process.ANSWER)
                return state
            self.set_next(Process.TOOL_USE)
            state.return_to = Process.TOOL_CALL
            return state
        except NoCodeBlockError:
            # see tool_call.py -- text ending in "?" is treated as a dropped
            # question and routed to the real ask flow directly rather than
            # gambling on a corrective retry.
            text = response['content'][0]['text'].strip()
            if text.endswith('?'):
                # see tool_call.py -- goes through ToolUse like a real call.
                state.candidated_tools = [{"name": "ask_user_question", "input": {"question": text}}]
                self.set_next(Process.TOOL_USE)
                state.return_to = Process.SKILL_CALL
                return state
            state.error_message = (
                "Your last response wasn't in the required JSON tool_use format. "
                "If you have nothing left to do, respond with {\"tool_use\": []}. "
                "If you need to ask the user something, use the ask_user_question "
                "tool instead of asking in plain text."
            )
            state.return_to = Process.SKILL_CALL
            self.set_next(Process.FAIL_RECOVERY)
            return state
        except Exception as e:
            state.error_message = str(e)
            print(str(e))
            state.return_to = Process.SKILL_CALL
            self.set_next(Process.FAIL_RECOVERY)
            return state
