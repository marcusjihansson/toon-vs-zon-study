#!/usr/bin/env python3
"""
db_main.py - RAG from SQLite Database

This module demonstrates RAG (Retrieval Augmented Generation) using products
loaded from the SQLite database. It benchmarks different serialization
adapters (JSON, TOON, BAML, ZON) to compare token efficiency and performance.

Usage:
    python cli/db.py

This runs the complete benchmark comparing all strategies on database data.
"""

import os
import sys
import warnings
from typing import Any, Dict, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../..", ".env"))

# Suppress Pydantic serialization warnings from DSPy's internal response handling
# These warnings are cosmetic and don't affect functionality
warnings.filterwarnings("ignore", message=r"Pydantic.*", category=UserWarning)

import dspy
import tiktoken
from analyze import StrategyAnalyzer, create_default_strategies
from database import (get_product_count, get_product_price_range,
                      load_products_from_db, sync_from_api)
from pydantic import BaseModel, Field
from strategies import (BAMLStrategy, BaselineStrategy, BaseStrategy,
                        CombinedStrategy, JSONStrategy, ToonStrategy,
                        ToonStrictStrategy, ZONStrictStrategy,
                        ZONCombinedStrategy)

from toon import encode as toon_encode

# =============================================================================
# DSPy Signatures and Models
# =============================================================================


class ProductInfo(BaseModel):
    """Basic product information."""

    product_id: str
    title: str
    price: float
    description: str = ""


class ProductRecommendation(BaseModel):
    """Product recommendation for a query."""

    product_id: str
    title: str
    reason: str = Field(description="Why this product matches the query")
    confidence: float = Field(ge=0, le=1, description="Confidence score")


class RAGResponse(BaseModel):
    """Response to a product question."""

    recommendations: List[ProductRecommendation] = Field(
        description="Products relevant to the answer"
    )
    total_products_reviewed: int = Field(
        description="How many products were considered"
    )
    answer: str = Field(description="Natural language answer to the query")


class ProductRAGSignature(dspy.Signature):
    """Analyze product catalog and provide recommendations based on user query."""

    context: str = dspy.InputField(description="Product catalog data")
    query: str = dspy.InputField(description="User's product search query")
    response: RAGResponse = dspy.OutputField(description="Recommendations and answer")


# =============================================================================
# RAG System
# =============================================================================


class DatabaseRAG:
    """RAG system that loads products from SQLite database."""

    def __init__(
        self, strategy: BaseStrategy, model_name: str = "openrouter/openai/gpt-4o-mini"
    ):
        """Initialize the RAG system with a strategy.

        Args:
            strategy: Strategy to use for serialization
            model_name: LLM model to use
        """
        self.strategy = strategy

        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = "https://openrouter.ai/api/v1"

        lm = dspy.LM(model_name, cache=False, api_key=api_key, base_url=base_url)
        # Note: dspy.configure is called by the analyzer, not here

        self.lm = lm
        self.adapter = strategy.adapter
        self.predictor = dspy.ChainOfThought(ProductRAGSignature)

    def load_products(self) -> List[Dict[str, Any]]:
        """Load products from SQLite database.

        Returns:
            list: List of product dictionaries
        """
        return load_products_from_db()

    def prepare_context(self, products: List[Dict[str, Any]], query: str) -> str:
        """Prepare product context for the LLM.

        Args:
            products: List of products
            query: User query

        Returns:
            str: Formatted context for LLM
        """
        from adapters.serializers import (
            serialize_json, serialize_toon, serialize_zon,
            serialize_baml, serialize_combined
        )

        strategy_name = self.strategy.name if hasattr(self.strategy, "name") else "baseline"

        if strategy_name == "toon_adapter":
            context_data = serialize_toon(products)
            format_name = "TOON"
        elif strategy_name == "toon_strict":
            context_data = serialize_toon(products)
            format_name = "TOON (Strict)"
        elif strategy_name == "zon_adapter":
            context_data = serialize_zon(products)
            format_name = "ZON"
        elif strategy_name == "zon_strict":
            context_data = serialize_zon(products)
            format_name = "ZON (Strict)"
        elif strategy_name == "zon_combined":
            context_data = serialize_zon(products)
            format_name = "ZON (Combined)"
        elif strategy_name == "baml_adapter":
            context_data = serialize_baml(products)
            format_name = "BAML"
        elif strategy_name == "combined":
            context_data = serialize_combined(products)
            format_name = "Combined (TOON)"
        elif strategy_name == "json_baseline":
            context_data = serialize_json(products, compact=True)
            format_name = "Minified JSON"
        else:  # baseline
            context_data = serialize_json(products, compact=False)
            format_name = "JSON"

        context = f"""Product Catalog (loaded from SQLite database in {format_name} format):

{context_data}

Total products: {len(products)}

Query: {query}"""

        return context

    def ask(self, query: str) -> RAGResponse:
        """Answer a question about products.

        Args:
            query: User question

        Returns:
            RAGResponse: Structured response with recommendations
        """
        products = self.load_products()
        context = self.prepare_context(products, query)

        result = self.predictor(context=context, query=query)

        return result.response

    def get_context(self, query: str) -> str:
        """Get the formatted context string for a query.

        This helper method is used by the analyzer to calculate token usage.

        Args:
            query: User query

        Returns:
            str: The full context string that would be sent to the LLM
        """
        products = self.load_products()
        return self.prepare_context(products, query)

    def get_token_usage(self, query: str) -> Dict[str, int]:
        """Get estimated token usage for a query.

        Args:
            query: User query

        Returns:
            dict: Token usage estimates
        """
        products = self.load_products()
        context = self.prepare_context(products, query)

        enc = tiktoken.encoding_for_model("gpt-4")
        context_tokens = len(enc.encode(context))
        query_tokens = len(enc.encode(query))

        return {
            "input_tokens": context_tokens + query_tokens,
            "estimated_output_tokens": 150,
            "total_estimated_tokens": context_tokens + query_tokens + 150,
        }


# =============================================================================
# Benchmark Functions
# =============================================================================


def run_database_benchmark(queries: List[str]) -> Dict[str, Any] | None:
    """Run benchmark comparing all strategies on database data.

    Args:
        queries: List of queries to test

    Returns:
        dict: Benchmark results
    """
    print("\n" + "=" * 70)
    print("DATABASE RAG BENCHMARK")
    print("=" * 70)
    print(f"Queries: {len(queries)}")
    print("Mode: REAL API CALLS")

    product_count = get_product_count()
    print(f"Products in database: {product_count}")

    if product_count == 0:
        print("\nNo products in database. Syncing from API first...")
        result = sync_from_api(limit=10)
        print(f"Sync result: {result}")

    strategies = create_default_strategies()
    analyzer = StrategyAnalyzer(strategies)

    try:
        results = analyzer.run_benchmark(
            queries, runs_per_query=2, rag_class=DatabaseRAG
        )
    except ValueError as e:
        print(f"Benchmark aborted: {e}")
        return None
    report = analyzer.analyze_metrics(results)
    analyzer.print_report(report)

    return {
        "results": results,
        "report": report,
    }


def demo_single_query(strategy_name: str, query: str):
    """Demo a single query with a specific strategy.

    Args:
        strategy_name: Name of the strategy to use
        query: Question to ask
        dry_run: Skip API calls
    """
    strategies = create_default_strategies()
    strategy = strategies.get(strategy_name)

    if not strategy:
        print(f"Unknown strategy: {strategy_name}")
        print(f"Available: {', '.join(strategies.keys())}")
        return

    print(f"\n{'=' * 60}")
    print(f"Strategy: {strategy_name}")
    print(f"Query: {query}")
    print("=" * 60)

    if dry_run:
        print("\n[Dry run - no API call made]")
        tokens = (
            strategy.adapter.get_token_usage
            if hasattr(strategy.adapter, "get_token_usage")
            else None
        )
        print(f"Strategy adapter: {type(strategy.adapter).__name__}")
        return

    try:
        rag = DatabaseRAG(strategy)
        response = rag.ask(query)

        print(f"\nAnswer: {response.answer}")
        print(f"\nRecommendations ({len(response.recommendations)}):")
        for rec in response.recommendations:
            print(f"  - {rec.title} (confidence: {rec.confidence:.2f})")
            print(f"    {rec.reason}")

        tokens = rag.get_token_usage(query)
        print(f"\nToken usage: {tokens}")

    except Exception as e:
        print(f"Error: {e}")


def compare_token_efficiency(query: str = "What products are available?"):
    """Compare token efficiency between strategies on database data.

    Args:
        query: Query to use for comparison
    """
    from adapters.serializers import (
        serialize_json, serialize_toon, serialize_zon,
        serialize_baml, serialize_combined
    )

    print("\n" + "=" * 70)
    print("TOKEN EFFICIENCY COMPARISON (SQLite Database)")
    print("=" * 70)
    print(f"Query: {query}")

    product_count = get_product_count()
    print(f"Products in database: {product_count}")

    if product_count == 0:
        print("\nNo products in database. Syncing from API...")
        sync_from_api(limit=10)

    strategies = create_default_strategies()
    enc = tiktoken.encoding_for_model("gpt-4")

    products = None
    results = {}

    for name, strategy in strategies.items():
        try:
            if products is None:
                rag = DatabaseRAG(strategy)
                products = rag.load_products()

            if name == "toon_adapter":
                context = serialize_toon(products)
            elif name == "toon_strict":
                context = serialize_toon(products)
            elif name == "zon_adapter":
                context = serialize_zon(products)
            elif name == "zon_strict":
                context = serialize_zon(products)
            elif name == "zon_combined":
                context = serialize_zon(products)
            elif name == "baml_adapter":
                context = serialize_baml(products)
            elif name == "combined":
                context = serialize_combined(products)
            elif name == "json_baseline":
                context = serialize_json(products, compact=True)
            else:  # baseline
                context = serialize_json(products, compact=False)

            full_prompt = f"Product Catalog:\n{context}\n\nQuery: {query}"
            tokens = len(enc.encode(full_prompt))

            results[name] = {
                "tokens": tokens,
                "adapter": type(strategy.adapter).__name__,
            }

            print(f"\n{name}: {tokens} tokens ({type(strategy.adapter).__name__})")

        except Exception as e:
            print(f"\n{name}: Error - {e}")
            results[name] = {"error": str(e)}

    if len(results) >= 2:
        baseline = list(results.keys())[0]
        baseline_tokens = results[baseline].get("tokens", 0)

        print(f"\n{'=' * 70}")
        print("TOKEN SAVINGS vs BASELINE")
        print("=" * 70)

        for name, data in results.items():
            if "tokens" in data and baseline_tokens > 0:
                savings = ((baseline_tokens - data["tokens"]) / baseline_tokens) * 100
                print(f"{name}: {savings:+.1f}% ({data['tokens']} tokens)")


# =============================================================================
# Demo Questions
# =============================================================================


QUESTIONS = [
    "What products are available?",
    "Show me the prices of all products",
    "Which is the most expensive product?",
    "Are there any products under $50?",
    "What product do you recommend I add to my storefront?",
]


def run_all_demos():
    """Run all demo questions."""
    print("\n" + "=" * 70)
    print("RUNNING ALL DEMO QUESTIONS")
    print("=" * 70)

    product_count = get_product_count()
    if product_count == 0:
        print("No products in database. Syncing from API...")
        sync_from_api(limit=10)

    for question in QUESTIONS:
        print(f"\n{'=' * 60}")
        print(f"Q: {question}")
        print("=" * 60)

        for name in ["baseline", "toon_adapter", "toon_strict", "baml_adapter", "zon_adapter", "zon_strict", "zon_combined"]:
            demo_single_query(name, question)


# =============================================================================
# Main
# =============================================================================


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("DATABASE RAG - Strategy Benchmarking")
    print("=" * 70)

    product_count = get_product_count()
    print(f"Products in database: {product_count}")

    if product_count == 0:
        print("\nNo products in database. Syncing from API...")
        result = sync_from_api(limit=10)
        if result["products_count"] == 0:
            print("Failed to sync products. Please check API credentials.")
            return

    has_api_key = bool(os.getenv("OPENROUTER_API_KEY"))
    if not has_api_key:
        print("\nNo OPENROUTER_API_KEY found.")
        print("Set OPENROUTER_API_KEY in .env to run benchmarks.\n")
        return

    print("\nMode: REAL LLM CALLS\n")

    compare_token_efficiency()

    run_database_benchmark(QUESTIONS)


if __name__ == "__main__":
    main()
