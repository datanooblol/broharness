from broflow import BaseTask
from broharness.data_model import State, Process, record_usage, render_tool_results
from broharness.llms.bedrock import SystemMessage, AIMessage
from broharness.toolblock import tool_to_yaml, load_skill_tool, ask_user_question_tool
from broharness.codeblock import parse_json_codeblock
import yaml

# Always present, not just a fallback -- a loaded skill's Instructions/Errors
# sections are written for a task that calls tools (ToolCall), and without
# this Answer can start imitating that (writing fake tool calls / pseudocode)
# instead of just answering, since it's the only role with zero tool-calling
# ability of its own.
ANSWER_SYSTEM_PROMPT = (
    "You are giving the user their final answer, in plain natural language. "
    "You cannot call tools or run code here, and nothing you write as code "
    "will execute -- never write code or pseudocode describing how you would "
    "fetch something. If tool results are shown below under 'Tool Use and "
    "Result', use that content directly to answer; don't re-describe how it "
    "was obtained. If no skill or tool result is shown, no skill was needed "
    "for this request -- answer using your own general knowledge instead. "
    "Never state a specific fact, file content, or value unless it actually "
    "appears in what's shown below -- if the exact thing the user asked for "
    "isn't present (e.g. an error is shown instead of the content, or nothing "
    "relevant was fetched at all), say plainly that it couldn't be retrieved "
    "and why, instead of inventing a plausible-sounding answer."
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
            local_prompt = ANSWER_SYSTEM_PROMPT
            if self.system_prompt:
                local_prompt = f"{local_prompt}\n{self.system_prompt}"
            if skill_prompt:
                local_prompt = f"{local_prompt}\n{skill_prompt}"
            if state.tool_results:
                # without this, Answer only ever sees a skill's static
                # instructions -- never what a script actually returned, so
                # it has no way to answer with real fetched content and can
                # end up hallucinating a fake tool call instead.
                local_prompt = f"{local_prompt}\n## Tool Use and Result:\n{render_tool_results(state.tool_results)}"
            if state.error_message:
                # set when FailRecovery gives up and falls through here with
                # the underlying task still unresolved -- without this, Answer
                # has no way to know the thing it's being asked about was
                # never actually fetched, and can confidently make something
                # up instead of saying so.
                local_prompt = f"{local_prompt}\n## Last Error (task did not complete):\n{state.error_message}"
                state.error_message = ''
            response = self.llm(messages=state.session_messages, system_prompt=SystemMessage(local_prompt), modelId=state.model_id.ANSWER)
            state.debug.append(response)
            record_usage(state, "ANSWER", state.model_id.ANSWER, response)
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
