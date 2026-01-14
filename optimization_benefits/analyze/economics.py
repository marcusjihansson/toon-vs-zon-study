#!/usr/bin/env python3
"""
economics.py - Economic Analysis of Token Savings

This script projects annual infrastructure savings based on token reduction
metrics observed in the benchmark study. It allows industry professionals to
input their own scale (daily inferences) and pricing models to estimate ROI.

Usage:
    python analyze/economics.py [--daily_inferences N] [--input_token_price P]

Defaults based on Shopify scale (40M/day) and GPT-4o-mini pricing.
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

# Benchmark Findings (from paper.md)
BASELINE_TOKENS = 7777
COMBINED_TOKENS = 4836
SAVINGS_PCT = 0.378

def calculate_savings(
    daily_inferences: int,
    input_price: float,
    model_name: str = "Custom"
):
    """
    Calculate and print economic analysis.
    """
    
    # Calculate daily volumes
    baseline_daily_tokens = daily_inferences * BASELINE_TOKENS
    optimized_daily_tokens = daily_inferences * COMBINED_TOKENS
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
    print(f"Token Reduction:          {SAVINGS_PCT:.1%}")
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
    print(f"This assumes the benchmarked average of {BASELINE_TOKENS} tokens per context.")

def main():
    parser = argparse.ArgumentParser(description="Calculate token cost savings.")
    parser.add_argument("--daily_inferences", type=int, default=40_000_000, help="Number of RAG inferences per day")
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
