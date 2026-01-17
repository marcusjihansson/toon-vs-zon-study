# Cost & Savings Notes (derived from `docs/results/`)

This file is a short, reproducible summary of cost/latency considerations. For the authoritative benchmark outputs, see:

- `docs/results/api_results.txt`
- `docs/results/db_results.txt`
- `docs/results/comparative_results.txt`

## 1) Why strict formats fail while combined strategies succeed

The benchmark results show:

- `toon_strict`: **0%** parse success
- `zon_strict`: **20%** parse success (DB run)
- `combined` / `zon_combined`: **100%** parse success

This matches the observed behavior that LLMs default to emitting JSON-like structures for nested outputs, while the combined adapters recover by parsing JSON when strict parsing fails.

## 2) Token savings: prompt-only vs end-to-end

There are two different “token” measurements in this repo:

1. **Prompt token size** (context + query), reported in the "TOKEN EFFICIENCY COMPARISON" sections.
2. **End-to-end total tokens** (prompt + completion), reported in the "STRATEGY ANALYSIS REPORT" summary.

Example (API run, 17 products):

- Prompt-only: `baseline` **7,777** → `combined` **4,836** (**-37.8%**)
- End-to-end: `baseline` avg **9,043** → `combined` avg token reduction **-33.8%**

## 3) Latency: typical ranges vs outliers

Latency is noisy and can include extreme outliers:

- `zon_adapter` (DB run): **322,515ms** for query "What products are available?" (source: `docs/results/comparative_results.txt`)
- `zon_strict` (DB run): **307,684ms** for query "Are there any products under $50?" (source: `docs/results/db_results.txt`)

These outliers are consistent with a parse-failure retry cascade and/or provider retries.

## 4) Economic impact (input tokens)

If your cost model is primarily driven by **input tokens**, then annual savings scale linearly with:

```
annual_savings_usd = (baseline_tokens - optimized_tokens)
                     * daily_inferences
                     / 1_000_000
                     * input_price_per_1m
                     * 365
```

Using the measured prompt sizes (7,777 → 4,836) and an example volume of **1M requests/day**:

- Tokens saved / request: **2,941**
- Tokens saved / year: **~1.07T**
- At **$0.15 / 1M input tokens**: **~$161k/year**

For a turnkey calculator, run:

```bash
python analyze/economics.py --help
python analyze/economics.py --daily_inferences 1000000 --input_token_price 0.15
```
