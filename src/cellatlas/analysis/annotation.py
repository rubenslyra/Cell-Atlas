"""
Cell type annotation following Single Responsibility Principle.

Two complementary steps:

1. Data-driven: differential expression (Wilcoxon) per Leiden cluster.
2. Knowledge-driven: each cluster receives the cell type whose canonical
   marker set is most strongly expressed in it (``obs["cell_type"]``).
   The label is a *suggestion* that must be checked against the literature.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import anndata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse

from ..core.config import Config
from ..utils.io import write_h5ad
from ..core.interfaces import IAnnotator

UNASSIGNED = "Unassigned"


class CellTypeAnnotator(IAnnotator):
    """Annotate cell clusters using marker genes."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def annotate(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Execute annotation pipeline."""
        target_res = self.config.target_resolution

        if target_res not in adata.obs.columns:
            raise ValueError(f"Resolution {target_res} not found. Run clustering first.")

        use_raw = adata.raw is not None

        os.makedirs(self.config.figures_dir, exist_ok=True)
        os.makedirs(self.config.results_dir, exist_ok=True)

        print(f"🔹 Identifying marker genes — {target_res}...")
        sc.tl.rank_genes_groups(adata, groupby=target_res, method="wilcoxon", use_raw=use_raw)

        sc.pl.rank_genes_groups(adata, n_genes=5, sharey=False, show=False)
        plt.savefig(self.config.figures_dir / "genes_marcadores.png", dpi=150, bbox_inches="tight")
        plt.close()

        print("🔹 Checking canonical markers...")
        marker_list, missing = self._resolve_markers(adata)

        if missing:
            print(f"⚠️  Markers not present in the dataset (skipped): {', '.join(missing)}")

        if marker_list:
            sc.pl.umap(adata, color=marker_list, use_raw=use_raw, show=False)
            plt.savefig(self.config.figures_dir / "marcadores_classicos.png", dpi=150, bbox_inches="tight")
            plt.close()
        else:
            print("⚠️  No canonical markers available — skipping marker UMAP.")

        print("🔹 Assigning cell types from canonical marker scores...")
        labels = self._assign_cell_types(adata, target_res)
        adata.obs["cell_type"] = pd.Categorical(
            adata.obs[target_res].astype(str).map(labels)
        )
        if "X_umap" in adata.obsm:
            sc.pl.umap(adata, color="cell_type", legend_loc="on data",
                       legend_fontsize=7, title="Cell types (suggested)", show=False)
            plt.savefig(self.config.figures_dir / "umap_tipos_celulares.png", dpi=150, bbox_inches="tight")
            plt.close()

        self._generate_summary(adata, target_res, labels)

        return adata

    def annotate_and_save(self, adata: anndata.AnnData, output_path: Optional[str] = None) -> anndata.AnnData:
        """Annotate and save results."""
        adata = self.annotate(adata)
        output = output_path or self.config.annotated_path
        write_h5ad(adata, output)
        print(f"✅ Saved to: {output}")
        return adata

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _resolve_markers(self, adata: anndata.AnnData) -> Tuple[List[str], List[str]]:
        """
        Return (available, missing) canonical markers.

        Markers are looked up in .raw when present because they are often not
        highly variable and therefore absent from the HVG-subset .var.
        """
        marker_list: List[str] = []
        for genes in self.config.marker_genes.values():
            marker_list.extend(genes)
        marker_list = list(dict.fromkeys(marker_list))

        available_set = set(self._expression_source(adata).var_names)
        available = [gene for gene in marker_list if gene in available_set]
        missing = [gene for gene in marker_list if gene not in available_set]
        return available, missing

    @staticmethod
    def _expression_source(adata: anndata.AnnData):
        """Full log-normalized matrix: ``.raw`` when present, else ``adata`` itself."""
        return adata.raw if adata.raw is not None else adata

    def _cluster_marker_scores(self, adata: anndata.AnnData, groupby: str) -> pd.DataFrame:
        """
        Score each (cluster × cell type) pair.

        For every marker gene the mean expression per cluster is min-max scaled
        across clusters (so highly expressed genes such as LYZ do not dominate);
        the score of a cell type is the average of its markers' scaled values.
        """
        source = self._expression_source(adata)
        clusters = adata.obs[groupby].astype(str)
        order = self._sorted_groups(clusters.unique())

        scores: Dict[str, pd.Series] = {}
        for cell_type, genes in self.config.marker_genes.items():
            genes = [g for g in genes if g in source.var_names]
            if not genes:
                continue
            matrix = source[:, genes].X
            matrix = matrix.toarray() if sparse.issparse(matrix) else np.asarray(matrix)
            means = (
                pd.DataFrame(matrix, columns=genes, index=adata.obs_names)
                .groupby(clusters.values).mean()
                .reindex(order)
            )
            span = (means.max() - means.min()).replace(0, np.nan)
            scaled = ((means - means.min()) / span).fillna(0.0)
            scores[cell_type] = scaled.mean(axis=1)

        return pd.DataFrame(scores, index=order)

    def _assign_cell_types(self, adata: anndata.AnnData, groupby: str) -> Dict[str, str]:
        """Map cluster id → best-scoring cell type (or ``Unassigned``)."""
        scores = self._cluster_marker_scores(adata, groupby)
        if scores.empty:
            return {str(c): UNASSIGNED for c in adata.obs[groupby].unique()}

        labels: Dict[str, str] = {}
        for cluster, row in scores.iterrows():
            best = row.idxmax()
            labels[str(cluster)] = best if row[best] >= self.config.min_annotation_score else UNASSIGNED
        return labels

    @staticmethod
    def _sorted_groups(groups) -> List[str]:
        """Sort cluster ids numerically when possible ('0', '1', '10' — not '0', '10', '1')."""
        groups = [str(g) for g in groups]
        try:
            return sorted(groups, key=int)
        except ValueError:
            return sorted(groups)

    def _generate_summary(self, adata: anndata.AnnData, target_res: str,
                          labels: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """Generate cluster summary table (``resultados/resumo_grupos.csv``)."""
        grupos = self._sorted_groups(adata.obs[target_res].unique())
        nomes = adata.uns["rank_genes_groups"]["names"]
        clusters = adata.obs[target_res].astype(str)

        registros = []
        for g in grupos:
            registro = {
                "Grupo": g,
                "Top_genes": ", ".join(nomes[g][:3]),
                "Celulas": int((clusters == g).sum()),
            }
            if labels is not None:
                registro["Tipo_celular_sugerido"] = labels.get(g, UNASSIGNED)
            registros.append(registro)

        tabela = pd.DataFrame.from_records(registros)
        tabela.to_csv(self.config.results_dir / "resumo_grupos.csv", index=False)

        print("\n📋 CLUSTER SUMMARY:")
        print(tabela.to_string(index=False))
        print("\n✅ Annotation completed!")
        print("💡 'Tipo_celular_sugerido' is a marker-based suggestion — validate it against the literature.")
        return tabela
