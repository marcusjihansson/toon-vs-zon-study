"""Strict ZON Adapter for DSPy.

This is intentionally *strict*: it expects the model to output valid ZON and will
raise `AdapterParseError` if it cannot parse ZON or if required output fields are
missing.

Rationale:
- The project uses this adapter to benchmark ZON formatting compliance and
  token/latency tradeoffs.
- Unlike the TOON adapter reference implementation, this adapter does NOT fall
  back to JSON parsing.

If you want a resilient "ZON-or-JSON" adapter, implement it as a separate
strategy (similar to the CombinedAdapter approach).
"""

from __future__ import annotations

import inspect
import logging
import re
import types
from typing import Any, Literal, Union, get_args, get_origin

from dspy.adapters.base import Adapter  # type: ignore[import-untyped]
from dspy.adapters.types import History  # type: ignore[import-untyped]
from dspy.signatures.signature import Signature  # type: ignore[import-untyped]
from dspy.utils.callback import BaseCallback  # type: ignore[import-untyped]
from dspy.utils.exceptions import AdapterParseError  # type: ignore[import-untyped]
from pydantic import BaseModel

try:
    from zon import decode as zon_decode, encode as zon_encode

    _ZON_AVAILABLE = True
except ImportError:  # pragma: no cover
    zon_decode = None
    zon_encode = None
    _ZON_AVAILABLE = False

logger = logging.getLogger(__name__)

COMMENT_SYMBOL = "#"


def _extract_zon_content(text: str) -> str:
    """Extract ZON content from text.
    
    ZON format doesn't use top-level braces, so we extract the entire content
    or just the field assignments without surrounding braces.
    """
    text = text.strip()
    
    # If text starts with a field assignment, return as-is
    for field_name in ["reasoning", "response"]:
        if re.match(rf"^\s*{re.escape(field_name)}\s*:", text):
            return text
    
    # If text is wrapped in braces, extract content without outer braces
    if text.startswith("{") and text.endswith("}"):
        # Extract content between braces, handling nested braces
        content = text[1:-1].strip()
        return content
    
    return text


def _render_type_str(annotation: Any, depth: int = 0) -> str:
    """Render a Python annotation into a short schema type string."""
    if annotation is str:
        return "string"
    if annotation is int:
        return "int"
    if annotation is float:
        return "float"
    if annotation is bool:
        return "boolean"

    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        if depth == 0:
            # For top-level models, render full schema
            return _render_model_schema(annotation)
        return annotation.__name__

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (types.UnionType, Union):
        non_none_args = [a for a in args if a is not type(None)]
        parts = [_render_type_str(a, depth) for a in non_none_args]
        if len(non_none_args) < len(args):
            parts.append("null")
        return " | ".join(parts) if parts else "any"

    if origin is Literal:
        return " | ".join(str(a) for a in args)

    if origin is list:
        inner = _render_type_str(args[0], depth + 1) if args else "any"
        return f"list[{inner}]"

    if origin is dict:
        k = _render_type_str(args[0], depth + 1) if args else "any"
        v = _render_type_str(args[1], depth + 1) if len(args) > 1 else "any"
        return f"dict[{k},{v}]"

    return getattr(annotation, "__name__", str(annotation))


def _render_model_schema(model_class: type[BaseModel]) -> str:
    """Render a Pydantic model's full schema structure."""
    lines = ["{"]
    for field_name, field_info in model_class.model_fields.items():
        field_type = _render_type_str(field_info.annotation, depth=1)
        desc = f" - {field_info.description}" if field_info.description else ""
        lines.append(f"  {field_name}: {field_type}{desc}")
    lines.append("}")
    return "\n".join(lines)


def _encode_value(value: Any) -> str:
    """Encode a value to a ZON string for prompting."""
    if not _ZON_AVAILABLE or zon_encode is None:
        return str(value)

    if isinstance(value, BaseModel):
        return zon_encode(value.model_dump())
    if isinstance(value, (dict, list)):
        return zon_encode(value)

    return str(value)


class ZONAdapter(Adapter):
    """DSPy adapter using ZON (Zero Overhead Notation) for outputs."""

    def __init__(
        self,
        callbacks: list[BaseCallback] | None = None,
        use_native_function_calling: bool = False,
    ):
        # Do not raise at import/strategy creation time. Some environments (e.g., CI)
        # may not have optional deps installed. We remain *strict* at runtime: any
        # attempt to format/parse ZON without the dependency will raise.
        super().__init__(
            callbacks=callbacks,
            use_native_function_calling=use_native_function_calling,
        )

    # ------------------------ Formatting ------------------------

    def format_task_description(self, signature: type[Signature]) -> str:
        return signature.__doc__ or "Complete the task based on the inputs."

    def format_field_description(self, signature: type[Signature]) -> str:
        sections: list[str] = []

        if signature.input_fields:
            sections.append("Input fields:")
            for name, field in signature.input_fields.items():
                desc = f" - {field.description}" if field.description else ""
                sections.append(f"  {name}: {_render_type_str(field.annotation)}{desc}")

        if signature.output_fields:
            sections.append("\nOutput fields:")
            for name, field in signature.output_fields.items():
                desc = f" - {field.description}" if field.description else ""
                sections.append(f"  {name}: {_render_type_str(field.annotation)}{desc}")

        return "\n".join(sections)

    def format_field_structure(self, signature: type[Signature]) -> str:
        sections: list[str] = []
        sections.append(
            """
ZON Format (NOT JSON):
- Output MUST be valid ZON
- Return field assignments at top level (NO braces around entire output)
- Keys should match output field names exactly
- No markdown code fences
- Use braces only for nested objects/arrays
""".strip()
        )

        sections.append("\nOutput structure (types):")
        for name, field in signature.output_fields.items():
            # Render full schema for complex types
            type_str = _render_type_str(field.annotation, depth=0)
            sections.append(f"{COMMENT_SYMBOL} {name}: {type_str}")

        sections.append(
            "\nExample (illustrative only; match the schema above):\n"
            "reasoning: \"...\"\nresponse: { answer: \"...\", recommendations: [], total_products_reviewed: 0 }"
        )

        return "\n".join(sections)

    def format_user_message_content(
        self,
        signature: type[Signature],
        inputs: dict[str, Any],
        prefix: str = "",
        suffix: str = "",
        main_request: bool = False,
    ) -> str:
        parts: list[str] = []
        if prefix:
            parts.append(prefix)

        for name in signature.input_fields.keys():
            if name in inputs:
                value = inputs[name]
                encoded = _encode_value(value)
                if "\n" in encoded or isinstance(value, (BaseModel, list, dict)):
                    parts.append(f"{name}:\n{encoded}")
                else:
                    parts.append(f"{name}: {encoded}")

        if main_request:
            parts.append("\nProvide output in strict ZON format as specified above. Each field on its own line.")

        if suffix:
            parts.append(suffix)

        return "\n\n".join(parts).strip()

    def format_assistant_message_content(
        self,
        signature: type[Signature],
        outputs: dict[str, Any],
        missing_field_message: str | None = None,
    ) -> str:
        # Primarily used for few-shot demos.
        out: dict[str, Any] = {}
        for name in signature.output_fields.keys():
            value = outputs.get(name, missing_field_message)
            if value is None:
                continue
            if isinstance(value, BaseModel):
                out[name] = value.model_dump()
            else:
                out[name] = value

        if not _ZON_AVAILABLE or zon_encode is None:
            raise RuntimeError(
                "ZONAdapter requires `zon-format` to encode outputs for demos. "
                "Install it with: pip install zon-format"
            )

        # Encode entire output object as ZON.
        return zon_encode(out)  # type: ignore[misc]

    def format_conversation_history(
        self,
        signature: type[Signature],
        history_field_name: str,
        inputs: dict[str, Any],
    ) -> list[dict[str, Any]]:
        history_value = inputs.get(history_field_name)

        if history_value is None:
            if history_field_name in inputs:
                del inputs[history_field_name]
            return []

        if hasattr(history_value, "messages"):
            conversation_history = history_value.messages
        elif isinstance(history_value, list):
            conversation_history = history_value
        else:
            logger.warning(
                f"Unexpected history format for field '{history_field_name}': {type(history_value)}"
            )
            del inputs[history_field_name]
            return []

        messages: list[dict[str, Any]] = []
        for message in conversation_history:
            if isinstance(message, dict):
                if "user" in message:
                    messages.append({"role": "user", "content": str(message["user"])})
                if "assistant" in message:
                    messages.append({"role": "assistant", "content": str(message["assistant"])})
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": self.format_user_message_content(signature, message),
                    }
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": self.format_assistant_message_content(signature, message),
                    }
                )

        del inputs[history_field_name]
        return messages

    def _get_history_field_name(self, signature: type[Signature]) -> str | None:
        for name, field in signature.input_fields.items():
            if field.annotation == History:
                return name
        return None

    # ------------------------ Parsing ------------------------

    def parse(self, signature: type[Signature], completion: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        completion = (completion or "").strip()

        debug: dict[str, Any] = {
            "completion_preview": completion[:500],
            "output_fields": list(signature.output_fields.keys()),
            "scalar_extracted": {},
        }

        # First try: extract *scalar* field values from `field: value` lines.
        # (For objects/arrays we rely on full ZON decoding.)
        for field_name, field in signature.output_fields.items():
            value = self._extract_field_value(completion, field_name)
            if value is not None:
                debug["scalar_extracted"][field_name] = True
                result[field_name] = self.convert_field(value, field.annotation)
                debug[f"scalar_{field_name}"] = repr(value)
            else:
                debug["scalar_extracted"][field_name] = False

        # If we got all fields from scalar extraction, return early
        if result.keys() == signature.output_fields.keys():
            return result

        if not _ZON_AVAILABLE or zon_decode is None:
            raise AdapterParseError(
                adapter_name="ZONAdapter",
                signature=signature,
                lm_response=completion,
                message=(
                    "ZONAdapter requires `zon-format` to decode outputs. "
                    "Install it with: pip install zon-format"
                ),
                parsed_result=result,
            )

        # Second try: decode a top-level braced object extracted from the completion.
        # This keeps the adapter strict (must be ZON) but more robust to accidental prose.
        candidate = _extract_zon_content(completion) or completion
        debug["decoded_candidate_preview"] = candidate[:500]

        try:
            parsed = zon_decode(candidate)  # type: ignore[misc]
            debug["zon_decode_type"] = type(parsed).__name__
            if isinstance(parsed, dict):
                # Extract top-level fields from the decoded dict
                for field_name, field in signature.output_fields.items():
                    if field_name in parsed:
                        raw_value = parsed[field_name]
                        converted_value = self.convert_field(raw_value, field.annotation)
                        result[field_name] = converted_value
                        debug["scalar_extracted"][field_name] = True
                        debug[f"raw_{field_name}"] = repr(raw_value)
                        debug[f"converted_{field_name}"] = repr(converted_value)
        except Exception as e:
            debug["zon_decode_error"] = repr(e)
            logger.debug("ZONAdapter decode failed", extra={"debug": debug})

        if result.keys() != signature.output_fields.keys():
            missing = [k for k in signature.output_fields.keys() if k not in result]
            raise AdapterParseError(
                adapter_name="ZONAdapter",
                signature=signature,
                lm_response=completion,
                message=(
                    "Failed to parse strict ZON output. "
                    f"Missing fields: {missing}. "
                    "If the model included prose, ensure output is a single top-level ZON object. "
                    f"Debug: {debug}"
                ),
                parsed_result=result,
            )

        return result

    def _extract_field_value(self, completion: str, field_name: str) -> Any | None:
        """Try to extract a top-level field using a simple pattern.

        This is best-effort; ZON is not line-based, but in practice LMs often emit
        `field: <value>` on its own line.
        """

        # Match `field_name: <rest of line>` - more flexible pattern
        pattern = rf"^\s*{re.escape(field_name)}\s*:\s*(.+)$"
        m = re.search(pattern, completion, re.MULTILINE)
        if not m:
            return None

        value_str = m.group(1).strip()
        # If value appears to start an object/array, let full decode handle it.
        if value_str.startswith("{") or value_str.startswith("["):
            return None

        # Try decoding scalar value.
        try:
            decoded = zon_decode(value_str)  # type: ignore[misc]
            # Only return if decoded is actually a scalar
            if not isinstance(decoded, (dict, list)):
                return decoded
        except Exception:
            pass
        return value_str

    def convert_field(self, value: Any, field_type: Any) -> Any:
        # For primitive types, return as-is if already correct type
        if field_type in (str, int, float, bool):
            if isinstance(value, field_type):
                return value
            # Try basic conversion for primitives
            try:
                if field_type is str:
                    return str(value)
                elif field_type is int:
                    return int(value)
                elif field_type is float:
                    return float(value)
                elif field_type is bool:
                    return bool(value)
            except (ValueError, TypeError):
                return value
        
        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin in (types.UnionType, Union):
            non_none_args = [a for a in args if a is not type(None)]
            try:
                return self.convert_field(value, non_none_args[0])
            except Exception:
                # Fallback: return value as-is if conversion fails
                return value

        if origin is list and args:
            inner = args[0]
            if inspect.isclass(inner) and issubclass(inner, BaseModel):
                if isinstance(value, list):
                    converted = []
                    for v in value:
                        try:
                            if isinstance(v, dict):
                                converted.append(inner.model_validate(v))
                            else:
                                converted.append(v)
                        except Exception:
                            # Skip invalid items or keep as-is
                            converted.append(v)
                    return converted

        if inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            if isinstance(value, dict):
                try:
                    return field_type.model_validate(value)
                except Exception:
                    # Return raw dict if validation fails
                    return value

        return value

        if origin is list and args:
            inner = args[0]
            if inspect.isclass(inner) and issubclass(inner, BaseModel):
                if isinstance(value, list):
                    converted = []
                    for v in value:
                        try:
                            if isinstance(v, dict):
                                converted.append(inner.model_validate(v))
                            else:
                                converted.append(v)
                        except Exception:
                            # Skip invalid items or keep as-is
                            converted.append(v)
                    return converted

        if inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            if isinstance(value, dict):
                try:
                    return field_type.model_validate(value)
                except Exception:
                    # Return raw dict if validation fails
                    return value

        return value
