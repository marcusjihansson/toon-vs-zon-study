"""Combined strategy using JSON↔TOON conversion at LLM boundary.

This strategy implements the pattern described in the TOON documentation:
- JSON is used everywhere in the system (databases, APIs, etc.)
- TOON is used only at the LLM boundary for optimization
- TOON responses are converted back to JSON for internal processing

Flow:
    JSON (everywhere in system)
      ↓
    TOON (conversion at LLM boundary)
      ↓
    LLM processes in TOON format
      ↓
    TOON (output from LLM)
      ↓
    JSON (converted back for rest of system)

Usage:
    from optimization_benefits.strategies import CombinedStrategy

    strategy = CombinedStrategy()
    rag = strategy.create_rag_system()
"""

from typing import Any
from .base import BaseStrategy
from adapters.combined_adapter import CombinedAdapter


class CombinedStrategy(BaseStrategy):
    """Strategy that converts JSON↔TOON at the LLM boundary.

    This is the "optimization layer at the LLM edge" described in the TOON docs.
    It provides:
    - TOON input: Converts JSON data to TOON for LLM processing (token savings)
    - TOON output: Parses TOON responses back to JSON (compatibility)

    This combines the best of both worlds:
    - JSON for internal systems (compatibility, ecosystem support)
    - TOON for LLM communication (token efficiency, cost savings)
    """

    def __init__(self):
        """Initialize the combined strategy."""
        super().__init__("combined", CombinedAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        """Create and return configured RAG system.

        Args:
            model_name: LLM model to use
            rag_class: Optional class to use for RAG system instantiation

        Returns:
            Configured RAG system instance
        """
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG

        return rag_class(strategy=self, model_name=model_name)


class ZONCombinedStrategy(BaseStrategy):
    """CombinedStrategy using ZON format for maximum compression.

    ZON achieves 35-70% token reduction compared to JSON.
    Use this when maximum token savings is the priority.
    """

    def __init__(self):
        from adapters.combined_adapter import ZONCombinedAdapter

        super().__init__("zon_combined", ZONCombinedAdapter())

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        """Create and return configured RAG system.

        Args:
            model_name: LLM model to use
            rag_class: Optional class to use for RAG system instantiation.
                       If None, implementation should use a default.
        """
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG

        return rag_class(strategy=self, model_name=model_name)
