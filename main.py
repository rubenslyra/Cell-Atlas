#!/usr/bin/env python
"""
Cell-Atlas — convenience entry point at the repository root.

    python main.py run-all
    python main.py --help

Works without installing the package (``src/`` is added to ``sys.path``).
The installed equivalents are ``cellatlas <command>`` and
``python -m cellatlas <command>``.
"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cellatlas.cli.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
