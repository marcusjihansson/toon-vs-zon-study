# Demo Scripts

This directory contains demo scripts that showcase the benchmarking functionality without requiring API keys or making real LLM calls.

## Available Demos

### 1. API Demo (`demo/api_demo.py`)

Demonstrates the Shopify API RAG benchmark using mock metrics.

```bash
python optimization_benefits/demo/api_demo.py
```

**What it does:**
- Simulates running benchmarks against the Shopify API data source
- Uses deterministic mock metrics (no real API calls)
- Shows all strategy comparisons (baseline, TOON, BAML, ZON, etc.)
- Displays analysis reports with token reduction percentages

### 2. Database Demo (`demo/db_demo.py`)

Demonstrates the SQLite Database RAG benchmark using mock metrics.

```bash
python optimization_benefits/demo/db_demo.py
```

**What it does:**
- Simulates running benchmarks against the database data source
- Uses deterministic mock metrics (no real API calls)
- Shows all strategy comparisons
- Displays analysis reports

### 3. Comparative Demo (`demo/comparative_demo.py`)

Demonstrates the API vs Database comparison using mock metrics.

```bash
python optimization_benefits/demo/comparative_demo.py
```

**What it does:**
- Simulates both API and Database benchmarks
- Compares performance between data sources
- Shows side-by-side analysis reports
- Uses deterministic mock metrics (no real API calls)

## Mock Metrics

All demo scripts use the mock metrics generator located in `test/mock_metrics.py`. This provides:

- **Deterministic results**: Same inputs always produce same outputs
- **Realistic patterns**: Mock data reflects expected performance characteristics
- **Strategy-specific behavior**: Each strategy has appropriate token reduction ratios
  - Baseline: No reduction (1.0x)
  - TOON: ~30% reduction (0.7x)
  - BAML: ~20% reduction (0.8x)
  - ZON: ~50% reduction (0.5x)
  - Combined: ~35% reduction (0.65x)

## Real Benchmarks

To run real benchmarks with actual LLM calls, use the main CLI scripts:

```bash
# Set your API key first
export OPENROUTER_API_KEY="your-key-here"

# Run real benchmarks
python cli/api.py          # API benchmark
python cli/db.py           # Database benchmark
python cli/compare.py      # Comparative benchmark
```

## Purpose

These demo scripts are useful for:
- **Testing**: Verify benchmark functionality without API costs
- **Demonstrations**: Show how the system works without requiring API access
- **Development**: Quickly test changes to analysis logic
- **Documentation**: Provide working examples of the benchmark system
