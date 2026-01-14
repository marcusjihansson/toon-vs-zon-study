"""BAML strategy implementation using reference_implementation adapter."""

from typing import Any
from .base import BaseStrategy
from reference_implementation.baml_adapter import BAMLAdapter


class BAMLStrategy(BaseStrategy):
    """BAML-inspired format strategy for structured outputs.

    BAML (BoundaryML) format provides improved rendering of complex/nested
    Pydantic models with compact, human-readable schema representation.
    This strategy uses the BAMLAdapter from reference_implementation.
    """

    def __init__(self):
        super().__init__("baml_adapter", BAMLAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG

        return rag_class(strategy=self, model_name=model_name)
