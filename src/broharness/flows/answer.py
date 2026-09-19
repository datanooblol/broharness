from broflow import BaseTask
from broharness.data_model import State, Process
from broharness.llms.bedrock import SystemMessage, AIMessage
from broharness.toolblock import tool_to_yaml, load_skill_tool, ask_user_question_tool
from broharness.codeblock import parse_json_codeblock
import yaml

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's request directly and "
    "concisely. If a skill's instructions are shown above, follow them. If "
    "none are shown, no skill or tool was needed for this request -- answer "
    "using your own general knowledge instead."
)

class Answer(BaseTask):
    possible_next = {Process.END, Process.TOOL_USE}
    def __init__(self, name, llm, system_prompt:str):
        super().__init__(name=name)
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state:State)->State:
        print(__file__)
        try:
            # skill_prompt = "\n".join([f"{p}"  for s, p in state.registered_skills.items()])
            skill_prompt = "\n".join([
                f"Skill name: {s}\n-----\n{p}\n{state.extension_skills.get(s, '')}"
                for s, p in state.registered_skills.items()
            ])
            local_prompt = f"{self.system_prompt}\n{skill_prompt}".strip()
            if not local_prompt:
                # nothing loaded and no caller system_prompt -- Bedrock rejects
                # a blank system field outright, and this is also exactly the
                # "no skill needed, use your own knowledge" case.
                local_prompt = DEFAULT_SYSTEM_PROMPT
            response = self.llm(messages=state.session_messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.ANSWER)
            state.debug.append(response)
            text = response['content'][0]['text'].strip()
            if text.endswith('?'):
                # Answer has no tool-calling contract of its own -- it can
                # still genuinely need to ask something (e.g. ToolCall handed
                # off here with the topic still unknown). Same handling as
                # ToolCall/SkillCall: route through the real ask flow instead
                # of treating a question as the final answer. return_to is
                # ANSWER, not the earlier caller -- once answered, come
                # straight back here rather than re-running the whole
                # skill/tool selection from scratch.
                state.candidated_tools = [{"name": "ask_user_question", "input": {"question": text}}]
                state.return_to = Process.ANSWER
                self.set_next(Process.TOOL_USE)
                return state
            state.messages.append(AIMessage(text))
            state.session_messages.append(AIMessage(text))
            self.set_next(Process.END)
            state.return_to = None
            return state
        except Exception as e:
            state.error_message = str(e)
            print(str(e))
            self.set_next(Process.FAIL_RECOVERY)
            state.return_to = Process.ANSWER
            return state
