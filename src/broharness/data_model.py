from enum import StrEnum
from dataclasses import dataclass, field
from broskill import SkillControl, ToolControl
from typing import Any

class Process(StrEnum):
    SKILL_CALL = 'skill_call'
    TOOL_CALL = 'tool_call'
    TOOL_USE = 'tool_use'
    ASK_USER_QUESTION = 'ask_user_question'
    FAIL_RECOVERY = 'fail_recovery'
    ANSWER = 'answer'
    END = 'end'

@dataclass
class LLMUse:
    XXX_CALL:str = 'google.gemma-3-12b-it'
    REASONING:str = 'google.gemma-3-12b-it'
    ANSWER:str = 'google.gemma-3-12b-it'

@dataclass
class State:
    messages:list
    skill_control:SkillControl
    tool_control:ToolControl
    system_prompt:str = ''
    registered_skills:dict[str, Any] = field(default_factory=dict)
    tool_calls:dict[str, Any] = field(default_factory=dict)
    tool_uses:dict[str, Any] = field(default_factory=dict)
    error_message:str = ''
    return_to:Process|None = None
    debug:list = field(default_factory=list)
    model_id:LLMUse = field(default_factory=LLMUse)
    retry_count:int = 0
    max_retries:int = 3