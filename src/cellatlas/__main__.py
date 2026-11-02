"""
Allow ``python -m cellatlas <command>``.

Also tolerates ``python src/cellatlas <command>`` (running the package
directory directly), which would otherwise break the package's relative
imports.
"""
import sys

if not __package__:
    from pathlib import Path

    _pkg_dir = Path(__file__).resolve().parent
    # Drop the package directory itself (its subfolders `data`, `core`, ...
    # must not shadow top-level modules) and expose its parent (`src/`).
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _pkg_dir]
    sys.path.insert(0, str(_pkg_dir.parent))

from cellatlas.cli.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
