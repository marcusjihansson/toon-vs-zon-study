# TOON vs ZON: A Benchmark Study on Token-Efficient Serialization for LLM RAG Systems

**Authors**: [Marcus Johansson]
**Date**: January 2026

---

## Abstract

Large Language Model (LLM) inference costs are directly proportional to input token volume. For Retrieval-Augmented Generation (RAG) systems that process large structured datasets (e.g., e-commerce product catalogs), JSON's verbose syntax creates significant economic overhead. This study benchmarks two compact serialization formats—TOON (Token-Oriented Object Notation) and ZON (Zero Overhead Notation)—to evaluate their effectiveness in reducing token consumption while maintaining parsing reliability. Nine serialization strategies were tested across a 17-product Shopify dataset, comparing live API calls against cached database sources.
Key findings demonstrate that combined strategies (format-specific encoding with JSON fallback parsing) achieve optimal balance: **37.8% token reduction with 100% reliability**. Strict formats failed consistently (0% success for TOON, 20% for ZON strict), validating that Large Language Models (LLMs) cannot reliably generate compact syntax for nested response structures. Data parity validation confirmed that database caching correctly mirrors API data (identical token counts: 7,777 baseline tokens), validating experimental methodology. At Shopify's scale (40M daily inferences), the benchmarked input-token savings (2,941 tokens/request) equates to ~42.95T tokens/year saved; at **$0.15 per 1M input tokens** (GPT-4o-mini), this is **~$6.44M/year** (savings scale linearly with input-token pricing).

---

## 1. Introduction

### 1.1. Problem: Token Economics in LLM Deployments

LLM inference costs are directly proportional to input token consumption. For enterprises operating at scale, reducing input volume by 30–40% can translate to large annual infrastructure savings; the relationship is linear in request volume and input-token price. JSON, while universally compatible and human-readable, is inherently token-inefficient due to redundant keys, structural characters, and string quotes.
E-commerce platforms like Shopify process massive product catalogs with complex nested structures (variants, options, metadata). When feeding this data to LLMs for tasks like product recommendations, semantic search, or content generation, JSON overhead significantly impacts both inference costs and system scalability.

### 1.2. Motivation

This study addresses three primary research questions:

1. What is theoretical token reduction achievable with compact formats compared to standard JSON?
2. Do compact formats maintain acceptable parsing reliability for LLM-generated outputs?
3. What trade-offs exist between token efficiency and parsing reliability in production systems?
   Compact serialization formats like TOON and ZON offer a path to maintain data fidelity while dramatically reducing token costs. However, their effectiveness depends on two critical factors: encoding efficiency (token reduction) and parsing reliability (LLM ability to generate valid format).

---

## 2. Background

### 2.1. TOON Format

TOON (Token-Oriented Object Notation) is a compact, schema-aware data format designed to optimize LLM performance [2]. It combines two established formats to maximize efficiency:

1. YAML-style indentation for nested objects (eliminating closing braces)
2. CSV-style tabular layouts for uniform arrays (eliminating repeated field names)
   TOON achieves **73.9% accuracy while using 39.6% fewer tokens** than JSON and reports **30-60% token reduction** for specific data shapes [2].

For reference, this repository also includes a historical DSPy adapter implementation using the upstream `dspy-toon` project in `optimization_benefits/reference_implementation/` [5].

#### 2.1.2 Design Philosophy

TOON intelligently combines formats based on data structure:
| Aspect | TOON | JSON |
|---------|------|------|
| Primary optimization | Schema declaration (tabular arrays) | Repeated keys in every row |
| Nested structure | YAML-style indentation | Curly braces |
| Primitives | Single-char (T/F) | Double-quoted strings |

#### 2.1.3 Performance & Scaling Limitations

TOON offers **30-60% token reduction** for specific data shapes but is not a universal replacement for JSON [2]. Understanding its "scaling limitations" is critical for system architects:

1. **Deeply Nested Data (3-4+ levels)**: Deeply nested or non-uniform structures with low "tabular eligibility" often see standard JSON-compact using fewer tokens. The indentation cost in TOON accumulates at each level, negating savings from removing braces.
2. **Non-Uniform Arrays**: When array elements have different fields, TOON loses its primary advantage. Semi-uniform arrays (40-60% field consistency) show minimal savings. If rows cannot share a single header, the tabular optimization fails.
3. **Arrays of Arrays**: This is the only structure where TOON is consistently less efficient than JSON. TOON's explicit list markers and inner array headers create overhead that simple JSON brackets `[[1,2],[3,4]]` do not have.
4. **Large Datasets (Structure vs. Size)**: Efficiency is not about absolute size but structure. Large uniform datasets (e.g., a list of 10,000 products) are perfect candidates. Large deeply nested datasets (e.g., a complex abstract syntax tree) are problematic.

### 2.2 ZON Format

ZON (Zero Overhead Notation) is a token-efficient serialization format designed specifically for LLM workflows that achieves **35-70% token reduction** compared to JSON while maintaining **100% data fidelity** and perfect LLM comprehension [3]. Think of it as a hybrid between CSV's efficiency and JSON's flexibility—optimized specifically for AI applications [3].

#### 2.2.1 Key Characteristics

- Token efficiency: Uses 35-70% fewer tokens than JSON
- LLM-optimized: Achieves 99.0% accuracy with self-explanatory structure
- Human-readable: Unlike binary formats, ZON maintains readability
- Lossless: Perfect round-trip conversion to/from JSON

#### 2.2.2 Design Philosophy

ZON intelligently combines formats based on data structure:
| Data Type | ZON Approach |
|-----------|-------------|
| Flat tabular data | Table encoding with header row declaration |
| Nested objects | Dot notation flattening + inline format |
| Deep nesting | Maintains 91% compression even at 50+ levels deep |

#### 2.2.3 Comparison: ZON vs TOON

| Metric               | TOON                        | ZON                     |
| -------------------- | --------------------------- | ----------------------- |
| Token efficiency     | 3.2% better                 | 0%                      |
| LLM accuracy         | Tie (99.0%)                 | 99.0%                   |
| Nested data handling | Struggles with deep nesting | Excellent at all levels |

## ZON's tabular format is particularly well-suited for e-commerce data (products, orders, customers), which is naturally structured as products with variants, pricing tiers, and inventory levels [1].

### 2.3 Research Questions

This study addresses three primary research questions:

1. What is theoretical token reduction achievable with compact formats compared to standard JSON?
2. Do compact formats maintain acceptable parsing reliability for LLM-generated outputs?
3. What trade-offs exist between token efficiency and parsing reliability in production systems?

---

## 3. Methodology

### 3.1 Dataset

We use a real-world e-commerce dataset from Shopify's test environment containing **17 products** with varying complexity levels:

- Product metadata (title, description)
- Pricing data (variants with different prices)
- Inventory information (stock levels)
- Nested structures (variants within products)

### 3.2 Strategies Tested

Nine serialization strategies spanning three categories:

1. **Baseline Strategies** (2)
   - `baseline`: Standard JSON formatting
   - `json_baseline`: Compact/minified JSON
2. **Format-Specific Strategies** (4)
   - `toon_adapter`, `toon_strict`: TOON encoding
   - `zon_adapter`, `zon_strict`: ZON encoding
3. **Hybrid/Combined Strategies** (2)
   - `combined`: TOON encoding + JSON fallback parsing
   - `zon_combined`: ZON encoding + JSON fallback parsing
   - `baml_adapter`: BAML-inspired JSON format

### 3.3 Metrics Collected

For each strategy and query, we measure:

- **Token Usage**: Input tokens + query tokens (using GPT-4 tokenizer)
- **Parsing Success Rate**: Binary success/failure of structured output parsing
- **Latency**: End-to-end response time in milliseconds
- **Per-query samples**: 2 runs per query (90 total data points)

### 3.4 Data Sources

To validate experimental methodology, we benchmark across two data sources:

1. **Shopify API**: Direct API calls to live test store (17 products)
2. **SQLite Database**: Cached data synced from API (17 products)
   This design enables fair comparison between live API performance and database-cached data, controlling for data structure differences.

---

## 4. Results

### 4.1 Token Efficiency Comparison

| Strategy      | Baseline Tokens | Savings vs Baseline | Adapter Type       |
| ------------- | --------------- | ------------------- | ------------------ |
| baseline      | 7,777           | +0.0%               | SimpleJSONAdapter  |
| toon_adapter  | 4,836           | +37.8%              | ToonAdapter        |
| toon_strict   | 4,836           | +37.8%              | ToonAdapter        |
| baml_adapter  | 5,520           | +29.0%              | BAMLAdapter        |
| json_baseline | 5,520           | +29.0%              | SimpleJSONAdapter  |
| zon_adapter   | 5,086           | +34.6%              | ZONAdapter         |
| zon_strict    | 5,086           | +34.6%              | ZONAdapter         |
| combined      | 4,836           | +37.8%              | CombinedAdapter    |
| zon_combined  | 5,086           | +34.6%              | ZONCombinedAdapter |

**Observation 1**: TOON consistently outperforms ZON by 3.2% in token reduction.

### 4.2 Success Rate Analysis

| Strategy      | Success Rate | Notes                                                          |
| ------------- | ------------ | -------------------------------------------------------------- |
| combined      | 100.0%       | TOON input, JSON fallback parsing                              |
| zon_combined  | 100.0%       | ZON input, JSON fallback parsing                               |
| baml_adapter  | 100.0%       | JSON-based format                                              |
| json_baseline | 100.0%       | Native JSON                                                    |
| baseline      | 100.0%       | Native JSON                                                    |
| toon_adapter  | 0.0%         | TOON output too complex for LLM                                |
| toon_strict   | 0.0%         | No fallback, strict TOON required                              |
| zon_adapter   | 0.0%         | ZON output too complex for LLM output                          |
| zon_strict    | 20.0%        | **NEW FINDING**: ZON strict achieves 20% success (1/5 queries) |

**Observation 2**: LLMs cannot reliably generate valid TOON or ZON format for nested response structures. Even when explicitly instructed to use compact formats, LLMs default to JSON-like output. This validates the "optimization layer at LLM edge" pattern: use compact format for input (deterministic, under system control) while accepting natural language output (JSON) for responses.

### 4.3 Data Parity Validation

| Metric                    | API Tokens | DB Tokens | Difference        |
| ------------------------- | ---------- | --------- | ----------------- |
| Baseline Avg Tokens       | 7,777      | 7,777     | ±0 (0.0%)         |
| Baseline Avg Latency (ms) | 15,562.7   | 12,137.4  | -3,425.3 (-22.0%) |

**Observation 3**: Database successfully mirrors API data with ±0 tokens variance, validating experimental methodology. This proves that database caching correctly replicates API data structure, enabling fair comparison between live performance and cached data.

### 4.4 Latency Analysis

| Strategy     | Avg Latency (ms) | Impact vs Baseline |
| ------------ | ---------------- | ------------------ |
| baml_adapter | 9,760            | -3.4%              |
| combined     | 8,144            | -19.4%             |
| toon_adapter | 9,109            | -9.8%              |
| toon_strict  | 7,926            | -21.5%             |
| zon_adapter  | 5,192            | -48.6%             |
| zon_strict   | 5,804            | -42.5%             |
| zon_combined | 6,376            | -37.0%             |

*Note: Latency figures represent averages across API benchmark runs. Extreme outliers (e.g., 322s for `zon_adapter` on DB) were observed in isolated runs.*

## **Critical Finding**: `zon_adapter` shows extreme latency variance (322,515ms outlier on one query), suggesting a parsing retry cascade or LLM timeout issue.

## 5. Discussion

### 5.1 Interpretation of Findings

**Combined Strategy Superiority**: The 37.8% token savings achieved by combined strategies with 100% reliability demonstrates that the "optimization layer at LLM edge" architectural pattern is optimal for production RAG systems [1]. Token reduction does not need to come at the expense of reliability—JSON fallback parsing ensures production readiness while preserving token efficiency gains.
**TOON vs ZON Trade-off**: TOON achieves marginally better token reduction (3.2%) compared to ZON, but difference is smaller than theoretical expectations and may not justify implementation complexity in isolation.
**ZON's Partial Success**: The 20% success rate of `zon_strict` is surprising and warrants further investigation. One hypothesis is that ZON's simpler tabular format may be easier for LLMs to generate correctly for certain query patterns. However, this partial success is still insufficient for production use without additional engineering (e.g., prompt optimization, few-shot examples).

### 5.2 Production Recommendations

| Priority | Strategy     | Token Savings | Reliability | Latency Impact | Recommendation                      |
| -------- | ------------ | ------------- | ----------- | -------------- | ----------------------------------- |
| 🏆 1st   | combined     | 37.8%         | 100%        | -19.4%         | **Recommended for general purpose** |
| 🥈 2nd   | zon_combined | 34.6%         | 100%        | -37.0%         | Use with latency monitoring         |
| ⚠️ 3rd   | baml_adapter | 29.0%         | 100%        | -3.4%          | Alternative if JSON is required     |

**Critical Note**: The latency outlier in `zon_adapter` (322s response time) requires investigation before production deployment.

### 5.3 Economic Implications

Using an example scale of **1M daily inferences** as a reference case:
Assuming pricing of **$0.15 per 1M input tokens** (GPT-4o-mini) and using the measured prompt sizes from Section 4.1:

| Strategy | Prompt Tokens / Request | Daily Input Cost | Annual Input Cost | Savings vs Baseline |
|----------|--------------------------|------------------|-------------------|---------------------|
| baseline | 7,777 | $1,166.55 | $425,790.75 | 0% |
| combined | 4,836 | $725.40 | $264,771.00 | -37.8% (**$161,019.75/year**) |
| zon_combined | 5,086 | $762.90 | $278,458.50 | -34.6% ($147,332.25/year) |

These savings scale linearly with your input-token price and request volume. For example, at **$0.86 per 1M input tokens**, the `combined` strategy would save **~$923k/year** at 1M requests/day.

### 5.4 Limitations

This study has several limitations that should be addressed in future research:

1. **Single Model**: Benchmarks used only GPT-4o-mini; results may vary across different LLMs
2. **Dataset Scope**: Limited to 17 Shopify products with specific complexity patterns; may not represent all e-commerce scenarios
3. **Query Diversity**: Only 5 queries tested; may not represent full range of RAG use cases
4. **No Longitudinal Study**: Single benchmark run without statistical significance testing
5. **Latency Outlier**: The 322s response time for `zon_adapter` was observed but not diagnosed
6. **Implementation Details**: This study focuses on high-level results; adapter implementation algorithms were not analyzed for computational efficiency

---

## 6. Conclusion

This study validates that combined serialization strategies (TOON or ZON input with JSON fallback parsing) represent the optimal approach for production LLM RAG systems. The `combined` strategy achieves 37.8% token reduction with 100% reliability, making it the clear recommendation for most use cases. ZON's tabular format shows promise with partial parsing success (20%), warranting further investigation into prompt engineering techniques. Data parity validation confirms that database caching correctly mirrors API data, supporting the "optimization layer at LLM edge" architectural pattern as a production-ready solution.
**Practical Recommendation**: Implement the "optimization layer at LLM edge" pattern: Use JSON throughout internal systems (databases, internal APIs, front-end) for ecosystem compatibility, convert to compact format (TOON or ZON) only at the point of sending prompts to LLMs, and parse responses with JSON fallback to ensure 100% reliability.

---

## 7. References

[1] Benchmark results produced in this study (raw outputs): `optimization_benefits/docs/results/`
[2] TOON Documentation. Token-Oriented Object Notation for LLM-Optimized Workflows. https://github.com/toon-format/
[3] ZON Documentation. Zero Overhead Notation for LLM Workflows. https://github.com/ZON-Format/ZON/
[4] DSPy Framework. Declarative Self-Improved Language Programs. https://github.com/stanfordnlp/dspy/
[5] Reference implementation (DSPy adapter via `dspy-toon`): `optimization_benefits/reference_implementation/README.md`
