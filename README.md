# TOON Research Repository

> Research project exploring token-efficient serialization formats for LLM RAG systems.

## Overview

This repository contains the benchmark study and reference implementation for the paper:

**"TOON vs ZON: A Benchmark Study on Token-Efficient Serialization for LLM RAG Systems"**

The study compares JSON, TOON, and ZON serialization formats for Retrieval-Augmented Generation (RAG) systems, focusing on token efficiency, parsing reliability, and economic implications at scale.

## Key Findings

- **37.8% token reduction** using the "Combined Strategy" (TOON input + JSON fallback)
- **100% reliability** maintained with JSON fallback parsing
- Savings scale linearly with input-token pricing (e.g. at **1M requests/day**, about **~$161k/year** at **$0.15 per 1M input tokens**; see `optimization_benefits/analyze/economics.py`)

## Projects

| Directory | Description |
|-----------|-------------|
| [optimization_benefits/](./optimization_benefits/) | Complete benchmark suite, adapters, and analysis tools |

## Quick Start

```bash
cd optimization_benefits
./run_benchmark.sh
```

See [optimization_benefits/docs/REPRODUCIBILITY.md](./optimization_benefits/docs/REPRODUCIBILITY.md) for detailed setup instructions.

Or try the demo scripts without API keys:
```bash
python optimization_benefits/demo/comparative_demo.py
```

## License

MIT
