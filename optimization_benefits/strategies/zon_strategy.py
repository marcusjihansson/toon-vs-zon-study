"""ZON format strategy implementation."""

from typing import Any
from .base import BaseStrategy
from adapters.zon_adapter import ZONAdapter


class ZONStrategy(BaseStrategy):
    """ZON format strategy for maximum token efficiency.

    ZON (Zero Overhead Notation) achieves 35-70% token reduction
    compared to JSON while maintaining 100% data fidelity.
    """

    def __init__(self):
        super().__init__("zon_adapter", ZONAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG

        return rag_class(strategy=self, model_name=model_name)
