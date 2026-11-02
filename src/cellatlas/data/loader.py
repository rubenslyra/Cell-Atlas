"""
Data loading implementations following Strategy Pattern.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import anndata
import scanpy as sc

from ..core.config import Config
from ..core.interfaces import IDataLoader
from ..utils.io import write_h5ad


class PBMC3kLoader(IDataLoader):
    """Loader for the PBMC3k reference dataset (10x Genomics, via Scanpy)."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def load(self, source: Optional[Union[str, Path]] = None) -> anndata.AnnData:
        """
        Load PBMC3k from ``source`` (default: ``config.raw_path``).

        If the file does not exist yet, the dataset is downloaded once through
        ``scanpy.datasets.pbmc3k()`` and cached at that path.
        """
        output_path = Path(source) if source else self.config.raw_path

        if output_path.exists():
            print(f"ℹ️  Using cached dataset: {output_path}")
            return sc.read_h5ad(output_path)

        print("📥 Downloading PBMC3k — Human Immune Cells")
        print("Source: 10x Genomics (Zheng et al., 2017) via Scanpy datasets")
        print("-" * 50)

        adata = sc.datasets.pbmc3k()
        write_h5ad(adata, output_path)

        print(f"✅ Completed: {adata.n_obs} cells × {adata.n_vars} genes")
        print(f"Saved to: {output_path}")

        return adata


class DataLoader(IDataLoader):
    """Generic data loader supporting ``.h5ad`` and 10x ``.h5`` files."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def load(self, source: Union[str, Path]) -> anndata.AnnData:
        """Load data from various formats."""
        path = Path(source)

        if path.suffix == ".h5ad":
            return sc.read_h5ad(path)
        if path.suffix == ".h5":
            return sc.read_10x_h5(path)
        raise ValueError(f"Unsupported format: {path.suffix}")
