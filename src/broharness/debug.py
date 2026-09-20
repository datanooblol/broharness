"""Pretty-printing for state.debug -- turns the raw list of LLM responses
(nested dicts, escaped-newline JSON strings) into a readable step-by-step
trace, so you don't have to eyeball the raw structure by hand.
"""
from broharness.codeblock import parse_json_codeblock, CodeBlockError


def _summarize_call(text: str) -> str:
    try:
        parsed = parse_json_codeblock(text)
    except CodeBlockError:
        return f"[free text] {text}"

    tool_use = parsed.get('tool_use', [])
    if not tool_use:
        return "(tool_use: [] -- nothing to do)"
    return "; ".join(
        f"{t.get('name', '?')}({t.get('input', {})})" for t in tool_use
    )


def render_debug(debug: list) -> str:
    """Renders state.debug as one readable line per call: step number, role,
    a parsed summary of the tool_use decision (or the raw text if it wasn't
    valid tool_use JSON), and token usage.
    """
    lines = []
    for i, msg in enumerate(debug, start=1):
        role = msg.get('role', '?')
        text = msg.get('content', [{}])[0].get('text', '')
        usage = msg.get('usage') or {}
        summary = _summarize_call(text)
        usage_str = (
            f"  (in={usage.get('inputTokens', '?')} out={usage.get('outputTokens', '?')})"
            if usage else ""
        )
        lines.append(f"[{i}] {role}: {summary}{usage_str}")
    return "\n".join(lines)


def print_debug(debug: list) -> None:
    print(render_debug(debug))
