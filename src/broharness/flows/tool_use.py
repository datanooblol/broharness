from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import AIMessage
from broskill.processing.tool import to_args
import subprocess
import sys
from pathlib import Path

class ToolUseError(Exception):
    pass

def _script_call(root:Path, scrtip_path:Path, arg:dict)->str:
    result = subprocess.run(
        ['uv', 'run', str(scrtip_path), *to_args(arg)],
        capture_output=True,
        cwd=root,
        text=True,
        encoding='utf-8'
    )
    if result.returncode != 0:
        raise ToolUseError(result.stderr)
    return result.stdout

class ToolUse(BaseTask):
    possible_next = {Process.TOOL_CALL, Process.ASK_USER_QUESTION, Process.FAIL_RECOVERY}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def ask_user_question(self, state:State, fn, arg)->bool|None:
        if (fn == 'ask_user_question') and (arg['question']):
            state.question = arg['question']
            print('ask_user_question passed')
            return True

    def load_skill(self, state:State, fn, arg)->bool|None:
        if fn == 'load_skill':
            if arg['skill_name'] not in state.registered_skills:
                state.registered_skills[arg['skill_name']] = state.session_tools[fn](**arg)
                print('load_skill passed')
            return True

    def load_skill_extension(self, state:State, fn, arg)->bool|None:
        if (fn == 'load_skill_extension'):
            if (arg['skill_name'] not in state.extension_skills):
                state.extension_skills[arg['skill_name']] = state.session_tools[fn](**arg)
            else:
                state.extension_skills[arg['skill_name']] += state.session_tools[fn](**arg)
            print('load_skill_extension passed')
            return True

    def load_tool(self, state:State, fn, arg)->bool|None:
        if fn == 'load_tool':
            if arg['skill_name'] not in state.registered_tools:
                tool = state.session_tools[fn](**arg)
                state.registered_tools[tool.name] = tool
                print('load_tool passed')
            return True

    def script_call(self, state:State, fn, arg):
        tool = state.registered_tools[fn]
        result = _script_call(state.root, tool.path, arg)
        state.tool_results.append({fn: result})
        return result

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            asked = False
            print(state.candidated_tools)
            while state.candidated_tools:
                t = state.candidated_tools.pop(0)
                fn = t.get('name', None)
                arg = t.get('input', {})
                if self.ask_user_question(state, fn, arg): asked=True; break
                if self.load_skill(state, fn, arg): state.executed_calls.append(t); continue
                if self.load_skill_extension(state, fn, arg): state.executed_calls.append(t); continue
                if self.load_tool(state, fn, arg): state.executed_calls.append(t); continue
                _ = self.script_call(state, fn, arg)
                state.executed_calls.append(t)
            if asked:
                self.set_next(Process.ASK_USER_QUESTION)
            else:
                self.set_next(Process.TOOL_CALL)
            return state
        except Exception as e:
            state.error_message = str(e)
            print(str(e))
            # don't touch state.return_to here -- whoever routed into TOOL_USE
            # (SkillCall, ToolCall, or now Answer) already set it to itself
            # before calling in, and that's still the correct resume point.
            self.set_next(Process.FAIL_RECOVERY)
            return state
