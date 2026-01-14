# TOON: Token-Oriented Object Notation

**A compact, schema-aware data format designed to optimize Large Language Model (LLM) performance.**

## What is TOON?

**TOON** (Token-Oriented Object Notation) is a data serialization format created to address a critical inefficiency in AI systems: the verbose grammar of JSON. While JSON is the standard for web APIs, its reliance on repeated keys, curly braces, and quotes generates excessive tokens—the "currency" of LLM computing and billing.

TOON is **lossless** (convertible 1:1 with JSON) and designed to be human-readable while minimizing the token footprint for structured data.

### Design Philosophy

  TOON combines two established formats to maximize efficiency:

  1. **YAML-style indentation** for nested objects (eliminating closing braces)
  2. **CSV-style tabular layouts** for uniform arrays (eliminating repeated field names)

### Key Performance Metrics

  - **Token Efficiency:** TOON achieves **73.9% accuracy** while using **39.6% fewer tokens** than JSON
  - **Token Reduction:** Reports indicate a **30-60%** token reduction compared to traditional JSON
  - **Lossless Conversion:** Fully compatible with JSON for bidirectional conversion without data loss

### Syntax Comparison

**Standard JSON:**
_High redundancy in repeated keys ("id", "name", "role") and structural characters._

```json
{
  "users": [
    { "id": 1, "name": "Alice", "role": "admin" },
    { "id": 2, "name": "Bob", "role": "editor" },
    { "id": 3, "name": "Charlie", "role": "viewer" }
  ]
}
```

**TOON:**
_Declares schema once; data follows in a dense, token-efficient stream._

```toon
users[3]{id,name,role}:
  1,Alice,admin
  2,Bob,editor
  3,Charlie,viewer
```

---

## Performance & Scaling Limitations

While TOON offers token reductions of **30-60%** for specific data shapes, it is not a universal replacement for JSON. Understanding its "scaling limitations" is vital for system architects.

### Where TOON's Scaling Limitations Come Into Play

TOON has specific weaknesses in these scenarios:

1. **Deeply Nested Data (3-4+ levels):**
   Deeply nested or non-uniform structures with "tabular eligibility" around 0% often see standard JSON-compact using fewer tokens. The indentation cost in TOON accumulates at each level, negating the savings from removing braces.

2. **Non-Uniform Arrays:**
   When array elements have different fields, TOON loses its primary advantage. Benchmark data shows that semi-uniform arrays with only 40-60% field consistency see minimal savings. If rows cannot share a single header, the tabular optimization fails.

3. **Arrays of Arrays:**
   This is the only structure where TOON is consistently less efficient than JSON. TOON's requirement for explicit list markers and inner array headers creates overhead that simple JSON brackets `[[1,2],[3,4]]` do not have.

4. **Large Datasets (Structure vs. Size):**
   Efficiency is not about absolute size but structure. Large _uniform_ datasets (e.g., a list of 10,000 products) are perfect candidates. Large _deeply nested_ datasets (e.g., a complex abstract syntax tree) are problematic.

---

## Strategic Implementation

### Strategic Use in Agent Systems

**The key insight is: Use TOON strategically at specific boundaries, not everywhere.**

The recommended architecture pattern is:

1. **Internal Systems:** Use JSON throughout your application (databases, internal APIs, front-end) to maintain ecosystem compatibility.
2. **The LLM Boundary:** Convert data to TOON _only_ at the point of sending the prompt to the LLM.
3. **Output Parsing:** If the LLM replies in TOON, convert it back to JSON immediately for internal processing.

This "Just-In-Time" conversion strategy gives you the rich ecosystem benefits of JSON with TOON's cost and latency efficiency where it matters most.

### Core Pattern: Boundary Optimization

To maximize benefits without incurring technical debt, use TOON strategically at specific boundaries rather than replacing JSON entirely:

- **Internal Architecture:** Use JSON throughout your application (databases, internal APIs, front-end) to maintain ecosystem compatibility
- **The LLM Boundary:** Convert data to TOON _only_ when sending the prompt to the LLM
- **The Return Loop:** If the LLM outputs data, parse the TOON response back into JSON immediately for internal processing

This approach provides the rich ecosystem benefits of JSON with TOON's efficiency where it counts: the inference cost.

---

## Case Study: Optimizing LLM Performance at Shopify

**Context:**

Shopify processes billions of product listings and manages a "Global Catalogue" to standardize unstructured merchant data. Their architecture relies heavily on LLM inferences to classify products, generate descriptions, and power agentic sidekicks.

**The Problem:**

Shopify's `Product` objects are notoriously heavy. A single API call might return a JSON payload containing dozens of variants, options, and meta-fields. When fed into an LLM for tasks like "Generate a marketing email for this product collection," the JSON overhead significantly eats into the context window and drives up inference costs.

### Scenario: The "Product Collection" Prompt

**Original JSON Payload (High Token Cost):**
_Repeated keys `variant_id`, `price`, `sku`, and `inventory_qty` for every variant waste hundreds of tokens per product._

```json
{
  "collection": "Summer Sale",
  "products": [
    {
      "title": "Ocean Breeze T-Shirt",
      "vendor": "Shopify",
      "variants": [
        {
          "variant_id": 4391,
          "price": "25.00",
          "sku": "TSH-BLU-S",
          "inventory_qty": 150
        },
        {
          "variant_id": 4392,
          "price": "25.00",
          "sku": "TSH-BLU-M",
          "inventory_qty": 120
        },
        {
          "variant_id": 4393,
          "price": "25.00",
          "sku": "TSH-BLU-L",
          "inventory_qty": 80
        }
      ]
    }
    // ... repeated for 50 more products
  ]
}
```

**Optimized TOON Payload:**
_Using TOON's tabular array feature for the variants list._

```toon
collection: Summer Sale
products[50]{title,vendor,variants}:
  Ocean Breeze T-Shirt,Shopify,
    variants[3]{variant_id,price,sku,inventory_qty}:
      4391,25.00,TSH-BLU-S,150
      4392,25.00,TSH-BLU-M,120
      4393,25.00,TSH-BLU-L,80
  // ... subsequent products
```

### Impact Analysis for Shopify

1. **Token Reduction (~45%):**
   For a prompt containing 50 products with 5 variants each, the elimination of repeated keys (`"variant_id"`, `"price"`, etc.) saves thousands of tokens per request.

2. **Latency Improvement:**
   LLM generation speed (Time to First Token and Total Processing Time) is inversely proportional to input size. By compressing the input, Shopify's AI agents can reason over larger catalogs faster.

3. **Cost Savings at Scale:**
   At 40 million daily inferences (a figure aligned with Shopify's scale), a 40% reduction in input token volume translates to massive infrastructure savings, whether using external APIs (OpenAI/Anthropic) or self-hosted models (Llama/Mistral on Triton Inference Server).

4. **Enhanced Context Window:**
   TOON allows the model to "see" more products in a single pass. Instead of fitting only 20 products into a context window for a recommendation task, TOON allows fitting 35-40 products, improving the quality of the AI's reasoning.

5. **Expanded Context Window (Alternative Metric):**
   By compressing the data format, Shopify can fit **nearly 2x the number of products** into a single prompt context. This allows the LLM to perform reasoning tasks (e.g., "Find the best matching pants for this shirt") over a larger inventory segment in a single pass.

### Conclusion

For large-scale enterprises like Shopify, adopting TOON is not about replacing JSON in the database.
It is an **optimization layer** at the LLM edge. By converting high-volume, uniform data structures
(like product lists and inventory logs) into TOON before inference, companies can achieve significant
cost efficiency and performance gains without sacrificing data integrity.
