"""Regression tests for the preprocessing invariants used by annotation."""
import anndata as ad
import numpy as np
import pandas as pd

from cellatlas.analysis.preprocessing import Preprocessor
from cellatlas.core.config import Config


def _synthetic_dataset(n_cells: int = 60, n_genes: int = 1200) -> ad.AnnData:
    rng = np.random.default_rng(42)
    genes = [f"GENE{i}" for i in range(n_genes - 2)] + ["CD3E", "MS4A1"]
    counts = rng.poisson(1.0, size=(n_cells, n_genes)).astype("float32")
    # Constant expression keeps canonical markers out of the HVG selection.
    counts[:, -2] = 50
    counts[:, -1] = 50

    return ad.AnnData(
        X=counts,
        obs=pd.DataFrame(index=[f"cell{i}" for i in range(n_cells)]),
        var=pd.DataFrame(index=pd.Index(genes, name="gene")),
    )


def test_raw_preserves_markers_excluded_from_hvg(tmp_path):
    config = Config(
        data_dir=tmp_path,
        results_dir=tmp_path,
        figures_dir=tmp_path,
        min_genes_per_cell=1,
        max_genes_per_cell=2000,
        max_mito_percent=100.0,
        min_cells_per_gene=1,
        n_top_genes=60,
    )

    adata = Preprocessor(config).preprocess(_synthetic_dataset())

    assert adata.raw is not None
    assert adata.n_vars == 60
    assert "CD3E" in adata.raw.var_names
    assert "CD3E" not in adata.var_names
    assert adata.raw.n_vars > adata.n_vars
