"""
Command-line interface for the Cell-Atlas pipeline.

Entry points (all equivalent):

    cellatlas <command>          # console script (after ``pip install -e .``)
    python -m cellatlas <command>
    python main.py <command>     # from the repository root, no install needed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from .. import __version__
from ..core.config import Config

COMMANDS = ("download", "preprocess", "cluster", "annotate", "run-all")


# ---------------------------------------------------------------------- #
# Pipeline steps (heavy imports are deferred so `--help` stays instant)
# ---------------------------------------------------------------------- #
def _read(path: Path, hint: str):
    import scanpy as sc

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}. Run `cellatlas {hint}` first.")
    return sc.read_h5ad(path)


def cmd_download(config: Config):
    from ..data.loader import PBMC3kLoader

    return PBMC3kLoader(config).load()


def cmd_preprocess(config: Config, adata=None):
    from ..analysis.preprocessing import Preprocessor

    adata = adata if adata is not None else _read(config.raw_path, "download")
    return Preprocessor(config).preprocess_and_save(adata)


def cmd_cluster(config: Config, adata=None):
    from ..analysis.clustering import LeidenClusterer

    adata = adata if adata is not None else _read(config.processed_path, "preprocess")
    return LeidenClusterer(config).cluster_and_save(adata)


def cmd_annotate(config: Config, adata=None):
    from ..analysis.annotation import CellTypeAnnotator

    adata = adata if adata is not None else _read(config.clustered_path, "cluster")
    return CellTypeAnnotator(config).annotate_and_save(adata)


def cmd_run_all(config: Config):
    adata = cmd_download(config)
    adata = cmd_preprocess(config, adata)
    adata = cmd_cluster(config, adata)
    adata = cmd_annotate(config, adata)
    print("\n🎉 Pipeline completed successfully!")
    return adata


HANDLERS: Dict[str, Callable[[Config], object]] = {
    "download": cmd_download,
    "preprocess": cmd_preprocess,
    "cluster": cmd_cluster,
    "annotate": cmd_annotate,
    "run-all": cmd_run_all,
}


# ---------------------------------------------------------------------- #
# Argument parsing
# ---------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cellatlas",
        description="Cell-Atlas: reproducible scRNA-seq analysis pipeline (PBMC3k).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  download     Download (or reuse) the PBMC3k dataset
  preprocess   QC, filtering, normalization, HVG and PCA
  cluster      k-NN graph, UMAP and Leiden at multiple resolutions
  annotate     Marker genes, canonical markers and suggested cell types
  run-all      Run the complete pipeline end to end

examples:
  cellatlas run-all
  python -m cellatlas cluster --resolutions 0.4 0.8
  python main.py annotate --target-resolution leiden_1.0
""",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("command", choices=COMMANDS, help="pipeline step to execute")
    parser.add_argument("-c", "--config", type=Path,
                        help="TOML/JSON file overriding default parameters")
    parser.add_argument("--data-dir", type=Path, help="directory for .h5ad files (default: dados/)")
    parser.add_argument("--figures-dir", type=Path, help="directory for figures (default: figuras/)")
    parser.add_argument("--results-dir", type=Path, help="directory for tables (default: resultados/)")
    parser.add_argument("--resolutions", type=float, nargs="+", metavar="R",
                        help="Leiden resolutions (default: 0.2 0.4 0.6 1.0)")
    parser.add_argument("--target-resolution", metavar="KEY",
                        help="clustering column used for annotation (default: leiden_0.6)")
    parser.add_argument("--seed", type=int, dest="random_state",
                        help="random seed for neighbors/UMAP/Leiden (default: 0)")
    parser.add_argument("--debug", action="store_true", help="show full traceback on errors")
    return parser


def build_config(args: argparse.Namespace) -> Config:
    """Defaults < config file < explicit CLI flags."""
    config = Config.from_file(args.config) if args.config else Config()

    overrides = {
        "data_dir": args.data_dir,
        "figures_dir": args.figures_dir,
        "results_dir": args.results_dir,
        "resolutions": args.resolutions,
        "target_resolution": args.target_resolution,
        "random_state": args.random_state,
    }
    values = {k: v for k, v in overrides.items() if v is not None}
    if values:
        merged = {**config.__dict__, **values}
        config = Config.from_mapping(merged)
    return config


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = build_config(args)
        config.ensure_dirs()
        HANDLERS[args.command](config)
    except KeyboardInterrupt:
        print("\n⛔ Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        if args.debug:
            raise
        print(f"❌ Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
