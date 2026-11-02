"""
Clustering implementation using Leiden algorithm.
Follows Strategy Pattern for different clustering approaches.
"""
import os
from typing import Optional, List

import scanpy as sc
import matplotlib.pyplot as plt
import anndata

from ..core.interfaces import IClusterer
from ..core.config import Config
from ..utils.io import write_h5ad


class LeidenClusterer(IClusterer):
    """Leiden clustering with multi-resolution analysis."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def cluster(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Execute clustering pipeline."""
        print("🔹 Building k-NN neighborhood graph...")
        print(f"   Each cell connected to {self.config.n_neighbors} nearest neighbors ({self.config.n_pcs} PCs)")
        sc.pp.neighbors(adata, n_neighbors=self.config.n_neighbors, n_pcs=self.config.n_pcs,
                        random_state=self.config.random_state)
        
        print("🔹 Computing UMAP...")
        sc.tl.umap(adata, random_state=self.config.random_state)
        
        print(f"🔹 Applying Leiden at resolutions: {self.config.resolutions}")
        for res in self.config.resolutions:
            sc.tl.leiden(adata, 
                        resolution=res, 
                        key_added=f"leiden_{res}",
                        flavor=self.config.leiden_flavor,
                        n_iterations=self.config.leiden_n_iterations,
                        random_state=self.config.random_state)
            print(f"   resolution {res:4} → {adata.obs[f'leiden_{res}'].nunique()} groups")
        
        self._plot_multi_resolution(adata)
        
        return adata
    
    def _plot_multi_resolution(self, adata: anndata.AnnData):
        """Plot UMAP for all resolutions."""
        os.makedirs(self.config.figures_dir, exist_ok=True)
        n = len(self.config.resolutions)
        fig, eixos = plt.subplots(1, n, figsize=(4 * n, 4), squeeze=False)
        for i, res in enumerate(self.config.resolutions):
            sc.pl.umap(adata, color=f"leiden_{res}", ax=eixos[0][i],
                       show=False, legend_loc="on data", title=f"Resolution {res}")
        plt.suptitle("Cell-Atlas — Resolution Comparison", y=1.05, fontsize=14)
        plt.tight_layout()
        plt.savefig(self.config.figures_dir / "umap_todas_resolucoes.png", dpi=150, bbox_inches="tight")
        plt.close()
    
    def cluster_and_save(self, adata: anndata.AnnData, output_path: str = None) -> anndata.AnnData:
        """Cluster and save to disk."""
        adata = self.cluster(adata)
        output = output_path or self.config.clustered_path
        write_h5ad(adata, output)
        print(f"✅ Completed — saved to: {output}")
        return adata
