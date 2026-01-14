#!/usr/bin/env python3
"""Quick smoke tests for the strategy analysis implementation.

This repo evolved over time; this script is intentionally lightweight and does
not make expensive LLM API calls.

It verifies:
- imports work when run from the `test/` directory
- default strategies can be created
- each strategy can construct a RAG system instance (without calling the API)
- adapters are DSPy-compatible (callable)
"""

from __future__ import annotations

import os
import sys


# Ensure repo root is on sys.path when executing `python test/test_implementation.py`
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def test_imports() -> bool:
    try:
        from analyze import StrategyAnalyzer, create_default_strategies  # noqa: F401

        print("✅ Imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_strategy_creation() -> bool:
    try:
        from analyze import create_default_strategies

        strategies = create_default_strategies()
        expected = {
            "baseline", "toon_adapter", "toon_strict", "baml_adapter",
            "json_baseline", "zon_adapter", "zon_strict", "combined", "zon_combined"
        }

        if set(strategies.keys()) != expected:
            print(f"❌ Strategy mismatch. Expected: {sorted(expected)}, Got: {sorted(strategies.keys())}")
            return False

        print("✅ Default strategies created")
        return True
    except Exception as e:
        print(f"❌ Strategy creation failed: {e}")
        return False


def test_adapter_callability() -> bool:
    try:
        from analyze import create_default_strategies

        strategies = create_default_strategies()
        for name, strategy in strategies.items():
            if not callable(strategy.adapter):
                print(f"❌ Adapter for {name} is not callable: {type(strategy.adapter)}")
                return False

        print("✅ All adapters are callable (DSPy-compatible)")
        return True
    except Exception as e:
        print(f"❌ Adapter callability test failed: {e}")
        return False


def test_rag_creation() -> bool:
    """Create RAG system objects without executing network calls."""

    try:
        from analyze import create_default_strategies
        from cli.execution.api_main import ShopifyAPIRAG

        strategies = create_default_strategies()

        for name, strategy in strategies.items():
            rag = strategy.create_rag_system(model_name="openrouter/openai/gpt-4o-mini", rag_class=ShopifyAPIRAG)
            if not hasattr(rag, "predictor") or not hasattr(rag, "adapter"):
                print(f"❌ RAG missing expected attributes for {name}")
                return False

        print("✅ RAG instances created for all strategies")
        return True
    except Exception as e:
        print(f"❌ RAG creation test failed: {e}")
        return False


def main() -> None:
    print("🧪 Running smoke tests\n")

    tests = [
        test_imports,
        test_strategy_creation,
        test_adapter_callability,
        test_rag_creation,
    ]

    passed = 0
    for test in tests:
        print(f"\n--- {test.__name__} ---")
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
