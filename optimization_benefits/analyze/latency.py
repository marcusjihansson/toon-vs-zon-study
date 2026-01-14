#!/usr/bin/env python3
"""
Comprehensive Latency Analysis for DSPy TOON Optimization

This module provides detailed latency profiling and analysis tools to identify
performance bottlenecks in the JSON vs TOON serialization pipeline.

Key Features:
- Multi-stage latency profiling (data loading, serialization, LLM calls, parsing)
- Statistical analysis with percentiles and variance
- Latency trap detection and recommendations
- Integration with existing benchmarking infrastructure
"""

import time
import statistics
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import gc
import psutil
import os
import sys


# =============================================================================
# Timing and Profiling Utilities
# =============================================================================


@dataclass
class LatencyMetrics:
    """Detailed latency metrics for a single operation."""

    operation_name: str
    total_time_ms: float = 0.0
    stages: Dict[str, float] = field(default_factory=dict)
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    timestamp: float = field(default_factory=time.time)

    @property
    def bottleneck_stage(self) -> str:
        """Identify the stage with highest latency contribution."""
        if not self.stages:
            return "unknown"
        return max(self.stages.items(), key=lambda x: x[1])[0]


@dataclass
class LatencyProfile:
    """Statistical profile of latency measurements."""

    operation_name: str
    measurements: List[LatencyMetrics] = field(default_factory=list)

    @property
    def avg_total_time(self) -> float:
        return statistics.mean(m.total_time_ms for m in self.measurements)

    @property
    def median_total_time(self) -> float:
        return statistics.median(m.total_time_ms for m in self.measurements)

    @property
    def p95_total_time(self) -> float:
        if len(self.measurements) < 2:
            return self.avg_total_time
        return statistics.quantiles([m.total_time_ms for m in self.measurements], n=20)[18]  # 95th percentile

    @property
    def p99_total_time(self) -> float:
        if len(self.measurements) < 2:
            return self.avg_total_time
        return statistics.quantiles([m.total_time_ms for m in self.measurements], n=100)[98]  # 99th percentile

    @property
    def std_dev_total_time(self) -> float:
        if len(self.measurements) < 2:
            return 0.0
        return statistics.stdev(m.total_time_ms for m in self.measurements)

    @property
    def common_bottleneck(self) -> str:
        """Most common bottleneck stage across measurements."""
        bottlenecks = [m.bottleneck_stage for m in self.measurements]
        return max(set(bottlenecks), key=bottlenecks.count) if bottlenecks else "unknown"


class LatencyProfiler:
    """
    High-precision latency profiler with multi-stage timing and resource monitoring.
    """

    def __init__(self):
        self.process = psutil.Process(os.getpid())

    def measure_latency(self, operation_name: str, func: Callable, *args, **kwargs) -> tuple[LatencyMetrics, Any]:
        """
        Measure detailed latency metrics for a function execution.

        Args:
            operation_name: Name of the operation being measured
            func: Function to execute and measure
            *args, **kwargs: Arguments to pass to func

        Returns:
            LatencyMetrics with detailed timing and resource data
        """
        metrics = LatencyMetrics(operation_name=operation_name)

        # Memory and CPU baseline
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = self.process.cpu_percent()

        # Execute with timing
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        # Final resource measurements
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = self.process.cpu_percent()

        # Calculate metrics
        metrics.total_time_ms = (end_time - start_time) * 1000
        metrics.memory_usage_mb = final_memory - initial_memory
        metrics.cpu_percent = max(initial_cpu, final_cpu)  # Peak CPU usage

        return metrics, result

    def profile_stages(self, operation_name: str, stages: Dict[str, Callable]) -> tuple[LatencyMetrics, Dict[str, Any]]:
        """
        Profile multiple stages of an operation individually and combined.

        Args:
            operation_name: Name of the overall operation
            stages: Dict mapping stage names to callables

        Returns:
            LatencyMetrics with stage-by-stage timing
        """
        metrics = LatencyMetrics(operation_name=operation_name)
        stage_results = {}

        total_start = time.perf_counter()

        for stage_name, stage_func in stages.items():
            stage_start = time.perf_counter()
            stage_result = stage_func()
            stage_end = time.perf_counter()

            stage_time_ms = (stage_end - stage_start) * 1000
            metrics.stages[stage_name] = stage_time_ms
            stage_results[stage_name] = stage_result

        total_end = time.perf_counter()
        metrics.total_time_ms = (total_end - total_start) * 1000

        return metrics, stage_results


# =============================================================================
# QnA Pipeline Latency Analysis
# =============================================================================


class QnALatencyAnalyzer:
    """
    Specialized latency analyzer for the QnA pipeline, focusing on JSON vs TOON comparisons.
    """

    def __init__(self):
        self.profiler = LatencyProfiler()
        self.profiles: Dict[str, LatencyProfile] = {}

    def analyze_qna_pipeline(self, strategy_name: str, qna_system, query: str, runs: int = 5) -> LatencyProfile:
        """
        Analyze latency of the complete QnA pipeline for a given strategy.

        Args:
            strategy_name: Name of the serialization strategy (JSON/TOON)
            qna_system: ProductQnASystem instance
            query: Query to analyze
            runs: Number of measurement runs

        Returns:
            LatencyProfile with statistical analysis
        """
        profile = LatencyProfile(f"qna_pipeline_{strategy_name}")

        for run in range(runs):
            # Define pipeline stages
            stages = {
                "context_prep": lambda: qna_system._prepare_context(),
                "llm_call": lambda: qna_system.predictor(context=qna_system._prepare_context(), query=query),
            }

            # Profile the pipeline
            metrics, results = self.profiler.profile_stages(f"qna_run_{run}", stages)

            # Store additional context
            metrics.memory_usage_mb = self.profiler.process.memory_info().rss / 1024 / 1024
            profile.measurements.append(metrics)

            # Force cleanup between runs
            gc.collect()

        self.profiles[strategy_name] = profile
        return profile

    def analyze_serialization_only(
        self, strategy_name: str, strategy, products: List[Dict], runs: int = 10
    ) -> LatencyProfile:
        """
        Analyze serialization latency in isolation (no LLM calls).

        Args:
            strategy_name: Name of the serialization strategy
            strategy: SerializationStrategy instance
            products: Product data to serialize
            runs: Number of measurement runs

        Returns:
            LatencyProfile for serialization timing
        """
        profile = LatencyProfile(f"serialization_{strategy_name}")

        for run in range(runs):

            def serialize_op():
                return strategy.prepare_context(products)

            metrics, _ = self.profiler.measure_latency(f"serialize_run_{run}", serialize_op)
            profile.measurements.append(metrics)

        self.profiles[f"{strategy_name}_serialization"] = profile
        return profile

    def compare_strategies(self, strategy_names: List[str]) -> Dict[str, Any]:
        """
        Compare latency profiles between strategies.

        Args:
            strategy_names: List of strategy names to compare

        Returns:
            Comparison analysis with recommendations
        """
        comparison = {}

        for name in strategy_names:
            if name in self.profiles:
                profile = self.profiles[name]
                comparison[name] = {
                    "avg_latency_ms": profile.avg_total_time,
                    "median_latency_ms": profile.median_total_time,
                    "p95_latency_ms": profile.p95_total_time,
                    "p99_latency_ms": profile.p99_total_time,
                    "std_dev_ms": profile.std_dev_total_time,
                    "common_bottleneck": profile.common_bottleneck,
                    "measurement_count": len(profile.measurements),
                }

        # Calculate improvements
        if len(strategy_names) >= 2:
            baseline = comparison.get(strategy_names[0], {})
            comparison_name = comparison.get(strategy_names[1], {})

            if baseline and comparison_name:
                latency_diff = comparison_name["avg_latency_ms"] - baseline["avg_latency_ms"]
                latency_improvement_pct = (
                    (latency_diff / baseline["avg_latency_ms"]) * 100 if baseline["avg_latency_ms"] > 0 else 0
                )

                comparison["comparison"] = {
                    "latency_difference_ms": latency_diff,
                    "latency_improvement_pct": latency_improvement_pct,
                    "faster_strategy": strategy_names[1] if latency_diff < 0 else strategy_names[0],
                    "slower_strategy": strategy_names[0] if latency_diff < 0 else strategy_names[1],
                }

        return comparison


# =============================================================================
# Latency Trap Detection
# =============================================================================


class LatencyTrapDetector:
    """
    Detects common latency bottlenecks and performance issues.
    """

    def __init__(self):
        self.thresholds = {
            "serialization_too_slow": 50.0,  # ms
            "llm_call_too_slow": 2000.0,  # ms
            "parsing_too_slow": 100.0,  # ms
            "memory_spike": 100.0,  # MB
            "high_variance": 0.3,  # 30% coefficient of variation
        }

    def detect_traps(self, profile: LatencyProfile) -> List[str]:
        """
        Analyze a latency profile for potential performance issues.

        Args:
            profile: LatencyProfile to analyze

        Returns:
            List of detected latency traps/issues
        """
        traps = []

        # High variance indicates inconsistent performance
        if profile.std_dev_total_time / profile.avg_total_time > self.thresholds["high_variance"]:
            traps.append(f"High latency variance ({profile.std_dev_total_time:.1f}ms std dev)")

        # Check individual measurements for issues
        for metrics in profile.measurements:
            # Memory spikes
            if metrics.memory_usage_mb > self.thresholds["memory_spike"]:
                traps.append(f"High memory usage ({metrics.memory_usage_mb:.1f}MB)")  # Stage-specific issues
            for stage, time_ms in metrics.stages.items():
                if stage == "serialization" and time_ms > self.thresholds["serialization_too_slow"]:
                    traps.append(f"Slow serialization ({time_ms:.1f}ms)")
                elif stage == "llm_call" and time_ms > self.thresholds["llm_call_too_slow"]:
                    traps.append(f"Slow LLM call ({time_ms:.1f}ms)")
                elif stage == "parsing" and time_ms > self.thresholds["parsing_too_slow"]:
                    traps.append(f"Slow parsing ({time_ms:.1f}ms)")

        return list(set(traps))  # Remove duplicates

    def generate_recommendations(self, traps: List[str]) -> List[str]:
        """
        Generate optimization recommendations based on detected traps.

        Args:
            traps: List of detected latency traps

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        for trap in traps:
            if "serialization" in trap.lower():
                recommendations.append("Consider caching serialized contexts or optimizing TOON encoding")
            elif "llm_call" in trap.lower():
                recommendations.append("Consider model optimization, request batching, or caching")
            elif "parsing" in trap.lower():
                recommendations.append("Review response parsing logic or consider alternative parsing strategies")
            elif "memory" in trap.lower():
                recommendations.append("Monitor memory usage patterns and consider streaming for large datasets")
            elif "variance" in trap.lower():
                recommendations.append("Investigate sources of performance inconsistency (network, caching, etc.)")

        return recommendations


# =============================================================================
# Integration with Existing Benchmarking
# =============================================================================


def run_latency_analysis_demo():
    """
    Demo function showing latency analysis capabilities.
    Integrates with existing QnA system for comprehensive profiling.
    """
    try:
        from qna import load_products_from_db, JSONStrategy, ToonStrategy, ProductQnASystem

        print("🔬 QnA Latency Analysis Demo")
        print("=" * 50)

        # Load test data
        products = load_products_from_db()
        print(f"📦 Loaded {len(products)} products for analysis")

        # Initialize analyzer
        analyzer = QnALatencyAnalyzer()
        detector = LatencyTrapDetector()

        # Test serialization latency (no LLM calls)
        print("\n⏱️  Analyzing serialization latency...")
        json_profile = analyzer.analyze_serialization_only("JSON", JSONStrategy(), products)
        toon_profile = analyzer.analyze_serialization_only("TOON", ToonStrategy(), products)

        print(f"JSON Serialization - Avg: {json_profile.avg_total_time:.2f}ms")
        print(f"TOON Serialization - Avg: {toon_profile.avg_total_time:.2f}ms")

        # Check for API keys for full pipeline analysis
        has_api_key = bool(os.getenv("OPENROUTER_API_KEY"))

        if has_api_key:
            print("\n🔗 Analyzing full QnA pipeline...")  # Test with sample query
            query = "What products are there listed?"

            json_system = ProductQnASystem(JSONStrategy())
            toon_system = ProductQnASystem(ToonStrategy())

            json_pipeline = analyzer.analyze_qna_pipeline("JSON", json_system, query, runs=3)
            toon_pipeline = analyzer.analyze_qna_pipeline("TOON", toon_system, query, runs=3)

            print(
                f"JSON Pipeline - Avg: {json_pipeline.avg_total_time:.2f}ms (P95: {json_pipeline.p95_total_time:.2f}ms)"
            )
            print(
                f"TOON Pipeline - Avg: {toon_pipeline.avg_total_time:.2f}ms (P95: {toon_pipeline.p95_total_time:.2f}ms)"
            )

            # Compare strategies
            comparison = analyzer.compare_strategies(["JSON", "TOON"])
            if "comparison" in comparison:
                comp = comparison["comparison"]
                print("\n🏁 Comparison:")
                print(f"  Latency Difference: {comp['latency_difference_ms']:+.1f}ms")
                print(f"  Improvement: {comp['latency_improvement_pct']:+.1f}%")
                print(f"  Faster Strategy: {comp['faster_strategy']}")

            # Detect latency traps
            print("\n🔍 Latency Trap Detection:")
            for strategy in ["JSON", "TOON"]:
                if strategy in analyzer.profiles:
                    traps = detector.detect_traps(analyzer.profiles[strategy])
                    if traps:
                        print(f"{strategy} Issues: {', '.join(traps)}")
                        recommendations = detector.generate_recommendations(traps)
                        for rec in recommendations:
                            print(f"  💡 {rec}")
                    else:
                        print(f"{strategy}: No significant latency traps detected")

        else:
            print("\n🔑 No API key found - skipping full pipeline analysis")
            print("Set OPENROUTER_API_KEY for complete latency profiling")

        print("\n✅ Latency analysis complete!")
        return analyzer, detector

    except Exception as e:
        print(f"❌ Latency analysis failed: {e}")
        return None, None


# =============================================================================
# Main
# =============================================================================


class Tee:
    """Helper to write to both stdout and a file."""

    def __init__(self, filename):
        self.file = open(filename, "w")
        self.stdout = sys.stdout

    def write(self, message):
        self.stdout.write(message)
        self.file.write(message)
        self.file.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.stdout
        self.file.close()


if __name__ == "__main__":
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)
    
    with Tee("results/latency_output.txt"):
        run_latency_analysis_demo()
