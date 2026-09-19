from broflow import BaseTask
from broharness.data_model import State, Process, all_already_executed, record_usage
from broharness.llms.bedrock import SystemMessage
from broharness.toolblock import tool_to_yaml, ask_user_question_tool, load_skill_extension_tool, load_tool_tool
from broharness.codeblock import parse_json_codeblock, NoCodeBlockError
import yaml

class ToolCall(BaseTask):
    possible_next = {Process.ANSWER, Process.FAIL_RECOVERY, Process.ASK_USER_QUESTION}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            skill_prompt = "\n".join([
                f"Skill name: {s}\n-----\n{p}\n{state.extension_skills.get(s, '')}"
                for s, p in state.registered_skills.items()
            ])
            tool_prompt = state.skill_control.load_skill('tool-call')
            available_tools = [
                tool_to_yaml(t) 
                for t in state.registered_tools.values() if t.name not in ['load_skill_tool']
            ]
            available_tools = f"## Availale Tools:\n{yaml.dump(available_tools, sort_keys=False)}"
            local_prompt = f"{self.system_prompt}\n{skill_prompt}\n{tool_prompt}\n{available_tools}"
            if state.error_message:
                local_prompt = f"{local_prompt}\n## Error Message:\n{state.error_message}"
            state.error_message = ''
            if state.tool_results:
                tool_results = "\n".join([f"\t- {t}" for t in state.tool_results])
                local_prompt = f"{local_prompt}\n## Tool Use and Result:\n{tool_results}"
            response = self.llm(messages=state.session_messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.XXX_CALL)
            state.debug.append(response)
            record_usage(state, "XXX_CALL", state.model_id.XXX_CALL, response)
            candidated_tools = parse_json_codeblock(response['content'][0]['text']).get('tool_use', [])
            state.candidated_tools = candidated_tools
            if not candidated_tools:
                self.set_next(Process.ANSWER)
                return state
            if all_already_executed(candidated_tools, state.executed_calls):
                # model asked for nothing it doesn't already have -- treat as
                # done rather than re-running (or re-asking it to reconsider).
                self.set_next(Process.ANSWER)
                return state
            self.set_next(Process.TOOL_USE)
            state.return_to = Process.TOOL_CALL
            return state
        except NoCodeBlockError:
            # model answered in free text instead of the tool_use contract.
            # A model can be stubborn about this even after being told to
            # reformat (observed: 3 corrective retries, still plain text
            # every time) -- so don't gamble another retry on a question that
            # reads like a question. Text ending in "?" is almost certainly a
            # dropped ask_user_question call; route it into the real ask flow
            # directly instead of letting it get silently treated as a final
            # answer.
            text = response['content'][0]['text'].strip()
            if text.endswith('?'):
                # wrap it in the same shape a real tool_use call would have,
                # so it flows through ToolUse (and executed_calls bookkeeping)
                # exactly like any other tool call, not a special-cased path.
                state.candidated_tools = [{"name": "ask_user_question", "input": {"question": text}}]
                self.set_next(Process.TOOL_USE)
                state.return_to = Process.TOOL_CALL
                return state
            # otherwise, likely a genuine "I'm done" case -- bounded
            # corrective retry, falling through to Answer if it never
            # reformats (FailRecovery's own exhausted-retries fallback).
            state.error_message = (
                "Your last response wasn't in the required JSON tool_use format. "
                "If you have nothing left to do, respond with {\"tool_use\": []}. "
                "If you need to ask the user something, use the ask_user_question "
                "tool instead of asking in plain text."
            )
            state.return_to = Process.TOOL_CALL
            self.set_next(Process.FAIL_RECOVERY)
            return state
        except Exception as e:
            state.error_message = str(e)
            print(str(e))
            state.return_to = Process.TOOL_CALL
            self.set_next(Process.FAIL_RECOVERY)
            return state
