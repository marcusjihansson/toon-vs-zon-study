# Reference Implementation

This directory contains reference implementations using [dspy-toon](https://github.com/Archelunch/dspy-toon), the official TOON (Token-Oriented Object Notation) adapter for DSPy that provides 40%+ token reduction for structured LLM outputs.

## Official Documentation

For complete documentation, examples, benchmarks, and updates, please refer to the official repository:
- **GitHub:** https://github.com/Archelunch/dspy-toon
- **PyPI:** https://pypi.org/project/dspy-toon/

## Overview

DSPy-TOON provides a custom adapter for [DSPy](https://github.com/stanfordnlp/dspy) that uses TOON format instead of JSON for structured outputs. TOON is a compact, human-readable serialization format optimized for LLM contexts, achieving **65% fewer output tokens** for tabular data.

## Files

- **`adapter.py`** - TOON adapter implementation for DSPy, providing structured output parsing with TOON format
- **`baml_adapter.py`** - BAML adapter implementation for comparison and alternative structured output handling

## Key Features

- 40%+ Total Token Reduction - Significant savings on both input and output tokens
- 65% Output Token Reduction - Tabular format dramatically reduces response tokens for lists
- Seamless DSPy Integration - Drop-in replacement for JSONAdapter
- Async & Streaming Support - Full support for `dspy.asyncify()` and `dspy.streamify()`

## Getting Started

For installation instructions, usage examples, and detailed API documentation, please visit the [official dspy-toon repository](https://github.com/Archelunch/dspy-toon).