from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import SystemMessage, AIMessage
from broharness.toolblock import tool_to_yaml, ask_user_question_tool, load_skill_extension_tool, load_tool_tool
from broharness.codeblock import parse_json_codeblock
import yaml

class ToolCall(BaseTask):
    possible_next = {Process.ANSWER, Process.FAIL_RECOVERY, Process.ASK_USER_QUESTION}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def register_tool(self, state:State, candidated_tools)->State:
        for s in candidated_tools:
            if (s['name'] not in ['ask_user_question']):
                if (s['name'] not in state.tool_calls):
                    state.tool_calls[s['name']] = [s['input']]
                else:
                    state.tool_calls[s['name']].append(s['input'])
        return state

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            skill_prompt = "\n".join([f"Skill name: {s}\n-----\n{p}"  for s, p in state.registered_skills.items()])
            tool_prompt = state.skill_control.load_skill('tool-call')
            available_tools = [
                tool_to_yaml(t) 
                for t in [
                    load_skill_extension_tool,
                    load_tool_tool,
                    ask_user_question_tool,
                ]
            ]
            available_tools = f"## Availale Tools:\n{yaml.dump(available_tools, sort_keys=False)}"
            local_prompt = f"{self.system_prompt}\n{skill_prompt}\n{tool_prompt}\n{available_tools}"
            if state.error_message:
                local_prompt = f"{local_prompt}\n## Error Message:\n{state.error_message}"
            # print("-"*10, local_prompt)
            state.system_prompt = local_prompt
            state.error_message = ''
            response = self.llm(messages=state.messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.XXX_CALL)
            # state.messages.append(response['content'])
            state.debug.append(response)
            candidated_tools = parse_json_codeblock(response['content'][0]['text']).get('tool_use', [])
            if not candidated_tools:
                self.set_next(Process.ANSWER)
                return state
            self.register_tool(state, candidated_tools)
            self.set_next(Process.TOOL_USE)
            questions = "\n".join([t['input']['question'] for t in candidated_tools if t['name']=='ask_user_question'])
            if questions:
                state.messages.append(AIMessage(questions))
                self.set_next(Process.ASK_USER_QUESTION)
                state.return_to = Process.TOOL_CALL
            return state
        except Exception as e:
            state.error_message = str(e)
            state.return_to = Process.TOOL_CALL
            self.set_next(Process.FAIL_RECOVERY)
            return state
