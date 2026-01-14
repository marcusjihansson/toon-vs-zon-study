"""JSON adapter for DSPy structured outputs.

The project originally had a minimal adapter with only a `parse()` method.
DSPy adapters must implement the `dspy.adapters.base.Adapter` interface (they are
invoked via `adapter.__call__()` and rely on `format()`/`parse()` methods).

This adapter subclasses DSPy's built-in `JSONAdapter` and adds a small amount of
robustness for common markdown code-fence wrappers.
"""

from __future__ import annotations

from typing import Any

from dspy.adapters.json_adapter import JSONAdapter


def _strip_markdown_code_fences(text: str) -> str:
    """Remove common markdown code-fence wrappers.

    DSPy/OpenRouter responses sometimes include ```json ...``` or generic ``` ...```.
    The built-in JSONAdapter already tries to locate JSON objects in text, but
    stripping fences reduces noise and improves repair success.
    """

    if not isinstance(text, str):
        return str(text)

    completion = text.strip()

    # Prefer typed fences first
    for fence in ("```json", "```JSON"):
        if fence in completion:
            return completion.split(fence, 1)[1].split("```", 1)[0].strip()

    if "```" in completion:
        # Take the first fenced block.
        return completion.split("```", 1)[1].split("```", 1)[0].strip()

    return completion


class SimpleJSONAdapter(JSONAdapter):
    """DSPy-compatible JSON adapter used by the baseline and JSON strategies."""

    def parse(self, signature: Any, completion: str):  # type: ignore[override]
        return super().parse(signature, _strip_markdown_code_fences(completion))
