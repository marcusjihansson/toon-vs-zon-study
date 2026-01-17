# Reproducibility Guide

This guide provides step-by-step instructions to reproduce the findings presented in the paper **"TOON vs ZON: A Benchmark Study on Token-Efficient Serialization for LLM RAG Systems"**.

## Prerequisites

- **Python**: Version 3.11 or higher.
- **API Key**: An `OPENROUTER_API_KEY` is required to run live benchmarks against LLMs (specifically GPT-4o-mini as used in the study).
- **Package Manager**: `pip` (or `uv` for faster resolution).

## Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/marcusjihansson/memory_opt.git
    cd memory_opt
    ```

2.  **Install dependencies**:

    ```bash
    # Using pip (standard)
    pip install -e ".[research]"

    # OR using uv (faster)
    uv pip install -e ".[research]"
    ```

3.  **Configure Environment**:
    Create a `.env` file in the `optimization_benefits` directory:

    ```bash
    cd optimization_benefits
    cp .env.example .env
    # Edit .env and add your credentials
    ```

    Required variables:
    - `OPENROUTER_API_KEY` (required to run live LLM calls)
    - `SHOPIFY_URL` (e.g. `https://your-store.myshopify.com`)
    - `SHOPIFY_TOKEN` (Admin API access token)

    _Note: If `OPENROUTER_API_KEY` is missing, you can use the **demo scripts** located in `demo/` which use mock data and don't require any API keys. See [demo/README.md](../demo/README.md) for details._

## Running the Benchmarks

### 1. Full Comparison (Recommended)

To run the complete suite comparing live API performance against cached database performance:

```bash
./run_benchmark.sh
```

Or manually:

```bash
python cli/compare.py
```

This script will:

1.  Fetch live data from the Shopify Admin API.
2.  Sync this data to a local SQLite database for the "Cached" comparison.
3.  Run 5 standard queries across 9 serialization strategies.
4.  Output a comparative summary of Token Usage, Latency, and Reliability.

### 2. Individual Component Benchmarks

- **API-only Benchmark**:

  ```bash
  python cli/api.py
  ```

  Focuses solely on the performance of serializing live API responses.

- **Database-only Benchmark**:
  ```bash
  python cli/db.py
  ```
  Focuses on the performance of RAG over stored data (simulating a production vector/SQL retrieval system).

### 3. Demo Mode (No API Key Required)

If you don't have API keys or want to test the system without making real LLM calls:

```bash
python demo/api_demo.py          # API benchmark with mock data
python demo/db_demo.py           # Database benchmark with mock data
python demo/comparative_demo.py  # Comparative benchmark with mock data
```

See [demo/README.md](../demo/README.md) for more details on demo scripts.

## Economic Analysis

To project cost savings for your specific scale based on our experimental findings:

```bash
python analyze/economics.py --daily_inferences 1000000 --input_token_price 0.15
```

Arguments:

- `--daily_inferences`: Number of RAG calls per day (default: 1M; provide your own volume).
- `--input_token_price`: Cost per 1M input tokens (default: $0.15 for GPT-4o-mini).
- `--model`: Optional preset pricing model (see `--help`).

## Validating Results

The expected results (as of Jan 2026) should align with:

- **Baseline (JSON)**: ~7,700 tokens per query context.
- **Combined Strategy (TOON input/JSON fallback)**: ~4,800 tokens (approx. 37-38% reduction).
- **Reliability**: Combined strategies should show 100% parse success, while strict formats (TOON/ZON strict) will likely fail (0-20% success).

## Troubleshooting

- **Latency Outliers**: You may observe occasional high latency (e.g., >10s) with `zon_strict` or `zon_adapter`. This is a known issue discussed in the paper (likely due to LLM struggling to format the output).
- **Missing Data**: If the database is empty, `cli/compare.py` / `cli/db.py` will attempt to sync from the Shopify Admin API (`SHOPIFY_URL/admin/api/...`). Ensure `SHOPIFY_URL` and `SHOPIFY_TOKEN` are set correctly.
