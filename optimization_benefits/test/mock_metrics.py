"""Mock metrics generation for demo purposes."""

import hashlib
import random
from typing import Any

from analyze.analyze import QueryMetrics
from strategies import BaseStrategy


def generate_mock_metrics(strategy: BaseStrategy, query: str) -> QueryMetrics:
    """Generate deterministic mock metrics for demo purposes.
    
    Args:
        strategy: Strategy to generate metrics for
        query: Query string
        
    Returns:
        Mock QueryMetrics with deterministic values
    """
    base_tokens = 150
    base_latency = 800

    # Strategy-specific multipliers
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

    # Create deterministic seed from strategy name and query
    seed_material = f"{strategy.name}|{query}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    rng = random.Random(seed)

    # Apply variations
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
