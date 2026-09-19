import boto3
from typing import Any
from functools import partial
from brollm import BaseContract

model = boto3.client('bedrock-runtime', region_name='us-east-1')

def UserMessage(text:str): return {'role': 'user', 'content': [{'text': text}]}
def AIMessage(text:str): return {'role': 'assistant', 'content': [{'text': text}]}
def SystemMessage(text:str): return [{"text": text}]

def input_fn(
        messages:list[Any],
        system_prompt:Any|None=None,
        modelId:str|None=None,
)->Any:
    kwargs = {
        "modelId": modelId,
        "messages": messages,
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    return model.converse(**kwargs)

def output_fn(response:Any)->Any:
    message = response['output']['message']
    message['usage'] = response.get('usage', {})
    return message
    
bedrock = BaseContract(input_fn=input_fn, output_fn=output_fn)