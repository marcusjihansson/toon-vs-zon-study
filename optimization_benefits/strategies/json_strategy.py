"""JSON-based strategy implementations."""

from typing import Any
from .base import BaseStrategy
from adapters.json_adapter import SimpleJSONAdapter


class BaselineStrategy(BaseStrategy):
    """Current hybrid approach: native TOON for inputs, JSON for outputs.

    This is the baseline strategy that uses JSON for output parsing.
    """

    def __init__(self):
        super().__init__("baseline", SimpleJSONAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG
        
        return rag_class(strategy=self, model_name=model_name)


class JSONStrategy(BaseStrategy):
    """Pure JSON strategy (baseline for comparison).

    Uses JSON for all parsing operations.
    """

    def __init__(self):
        super().__init__("json_baseline", SimpleJSONAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG
        
        return rag_class(strategy=self, model_name=model_name)
