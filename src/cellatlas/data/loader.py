"""
Data loading implementations following Strategy Pattern.
"""
import os
from pathlib import Path
from typing import Optional

import scanpy as sc
import anndata

from ..core.interfaces import IDataLoader
from ..core.config import Config


class PBMC3kLoader(IDataLoader):
    """Loader for PBMC3k reference dataset from 10x Genomics."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def load(self, source: str = None) -> anndata.AnnData:
        """
        Load PBMC3k dataset.
        If source is None, uses config.raw_path.
        """
        output_path = source or self.config.raw_path
        
        if os.path.exists(output_path):
            print(f"⚠️  File already exists — loading from: {output_path}")
            return sc.read_h5ad(output_path)
        
        print("📥 Downloading PBMC3k — Human Immune Cells")
        print("Source: 10x Genomics / Scanpy Repository")
        print("Alternative: GEO GSE139324")
        print("-" * 50)
        
        adata = sc.datasets.pbmc3k()
        adata.write(output_path)
        
        print(f"✅ Completed: {adata.n_obs} cells × {adata.n_vars} genes")
        print(f"Saved to: {output_path}")
        
        return adata


class DataLoader(IDataLoader):
    """Generic data loader supporting multiple formats."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def load(self, source: str) -> anndata.AnnData:
        """Load data from various formats."""
        path = Path(source)
        
        if path.suffix == '.h5ad':
            return sc.read_h5ad(source)
        elif path.suffix == '.h5':
            return sc.read_10x_h5(source)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")
