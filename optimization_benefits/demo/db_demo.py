#!/usr/bin/env python3
"""
db_demo.py - Demo of Database Benchmark with Mock Data

This demo script shows how the database benchmark works using mock metrics 
instead of real LLM calls. Perfect for testing and demonstrations without API costs.

Usage:
    python cli/execution/db_demo.py
"""

import os
import sys
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyze import StrategyAnalyzer, create_default_strategies
from test.mock_metrics import generate_mock_metrics

# Questions to test
DEMO_QUESTIONS = [
    "What products are available?",
    "Show me the prices of all products",
    "Which is the most expensive product?",
]


def run_demo_benchmark(queries: List[str]) -> Dict[str, Any]:
    """Run demo benchmark with mock metrics.
    
    Args:
        queries: List of queries to test
        
    Returns:
        dict: Benchmark results with mock data
    """
    print("\n" + "=" * 70)
    print("DEMO: DATABASE RAG BENCHMARK (MOCK DATA)")
    print("=" * 70)
    print(f"Queries: {len(queries)}")
    print("Mode: DEMO - Using mock metrics (no real API calls)")
    print("=" * 70)
    
    strategies = create_default_strategies()
    
    # Manually create results using mock metrics
    from analyze.analyze import AnalysisResults, StrategyResults
    
    results = AnalysisResults()
    
    for strategy_name, strategy in strategies.items():
        print(f"\nTesting strategy: {strategy_name}")
        strategy_results = StrategyResults(strategy_name=strategy_name)
        
        for query in queries:
            print(f"  Query: {query[:50]}{'...' if len(query) > 50 else ''}")
            
            # Generate mock metrics
            metrics = generate_mock_metrics(strategy, query)
            strategy_results.queries.append(metrics)
            print(f"    Mock: {metrics.total_tokens} tokens, {metrics.latency_ms:.1f}ms")
        
        results.strategies.append(strategy_results)
    
    # Generate analysis report
    analyzer = StrategyAnalyzer(strategies)
    report = analyzer.analyze_metrics(results)
    analyzer.print_report(report)
    
    return {"results": results, "report": report}


def main():
    """Main entry point for demo."""
    print("\n" + "=" * 70)
    print("DATABASE BENCHMARK DEMO")
    print("=" * 70)
    print("\nThis demo uses mock metrics to show benchmark functionality")
    print("without making real LLM API calls.")
    print("\nFor real benchmarks with actual LLM calls, use:")
    print("  python cli/db.py")
    print("=" * 70)
    
    run_demo_benchmark(DEMO_QUESTIONS)
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nNote: These are mock metrics for demonstration only.")
    print("Real benchmarks require OPENROUTER_API_KEY to be set.")


if __name__ == "__main__":
    main()
