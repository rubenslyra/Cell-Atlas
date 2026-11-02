"""
Cell type annotation following Single Responsibility Principle.
"""
import os
from typing import Optional

import scanpy as sc
import pandas as pd
import matplotlib.pyplot as plt
import anndata

from ..core.interfaces import IAnnotator
from ..core.config import Config


class CellTypeAnnotator(IAnnotator):
    """Annotate cell clusters using marker genes."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def annotate(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Execute annotation pipeline."""
        target_res = self.config.target_resolution
        
        if target_res not in adata.obs.columns:
            raise ValueError(f"Resolution {target_res} not found. Run clustering first.")
        
        print(f"🔹 Identifying marker genes — {target_res}...")
        sc.tl.rank_genes_groups(adata, groupby=target_res, method="wilcoxon")
        
        os.makedirs(self.config.figures_dir, exist_ok=True)
        os.makedirs(self.config.results_dir, exist_ok=True)
        
        # Plot top markers
        sc.pl.rank_genes_groups(adata, n_genes=5, sharey=False, show=False)
        plt.savefig(self.config.figures_dir / "genes_marcadores.png", dpi=150, bbox_inches="tight")
        plt.close()
        
        print("🔹 Checking canonical markers...")
        marker_list = []
        for cell_type, genes in self.config.marker_genes.items():
            marker_list.extend(genes)
        # Remove duplicates while preserving order
        marker_list = list(dict.fromkeys(marker_list))
        
        sc.pl.umap(adata, color=marker_list, show=False)
        plt.savefig(self.config.figures_dir / "marcadores_classicos.png", dpi=150, bbox_inches="tight")
        plt.close()
        
        self._generate_summary(adata, target_res)
        
        return adata
    
    def _generate_summary(self, adata: anndata.AnnData, target_res: str):
        """Generate cluster summary table."""
        tabela = pd.DataFrame()
        for g in sorted(adata.obs[target_res].unique()):
            top = adata.uns["rank_genes_groups"]["names"][g][:3]
            tabela = pd.concat([tabela, pd.DataFrame({
                "Grupo": [g], 
                "Top_genes": [", ".join(top)],
                "Celulas": [(adata.obs[target_res] == g).sum()]
            })])
        tabela.to_csv(self.config.results_dir / "resumo_grupos.csv", index=False)
        
        print("\n📋 CLUSTER SUMMARY:")
        print(tabela.to_string(index=False))
        print("\n✅ Annotation completed!")
        print("💡 Compare 'Top_genes' with canonical markers to identify each cell type.")
    
    def annotate_and_save(self, adata: anndata.AnnData, output_path: str = None) -> anndata.AnnData:
        """Annotate and save results."""
        adata = self.annotate(adata)
        if output_path:
            adata.write(output_path)
            print(f"✅ Saved to: {output_path}")
        return adata
