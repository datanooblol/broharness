from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import SystemMessage, AIMessage
from broharness.toolblock import tool_to_yaml, load_skill_tool, ask_user_question_tool
from broharness.codeblock import parse_json_codeblock
import yaml

class SkillCall(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.ANSWER, Process.FAIL_RECOVERY, Process.ASK_USER_QUESTION}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def register_skill(self, state:State, candidated_tools)->State:
        for s in candidated_tools:
            if (s['input']['skill_name'] not in state.registered_skills) and (s['name']=='load_skill'):
                state.registered_skills[s['input']['skill_name']] = state.skill_control.load_skill(**s['input'])
        return state

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            skill_prompt = state.skill_control.load_skill('skill-call')
            available_skills = [f"- {s.name}: {s.description}" for s in state.skill_control.list_skills() if s.name not in ['skill-call', 'tool-call']]
            available_skills = f"## Available Skills:\n{'\n'.join(available_skills)}"
            available_tools = [
                tool_to_yaml(t) 
                for t in [
                    load_skill_tool, 
                    ask_user_question_tool
                ]
            ]
            available_tools = f"## Availale Tools:\n{yaml.dump(available_tools, sort_keys=False)}"
            local_prompt = f"{self.system_prompt}\n{skill_prompt}\n{available_skills}\n{available_tools}"
            response = self.llm(messages=state.messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.XXX_CALL)
            # state.messages.append(response['content'])
            state.debug.append(response)
            # name: input
            candidated_tools = parse_json_codeblock(response['content'][0]['text']).get('tool_use', [])
            if not candidated_tools:
                self.set_next(Process.ANSWER)
                return state
            else:
                self.register_skill(state, candidated_tools)
                self.set_next(Process.TOOL_CALL)
            questions = "\n".join([t['input']['question'] for t in candidated_tools if t['name']=='ask_user_question'])
            if questions:
                state.messages.append(AIMessage(questions))
                self.set_next(Process.ASK_USER_QUESTION)
                state.return_to = Process.SKILL_CALL
            return state
        except Exception as e:
            state.error_message = str(e)
            state.return_to = Process.SKILL_CALL
            self.set_next(Process.FAIL_RECOVERY)
            return state
