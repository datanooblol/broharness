import yaml
from broskill import Arg, Tool
from pathlib import Path

def pack_arg(arg:Arg)->dict:
    _base = {"type": arg.type}
    if arg.description:
        _base["description"] = arg.description
    return _base

def tool_to_yaml(tool:Tool)->dict:
    fn_metadata = dict(
        name=tool.name,
        description=tool.description,
        parameters={
            "type": "object",
            "properties": {arg.name: pack_arg(arg) for arg in tool.args},
            "required": [arg.name for arg in tool.args if arg.required==True]
        }
    )
    return {"type": "function", "function": fn_metadata}

load_skill_tool = Tool(
    name="load_skill",
    description="Load the full instructions for a registered skill by name. Call this only when the current task clearly matches that skill's description.",
    args=[
        Arg(name="skill_name", type="string", required=True)
    ],
    path=Path()
)

load_skill_extension_tool = Tool(
    name="load_skill_extension",
    description="Load the full contents of one `references/*.md` document belonging to an already-loaded skill. Call this only when that skill's instructions point you to a specific reference/asset file for more detail — don't call it speculatively.",
    args=[
        Arg(name="skill_name", type="string", required=True, description="The name of the skill whose reference/asset you want to load."),
        Arg(name="path", type="string", required=True, description="The `references/*.md` file's path exactly as shown in the skill's instructions, e.g. `references/aws.md` or `assets/color.ts`.")
    ],
    path=Path()
)

load_tool_tool = Tool(
    name="load_tool",
    description="Register a skill's script as a callable tool by loading its schema from scripts/*.py. Call this only when that skill's instructions point you to a specific script for the task at hand — the script becomes available to call by its own name only after this runs, not before.",
    args=[
        Arg(name="skill_name", type="string", required=True, description="The name of the skill whose script you want to register as a tool."),
        Arg(name="path", type="string", required=True, description="The script's path exactly as shown in the skill's instructions, e.g. `scripts/read_file.py`.")
    ],
    path=Path()
)

ask_user_question_tool = Tool(
    name="ask_user_question",
    description="Signal that you need the user to answer something before you can continue. Write the actual question as your normal response content, then call this tool with no arguments to pause the turn and wait for their reply.",
    args=[
        Arg(name='question', type='string', required=True, description='questions you need user to clarify')
    ],
    path=Path()
)
tools = [
   tool_to_yaml(t)
   for t in [
      load_skill_tool,
      load_skill_extension_tool,
      load_tool_tool,
      ask_user_question_tool
   ]
]

# available_tools = yaml.dump(tools, sort_keys=False)