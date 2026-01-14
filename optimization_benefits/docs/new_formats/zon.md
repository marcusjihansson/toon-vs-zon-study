# ZON Format: Shopify Case Study

## Overview

**ZON (Zero Overhead Notation)** is a compact, human-readable data serialization format designed specifically for Large Language Model (LLM) workflows. It achieves 35-70% token reduction compared to JSON while maintaining 100% data fidelity and perfect LLM comprehension.

**File Extension:** `.zonf`  
**Media Type:** `text/zonf`  
**Encoding:** UTF-8

---

## What is ZON?

ZON is a token-efficient serialization format designed for LLM workflows that achieves 35-50% token reduction compared to JSON through tabular encoding, single-character primitives, and intelligent compression while maintaining 100% data fidelity. Think of it as a hybrid between CSV's efficiency and JSON's flexibility—optimized specifically for AI applications.

### Key Characteristics

- **Token efficiency**: Uses 35-70% fewer tokens than JSON
- **LLM-optimized**: Achieves 99.0% accuracy with self-explanatory structure
- **Human-readable**: Unlike binary formats, ZON maintains readability
- **Lossless**: Perfect round-trip conversion to/from JSON

### Why ZON?

#### The Problem

- LLM tokens cost money
- JSON is verbose and token-expensive
- Larger context windows enable larger inputs, but at what cost?

#### The Solution

ZON provides:

- **35-70% fewer tokens than JSON**
- **4-35% fewer tokens than TOON** (another compact format)
- **100% retrieval accuracy** with LLMs
- **Zero parsing overhead** - simpler than CSV for LLMs to understand

#### Real-World Impact

> "Dropped ZON into my LangChain agent loop and my monthly bill dropped $400 overnight" Source: zon-format Github

---

## Quick Start

```python
import zon

# Your data
data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin", "active": True},
        {"id": 2, "name": "Bob", "role": "user", "active": True}
    ]
}

# Encode to ZON
encoded = zon.encode(data)
print(encoded)
# users:@(2):active,id,name,role
# T,1,Alice,admin
# T,2,Bob,user

# Decode back
decoded = zon.decode(encoded)
assert decoded == data  # ✓ Lossless!
```

---

## Format Examples

### Tabular Arrays (Most Efficient)

**Best for:** Arrays of objects with consistent structure

**JSON:**

```json
{
  "users": [
    { "id": 1, "name": "Alice", "active": true },
    { "id": 2, "name": "Bob", "active": false }
  ]
}
```

**ZON:**

```
users:@(2):active,id,name
T,1,Alice
F,2,Bob
```

**How it works:**

- `@(2)` declares row count
- Column names listed once
- Data rows follow (comma-separated)
- `T`/`F` for booleans (saves tokens)

### Nested Objects

**Best for:** Configuration and hierarchical data

**JSON:**

```json
{
  "config": {
    "database": {
      "host": "localhost",
      "port": 5432
    },
    "features": {
      "darkMode": true
    }
  }
}
```

**ZON:**

```
config.database.host:localhost
config.database.port:5432
config.features.darkMode:T
```

**Or more compact:**

```
config:{database:{host:localhost,port:5432},features:{darkMode:T}}
```

### Mixed Structures

**ZON intelligently combines formats:**

```
metadata:{version:1.0.4,env:production}
users:@(3):id,name,active
1,Alice,T
2,Bob,F
3,Carol,T
logs:[{id:101,level:INFO},{id:102,level:WARN}]
```

---

## Data Types

### Primitives

| Type    | JSON             | ZON                  |
| ------- | ---------------- | -------------------- |
| String  | `"hello"`        | `hello` or `"hello"` |
| Number  | `42` or `3.14`   | `42` or `3.14`       |
| Boolean | `true` / `false` | `T` / `F`            |
| Null    | `null`           | `null`               |

### Collections

| Type   | JSON        | ZON                   |
| ------ | ----------- | --------------------- |
| Array  | `[1, 2, 3]` | `[1,2,3]`             |
| Object | `{"a": 1}`  | `{a:1}`               |
| Table  | N/A         | `@(2):id,name` + rows |

### Type Preservation

✅ **Integers** stay integers: `42`  
✅ **Floats** preserve decimals: `3.14` (whole floats get `.0`)  
✅ **Booleans** are explicit: `T`/`F` not strings  
✅ **Null** is explicit: `null` not omitted  
✅ **No scientific notation**: `1000000` not `1e6`  
✅ **Special values normalized**: `NaN`/`Infinity` → `null`

---

## Encoding Modes

### Three Modes for Different Use Cases

| Mode              | Best For                | Token Efficiency | Readability |
| ----------------- | ----------------------- | ---------------- | ----------- |
| **compact**       | Production APIs, LLMs   | ⭐⭐⭐⭐⭐       | ⭐⭐        |
| **llm-optimized** | AI workflows            | ⭐⭐⭐⭐         | ⭐⭐⭐      |
| **readable**      | Config files, debugging | ⭐⭐             | ⭐⭐⭐⭐⭐  |

### Usage

```python
from zon import encode_adaptive, AdaptiveEncodeOptions, recommend_mode

# Compact mode (default - maximum compression)
output = encode_adaptive(data)

# Readable mode (human-friendly)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable', indent=2))

# LLM-optimized mode (balanced for AI)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))

# Get recommendation
recommendation = recommend_mode(data)
print(f"Use {recommendation['mode']} mode: {recommendation['reason']}")
```

### Mode Differences

**Compact Mode (Default):**

- Uses `T`/`F` for booleans
- Maximum table compression
- Dictionary compression for repeated values

**LLM-Optimized Mode:**

- Uses `true`/`false` for better LLM understanding
- Disables dictionary compression
- Balanced token efficiency

**Readable Mode:**

- Multi-line indentation
- Pretty-printed structures
- Easy editing and version control

---

## Advanced Features

### Binary Format (ZON-B)

40-60% space savings over JSON:

```python
from zon import encode_binary, decode_binary

# Encode to binary
binary = encode_binary(data)  # Compact binary format

# Decode from binary
decoded = decode_binary(binary)
```

**Features:**

- MessagePack-inspired format
- Magic header: `ZNB\x01`
- Perfect round-trip fidelity
- Ideal for storage, APIs, network transmission

### Versioning System

Document-level schema versioning with automatic migrations:

```python
from zon import embed_version, extract_version, ZonMigrationManager

# Embed version metadata
versioned = embed_version(data, "2.0.0", "user-schema")

# Extract version info
meta = extract_version(versioned)

# Setup migration manager
manager = ZonMigrationManager()
manager.register_migration("1.0.0", "2.0.0", upgrade_function)

# Automatically migrate
migrated = manager.migrate(old_data, "1.0.0", "2.0.0")
```

**Features:**

- Semantic versioning support
- BFS-based migration path finding
- Backward/forward compatibility checking
- Chained migrations for complex upgrades

### Developer Tools

```python
from zon import size, compare_formats, analyze, ZonValidator

# Compare format sizes
comparison = compare_formats(data)
# {'json': {'size': 1200, 'percentage': 100.0},
#  'zon': {'size': 800, 'percentage': 66.7},
#  'binary': {'size': 480, 'percentage': 40.0}}

# Analyze data complexity
analysis = analyze(data)
# {'depth': 3, 'complexity': 'moderate', 'recommended_format': 'zon'}

# Enhanced validation
validator = ZonValidator()
result = validator.validate(zon_string)
if not result.is_valid:
    for error in result.errors:
        print(f"Error at line {error.line}: {error.message}")
```

### Schema Validation

Built-in validation for LLM guardrails:

```python
from zon import zon, validate

# 1. Define schema
UserSchema = zon.object({
    'name': zon.string().describe("The user's full name"),
    'age': zon.number().describe("Age in years"),
    'role': zon.enum(['admin', 'user']).describe("Access level"),
    'tags': zon.array(zon.string()).optional()
})

# 2. Generate system prompt
system_prompt = f"""
You are an API. Respond in ZON format with this structure:
{UserSchema.to_prompt()}
"""

# 3. Validate LLM output
result = validate(llm_output, UserSchema)
```

**Supported Types:**

- `zon.string()`
- `zon.number()`
- `zon.boolean()`
- `zon.enum(['a', 'b'])`
- `zon.array(schema)`
- `zon.object({ 'key': schema })`
- `.optional()` modifier

---

## Security

### Eval-Safe Design

✅ **No eval()** - Pure data format, zero code execution  
✅ **No object constructors** - Unlike YAML's exploits  
✅ **No prototype pollution** - Dangerous keys blocked  
✅ **Type-safe parsing** - Numbers via safe parsing

### DOS Prevention

Automatic protection against malicious input:

| Limit         | Maximum    | Error Code |
| ------------- | ---------- | ---------- |
| Document size | 100 MB     | E301       |
| Line length   | 1 MB       | E302       |
| Array length  | 1M items   | E303       |
| Object keys   | 100K keys  | E304       |
| Nesting depth | 100 levels | -          |

---

## Benchmarks

### Token Efficiency (vs Compact JSON)

| Tokenizer      | ZON Savings   | vs TOON | vs CSV |
| -------------- | ------------- | ------- | ------ |
| **GPT-4o**     | **-23.8%** 👑 | -36.1%  | -12.9% |
| **Claude 3.5** | **-21.3%** 👑 | -26.0%  | -9.9%  |
| **Llama 3**    | **-16.5%** 👑 | -26.6%  | -9.2%  |

### Retrieval Accuracy

**gpt-5-nano (Azure OpenAI) - Unified Dataset:**

```
ZON            ████████████████████  99.0% (306/309) │ 692 tokens 👑
TOON           ████████████████████  99.0% (306/309) │ 874 tokens
CSV            ████████████████████  99.0% (306/309) │ 714 tokens
JSON           ███████████████████░  96.8% (299/309) │ 1,300 tokens
JSON compact   ██████████████████░░  91.7% (283/309) │ 802 tokens
```

**Result:** ZON achieves 99% accuracy while using **20.8% fewer tokens** than TOON.

---

## LLM Integration

### OpenAI

```python
import zon
import openai

users = [{"id": i, "name": f"User{i}", "active": True} for i in range(100)]

# Compress with ZON
zon_data = zon.encode(users)

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You will receive data in ZON format."},
        {"role": "user", "content": f"Analyze this user data:\n\n{zon_data}"}
    ]
)
```

### Best Practice: Input Optimization Workflow

**Save money on input tokens, keep compatibility:**

```python
import zon

# 1. Encode context (Save ~50% tokens!)
context = zon.encode(large_dataset)

# 2. Send to LLM
prompt = f"""
Here is the data in ZON format:
{context}

Analyze this data and respond in standard JSON format.
"""

# 3. LLM outputs standard JSON
# No backend changes needed!
```

**Benefits:**

- ✅ Cheaper API calls (ZON input)
- ✅ Zero code changes (JSON output)
- ✅ Best of both worlds

---

## API Reference

### Core Functions

```python
from zon import (
    # Basic encoding/decoding
    encode, decode, encode_llm,

    # Adaptive encoding
    encode_adaptive, recommend_mode, AdaptiveEncodeOptions,

    # Binary format
    encode_binary, decode_binary,

    # Versioning
    embed_version, extract_version, compare_versions,
    is_compatible, strip_version, ZonMigrationManager,

    # Developer tools
    size, compare_formats, analyze, infer_schema,
    compare, is_safe, ZonValidator, expand_print
)
```

### encode(data: Any) -> str

Encodes Python data to ZON format.

```python
zon_str = zon.encode({"users": [{"id": 1, "name": "Alice"}]})
```

### decode(zon_string: str, strict: bool = True) -> Any

Decodes ZON format back to Python data.

```python
# Strict mode (default) - validates table structure
data = zon.decode(zon_string)

# Non-strict mode - allows mismatches
data = zon.decode(zon_string, strict=False)
```

**Error Handling:**

```python
from zon import decode, ZonDecodeError

try:
    data = decode(invalid_zon)
except ZonDecodeError as e:
    print(e.code)    # "E001" or "E002"
    print(e.message) # Detailed error
```

### Error Codes

| Code | Description                  |
| ---- | ---------------------------- |
| E001 | Row count mismatch in table  |
| E002 | Field count mismatch in row  |
| E301 | Document too large (>100MB)  |
| E302 | Line too long (>1MB)         |
| E303 | Array too large (>1M items)  |
| E304 | Too many object keys (>100K) |

---

# Shopify Case Study: How ZON Could Transform Their Systems

## 1. AI-Powered Product Recommendations & Search

**Current Challenge**: Shopify's product catalogs contain massive amounts of data (descriptions, variants, prices, inventory). When feeding this to LLMs for personalized recommendations or semantic search, JSON is extremely token-heavy.

**ZON Application**:

```zon
products:@(1000):id,name,price,inventory,tags
12345,Premium Leather Wallet,49.99,150,accessories|leather|wallet
12346,Organic Cotton T-Shirt,29.99,500,clothing|organic|casual
...
```

**Benefits**:

- **Cost reduction**: 35-50% fewer tokens means proportional reduction in OpenAI/Anthropic API costs
- **Faster responses**: Smaller payloads = quicker LLM processing
- **Larger context windows**: Fit more products in a single request (could go from 200 products to 350+ products in same token budget)

---

## 2. Shopify Magic (AI Assistant)

Shopify Magic helps merchants write product descriptions, generate marketing content, and answer customer questions. Currently, it needs to send store context (product data, customer history, store policies) to LLMs.

**ZON Application**:

```zon
store_context{
  name:MyShop
  currency:USD
  plan:Advanced
}
orders:@(50):id,total,status,customer_email
10001,299.99,fulfilled,customer@example.com
10002,450.00,pending,buyer@test.com
...
top_products:@(10):name,sales,revenue
Wireless Headphones,450,22500
Smart Watch,320,19200
```

**Benefits**:

- Provide richer context without hitting token limits
- Enable more sophisticated AI features (cross-referencing orders, inventory, customer behavior)
- Reduce latency in AI-powered merchant tools

---

## 3. Analytics & Reporting Dashboards

Shopify Plus merchants often need AI-powered insights from complex datasets (sales trends, customer segments, inventory forecasting).

**Current Problem**: Sending time-series data or large analytical datasets in JSON is extremely verbose.

**ZON Application**:

```zon
sales_by_day:@(365):date,revenue,orders,avg_order_value
2025-01-01,15400.50,87,177.02
2025-01-02,18200.75,102,178.44
...
customer_segments:@(5):segment,count,ltv
returning_high_value,1200,4500.00
first_time_buyers,8500,150.00
```

**Benefits**:

- Real-time AI analysis of larger datasets
- More sophisticated predictive analytics within token budgets
- Faster dashboard generation using LLMs

---

## 4. API & Webhook Efficiency

Shopify has extensive API usage (GraphQL, REST). When merchants build AI integrations, they're constantly shuttling data between Shopify APIs and AI services.

**ZON Application**:

- **Middleware layer**: Convert Shopify API responses to ZON before sending to LLM
- **Webhook optimization**: Compress webhook payloads when forwarding to AI services
- **Edge functions**: Process data in Cloudflare Workers/Vercel Edge with ZON's lightweight format

**Implementation Example**:

```javascript
// Shopify App using ZON
import { encode } from "zon-format";

const shopifyData = await fetchShopifyProducts();
const zonEncoded = encode(shopifyData); // 50% smaller

const aiResponse = await openai.chat.completions.create({
  messages: [
    { role: "system", content: "Data is in ZON format" },
    { role: "user", content: `Analyze: ${zonEncoded}` },
  ],
});
```

---

## 5. Customer Support AI (Shopify Inbox)

Shopify Inbox allows merchants to chat with customers. AI could enhance this by:

- Analyzing past conversations
- Suggesting responses based on order history
- Providing product recommendations

**ZON Application**:

```zon
conversation_history:@(20):timestamp,sender,message
2025-01-08T10:00:00,customer,Is my order shipped?
2025-01-08T10:01:00,merchant,Let me check for you
...
customer_orders:@(5):order_id,date,total,status
10045,2025-01-05,199.99,shipped
```

**Benefits**:

- Send entire conversation + order history in compressed format
- AI can provide more contextually aware responses
- Support more concurrent AI-powered conversations with same infrastructure

---

## 6. Multi-Store Management (Shopify Plus)

Enterprise merchants managing multiple stores need consolidated AI insights across all stores.

**ZON Application**:

```zon
stores:@(10):store_id,name,currency,total_revenue
1,US Store,USD,1500000
2,EU Store,EUR,1200000
...
aggregate_products:@(100):product_id,total_sales_all_stores,avg_price
...
```

**Benefits**:

- Consolidate multi-store data efficiently
- AI can provide cross-store insights without hitting token limits
- Enable enterprise-level predictive analytics

---

## 7. Shopify Flow (Automation Platform)

Shopify Flow uses AI to suggest automation workflows. It needs to analyze store events, customer behavior, and order patterns.

**ZON Application**:

- Encode event logs and workflow data in ZON
- Feed to LLM for workflow suggestions
- Get back AI-generated automation rules

**Example**:

```zon
events:@(1000):timestamp,event_type,customer_id,value
2025-01-08T09:00:00,order_placed,12345,299.99
2025-01-08T09:15:00,abandoned_cart,67890,450.00
```

---

## Implementation Strategy for Shopify

### Phase 1: AI Features (Immediate Wins)

1. Implement ZON in Shopify Magic's context encoding
2. Add ZON support to AI-powered product recommendations
3. Use in analytics AI features

### Phase 2: Developer Platform

1. Release ZON SDK for Shopify App developers
2. Add ZON output option to GraphQL API
3. Document best practices for AI app builders

### Phase 3: Infrastructure

1. Optimize internal AI services with ZON
2. Add ZON to Shopify Functions (serverless platform)
3. Integrate with Edge delivery network

---

## Technical Integration Points

```javascript
// Shopify App SDK with ZON
import { shopifyApi } from "@shopify/shopify-api";
import { encode as zonEncode } from "zon-format";

const products = await admin.rest.Product.all({ session });
const zonData = zonEncode(products);

// Send to AI with 50% fewer tokens
const aiInsights = await generateAIInsights(zonData);
```

---

## Cost Impact Analysis

### Example Merchant (Shopify Plus)

- 10,000 products
- 100 AI requests/day for recommendations
- Current cost: ~$200/month in LLM tokens

### With ZON

- Same data in 50% fewer tokens
- New cost: ~$100/month
- **Savings: $1,200/year per merchant**

For Shopify's 2M+ merchants, even partial adoption could save millions in AI infrastructure costs.

---

## Why ZON Makes Sense for Shopify

1. **Token efficiency = Cost efficiency**: Direct impact on AI feature profitability
2. **Developer-friendly**: Easy to adopt (similar to JSON, better performance)
3. **Production-ready**: MIT licensed, well-tested, multiple implementations
4. **Future-proof**: As AI features grow, token optimization becomes critical
5. **Competitive advantage**: Enable more sophisticated AI features than competitors

The format is particularly well-suited for Shopify's use case because e-commerce data (products, orders, customers) is naturally tabular—exactly what ZON excels at compressing.

### ZON vs TOON: Handling Nested Data

Unlike TOON (which struggles with deeply nested structures), **ZON excels at both flat and nested data**:

- **Flat tabular data**: Uses table encoding (like TOON)
- **Nested structures**: Automatically applies dot notation flattening + inline format
- **Deep nesting**: Maintains 91% compression even at 50+ levels deep
- **Benchmark proof**: On complex nested datasets, ZON beats TOON by 26-36% across all tokenizers

This makes ZON ideal for Shopify's mixed data structures:

- Product catalogs (flat/tabular) ✅
- Configuration objects (nested) ✅
- Order history with line items (mixed) ✅
- Multi-store hierarchies (deep nesting) ✅

---

## Installation

```bash
# Python
pip install zon-format

# Using UV (5-10x faster)
uv pip install zon-format

# JavaScript/TypeScript
npm install zon-format
```

### Command Line

```bash
# Encode JSON to ZON
zon encode data.json > data.zonf

# Decode ZON to JSON
zon decode data.zonf > output.json
```

---

## Resources

### Documentation

- [GitHub Repository](https://github.com/ZON-Format/ZON)
- [PyPI Package](https://pypi.org/project/zon-format/)
- [Complete Specification](https://github.com/ZON-Format/ZON/blob/main/SPEC.md)
- [Syntax Cheatsheet](https://github.com/ZON-Format/ZON/blob/main/zon-format/docs/syntax-cheatsheet.md)
- [API Reference](https://github.com/ZON-Format/ZON/blob/main/zon-format/docs/api-reference.md)
- [LLM Best Practices](https://github.com/ZON-Format/ZON/blob/main/zon-format/docs/llm-best-practices.md)

### TypeScript Implementation

- [zon-TS](https://github.com/ZON-Format/zon-TS)

### Official Website

- [https://zonformat.org/](https://zonformat.org/)

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## License

Copyright (c) 2025 ZON-FORMAT (Roni Bhakta)

MIT License - See [LICENSE](https://github.com/ZON-Format/ZON/blob/main/LICENSE) for details.

---

## Quality Assurance

### Testing

- **340/340 unit tests passed**
- **27/27 datasets verified** + 51 cross-language examples
- **Zero data loss or corruption**
- **51% exact match** with TypeScript implementation

---

## Summary

**ZON is the only format that:**

- Wins (or ties) on every LLM tokenizer
- Achieves 99%+ retrieval accuracy
- Maintains 100% data fidelity
- Provides built-in validation for LLM guardrails
- Includes enterprise features (binary, versioning, adaptive encoding)

**Perfect for:**

- 💰 Cost-sensitive LLM workflows
- 🤖 AI agents with large context windows
- 📊 Data-heavy prompts
- 🔄 JSON replacement in LLM pipelines
- 🛒 E-commerce AI applications (Shopify case study)

---

**Document Version**: 2.0  
**Last Updated**: January 13, 2026  
**License**: MIT
