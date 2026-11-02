"""Keep package metadata, README and the docs page on the same version."""
from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

import cellatlas

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_matches_pyproject():
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert cellatlas.__version__ == pyproject["project"]["version"]


def test_readme_and_docs_advertise_same_version():
    version = cellatlas.__version__
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    assert f"version-{version}-" in readme
    assert version in docs
