"""Study-derived constants.

This module centralizes the numeric values that come from the published benchmark
outputs under `docs/`.

Why this exists
---------------
Several calculators in this repo (e.g., `analyze/economics.py`, `analyze/scale.py`)
need a consistent set of baseline/optimized token counts. Keeping them in one
place reduces the risk of documentation drift.

Notes
-----
- The primary values here are **prompt-only** token counts (context + query)
  reported in the paper's "Token Efficiency" table.
- This repo also discusses "end-to-end" totals (prompt + completion). Those are
  inherently workload-dependent because completion length varies.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTokenStudy:
    """Prompt-only (input) token counts per request from the benchmark study."""

    dataset: str
    baseline_tokens: int
    combined_tokens: int
    zon_combined_tokens: int
    json_minified_tokens: int

    @property
    def combined_reduction_pct(self) -> float:
        return (self.baseline_tokens - self.combined_tokens) / self.baseline_tokens

    @property
    def zon_combined_reduction_pct(self) -> float:
        return (self.baseline_tokens - self.zon_combined_tokens) / self.baseline_tokens

    @property
    def tokens_saved_per_request_combined(self) -> int:
        return self.baseline_tokens - self.combined_tokens


# Source: `docs/paper.md` section 4.1 "Token Efficiency Comparison"
PROMPT_STUDY = PromptTokenStudy(
    dataset="Shopify test store (17 products; benchmark queries)",
    baseline_tokens=7777,
    combined_tokens=4836,
    zon_combined_tokens=5086,
    json_minified_tokens=5520,
)


@dataclass(frozen=True)
class EndToEndTokenStudy:
    """End-to-end (prompt + completion) summary figures.

    These numbers are included as *illustrative* examples taken from the repo's
    benchmark summaries. They should not be treated as universal because output
    length depends on task and prompting.
    """

    dataset: str
    baseline_avg_tokens: int
    combined_avg_tokens: int

    @property
    def combined_reduction_pct(self) -> float:
        return (self.baseline_avg_tokens - self.combined_avg_tokens) / self.baseline_avg_tokens


# Source: `docs/cost_savings.md` section 2.
END_TO_END_STUDY = EndToEndTokenStudy(
    dataset="API run (example summary in docs/cost_savings.md)",
    baseline_avg_tokens=9043,
    combined_avg_tokens=5985,  # derived from 33.8% reduction in docs/cost_savings.md
)
