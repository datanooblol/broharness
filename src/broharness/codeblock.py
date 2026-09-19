"""Parses fenced codeblocks out of LLM output.

Built for the skill-call/tool-call contract: the model must respond with
exactly one fenced codeblock and nothing else. Parsing enforces that -- zero
or more than one codeblock is a hard error, not a best-effort guess, matching
the project's "reliability from code, not from trusting the model" approach.
"""
import json
import re
from typing import Any


class CodeBlockError(Exception):
    """Raised when a response doesn't contain exactly one matching codeblock,
    or its content fails to decode."""


class NoCodeBlockError(CodeBlockError):
    """Raised when there's no cleanly-isolated codeblock in the response --
    either no fence at all, or a fence with extra text before/after it. Both
    mean the same thing downstream: the model didn't stick to "nothing but the
    codeblock," usually because it answered (or asked something) in free text
    instead of, or alongside, following the contract. Callers that want to
    treat "gave up on the format" differently from "tried and slipped" should
    catch this before the general CodeBlockError."""


class MultipleCodeBlocksError(CodeBlockError):
    """Raised when more than one matching codeblock was found."""


class CodeBlockParser:
    """Extracts the single fenced codeblock of a given language from LLM
    output. Subclass and override `decode` to parse the extracted text (JSON,
    YAML, ...) -- this base class only finds the fence and enforces there's
    exactly one.
    """

    language: str = ""  # e.g. "json", "yaml" -- "" matches any/untagged fence

    def _pattern(self) -> re.Pattern:
        # Opening fence: the exact language tag, or no tag at all -- a model
        # that forgets ```json and just writes ``` should still be caught.
        # (?![\w]) stops "json" from matching the start of e.g. "```jsonlines".
        tag = rf"(?:{re.escape(self.language)})?(?!\w)" if self.language else r"\w*"
        # Closing fence is optional too: if the model's output got cut off
        # mid-block with no closing ```, take everything to the end instead
        # of failing to match at all.
        return re.compile(rf"```{tag}[ \t]*\r?\n(.*?)(?:```|\Z)", re.DOTALL)

    def extract(self, text: str) -> str:
        matches = list(self._pattern().finditer(text))
        label = f"```{self.language}```" if self.language else "```...```"
        if not matches:
            raise NoCodeBlockError(f"no {label} codeblock found in response")
        if len(matches) > 1:
            raise MultipleCodeBlocksError(f"expected exactly one {label} codeblock, found {len(matches)}")
        match = matches[0]
        before, after = text[:match.start()], text[match.end():]
        if before.strip() or after.strip():
            # a codeblock exists, but it isn't the whole response -- treat
            # the same as no codeblock at all, since whatever's outside the
            # fence (often a real question or answer the model tacked on) is
            # otherwise silently discarded by only ever reading match.group(1)
            raise NoCodeBlockError(
                f"response must contain nothing but the {label} codeblock -- "
                f"found extra text outside it"
            )
        return match.group(1).strip()

    def decode(self, raw: str) -> Any:
        """Override to turn the extracted text into a real value. Default:
        return it unparsed."""
        return raw

    def parse(self, text: str) -> Any:
        return self.decode(self.extract(text))


class JsonCodeBlockParser(CodeBlockParser):
    language = "json"

    def decode(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise CodeBlockError(f"```json``` codeblock isn't valid JSON: {e}") from e


class YamlCodeBlockParser(CodeBlockParser):
    language = "yaml"

    def decode(self, raw: str) -> Any:
        import yaml
        try:
            return yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise CodeBlockError(f"```yaml``` codeblock isn't valid YAML: {e}") from e


def parse_json_codeblock(text: str) -> Any:
    """Extracts and json.loads() the single ```json ...``` codeblock in text.
    Raises CodeBlockError if there isn't exactly one, or it isn't valid JSON.
    """
    return JsonCodeBlockParser().parse(text)
