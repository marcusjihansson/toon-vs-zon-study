#!/usr/bin/env python3
"""
comparative_demo.py - Demo of API vs Database Comparison with Mock Data

This demo script shows how the comparative benchmark works using mock metrics 
instead of real LLM calls. Perfect for testing and demonstrations without API costs.

Usage:
    python cli/execution/comparative_demo.py
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


def run_demo_api_benchmark(queries: List[str]) -> Dict[str, Any]:
    """Run demo API benchmark with mock metrics."""
    print("\n" + "=" * 70)
    print("DEMO: API BENCHMARK (MOCK DATA)")
    print("=" * 70)
    
    strategies = create_default_strategies()
    from analyze.analyze import AnalysisResults, StrategyResults
    
    results = AnalysisResults()
    
    for strategy_name, strategy in strategies.items():
        print(f"\nTesting strategy: {strategy_name}")
        strategy_results = StrategyResults(strategy_name=strategy_name)
        
        for query in queries:
            print(f"  Query: {query[:50]}{'...' if len(query) > 50 else ''}")
            metrics = generate_mock_metrics(strategy, query)
            strategy_results.queries.append(metrics)
            print(f"    Mock: {metrics.total_tokens} tokens, {metrics.latency_ms:.1f}ms")
        
        results.strategies.append(strategy_results)
    
    analyzer = StrategyAnalyzer(strategies)
    report = analyzer.analyze_metrics(results)
    
    return {"results": results, "report": report}


def run_demo_db_benchmark(queries: List[str]) -> Dict[str, Any]:
    """Run demo database benchmark with mock metrics."""
    print("\n" + "=" * 70)
    print("DEMO: DATABASE BENCHMARK (MOCK DATA)")
    print("=" * 70)
    
    strategies = create_default_strategies()
    from analyze.analyze import AnalysisResults, StrategyResults
    
    results = AnalysisResults()
    
    for strategy_name, strategy in strategies.items():
        print(f"\nTesting strategy: {strategy_name}")
        strategy_results = StrategyResults(strategy_name=strategy_name)
        
        for query in queries:
            print(f"  Query: {query[:50]}{'...' if len(query) > 50 else ''}")
            metrics = generate_mock_metrics(strategy, query)
            strategy_results.queries.append(metrics)
            print(f"    Mock: {metrics.total_tokens} tokens, {metrics.latency_ms:.1f}ms")
        
        results.strategies.append(strategy_results)
    
    analyzer = StrategyAnalyzer(strategies)
    report = analyzer.analyze_metrics(results)
    
    return {"results": results, "report": report}


def main():
    """Main entry point for comparative demo."""
    print("\n" + "=" * 70)
    print("API vs DATABASE COMPARISON DEMO")
    print("=" * 70)
    print("\nThis demo uses mock metrics to show benchmark functionality")
    print("without making real LLM API calls.")
    print("\nFor real benchmarks with actual LLM calls, use:")
    print("  python cli/compare.py")
    print("=" * 70)
    
    # Run both benchmarks
    api_result = run_demo_api_benchmark(DEMO_QUESTIONS)
    db_result = run_demo_db_benchmark(DEMO_QUESTIONS)
    
    # Print reports
    print("\n" + "=" * 70)
    print("API BENCHMARK REPORT")
    print("=" * 70)
    analyzer = StrategyAnalyzer(create_default_strategies())
    analyzer.print_report(api_result["report"])
    
    print("\n" + "=" * 70)
    print("DATABASE BENCHMARK REPORT")
    print("=" * 70)
    analyzer.print_report(db_result["report"])
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nNote: These are mock metrics for demonstration only.")
    print("Real benchmarks require OPENROUTER_API_KEY to be set.")


if __name__ == "__main__":
    main()
