"""Combined adapter for JSON↔TOON conversion at the LLM boundary.

This adapter implements the "optimization layer at the LLM edge" pattern:
- Inputs: render complex values (dict/list/Pydantic models) in TOON (or ZON)
  for token efficiency.
- Outputs: parse TOON (or ZON) back into Python values and let DSPy cast them
  into the expected output field types.

Important: DSPy adapters must subclass `dspy.adapters.base.Adapter`.
We subclass DSPy's `JSONAdapter` to reuse its formatting pipeline and type
casting; we override formatting and parsing to support TOON/ZON.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Dict

from dspy.adapters.json_adapter import JSONAdapter
from dspy.adapters.utils import parse_value
from dspy.utils.exceptions import AdapterParseError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

try:
    from toon import encode as toon_encode, decode as toon_decode

    _TOON_AVAILABLE = True
except ImportError:  # pragma: no cover
    toon_encode = None
    toon_decode = None
    _TOON_AVAILABLE = False

try:
    from zon import encode as zon_encode, decode as zon_decode

    _ZON_AVAILABLE = True
except ImportError:  # pragma: no cover
    zon_encode = None
    zon_decode = None
    _ZON_AVAILABLE = False

from .json_adapter import _strip_markdown_code_fences


class CombinedAdapter(JSONAdapter):
    """Adapter that uses TOON at the boundary while keeping structured parsing."""

    def __init__(self, use_zon: bool = False, **kwargs: Any):
        super().__init__(**kwargs)
        self.use_zon = use_zon

        if not _TOON_AVAILABLE:
            raise ImportError(
                "toon package is required for CombinedAdapter. Install it with: pip install toon"
            )
        if self.use_zon and not _ZON_AVAILABLE:
            raise ImportError(
                "zon-format package is required for ZON mode. Install it with: pip install zon-format"
            )

    # ------------------------ Formatting ------------------------

    def format_field_structure(self, signature):  # type: ignore[override]
        base = super().format_field_structure(signature)
        fmt = "ZON" if self.use_zon else "TOON"
        return (
            base
            + f"\n\nIMPORTANT: Output MUST be valid {fmt} (not JSON). "
            "Return a single top-level object with exactly the output fields.\n"
        )

    def _format_value(self, value: Any) -> str:
        if isinstance(value, BaseModel):
            value = value.model_dump()

        if isinstance(value, (dict, list)):
            if self.use_zon:
                # zon_encode is only None if missing dependency, guarded in __init__.
                return zon_encode(value)  # type: ignore[misc]
            return toon_encode(value)  # type: ignore[misc]

        return str(value)

    def format_user_message_content(
        self,
        signature,
        inputs,
        prefix: str = "",
        suffix: str = "",
        main_request: bool = False,
    ) -> str:  # type: ignore[override]
        # Similar to ToonAdapter: print each input field as `name: value` or `name:\n<multiline>`.
        parts = []
        if prefix:
            parts.append(prefix)

        for name in signature.input_fields.keys():
            if name in inputs:
                formatted = self._format_value(inputs[name])
                if "\n" in formatted:
                    parts.append(f"{name}:\n{formatted}")
                else:
                    parts.append(f"{name}: {formatted}")

        if main_request:
            fmt = "ZON" if self.use_zon else "TOON"
            parts.append(f"\nProvide the output in {fmt} format.")

        if suffix:
            parts.append(suffix)

        return "\n\n".join(parts).strip()

    # ------------------------ Parsing ------------------------

    def _try_parse_as_json(self, completion: str) -> Dict[str, Any] | None:
        """Try to parse completion as JSON.
        
        Returns the parsed dict if successful, None otherwise.
        Handles common JSON variations (quoted keys, with/without code fences).
        """
        import json as json_module
        
        text = _strip_markdown_code_fences(completion)
        
        # Try direct JSON parsing first
        try:
            return json_module.loads(text)
        except Exception:
            pass
        
        # Try to extract JSON from text
        text = text.strip()
        
        # Look for JSON in code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            return json_module.loads(text)
        except Exception:
            return None
    
    def parse(self, signature: Any, completion: str) -> Dict[str, Any]:  # type: ignore[override]
        original_completion = completion
        completion = _strip_markdown_code_fences(completion)

        # Try ZON first if configured.
        if self.use_zon and _ZON_AVAILABLE and zon_decode is not None:
            try:
                decoded = zon_decode(completion)
                if isinstance(decoded, dict):
                    # Check if ZON produced a flat dict with quoted keys (JSON-like)
                    # This means the LLM output JSON, not ZON
                    has_quoted_keys = any(k.startswith('"') and k.endswith('"') for k in decoded.keys())
                    has_flat_nested = 'answer' in decoded and 'recommendations' in decoded
                    
                    if has_quoted_keys and has_flat_nested:
                        # LLM output JSON, parse as JSON instead
                        json_parsed = self._try_parse_as_json(original_completion)
                        if json_parsed and isinstance(json_parsed, dict):
                            return self._cast_and_validate(signature, json_parsed, original_completion)
                    
                    return self._cast_and_validate(signature, decoded, completion)
            except AdapterParseError:
                raise
            except Exception:
                pass

        # Try TOON.
        if _TOON_AVAILABLE and toon_decode is not None:
            try:
                decoded = toon_decode(completion)
                if isinstance(decoded, dict):
                    return self._cast_and_validate(signature, decoded, completion)
            except AdapterParseError:
                raise
            except Exception:
                pass

        # Fall back to JSON parsing (sometimes models ignore instructions).
        json_parsed = self._try_parse_as_json(original_completion)
        if json_parsed:
            return self._cast_and_validate(signature, json_parsed, original_completion)
        
        return super().parse(signature, completion)

    @staticmethod
    def _normalize_dict_keys(d: Any) -> Any:
        """Normalize dict keys by stripping quotes from ZON-decoded JSON.
        
        When ZON decoder parses JSON-like content, it may include quotes in keys.
        This method strips those quotes recursively.
        """
        if isinstance(d, dict):
            return {k.strip('"'): CombinedAdapter._normalize_dict_keys(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [CombinedAdapter._normalize_dict_keys(item) for item in d]
        return d
    
    def _cast_and_validate(self, signature: Any, decoded: Dict[str, Any], raw: str) -> Dict[str, Any]:
        """Cast and validate parsed fields against signature output fields.
        
        Handles nested Pydantic models by recursively validating them.
        Also handles ZON-decoded JSON responses with quoted keys.
        """
        # Normalize dict keys (handles ZON-decoded JSON with quoted keys)
        decoded = self._normalize_dict_keys(decoded)
        
        fields = {}
        
        for field_name, field_info in signature.output_fields.items():
            if field_name not in decoded:
                continue
                
            value = decoded[field_name]
            
            # Handle nested Pydantic models (like RAGResponse)
            if isinstance(value, dict):
                # Check if this matches an expected Pydantic model type
                annotation = field_info.annotation
                origin = getattr(annotation, '__origin__', None)
                args = getattr(annotation, '__args__', ())
                
                # Check if it's a List of Pydantic models
                if origin is list and args:
                    inner_type = args[0]
                    if inspect.isclass(inner_type) and issubclass(inner_type, BaseModel):
                        # Parse list of Pydantic models
                        if isinstance(value, list):
                            try:
                                fields[field_name] = [inner_type.model_validate(item) if isinstance(item, dict) else item for item in value]
                                continue
                            except Exception as e:
                                logger.debug(f"Failed to parse list of {inner_type.__name__}: {e}")
                
                # Check if it's a single Pydantic model
                if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                    try:
                        fields[field_name] = annotation.model_validate(value)
                        continue
                    except Exception as e:
                        logger.debug(f"Failed to validate {field_name} as {annotation.__name__}: {e}")
            
            # Fall back to regular parsing
            fields[field_name] = parse_value(value, field_info.annotation)
        
        if fields.keys() != signature.output_fields.keys():
            raise AdapterParseError(
                adapter_name="CombinedAdapter",
                signature=signature,
                lm_response=raw,
                parsed_result=str(fields),
            )
        return fields


class TOONCombinedAdapter(CombinedAdapter):
    """CombinedAdapter using TOON format (default)."""

    def __init__(self, **kwargs: Any):
        super().__init__(use_zon=False, **kwargs)


class ZONCombinedAdapter(CombinedAdapter):
    """CombinedAdapter using ZON format for maximum compression."""

    def __init__(self, **kwargs: Any):
        super().__init__(use_zon=True, **kwargs)
