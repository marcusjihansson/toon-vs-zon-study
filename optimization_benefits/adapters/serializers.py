"""Serialization methods for different formats to be used as input to RAG systems."""

import json
from typing import Any, List, Dict


def serialize_json(data: Any, compact: bool = False) -> str:
    """Serialize data to JSON format.
    
    Args:
        data: Data to serialize
        compact: If True, use compact JSON (minified)
        
    Returns:
        JSON formatted string
    """
    if compact:
        return json.dumps(data, separators=(",", ":"))
    return json.dumps(data, indent=2)


def serialize_zon(data: Any) -> str:
    """Serialize data to ZON (Zero Overhead Notation) format.
    
    ZON is a compact alternative to JSON that removes unnecessary quotes,
    braces, and commas where context allows. This achieves 35-70% token
    reduction compared to JSON.
    
    Args:
        data: Data to serialize
        
    Returns:
        ZON formatted string
    """
    try:
        from zon import encode as zon_encode
        return zon_encode(data)
    except ImportError:
        # Fallback to compact JSON if zon is not available
        return serialize_json(data, compact=True)


def serialize_toon(data: Any) -> str:
    """Serialize data to TOON (Token-Oriented Object Notation) format.
    
    TOON is designed for token efficiency while maintaining readability.
    It typically achieves 40-50% token reduction compared to JSON.
    
    Args:
        data: Data to serialize
        
    Returns:
        TOON formatted string
    """
    try:
        from toon import encode as toon_encode
        return toon_encode(data)
    except ImportError:
        # Fallback to compact JSON if toon is not available
        return serialize_json(data, compact=True)


def serialize_baml(data: Any) -> str:
    """Serialize data to BAML-inspired format.
    
    BAML (BoundaryML) format uses a compact, tag-based representation
    that is more efficient than JSON while remaining human-readable.
    For input data, we use a simplified compact JSON format with minification.
    
    Args:
        data: Data to serialize
        
    Returns:
        BAML-inspired formatted string
    """
    # BAML is primarily an output format. For input, we use compact JSON
    # as a reasonable approximation for input serialization
    return serialize_json(data, compact=True)


def serialize_combined(data: Any) -> str:
    """Serialize data using a combined/hybrid approach.
    
    The combined strategy uses TOON encoding for maximum efficiency while
    maintaining compatibility with output parsing.
    
    Args:
        data: Data to serialize
        
    Returns:
        Combined format string
    """
    return serialize_toon(data)
