"""The one LLM call primitive everything else builds on, plus routing."""
import boto3
from brollm import BaseContract

BEDROCK_REGION = "us-east-1"
BEDROCK_MODEL_ID = "google.gemma-3-4b-it"

_bedrock_client = None


def bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    return _bedrock_client


def call_bedrock(prompt: str) -> str:
    response = bedrock_client().converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    return response["output"]["message"]["content"][0]["text"]


def build_router_prompt(user_request: str, registry: dict) -> str:
    listing = "\n".join(f"- {name}: {info['description']}" for name, info in registry.items())
    return (
        "Given this user request, pick the single best-matching skill by name.\n"
        "Reply with only the skill name, nothing else.\n\n"
        f"Skills:\n{listing}\n\n"
        f"User request: {user_request}"
    )


def _router_input(user_request: str, registry: dict):
    return call_bedrock(build_router_prompt(user_request, registry))


def _router_output(text: str) -> str:
    return text.strip().strip("`").strip()


router = BaseContract(input_fn=_router_input, output_fn=_router_output)
