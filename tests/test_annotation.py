"""Unit tests for marker resolution and cluster summaries."""
import anndata as ad
import numpy as np
import pandas as pd

from cellatlas.analysis.annotation import CellTypeAnnotator
from cellatlas.core.config import Config


def test_resolve_markers_prefers_raw_gene_names(tmp_path):
    config = Config(data_dir=tmp_path, results_dir=tmp_path, figures_dir=tmp_path)
    config.marker_genes = {"T cells": ["CD3E", "TRAC"], "B cells": ["MS4A1"]}

    adata = ad.AnnData(
        X=np.zeros((4, 2)),
        var=pd.DataFrame(index=["HVG1", "HVG2"]),
    )
    adata.raw = ad.AnnData(
        X=np.zeros((4, 3)),
        var=pd.DataFrame(index=["HVG1", "CD3E", "MS4A1"]),
    )

    available, missing = CellTypeAnnotator(config)._resolve_markers(adata)

    assert available == ["CD3E", "MS4A1"]
    assert missing == ["TRAC"]


def test_summary_sorts_clusters_numerically(tmp_path):
    config = Config(data_dir=tmp_path, results_dir=tmp_path, figures_dir=tmp_path)

    names = np.zeros(3, dtype=[("0", "U5"), ("1", "U5"), ("10", "U5")])
    names["0"] = ["A", "B", "C"]
    names["1"] = ["D", "E", "F"]
    names["10"] = ["G", "H", "I"]

    adata = ad.AnnData(
        X=np.zeros((6, 1)),
        obs=pd.DataFrame(
            {"leiden_0.6": pd.Categorical(["0", "0", "1", "1", "10", "10"])}
        ),
    )
    adata.uns["rank_genes_groups"] = {"names": names}

    CellTypeAnnotator(config)._generate_summary(adata, "leiden_0.6")

    summary = pd.read_csv(tmp_path / "resumo_grupos.csv")
    assert summary["Grupo"].tolist() == [0, 1, 10]
    assert summary["Celulas"].tolist() == [2, 2, 2]


def test_assign_cell_types_uses_scaled_marker_scores(tmp_path):
    config = Config(data_dir=tmp_path, results_dir=tmp_path, figures_dir=tmp_path)
    config.marker_genes = {"T cells": ["CD3E"], "B cells": ["MS4A1"]}

    # cluster 0 expresses CD3E, cluster 1 expresses MS4A1, cluster 2 neither.
    X = np.array([[5, 0], [5, 0], [0, 5], [0, 5], [0, 0], [0, 0]], dtype=float)
    adata = ad.AnnData(
        X=X,
        obs=pd.DataFrame({"leiden_0.6": pd.Categorical(["0", "0", "1", "1", "2", "2"])}),
        var=pd.DataFrame(index=["CD3E", "MS4A1"]),
    )

    labels = CellTypeAnnotator(config)._assign_cell_types(adata, "leiden_0.6")

    assert labels == {"0": "T cells", "1": "B cells", "2": "Unassigned"}
