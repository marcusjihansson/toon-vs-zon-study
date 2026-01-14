"""Strict versions of TOON and ZON strategies for research purposes.

This module contains strict implementations that disable JSON fallback
to test how formats perform when LLM must output valid format
without any fallback mechanism.

Research documented in docs/hypothesis.md
"""

from typing import Any

from .base import BaseStrategy
from reference_implementation.adapter import ToonAdapter
from adapters.zon_adapter import ZONAdapter


class ToonStrictStrategy(BaseStrategy):
    """Strict TOON strategy with no JSON fallback.
    
    This tests TOON in its pure form - if LLM outputs invalid TOON,
    request will fail rather than falling back to JSON parsing.
    
    Expected behavior:
    - Input: Same token efficiency as regular TOON (~38% reduction)
    - Output: Only parses valid TOON, no fallback to JSON
    - Success rate: Likely lower than combined strategy
    - Purpose: Isolate TOON's standalone performance
    """
    
    def __init__(self):
        super().__init__("toon_strict", ToonAdapter())
    
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


class ZONStrictStrategy(BaseStrategy):
    """Strict ZON strategy with no JSON fallback.
    
    This tests ZON in its pure form - if LLM outputs invalid ZON,
    request will fail rather than falling back to JSON parsing.
    
    Expected behavior:
    - Input: Same token efficiency as regular ZON (~37% reduction)
    - Output: Only parses valid ZON, no fallback to JSON
    - Success rate: Likely lower than combined strategy
    - Purpose: Isolate ZON's standalone performance
    """
    
    def __init__(self):
        super().__init__("zon_strict", ZONAdapter())
    
    def create_rag_system(self, model_name: str = "openrouter/openai/gpt-4o-mini", rag_class: Any = None):
        """Create and return configured RAG system.

        Args:
            model_name: LLM model to use
            rag_class: Optional class to use for RAG system instantiation.
                       If None, implementation should use a default.

        Returns:
            Configured RAG system instance
        """
        if rag_class is None:
            from cli.execution.api_main import ShopifyAPIRAG
            rag_class = ShopifyAPIRAG
        
        return rag_class(strategy=self, model_name=model_name)


__all__ = ["ToonStrictStrategy", "ZONStrictStrategy"]
