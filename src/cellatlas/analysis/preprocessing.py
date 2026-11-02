"""
Preprocessing pipeline following Single Responsibility Principle.
Based on Luecken & Theis (2019) best practices.
"""
import os
from typing import Optional

import scanpy as sc
import matplotlib.pyplot as plt
import numpy as np
import anndata

from ..core.interfaces import IPreprocessor
from ..core.config import Config
from ..utils.io import write_h5ad


class Preprocessor(IPreprocessor):
    """Comprehensive preprocessing pipeline for scRNA-seq data."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def preprocess(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Execute complete preprocessing pipeline."""
        print("🔹 Loading raw data...")
        print(f"   Initial: {adata.n_obs} cells × {adata.n_vars} genes")
        
        print("🔹 Quality control...")
        # Plain numpy bool: with newer pandas `.str.startswith` may return a nullable
        # BooleanArray, which scipy.sparse cannot use as a column mask.
        adata.var["mt"] = np.asarray(adata.var_names.str.startswith("MT-"), dtype=bool)
        sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True)
        
        print("🔹 Filtering...")
        sc.pp.filter_cells(adata, min_genes=self.config.min_genes_per_cell)
        sc.pp.filter_cells(adata, max_genes=self.config.max_genes_per_cell)
        # .copy() materializes the view so later in-place steps do not warn/fail.
        adata = adata[adata.obs["pct_counts_mt"] < self.config.max_mito_percent, :].copy()
        sc.pp.filter_genes(adata, min_cells=self.config.min_cells_per_gene)
        print(f"   After filtering: {adata.n_obs} cells × {adata.n_vars} genes")
        
        print("🔹 Normalization and highly variable genes selection...")
        sc.pp.normalize_total(adata, target_sum=self.config.target_sum)
        sc.pp.log1p(adata)
        # Keep the full, log-normalized transcriptome in .raw before subsetting
        # to HVGs. Marker-based annotation (CD3E, MS4A1, ...) needs genes that
        # are frequently not highly variable.
        adata.raw = adata.copy()
        sc.pp.highly_variable_genes(adata, n_top_genes=self.config.n_top_genes, subset=True)
        
        print("🔹 PCA...")
        sc.pp.scale(adata, max_value=10)
        sc.tl.pca(adata, svd_solver=self.config.svd_solver)
        
        self._plot_pca_variance(adata)
        
        return adata
    
    def _plot_pca_variance(self, adata: anndata.AnnData):
        """Generate PCA variance ratio plot."""
        os.makedirs(self.config.figures_dir, exist_ok=True)
        plt.rcParams["figure.figsize"] = (6, 4)
        sc.pl.pca_variance_ratio(adata, log=True, show=False)
        plt.savefig(self.config.figures_dir / "pca_variancia.png", dpi=150, bbox_inches="tight")
        plt.close()
    
    def preprocess_and_save(self, adata: anndata.AnnData, output_path: str = None) -> anndata.AnnData:
        """Preprocess and save to disk."""
        adata = self.preprocess(adata)
        output = output_path or self.config.processed_path
        write_h5ad(adata, output)
        print(f"✅ Completed — saved to: {output}")
        return adata
