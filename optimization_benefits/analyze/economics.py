#!/usr/bin/env python3
"""
economics.py - Economic Analysis of Token Savings

This script projects annual infrastructure savings based on token reduction
metrics observed in the benchmark study. It allows industry professionals to
input their own scale (daily inferences) and pricing models to estimate ROI.

Usage:
    python analyze/economics.py [--daily_inferences N] [--input_token_price P]

Defaults are parameterized (you provide your own request volume) and use GPT-4o-mini pricing unless overridden.
"""

import argparse
from dataclasses import dataclass

@dataclass
class CostModel:
    name: str
    input_price_per_1m: float  # Price in USD per 1 million input tokens
    output_price_per_1m: float # Price in USD per 1 million output tokens

# Pricing Reference (Jan 2026)
MODELS = {
    "gpt-4o-mini": CostModel("GPT-4o-mini", 0.15, 0.60),
    "gpt-4o": CostModel("GPT-4o", 5.00, 15.00),
    "claude-3-haiku": CostModel("Claude 3 Haiku", 0.25, 1.25),
}

# Benchmark Findings (from docs/)
# Centralized in `analyze/study_constants.py` to prevent drift.
try:
    # Preferred when executed as a module: `python -m analyze.economics`
    from .study_constants import PROMPT_STUDY
except ImportError:  # pragma: no cover
    # Fallback for direct execution: `python analyze/economics.py`
    # NOTE: when executed this way, the `analyze/` directory is on sys.path and
    # `analyze/analyze.py` shadows the `analyze` package name.
    from study_constants import PROMPT_STUDY

def calculate_savings(
    daily_inferences: int,
    input_price: float,
    model_name: str = "Custom"
):
    """
    Calculate and print economic analysis.
    """
    
    # Calculate daily volumes
    baseline_daily_tokens = daily_inferences * PROMPT_STUDY.baseline_tokens
    optimized_daily_tokens = daily_inferences * PROMPT_STUDY.combined_tokens
    daily_token_saved = baseline_daily_tokens - optimized_daily_tokens
    
    # Calculate costs
    baseline_daily_cost = (baseline_daily_tokens / 1_000_000) * input_price
    optimized_daily_cost = (optimized_daily_tokens / 1_000_000) * input_price
    daily_savings = baseline_daily_cost - optimized_daily_cost
    
    # Annual projections
    annual_savings = daily_savings * 365
    
    print(f"\n{'='*70}")
    print(f"ECONOMIC ANALYSIS: Token Optimization ROI")
    print(f"{'='*70}")
    print(f"Model Pricing Used:       ${input_price:.2f} / 1M input tokens ({model_name})")
    print(f"Scale (Daily Inferences): {daily_inferences:,}")
    print(f"Reduction Strategy:       Combined (TOON Input + JSON Fallback)")
    print(f"Token Reduction:          {PROMPT_STUDY.combined_reduction_pct:.1%}")
    print(f"{'-'*70}")
    
    print(f"\nDaily Impact:")
    print(f"  Baseline Cost:          ${baseline_daily_cost:,.2f}")
    print(f"  Optimized Cost:         ${optimized_daily_cost:,.2f}")
    print(f"  Daily Savings:          ${daily_savings:,.2f}")
    
    print(f"\nAnnual Projection:")
    print(f"  Annual Savings:         ${annual_savings:,.2f}")
    print(f"{'='*70}")
    
    print(f"\nInterpretation:")
    print(f"At {daily_inferences/1_000_000:.1f}M daily requests, switching to TOON/Combined serialization")
    print(f"saves approximately ${annual_savings/1_000_000:.1f} million per year in inference costs.")
    print(
        f"This assumes the study prompt-only average of {PROMPT_STUDY.baseline_tokens} baseline tokens per request."
    )

def main():
    parser = argparse.ArgumentParser(description="Calculate token cost savings.")
    parser.add_argument(
        "--daily_inferences",
        type=int,
        default=1_000_000,
        help="Number of RAG inferences per day (provide your own volume)",
    )
    parser.add_argument("--input_token_price", type=float, default=0.15, help="Price per 1M input tokens (USD)")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", choices=MODELS.keys(), help="Preset model pricing")
    
    args = parser.parse_args()
    
    price = args.input_token_price
    model_name = "Custom"
    
    # Override custom price if model preset is selected and price wasn't manually changed
    if args.model in MODELS and args.input_token_price == 0.15:
        price = MODELS[args.model].input_price_per_1m
        model_name = MODELS[args.model].name
        
    calculate_savings(args.daily_inferences, price, model_name)

if __name__ == "__main__":
    main()
