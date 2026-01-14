"""TOON strategy implementation using reference_implementation adapter."""

from typing import Any
from .base import BaseStrategy
from reference_implementation.adapter import ToonAdapter


class ToonStrategy(BaseStrategy):
    """TOON format strategy using the official dspy-toon adapter.

    TOON (Token-Oriented Object Notation) achieves significant token reduction
    compared to JSON while maintaining readability. This strategy uses the
    official ToonAdapter from dspy-toon for both input and output handling.
    """

    def __init__(self):
        super().__init__("toon_adapter", ToonAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG

        return rag_class(strategy=self, model_name=model_name)
