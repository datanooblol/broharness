from broflow import BaseTask
from broharness.data_model import State, Process, trace
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
            trace(state, 'ask_user_question passed')
            return True

    def load_skill(self, state:State, fn, arg)->bool|None:
        if fn == 'load_skill':
            if arg['skill_name'] not in state.registered_skills:
                prompt = state.session_tools[fn](**arg)
                if prompt is None:
                    # SkillControl.load_skill returns None (not an
                    # exception) for a name that doesn't exist under
                    # skill_dir -- without this check, a hallucinated skill
                    # name would silently "succeed" and store None, which
                    # later renders as the literal text "None" in a prompt
                    # instead of ever telling the model the skill it named
                    # doesn't exist.
                    raise ToolUseError(
                        f"'{arg['skill_name']}' is not a real skill -- no "
                        f"skill directory by that name exists. Check the "
                        f"available skills list and use one of those names."
                    )
                state.registered_skills[arg['skill_name']] = prompt
                trace(state, 'load_skill passed')
                self._auto_register_scripts(state, arg['skill_name'])
            return True

    def _auto_register_scripts(self, state:State, skill_name:str)->None:
        # A model repeatedly proved unreliable at remembering to call
        # load_tool before using a script, even after explicit corrective
        # errors -- so registration happens automatically here instead of
        # depending on that extra step. This is free (just introspecting
        # get_args()), so there's no real cost to doing it eagerly.
        skill_path = state.skill_control.get_skill_path(skill_name)
        if skill_path is None:
            return
        scripts_dir = skill_path / 'scripts'
        if not scripts_dir.is_dir():
            return
        for script_path in sorted(scripts_dir.glob('*.py')):
            try:
                tool = state.session_tools['load_tool'](skill_name=skill_name, path=f'scripts/{script_path.name}')
                state.registered_tools[tool.name] = tool
                trace(state, f'auto-registered {tool.name}')
            except Exception as e:
                # one broken script (e.g. no get_args()) shouldn't block the
                # rest of the skill's tools from registering.
                trace(state, f'could not auto-register {script_path.name}: {e}')

    def load_skill_extension(self, state:State, fn, arg)->bool|None:
        if (fn == 'load_skill_extension'):
            if arg['skill_name'] not in state.registered_skills:
                # Checked against state.registered_skills (this
                # conversation's own record), not delegated straight to
                # SkillControl -- SkillControl tracks "is this skill
                # loaded" as its own internal state, not scoped per
                # conversation, so a skill loaded in an earlier, unrelated
                # run sharing the same SkillControl instance could let a
                # wrong skill_name silently succeed instead of failing.
                # Naming the actually-loaded skill(s) directly, rather than
                # a generic "check you meant..." -- a vague pointer left
                # the model repeating the exact same wrong skill_name
                # verbatim across every retry instead of correcting it, and
                # suggesting "call load_skill with skill_name=<the wrong
                # name>" was actively bad advice: it handed back the
                # model's own mistaken value as if it were a valid skill to
                # load, when it isn't one at all (skill_name is a skill's
                # own name, not a reference file's basename).
                loaded = ', '.join(state.registered_skills) or 'none yet'
                raise ToolUseError(
                    f"'{arg['skill_name']}' is not a loaded skill in this "
                    f"conversation -- skill_name must be an actual skill's "
                    f"name, not a reference file's name. Currently loaded "
                    f"skill(s): {loaded}. If the reference you want belongs "
                    f"to one of those, use its skill_name instead, e.g. "
                    f"skill_name='{next(iter(state.registered_skills), '...')}'."
                )
            if (arg['skill_name'] not in state.extension_skills):
                state.extension_skills[arg['skill_name']] = state.session_tools[fn](**arg)
            else:
                state.extension_skills[arg['skill_name']] += state.session_tools[fn](**arg)
            trace(state, 'load_skill_extension passed')
            return True

    def load_tool(self, state:State, fn, arg)->bool|None:
        if fn == 'load_tool':
            if arg['skill_name'] not in state.registered_tools:
                tool = state.session_tools[fn](**arg)
                state.registered_tools[tool.name] = tool
                trace(state, 'load_tool passed')
            return True

    def script_call(self, state:State, fn, arg):
        if fn not in state.registered_tools:
            # a bare KeyError here just says "'fn'" -- no hint of what went
            # wrong or how to fix it, so a retry just repeats the same
            # mistake instead of correcting it. Spell out the fix.
            raise ToolUseError(
                f"'{fn}' is not a registered tool yet -- call load_tool first "
                f"to register its script, then call '{fn}' again."
            )
        tool = state.registered_tools[fn]
        result = _script_call(state.root, tool.path, arg)
        state.tool_results.append({fn: result})
        return result

    def __call__(self, state:State)->State:
        trace(state, __file__)
        try:
            asked = False
            trace(state, state.candidated_tools)
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
            trace(state, str(e))
            # don't touch state.return_to here -- whoever routed into TOOL_USE
            # (SkillCall, ToolCall, or now Answer) already set it to itself
            # before calling in, and that's still the correct resume point.
            self.set_next(Process.FAIL_RECOVERY)
            return state
