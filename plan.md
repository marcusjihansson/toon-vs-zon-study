Specification for approval
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Goals

1.  Add a reference to optimization_benefits/reference_implementation/README.md in optimization_benefits/docs/paper.md.
2.  Re-evaluate “dry run without API key” behavior (currently auto-falls back to random mock metrics).
3.  Move optimization_benefits/database.py into a optimization_benefits/database/ package (similar to
    optimization_benefits/api/).
4.  Clean up the three entrypoint scripts (main.py, api_main.py, db_main.py) by moving them into a dedicated entrypoint
    directory.
5.  After the refactor, update all docs so paths and instructions are consistent.

──────────────────────────────────────────

Current state (what we’re refactoring)
• Dry run behavior lives in optimization_benefits/analyze/analyze.py (StrategyAnalyzer.run_benchmark +
\_generate_mock_metrics) and is triggered automatically when OPENROUTER_API_KEY is missing.
• Entrypoints: optimization_benefits/main.py, api_main.py, db_main.py (all use sys.path.insert(...) to work when run as
scripts).
• Database module is a single file: optimization_benefits/database.py (writes to
optimization_benefits/api/products.db).

──────────────────────────────────────────

1.  Paper reference to `reference_implementation/README.md`

Changes
• In docs/paper.md, add a short paragraph (best locations):
• Section 2.1 TOON Format (Background), or
• Section 3 Methodology (Implementation details), or
• References section.
• Add a new bibliography entry like:
• [5] Reference implementation (DSPy TOON adapter via dspy-toon):
optimization_benefits/reference_implementation/README.md
• Ensure citation numbering stays consistent with the current [1]..[4] mapping already in the paper.

Why

This clearly distinguishes “this repo’s benchmark harness” from the upstream adapter implementation.

──────────────────────────────────────────

2.  Dry-run behavior: move to `test/`? (two recommended options)

Option A (recommended): Keep dry-run capability, but make it **explicit** and deterministic

What changes
• Remove the auto fallback (“No API key found… falling back to dry run mode…”) from StrategyAnalyzer.run_benchmark.
• Add an explicit CLI flag for entrypoints (e.g. --dry-run) to enable mock metrics.
• Make mock metrics deterministic:
• seed RNG (e.g., random.Random(0)) or
• move mock generator to optimization_benefits/test/mock_metrics.py and import it.

Why
• Avoids accidental publication of “random benchmark results” if someone runs without a key.
• Still allows demos and fast local smoke runs.

Option B: Remove dry-run from runtime entirely; keep it only for tests

What changes
• Delete/relocate \_generate_mock_metrics into optimization_benefits/test/.
• StrategyAnalyzer.run_benchmark(dry_run=False) raises a clear error if no key.
• Update test/test_implementation.py to avoid calling run_benchmark and instead test only:
• strategy creation
• adapter callability
• RAG object creation

Why
• Strongest “research integrity” posture.
• Forces real runs for any benchmark output.

Decision point
Pick Option A if you want a demo mode; pick Option B if you want strict reproducibility and zero mock outputs outside tests.

──────────────────────────────────────────

3.  Move `database.py` → `optimization_benefits/database/`

Proposed layout
• optimization_benefits/database/**init**.py (exports the public API)
• optimization_benefits/database/store.py (or db.py) containing existing functions

Backwards compatibility (recommended)
• Keep a thin shim file optimization_benefits/database.py for one release cycle:
• from optimization_benefits.database.store import \*
• This prevents breaking existing imports immediately.

Required code updates
• Update imports in:
• optimization_benefits/main.py
• optimization_benefits/db_main.py
• anywhere else using from database import ...
• Decide where products.db should live:
• Keep as-is in optimization_benefits/api/products.db (minimal diff), or
• Move to optimization_benefits/database/products.db (cleaner separation; requires path update + .gitignore already
covers \*.db).

──────────────────────────────────────────

4.  Move the 3 entrypoints into a dedicated dir

Proposed layout

Create optimization_benefits/cli/:
• optimization_benefits/cli/compare.py (from main.py)
• optimization_benefits/cli/api.py (from api_main.py)
• optimization_benefits/cli/db.py (from db_main.py)

Keep existing commands working (recommended)

Leave tiny wrappers in the old locations:
• optimization_benefits/main.py → imports and calls optimization_benefits.cli.compare.main()
• optimization_benefits/api_main.py → wrapper for optimization_benefits.cli.api.main()
• optimization_benefits/db_main.py → wrapper for optimization_benefits.cli.db.main()

Import cleanup

As part of this step, remove sys.path.insert(...) hacks from the moved code and switch to package imports.

──────────────────────────────────────────

5.  Documentation updates after refactor (explicit checklist)

Update all references to paths, commands, and module locations:
• optimization_benefits/docs/paper.md
• add reference_implementation citation
• update any “implementation details” paths if database/entrypoints moved
• optimization_benefits/REPRODUCIBILITY.md
• update commands if entrypoints move (or keep old commands valid via wrappers)
• optimization_benefits/README.md
• update repository structure tree
• update quickstart commands
• Root README.md
• update quickstart commands and directory structure references
• Any supporting docs:
• optimization_benefits/docs/analysis.md, docs/hypothesis.md, etc. if they mention old paths

──────────────────────────────────────────

Validation plan (must pass before we finish)
• Run: python3 optimization_benefits/test/test_implementation.py
• If we add CLI flags or new modules, add at least one smoke test that imports the new cli modules.
• Ensure run_benchmark.sh still works (or update it and the docs accordingly).

──────────────────────────────────────────

Execution order (to minimize breakage)

1.  Add the reference_implementation citation in paper.md (safe, independent).
2.  Create database/ package + shim; update imports.
3.  Create cli/ directory + move code; add wrappers at old paths.
4.  Decide Option A vs B for dry-run and implement.
5.  Update run_benchmark.sh if needed.
6.  Update docs (REPRODUCIBILITY + READMEs + any doc trees).
7.  Run validators/tests.
