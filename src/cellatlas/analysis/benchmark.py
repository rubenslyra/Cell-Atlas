"""
Method comparison (scientific validation step).

Compares the marker-score annotation produced by :class:`CellTypeAnnotator`
against independent references on the *same cells*:

* ``expert`` — the curated labels of the classic PBMC3k tutorial
  (``scanpy.datasets.pbmc3k_processed()``, column ``louvain``), annotated by
  hand from marker genes in the Seurat/Scanpy guided-clustering tutorials;
* ``celltypist`` (optional) — a logistic-regression model trained on large
  immune atlases (Domínguez Conde et al., Science 2022). Requires
  ``pip install celltypist`` and internet access to download the model once.

Outputs agreement metrics (accuracy on harmonised labels, adjusted Rand index,
per-type precision/recall) and a confusion matrix.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Optional

import anndata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..core.config import Config

#: Expert labels of the PBMC3k tutorial → the coarse vocabulary used by Cell-Atlas.
EXPERT_TO_COARSE: Dict[str, str] = {
    "CD4 T cells": "T cells",
    "CD8 T cells": "T cells",
    "B cells": "B cells",
    "CD14+ Monocytes": "CD14+ Monocytes",
    "FCGR3A+ Monocytes": "FCGR3A+ Monocytes",
    "NK cells": "NK cells",
    "Dendritic cells": "Dendritic cells",
    "Megakaryocytes": "Platelets",  # platelets are fragments of megakaryocytes
}

#: Ordered rules mapping free-text CellTypist labels to the coarse vocabulary.
_CELLTYPIST_RULES = [
    (r"platelet|megakaryocyte", "Platelets"),
    (r"non-classical monocyte|cd16\+? monocyte|fcgr3a", "FCGR3A+ Monocytes"),
    (r"monocyte", "CD14+ Monocytes"),
    (r"\b[pm]?dc\d?\b|dendritic", "Dendritic cells"),
    (r"\bnk\b|natural killer|ilc", "NK cells"),
    (r"\bb cell|plasma|\bb\b", "B cells"),
    (r"t cell|\bt\b|mait|treg|tem|tcm|cd4|cd8", "T cells"),
]


def to_coarse_celltypist(label: str) -> str:
    """Map a CellTypist label (e.g. 'Tem/Effector helper T cells') to the coarse vocabulary."""
    text = str(label).lower()
    for pattern, coarse in _CELLTYPIST_RULES:
        if re.search(pattern, text):
            return coarse
    return "Other"


@dataclass
class Comparison:
    """Agreement between a prediction and a reference on shared cells."""

    name: str
    n_cells: int
    accuracy: float
    ari: float
    per_type: pd.DataFrame
    confusion: pd.DataFrame

    def summary(self) -> Dict[str, object]:
        return {"metodo": self.name, "celulas": self.n_cells,
                "acuracia": round(self.accuracy, 4), "ARI": round(self.ari, 4)}


def compare_labels(predicted: pd.Series, reference: pd.Series, name: str) -> Comparison:
    """
    Compare two label vectors indexed by cell barcode.

    Only cells present in both are used. ``accuracy`` is the fraction of cells
    with identical labels; ``ari`` (adjusted Rand index) measures partition
    agreement independent of label names (1 = identical, ~0 = random).
    """
    from sklearn.metrics import adjusted_rand_score

    common = predicted.index.intersection(reference.index)
    if len(common) == 0:
        raise ValueError("No shared cell barcodes between prediction and reference.")
    pred = predicted.loc[common].astype(str)
    ref = reference.loc[common].astype(str)

    confusion = pd.crosstab(ref.rename("referencia"), pred.rename("previsto"))
    rows = []
    for label in sorted(set(ref) | set(pred)):
        tp = int(((pred == label) & (ref == label)).sum())
        n_pred = int((pred == label).sum())
        n_ref = int((ref == label).sum())
        rows.append({
            "tipo": label,
            "celulas_referencia": n_ref,
            "celulas_previstas": n_pred,
            "precisao": round(tp / n_pred, 4) if n_pred else np.nan,
            "revocacao": round(tp / n_ref, 4) if n_ref else np.nan,
        })
    shared_names = set(pred) & set(ref)
    # Accuracy only makes sense when both sides use the same vocabulary
    # (e.g. not for cluster ids vs cell-type names); ARI works in both cases.
    accuracy = float((pred == ref).mean()) if shared_names else float("nan")
    return Comparison(
        name=name,
        n_cells=len(common),
        accuracy=accuracy,
        ari=float(adjusted_rand_score(ref, pred)),
        per_type=pd.DataFrame(rows),
        confusion=confusion,
    )


def load_expert_labels() -> pd.Series:
    """Curated PBMC3k tutorial labels (fine: CD4 T, CD8 T, ...), indexed by barcode."""
    import scanpy as sc

    return sc.datasets.pbmc3k_processed().obs["louvain"].astype(str)


def to_coarse_expert(labels: pd.Series) -> pd.Series:
    """Harmonise expert labels to the coarse vocabulary used by Cell-Atlas."""
    return labels.map(EXPERT_TO_COARSE).fillna("Other")


def run_celltypist(adata: anndata.AnnData, model: str = "Immune_All_Low.pkl") -> pd.Series:
    """Predict with CellTypist (majority voting over its own over-clustering)."""
    try:
        import celltypist
        from celltypist import models
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("CellTypist is not installed: pip install celltypist") from exc

    models.download_models(model=[model], force_update=False)
    source = adata.raw.to_adata() if adata.raw is not None else adata.copy()
    # CellTypist expects log1p-normalised counts to 10,000 per cell: exactly what .raw holds.
    result = celltypist.annotate(source, model=model, majority_voting=True)
    labels = result.predicted_labels["majority_voting"].astype(str)
    return labels.map(to_coarse_celltypist)


class MethodComparator:
    """Runs the comparisons and writes tables/figures."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def compare(self, adata: anndata.AnnData, celltypist_model: Optional[str] = None) -> pd.DataFrame:
        if "cell_type" not in adata.obs:
            raise ValueError("cell_type not found. Run `cellatlas annotate` first.")
        os.makedirs(self.config.results_dir, exist_ok=True)
        os.makedirs(self.config.figures_dir, exist_ok=True)

        ours = adata.obs["cell_type"].astype(str)
        comparisons = []

        print("🔹 Loading expert reference (PBMC3k tutorial labels)...")
        expert_fine = load_expert_labels()
        expert = to_coarse_expert(expert_fine)
        comp = compare_labels(ours, expert, "marcadores vs especialista")
        comparisons.append(comp)
        self._save(comp, "especialista")

        target = self.config.target_resolution
        if target in adata.obs:
            clusters = adata.obs[target].astype(str)
            comparisons.append(compare_labels(clusters, expert_fine, f"grupos {target} vs especialista (fino)"))

        if celltypist_model:
            print(f"🔹 Running CellTypist ({celltypist_model})...")
            ct = run_celltypist(adata, celltypist_model)
            comp_ct = compare_labels(ours, ct, "marcadores vs CellTypist")
            comparisons.append(comp_ct)
            self._save(comp_ct, "celltypist")
            comparisons.append(compare_labels(ct, expert, "CellTypist vs especialista"))

        summary = pd.DataFrame([c.summary() for c in comparisons])
        summary.to_csv(self.config.results_dir / "comparacao_resumo.csv", index=False)
        print("\n📋 METHOD COMPARISON:")
        print(summary.to_string(index=False))
        return summary

    def _save(self, comp: Comparison, tag: str) -> None:
        comp.per_type.to_csv(self.config.results_dir / f"comparacao_{tag}_por_tipo.csv", index=False)
        comp.confusion.to_csv(self.config.results_dir / f"matriz_confusao_{tag}.csv")
        self._plot_confusion(comp, self.config.figures_dir / f"matriz_confusao_{tag}.png")

    @staticmethod
    def _plot_confusion(comp: Comparison, path) -> None:
        conf = comp.confusion
        share = conf.div(conf.sum(axis=1), axis=0)
        fig, ax = plt.subplots(figsize=(1.1 * conf.shape[1] + 3, 0.6 * conf.shape[0] + 2))
        im = ax.imshow(share.values, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(conf.shape[1]), conf.columns, rotation=40, ha="right")
        ax.set_yticks(range(conf.shape[0]), conf.index)
        for i in range(conf.shape[0]):
            for j in range(conf.shape[1]):
                n = conf.values[i, j]
                if n:
                    ax.text(j, i, str(n), ha="center", va="center", fontsize=8,
                            color="white" if share.values[i, j] > 0.6 else "black")
        ax.set_xlabel("Cell-Atlas (marcadores)")
        ax.set_ylabel("Referência")
        ax.set_title(f"{comp.name} — acurácia {comp.accuracy:.1%}, ARI {comp.ari:.2f}")
        fig.colorbar(im, ax=ax, fraction=0.04, label="fração da linha")
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
