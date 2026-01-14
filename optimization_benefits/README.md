# TOON vs ZON: Benchmark Study & Implementation Guide

> **Latest Research (Jan 2026)**: This repository contains the reference implementation and benchmark suite for the paper *"TOON vs ZON: A Benchmark Study on Token-Efficient Serialization for LLM RAG Systems"*.

## 🚀 Executive Summary

We benchmarked token-efficient serialization formats (TOON and ZON) against standard JSON for high-scale RAG systems (e.g., e-commerce product catalogs).

**Key Findings:**
- **Winner**: "Combined Strategy" (TOON input + JSON fallback parsing).
- **Impact**: **37.8% reduction** in input tokens.
- **Reliability**: **100% success rate** (resolving the reliability issues of strict compact formats).
- **ROI**: At 40M daily inferences, savings scale linearly with input-token pricing (e.g. **~$6.44M/year** at **$0.15 per 1M input tokens**; see `analyze/economics.py`).

## 📂 Repository Structure

```
optimization_benefits/
├── cli/
│   ├── compare.py          # CLI: API vs DB comparison benchmark
│   ├── api.py              # CLI: API-only benchmark
│   ├── db.py               # CLI: DB-only benchmark
│   └── execution/          # Actual execution scripts (moved from root)
│       ├── comparative_main.py
│       ├── api_main.py
│       └── db_main.py
├── demo/                   # Demo scripts with mock data (no API key needed)
│   ├── api_demo.py
│   ├── db_demo.py
│   ├── comparative_demo.py
│   └── README.md
├── docs/
│   ├── paper.md            # Full academic paper with detailed analysis
│   ├── new_formats/        # Reference documentation for TOON and ZON
│   └── results/            # Raw benchmark output files (source of truth)
├── adapters/               # Core serialization logic
│   ├── serializers.py      # Universal interface for JSON, TOON, ZON
│   └── combined_adapter.py # The recommended production implementation
├── analyze/
│   ├── analyze.py          # Benchmark engine
│   └── economics.py        # ROI calculator script
├── database/
│   └── store.py            # SQLite cache helpers (DB file stored under api/)
├── strategies/             # DSPy strategy implementations
├── test/                   # Test utilities and mock data generators
│   ├── mock_metrics.py
│   └── test_implementation.py
├── run_benchmark.sh        # One-command benchmark runner
└── docs/REPRODUCIBILITY.md # Guide to running the experiments
```

## 🛠 Quick Start

### 1. Reproduce the Research
Follow the steps in [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) to run the full benchmark suite on your local machine.

```bash
# Run full comparison
./run_benchmark.sh

# Or run directly
python cli/compare.py
```

### 2. Calculate Your Savings
Use our provided economic analysis tool to estimate ROI for your specific traffic scale.

```bash
# Example: 5 million daily requests
python analyze/economics.py --daily_inferences 5000000
```

## 💡 The "Combined Strategy" Pattern

The study concludes that the optimal architectural pattern for production systems is **Boundary Optimization**:

1.  **Storage Layer**: Keep data in standard JSON/SQL (for compatibility).
2.  **Prompt Construction**: Convert to TOON/ZON *just-in-time* before sending to LLM (reduces input cost).
3.  **Response Handling**: Instruct LLM to reply in standard JSON (guarantees parsing reliability).

### Example Implementation

```python
# See adapters/serializers.py for full code
def get_llm_context(products: List[Dict]):
    # 1. Convert to TOON for input (Save ~38% tokens)
    return toon.encode(products)

def parse_llm_response(response_text: str):
    # 2. Parse standard JSON output (100% Reliability)
    return json.loads(response_text)
```

## 📚 Documentation

- [**Read the Full Paper**](docs/paper.md): In-depth analysis of methodology, results, and discussion.
- [**Reproducibility Guide**](docs/REPRODUCIBILITY.md): Setup instructions for the benchmark suite.
- [**Demo Scripts**](demo/README.md): Try the benchmarks without API keys using mock data.

## References

- **TOON Format**: [github.com/toon-format](https://github.com/toon-format/)
- **ZON Format**: [github.com/ZON-Format/ZON](https://github.com/ZON-Format/ZON/)
- **DSPy**: [github.com/stanfordnlp/dspy](https://github.com/stanfordnlp/dspy/)
