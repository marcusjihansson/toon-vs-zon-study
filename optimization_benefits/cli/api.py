"""Entry point for the Shopify API benchmark."""

import argparse
import os
import sys


def _ensure_repo_on_path() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)


def main() -> None:
    _ensure_repo_on_path()
    from cli.execution import api_main

    api_main.main()


if __name__ == "__main__":
    main()
