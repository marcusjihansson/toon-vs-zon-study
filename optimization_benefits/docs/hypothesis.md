# Research Hypotheses

**Date**: January 2026  
**Project**: TOON/ZON Serialization Format Benchmark for RAG Systems

---

## Overview

This document outlines the original research hypotheses for comparing serialization formats (TOON, ZON, JSON, BAML) in RAG systems. The goal is to determine the optimal strategy for token efficiency while maintaining parsing reliability.

---

## Hypothesis 1: "Strict formats will fail for nested output structures"

### Premise

LLMs struggle to output valid TOON/ZON format for complex nested response structures. Even when explicitly instructed to use these formats, the LLM tends to default to JSON-like output with quoted keys and standard JSON syntax.

### Example of Complex Nested Structure

```python
response: {
    answer: "Based on the products available...",
    recommendations: [
        {product_id: 1, name: "Widget Pro", price: 49.99},
        {product_id: 2, name: "Gadget Basic", price: 19.99}
    ],
    total_products_reviewed: 5,
    confidence: 0.95
}
```

### Prediction

Strict strategies (`toon_strict`, `zon_strict`) that require exact TOON/ZON format output will achieve:
- `toon_strict`: 0-5% success rate
- `zon_strict`: 5-25% success rate (due to simpler tabular syntax)

### Rationale

1. TOON/ZON are not native formats for most LLMs
2. Complex nested structures require precise indentation and syntax
3. LLMs have been trained primarily on JSON/JSON-like data
4. Small syntax errors in TOON/ZON cause complete parsing failures

---

## Hypothesis 2: "Combined approaches will succeed with JSON fallback"

### Premise

By encoding input data in TOON/ZON format (for token savings during context window usage) but allowing JSON output parsing (for reliability), combined strategies can achieve the best of both worlds:
- Token reduction on input (TOON/ZON encoding)
- Guaranteed parsing success (JSON fallback)

### Strategy Design

```
Combined Strategy = TOON/ZON Input Encoding + JSON Output Parsing
```

1. **Input**: Data is encoded in TOON/ZON format for context window efficiency
2. **Output**: LLM responds in whatever format it prefers (usually JSON)
3. **Parsing**: If TOON/ZON parsing fails, fall back to JSON parsing
4. **Result**: Maximum savings with 100% reliability

### Prediction

Combined strategies will achieve:
- `combined`: 95-100% success rate
- `zon_combined`: 90-100% success rate

### Rationale

1. Input encoding is controlled by the system (deterministic)
2. Output parsing is adaptive (tries format, falls back if needed)
3. JSON is the native format for most LLMs
4. The fallback mechanism handles any output format

---

## Hypothesis 3: "TOON will outperform ZON for token reduction"

### Premise

TOON's more compact syntax will yield better token reduction than ZON's tabular format. TOON eliminates the colon prefix for values, resulting in shorter representations.

### Syntax Comparison

**TOON Format** (compact):
```
products: [
    {id: 1, name: "Widget", price: 49.99},
    {id: 2, name: "Gadget", price: 19.99}
]
```

**ZON Format** (tabular):
```
products: [
    | id | name   | price |
    |----|--------|-------|
    | 1  | Widget | 49.99 |
    | 2  | Gadget | 19.99 |
]
```

### Prediction

TOON-based strategies will consistently beat ZON-based strategies by 3-8% in token reduction:
- API benchmark: TOON wins by 3-5%
- Database benchmark: TOON wins by 8-12%

### Rationale

1. TOON eliminates the `:` prefix for values
2. ZON's table headers add overhead for small datasets
3. TOON's array notation is more compact for nested structures
4. The difference is more pronounced for complex nested data

---

## Hypothesis 4: "Combined strategies will show best trade-off"

### Premise

The optimal production strategy balances three metrics:
1. **Token Savings**: Reduction in context window usage
2. **Reliability**: Parsing success rate (must be 100% for production)
3. **Latency**: Processing overhead impact

### Trade-off Matrix

| Strategy | Token Savings | Reliability | Latency | Overall |
|----------|--------------|-------------|---------|---------|
| strict (TOON/ZON) | High (35-40%) | Low (0-5%) | Low | ❌ Poor |
| combined | High (35-40%) | High (100%) | Low | ✅ Optimal |
| json_baseline | Low (0%) | High (100%) | None | ⚠️ Baseline |
| baml_adapter | Medium (25-30%) | High (100%) | Low | ✅ Good |

### Prediction

Combined strategies will achieve the best overall score:
- Token savings: 35-42%
- Reliability: 90-100%
- Latency impact: Minimal or positive

### Rationale

1. Strict strategies fail reliability check (unacceptable for production)
2. JSON baseline wastes tokens (no optimization)
3. BAML is JSON-based (limited savings)
4. Combined strategies optimize input without sacrificing output reliability

---

## Test Setup

### Benchmarks

1. **Shopify API RAG**: 17 products, complex nested data
2. **SQLite Database RAG**: 17 products (synced from API; data parity), same structure as API

### Strategies Tested

| Category | Strategy | Description |
|----------|----------|-------------|
| Baseline | `baseline` | Standard JSON formatting |
| Compact JSON | `json_baseline` | Minified JSON |
| TOON | `toon_adapter` | TOON encoding + JSON fallback |
| TOON Strict | `toon_strict` | Pure TOON (no fallback) |
| ZON | `zon_adapter` | ZON encoding + JSON fallback |
| ZON Strict | `zon_strict` | Pure ZON (no fallback) |
| BAML | `baml_adapter` | BAML-inspired format |
| Combined | `combined` | TOON input + JSON fallback |
| ZON Combined | `zon_combined` | ZON input + JSON fallback |

### Metrics

- **Token Usage**: Number of tokens in context window
- **Success Rate**: Percentage of successful parsing
- **Latency**: Time from query to response

---

## Expected Results

### Before Fix (Initial Expectations)

| Strategy | Token Savings | Success Rate | Status |
|----------|--------------|--------------|--------|
| `toon_strict` | 37-42% | 0-5% | ❌ Fails reliability |
| `zon_strict` | 33-38% | 5-25% | ❌ Fails reliability |
| `toon_adapter` | 37-42% | 0% | ❌ Fails reliability |
| `zon_adapter` | 33-38% | 20% | ❌ Fails reliability |
| `combined` | 37-42% | 95-100% | ✅ Optimal |
| `zon_combined` | 33-38% | 90-100% | ✅ Good |

### After Fix (With JSON Fallback)

| Strategy | Token Savings | Success Rate | Status |
|----------|--------------|--------------|--------|
| `combined` | 37-42% | 100% | 🏆 Best |
| `zon_combined` | 33-38% | 100% | 🥈 Excellent |
| `baml_adapter` | 28-30% | 100% | ✅ Good |
| `json_baseline` | 25-30% | 100% | Baseline |

---

## Conclusion

The research aims to validate that:

1. **Strict formats are unsuitable for production** due to low reliability
2. **Combined strategies provide optimal balance** of savings and reliability
3. **TOON slightly outperforms ZON** in token reduction
4. **The optimization layer pattern works** at the LLM edge for RAG systems

---

**End of Document**
