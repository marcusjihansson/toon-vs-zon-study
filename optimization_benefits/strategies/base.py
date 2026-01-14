"""Base strategy class for RAG strategies."""

from typing import Any


class BaseStrategy:
    """Base class for RAG strategies.

    All strategy implementations should inherit from this class
    and implement the create_rag_system method.
    """

    def __init__(self, name: str, adapter: Any):
        """Initialize the strategy.

        Args:
            name: Unique identifier for this strategy
            adapter: DSPy adapter instance for output parsing
        """
        self.name = name
        self.adapter = adapter

    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None) -> Any:
        """Create and return configured RAG system.

        Args:
            model_name: LLM model to use
            rag_class: Optional class to use for RAG system instantiation. 
                       If None, implementation should use a default.

        Returns:
            Configured RAG system instance
        """
        raise NotImplementedError
