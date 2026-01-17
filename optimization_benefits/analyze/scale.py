"""analyze/scale.py

Scale impact calculator.

This module answers: "If my prompt shrinks by (p)% (or from A tokens to B tokens),
what does that mean at N requests?".

Unlike earlier drafts, this file intentionally avoids *hard-coded traffic scale
claims* (e.g. hard-coded "X/day" numbers in docs) and instead provides a parameterized calculator.

Defaults are sourced from the benchmark study in `docs/` via
`analyze.study_constants.PROMPT_STUDY`.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

try:
    # Preferred when executed as a module: `python -m analyze.scale`
    from .study_constants import PROMPT_STUDY
except ImportError:  # pragma: no cover
    # Fallback for direct execution: `python analyze/scale.py`
    # NOTE: when executed this way, the `analyze/` directory is on sys.path and
    # `analyze/analyze.py` shadows the `analyze` package name.
    from study_constants import PROMPT_STUDY


@dataclass(frozen=True)
class ScaleImpact:
    n_requests: int
    baseline_tokens_per_request: float
    optimized_tokens_per_request: float
    token_reduction_pct: float

    total_tokens_baseline: float
    total_tokens_optimized: float
    total_tokens_saved: float

    baseline_cost_usd: float
    optimized_cost_usd: float
    savings_usd: float

    # Optional throughput modeling (token budget per minute)
    tpm_limit: float | None
    hours_baseline: float | None
    hours_optimized: float | None
    hours_saved: float | None

    # Capacity: extra requests you can run for the old token budget
    extra_requests_for_same_budget: float


def calculate_scale_impact(
    *,
    n_requests: int,
    baseline_tokens_per_request: float,
    optimized_tokens_per_request: float,
    input_price_per_1m_tokens: float,
    tpm_limit: float | None = None,
) -> ScaleImpact:
    if n_requests <= 0:
        raise ValueError("n_requests must be > 0")
    if baseline_tokens_per_request <= 0:
        raise ValueError("baseline_tokens_per_request must be > 0")
    if optimized_tokens_per_request <= 0:
        raise ValueError("optimized_tokens_per_request must be > 0")
    if input_price_per_1m_tokens < 0:
        raise ValueError("input_price_per_1m_tokens must be >= 0")

    token_reduction_pct = (
        baseline_tokens_per_request - optimized_tokens_per_request
    ) / baseline_tokens_per_request

    total_tokens_baseline = n_requests * baseline_tokens_per_request
    total_tokens_optimized = n_requests * optimized_tokens_per_request
    total_tokens_saved = total_tokens_baseline - total_tokens_optimized

    baseline_cost = (total_tokens_baseline / 1_000_000) * input_price_per_1m_tokens
    optimized_cost = (total_tokens_optimized / 1_000_000) * input_price_per_1m_tokens
    savings = baseline_cost - optimized_cost

    hours_baseline = hours_optimized = hours_saved = None
    if tpm_limit is not None:
        if tpm_limit <= 0:
            raise ValueError("tpm_limit must be > 0 when provided")
        minutes_baseline = total_tokens_baseline / tpm_limit
        minutes_optimized = total_tokens_optimized / tpm_limit
        hours_baseline = minutes_baseline / 60
        hours_optimized = minutes_optimized / 60
        hours_saved = hours_baseline - hours_optimized

    # capacity: requests possible with the baseline total token budget
    requests_for_same_budget = total_tokens_baseline / optimized_tokens_per_request
    extra_requests = requests_for_same_budget - n_requests

    return ScaleImpact(
        n_requests=n_requests,
        baseline_tokens_per_request=baseline_tokens_per_request,
        optimized_tokens_per_request=optimized_tokens_per_request,
        token_reduction_pct=token_reduction_pct,
        total_tokens_baseline=total_tokens_baseline,
        total_tokens_optimized=total_tokens_optimized,
        total_tokens_saved=total_tokens_saved,
        baseline_cost_usd=baseline_cost,
        optimized_cost_usd=optimized_cost,
        savings_usd=savings,
        tpm_limit=tpm_limit,
        hours_baseline=hours_baseline,
        hours_optimized=hours_optimized,
        hours_saved=hours_saved,
        extra_requests_for_same_budget=extra_requests,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scale impact calculator using study-derived token counts (parameterized)."
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=1_000_000,
        help="Number of requests to model.",
    )
    parser.add_argument(
        "--baseline_tokens",
        type=float,
        default=float(PROMPT_STUDY.baseline_tokens),
        help="Baseline prompt tokens per request (default: study baseline).",
    )
    parser.add_argument(
        "--optimized_tokens",
        type=float,
        default=float(PROMPT_STUDY.combined_tokens),
        help="Optimized prompt tokens per request (default: study combined).",
    )
    parser.add_argument(
        "--input_price_per_1m",
        type=float,
        default=0.15,
        help="USD per 1M input tokens (set to your provider/model price).",
    )
    parser.add_argument(
        "--tpm_limit",
        type=float,
        default=None,
        help="Optional token-per-minute budget to estimate time-to-process.",
    )
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()

    impact = calculate_scale_impact(
        n_requests=args.requests,
        baseline_tokens_per_request=args.baseline_tokens,
        optimized_tokens_per_request=args.optimized_tokens,
        input_price_per_1m_tokens=args.input_price_per_1m,
        tpm_limit=args.tpm_limit,
    )

    print("=" * 70)
    print("SCALE IMPACT (prompt tokens)")
    print("=" * 70)
    print(f"Requests:                 {impact.n_requests:,}")
    print(
        f"Tokens / request:         {impact.baseline_tokens_per_request:,.0f} → {impact.optimized_tokens_per_request:,.0f}"
    )
    print(f"Token reduction:          {impact.token_reduction_pct:.1%}")
    print(f"Total tokens saved:       {impact.total_tokens_saved:,.0f}")
    print(f"Baseline cost (USD):      ${impact.baseline_cost_usd:,.2f}")
    print(f"Optimized cost (USD):     ${impact.optimized_cost_usd:,.2f}")
    print(f"Savings (USD):            ${impact.savings_usd:,.2f}")
    print(
        f"Extra requests (same token budget): {impact.extra_requests_for_same_budget:,.0f}"
    )

    if impact.tpm_limit is not None:
        print("-" * 70)
        print(f"TPM limit:                {impact.tpm_limit:,.0f}")
        print(f"Time baseline:            {impact.hours_baseline:.2f} hours")
        print(f"Time optimized:           {impact.hours_optimized:.2f} hours")
        print(f"Time saved:               {impact.hours_saved:.2f} hours")


if __name__ == "__main__":
    # Support both `python -m analyze.scale` and `python analyze/scale.py`.
    # When executed as a script, relative imports may fail depending on PYTHONPATH.
    main()
