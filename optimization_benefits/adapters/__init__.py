"""Adapter implementations used by strategies.

These adapters are DSPy-compatible (subclass DSPy's adapter interfaces).
"""

from .json_adapter import SimpleJSONAdapter
from .zon_adapter import ZONAdapter
from .combined_adapter import CombinedAdapter, TOONCombinedAdapter, ZONCombinedAdapter

__all__ = [
    "SimpleJSONAdapter",
    "ZONAdapter",
    "CombinedAdapter",
    "TOONCombinedAdapter",
    "ZONCombinedAdapter",
]
