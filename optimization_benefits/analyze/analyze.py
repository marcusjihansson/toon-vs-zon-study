#!/usr/bin/env python3
"""
Comprehensive Strategy Analysis for DSPy RAG Systems

This module provides benchmarking and analysis tools to compare different
adapters and strategies for token efficiency, latency, and reliability in
DSPy-based RAG systems.

Usage:
    from optimization_benefits.analyze import StrategyAnalyzer
    analyzer = StrategyAnalyzer(strategies)
    results = analyzer.run_benchmark(queries)
    report = analyzer.analyze_metrics(results)
"""

import json
import os
import sys
import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import defaultdict
from statistics import mean

import dspy
import tiktoken
from pydantic import BaseModel, ValidationError

from strategies import (
    BaseStrategy,
    BaselineStrategy,
    ToonStrategy,
    ToonStrictStrategy,
    BAMLStrategy,
    JSONStrategy,
    ZONStrategy,
    ZONStrictStrategy,
    CombinedStrategy,
    ZONCombinedStrategy,
)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""

    strategy_name: str
    query: str
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    parse_success: bool = False
    field_completion_rate: float = 0.0
    schema_tokens: int = 0
    error: Optional[str] = None


@dataclass
class StrategyResults:
    """Results for a single strategy across all queries."""

    strategy_name: str
    queries: List[QueryMetrics] = field(default_factory=list)
    token_reduction_pct: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        valid_queries = [q.latency_ms for q in self.queries if q.error is None]
        return mean(valid_queries) if valid_queries else 0.0

    @property
    def avg_total_tokens(self) -> float:
        valid_queries = [q.total_tokens for q in self.queries if q.error is None]
        return mean(valid_queries) if valid_queries else 0.0

    @property
    def parse_success_rate(self) -> float:
        successful = sum(1 for q in self.queries if q.parse_success)
        return successful / len(self.queries) * 100

    @property
    def avg_field_completion_rate(self) -> float:
        valid_queries = [q.field_completion_rate for q in self.queries if q.parse_success]
        return mean(valid_queries) if valid_queries else 0.0


@dataclass
class AnalysisResults:
    """Complete results across all strategies."""

    strategies: List[StrategyResults] = field(default_factory=list)
    baseline_name: str = "baseline"

    def get_baseline(self) -> Optional[StrategyResults]:
        return next((s for s in self.strategies if s.strategy_name == self.baseline_name), None)

    def calculate_token_reductions(self):
        """Calculate token reduction percentages vs baseline."""
        baseline = self.get_baseline()
        if not baseline:
            return

        baseline_avg_tokens = baseline.avg_total_tokens
        if baseline_avg_tokens == 0:
            for strategy in self.strategies:
                if strategy.strategy_name != self.baseline_name:
                    strategy.token_reduction_pct = strategy.avg_total_tokens - baseline_avg_tokens
            return

        for strategy in self.strategies:
            if strategy.strategy_name != self.baseline_name:
                strategy.token_reduction_pct = (
                    (baseline_avg_tokens - strategy.avg_total_tokens) / baseline_avg_tokens * 100
                )


@dataclass
class AnalysisReport:
    """Analysis report with insights and recommendations."""

    results: AnalysisResults
    summary: Dict[str, Any] = field(default_factory=dict)

    def generate_summary(self):
        """Generate summary statistics and insights."""
        baseline = self.results.get_baseline()
        if not baseline:
            return

        self.results.calculate_token_reductions()

        sorted_strategies = sorted(self.results.strategies, key=lambda s: s.token_reduction_pct, reverse=True)

        baseline_avg_latency = baseline.avg_latency_ms
        self.summary = {
            "total_queries": len(baseline.queries),
            "baseline_avg_tokens": baseline.avg_total_tokens,
            "baseline_avg_latency": baseline_avg_latency,
            "strategy_rankings": [
                {
                    "name": s.strategy_name,
                    "token_reduction_pct": s.token_reduction_pct,
                    "latency_impact_pct": (
                        (s.avg_latency_ms - baseline_avg_latency) / baseline_avg_latency * 100
                        if baseline_avg_latency > 0
                        else 0.0
                    ),
                    "parse_success_rate": s.parse_success_rate,
                    "field_completion_rate": s.avg_field_completion_rate,
                }
                for s in sorted_strategies
            ],
            "recommendations": self._generate_recommendations(sorted_strategies, baseline),
        }

    def _generate_recommendations(self, strategies: List[StrategyResults], baseline: StrategyResults) -> Dict[str, str]:
        """Generate strategy recommendations based on metrics."""
        recommendations = {}

        if not strategies:
            return recommendations

        best_tokens = max(strategies, key=lambda s: s.token_reduction_pct)
        recommendations["max_token_reduction"] = best_tokens.strategy_name

        best_latency = min(strategies, key=lambda s: s.avg_latency_ms)
        recommendations["minimal_latency"] = best_latency.strategy_name

        best_reliability = max(strategies, key=lambda s: s.parse_success_rate)
        recommendations["highest_reliability"] = best_reliability.strategy_name

        candidates = [s for s in strategies if s.token_reduction_pct > 15]
        if candidates and baseline.avg_latency_ms > 0:
            balanced = min(
                candidates,
                key=lambda s: abs(s.avg_latency_ms - baseline.avg_latency_ms) / baseline.avg_latency_ms,
            )
        else:
            balanced = strategies[0] if strategies else None

        if balanced:
            recommendations["balanced_choice"] = balanced.strategy_name

        return recommendations


# =============================================================================
# Analysis Engine
# =============================================================================


class StrategyAnalyzer:
    """Comprehensive benchmarking and analysis engine."""

    def __init__(self, strategies: Dict[str, BaseStrategy]):
        self.strategies = strategies

    def run_benchmark(
        self,
        queries: List[str],
        runs_per_query: int = 3,
        model_name: str = "openai/gpt-4o-mini",
        enable_latency_profiling: bool = False,
        rag_class: Any = None,
    ) -> AnalysisResults:
        """
        Run comprehensive benchmark across all strategies.

        Args:
            queries: List of test queries
            runs_per_query: Number of runs per query for averaging
            model_name: LLM model to use
            enable_latency_profiling: If True, enable detailed latency profiling using latency.py
            rag_class: Optional class to use for RAG system instantiation (e.g. DatabaseRAG, ShopifyAPIRAG)

        Returns:
            Complete analysis results
        """
        print(f"\n{'='*70}")
        print("STRATEGY BENCHMARK ANALYSIS")
        print(f"Model: {model_name}")
        print(f"Queries: {len(queries)}")
        print(f"Runs per query: {runs_per_query}")
        print(f"Strategies: {', '.join(self.strategies.keys())}")
        if rag_class:
            print(f"RAG Class: {rag_class.__name__}")
        print("=" * 70)

        has_api_key = bool(os.getenv("OPENROUTER_API_KEY"))
        if not has_api_key:
            raise ValueError(
                "No OPENROUTER_API_KEY found. Set OPENROUTER_API_KEY environment variable."
            )

        latency_profiler = None
        if enable_latency_profiling:
            try:
                from .latency import LatencyProfiler

                latency_profiler = LatencyProfiler()
                print("Latency profiling enabled")
            except ImportError:
                print("Latency profiling requested but latency.py not available")

        results = AnalysisResults()

        for strategy_name, strategy in self.strategies.items():
            print(f"\nTesting strategy: {strategy_name}")
            strategy_results = StrategyResults(strategy_name=strategy_name)

            for query in queries:
                print(f"  Query: {query[:50]}{'...' if len(query) > 50 else ''}")

                query_metrics = []
                for run in range(runs_per_query):
                    try:
                        metrics = self._run_single_query(strategy, query, model_name, rag_class)
                        query_metrics.append(metrics)
                    except Exception as e:
                        print(f"    Run {run + 1} failed: {e}")
                        continue

                if query_metrics:
                    avg_metrics = self._average_metrics(query_metrics)
                    strategy_results.queries.append(avg_metrics)
                    print(f"    Avg: {avg_metrics.total_tokens} tokens, {avg_metrics.latency_ms:.1f}ms")
                    if avg_metrics.error:
                        print(f"    Error: {avg_metrics.error}")
                    if avg_metrics.total_tokens == 0 and not avg_metrics.error:
                        print(f"    WARNING: Zero tokens recorded despite no apparent error.")

            results.strategies.append(strategy_results)

        return results

    def _run_single_query(self, strategy: BaseStrategy, query: str, model_name: str, rag_class: Any = None) -> QueryMetrics:
        """Run a single query and collect metrics."""
        metrics = QueryMetrics(strategy_name=strategy.name, query=query)

        try:
            rag_system = strategy.create_rag_system(model_name, rag_class=rag_class)

            if not os.getenv("OPENROUTER_API_KEY"):
                raise ValueError("No API key found. Set OPENROUTER_API_KEY environment variable.")

            dspy.configure(lm=rag_system.lm, adapter=rag_system.adapter, track_usage=True)

            # Use standardized get_context method if available
            if hasattr(rag_system, "get_context"):
                context_str = rag_system.get_context(query)
            elif hasattr(rag_system, "_get_context"):
                context_str = rag_system._get_context(query)
            else:
                 # Fallback: try to manually reconstruct context if possible or warn
                 # This shouldn't happen with our updated RAG classes
                 raise AttributeError("RAG system missing 'get_context' method")

            enc = tiktoken.encoding_for_model("gpt-4")
            input_tokens_fallback = len(enc.encode(context_str + "\n\nQuery: " + query))

            # Some LM provider SDKs used under DSPy emit noisy Pydantic v2 warnings
            # about serializer field mismatches (e.g. Message/StreamingChoices).
            # These warnings are non-fatal and unrelated to our structured-output
            # correctness, so we suppress just this specific warning category.
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r"Pydantic serializer warnings:.*",
                    category=UserWarning,
                )
                # Also suppress the main.py:464 UserWarning from pydantic serialization
                warnings.filterwarnings(
                    "ignore", 
                    message=r"PydanticSerializationUnexpectedValue.*",
                    category=UserWarning,
                )
                start_time = time.perf_counter()
                result = rag_system.predictor(context=context_str, query=query)
                end_time = time.perf_counter()

            metrics.latency_ms = (end_time - start_time) * 1000

            usage = result.get_lm_usage()

            if usage:
                for lm_usage in usage.values():
                    metrics.input_tokens += lm_usage.get("prompt_tokens", 0)
                    metrics.output_tokens += lm_usage.get("completion_tokens", 0)
                metrics.total_tokens = metrics.input_tokens + metrics.output_tokens
            else:
                # If dspy doesn't return usage (some providers), fallback to manual calc
                print(f"    [Warning] No usage data from provider. Using manual calculation.")
                metrics.input_tokens = input_tokens_fallback
                # Estimate output based on result string length (approx 4 chars per token)
                response_str = str(result.response) if hasattr(result, "response") else ""
                estimated_output_tokens = len(response_str) // 4
                metrics.output_tokens = max(estimated_output_tokens, 1) # Ensure at least 1
                metrics.total_tokens = metrics.input_tokens + metrics.output_tokens

            response = result.response
            metrics.parse_success = self._validate_response(response)
            metrics.field_completion_rate = self._calculate_field_completion(response)

        except Exception as e:
            error_msg = str(e)
            if "No API key found" in error_msg:
                metrics.error = "API_KEY_MISSING: Set OPENROUTER_API_KEY"
            else:
                metrics.error = f"API_ERROR: {error_msg}"
            metrics.parse_success = False

        return metrics

    def _average_metrics(self, metrics_list: List[QueryMetrics]) -> QueryMetrics:
        """Average metrics across multiple runs."""
        if not metrics_list:
            return QueryMetrics(strategy_name="", query="")

        avg = QueryMetrics(
            strategy_name=metrics_list[0].strategy_name,
            query=metrics_list[0].query,
            parse_success=all(m.parse_success for m in metrics_list),
            error=next((m.error for m in metrics_list if m.error), None),
        )

        successful_metrics = [m for m in metrics_list if m.error is None]

        if successful_metrics:
            avg.latency_ms = mean(m.latency_ms for m in successful_metrics)
            avg.input_tokens = int(mean(m.input_tokens for m in successful_metrics))
            avg.output_tokens = int(mean(m.output_tokens for m in successful_metrics))
            avg.total_tokens = avg.input_tokens + avg.output_tokens
            parsed_metrics = [m.field_completion_rate for m in successful_metrics if m.parse_success]
            avg.field_completion_rate = mean(parsed_metrics) if parsed_metrics else 0.0
        else:
            avg.latency_ms = 0.0
            avg.input_tokens = 0
            avg.output_tokens = 0
            avg.total_tokens = 0
            avg.field_completion_rate = 0.0

        return avg

    def _generate_mock_metrics(self, strategy: BaseStrategy, query: str) -> QueryMetrics:
        """Generate mock metrics for dry run testing."""
        import hashlib
        import random

        base_tokens = 150
        base_latency = 800

        if strategy.name == "baseline":
            token_multiplier = 1.0
            latency_multiplier = 1.0
            success_rate = 0.9
        elif strategy.name == "toon_adapter":
            token_multiplier = 0.7
            latency_multiplier = 1.05
            success_rate = 0.95
        elif strategy.name == "baml_adapter":
            token_multiplier = 0.8
            latency_multiplier = 1.1
            success_rate = 0.98
        elif strategy.name == "zon_adapter":
            token_multiplier = 0.5
            latency_multiplier = 1.02
            success_rate = 0.95
        elif strategy.name == "combined":
            token_multiplier = 0.65
            latency_multiplier = 1.08
            success_rate = 0.97
        else:
            token_multiplier = 1.0
            latency_multiplier = 1.0
            success_rate = 0.9

        seed_material = f"{strategy.name}|{query}".encode("utf-8")
        seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
        rng = random.Random(seed)

        token_variation = rng.uniform(0.9, 1.1)
        latency_variation = rng.uniform(0.8, 1.2)

        total_tokens = int(base_tokens * token_multiplier * token_variation)
        latency_ms = base_latency * latency_multiplier * latency_variation

        parse_success = rng.random() < success_rate

        return QueryMetrics(
            strategy_name=strategy.name,
            query=query,
            latency_ms=latency_ms,
            input_tokens=int(total_tokens * 0.7),
            output_tokens=int(total_tokens * 0.3),
            total_tokens=total_tokens,
            parse_success=parse_success,
            field_completion_rate=rng.uniform(85, 100) if parse_success else 0.0,
        )

    def _validate_response(self, response: Any) -> bool:
        """Validate that response is properly structured."""
        try:
            if not hasattr(response, "recommendations"):
                return False
            if not hasattr(response, "total_products_reviewed"):
                return False
            if not hasattr(response, "answer"):
                return False

            for rec in response.recommendations:
                # Our ProductRecommendation model uses `title` (not `name`).
                if not all(hasattr(rec, attr) for attr in ["product_id", "title", "reason", "confidence"]):
                    return False

            return True
        except Exception:
            return False

    def _calculate_field_completion(self, response: Any) -> float:
        """Calculate what percentage of expected fields are present."""
        try:
            expected_fields = ["recommendations", "total_products_reviewed", "answer"]
            present_fields = sum(1 for field in expected_fields if hasattr(response, field))

            if hasattr(response, "recommendations") and response.recommendations:
                rec_fields = ["product_id", "title", "reason", "confidence"]
                rec_completion = sum(
                    1 for field in rec_fields if hasattr(response.recommendations[0], field)
                )
                present_fields += rec_completion / len(rec_fields)

            return present_fields / (len(expected_fields) + 1) * 100
        except Exception:
            return 0.0

    def analyze_metrics(self, results: AnalysisResults) -> AnalysisReport:
        """Generate detailed analysis report."""
        report = AnalysisReport(results=results)
        report.generate_summary()
        return report

    def print_report(self, report: AnalysisReport):
        """Print formatted analysis report."""
        print(f"\n{'='*70}")
        print("STRATEGY ANALYSIS REPORT")
        print("=" * 70)

        summary = report.summary

        print(f"\nBenchmark Summary:")
        print(f"   Total Queries: {summary['total_queries']}")
        print(f"   Baseline Avg Tokens: {summary['baseline_avg_tokens']:.0f}")
        print(f"   Baseline Avg Latency: {summary['baseline_avg_latency']:.1f}ms")

        print(f"\nStrategy Rankings (by token reduction):")
        print(f"{'Rank':<5} {'Strategy':<15} {'Token Reduction':<15} {'Latency Impact':<15} {'Success Rate':<12}")
        print("-" * 70)

        for i, strategy in enumerate(summary["strategy_rankings"], 1):
            print(
                f"{i:<5} {strategy['name']:<15} {strategy['token_reduction_pct']:+.1f}%{'':<8} {strategy['latency_impact_pct']:+.1f}%{'':<7} {strategy['parse_success_rate']:.1f}%"
            )

        print(f"\nRecommendations:")
        recs = summary["recommendations"]
        print(f"   Max Token Reduction: {recs['max_token_reduction']}")
        print(f"   Minimal Latency Impact: {recs['minimal_latency']}")
        print(f"   Highest Reliability: {recs['highest_reliability']}")
        print(f"   Balanced Choice: {recs['balanced_choice']}")

        print(f"\n{'='*70}")


# =============================================================================
# Utility Functions
# =============================================================================


def create_default_strategies() -> Dict[str, BaseStrategy]:
    """Create the default set of strategies for comparison."""
    return {
        "baseline": BaselineStrategy(),
        "toon_adapter": ToonStrategy(),
        "toon_strict": ToonStrictStrategy(),
        "baml_adapter": BAMLStrategy(),
        "json_baseline": JSONStrategy(),
        "zon_adapter": ZONStrategy(),
        "zon_strict": ZONStrictStrategy(),
        "combined": CombinedStrategy(),
        "zon_combined": ZONCombinedStrategy(),
    }


def run_quick_analysis(
    queries: Optional[List[str]] = None, model: str = "openrouter/openai/gpt-4o-mini"
) -> AnalysisReport:
    """Run a quick analysis with default settings."""
    if queries is None:
        queries = [
            "Find laptops under $1500",
            "Show me affordable accessories",
            "What products have the best reviews?",
        ]

    strategies = create_default_strategies()
    analyzer = StrategyAnalyzer(strategies)
    results = analyzer.run_benchmark(queries, runs_per_query=2, model_name=model)
    report = analyzer.analyze_metrics(results)

    return report


if __name__ == "__main__":
    report = run_quick_analysis()
    analyzer = StrategyAnalyzer(create_default_strategies())
    analyzer.print_report(report)
