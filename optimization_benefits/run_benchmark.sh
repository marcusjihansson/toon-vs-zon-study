#!/bin/bash
# run_benchmark.sh - Optimization Benefits Benchmark Runner

# Ensure script stops on first error
set -e

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: OPENROUTER_API_KEY not found."
    echo ""
    echo "To run real benchmarks, set your API key:"
    echo "  export OPENROUTER_API_KEY='your-key-here'"
    echo ""
    echo "To run demo benchmarks with mock data (no API key needed):"
    echo "  python demo/comparative_demo.py"
    echo ""
    exit 1
else
    echo "API Key found. Running LIVE benchmarks."
fi

echo "=========================================================="
echo "Starting TOON vs ZON Optimization Benchmark"
echo "=========================================================="
echo "Date: $(date)"
echo "Python: $(python3 --version)"
echo "=========================================================="

# 1. Run the Main Benchmark (Comparison)
echo ""
echo ">>> Running Main Comparison Benchmark (API vs DB)..."
python3 cli/compare.py

# 2. Run Economic Analysis (Default Scale)
echo ""
echo ">>> generating Economic Impact Projection..."
python3 analyze/economics.py

echo ""
echo "=========================================================="
echo "Benchmark Complete."
echo "See 'docs/paper.md' for detailed interpretation of results."
echo "=========================================================="
