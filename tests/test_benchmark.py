"""Method-comparison metrics and label harmonisation."""
import math

import pandas as pd

from cellatlas.analysis.benchmark import (
    compare_labels,
    to_coarse_celltypist,
    to_coarse_expert,
)


def _series(values):
    return pd.Series(values, index=[f"c{i}" for i in range(len(values))])


def test_compare_labels_perfect_and_partial():
    ref = _series(["T cells", "T cells", "B cells", "NK cells"])
    same = compare_labels(ref.copy(), ref, "same")
    assert same.accuracy == 1.0
    assert same.ari == 1.0

    pred = _series(["T cells", "NK cells", "B cells", "NK cells"])
    comp = compare_labels(pred, ref, "partial")
    assert comp.accuracy == 0.75
    per_type = comp.per_type.set_index("tipo")
    assert per_type.loc["NK cells", "precisao"] == 0.5
    assert per_type.loc["T cells", "revocacao"] == 0.5
    assert comp.confusion.loc["T cells", "NK cells"] == 1


def test_compare_labels_uses_only_shared_barcodes():
    ref = _series(["T cells", "B cells", "B cells"])
    pred = pd.Series(["B cells", "B cells"], index=["c1", "c9"])
    comp = compare_labels(pred, ref, "overlap")
    assert comp.n_cells == 1
    assert comp.accuracy == 1.0


def test_accuracy_is_nan_for_disjoint_vocabularies():
    clusters = _series(["0", "0", "1", "1"])
    names = _series(["T cells", "T cells", "B cells", "B cells"])
    comp = compare_labels(clusters, names, "clusters")
    assert math.isnan(comp.accuracy)
    assert comp.ari == 1.0  # same partition, different names


def test_label_harmonisation():
    assert to_coarse_expert(pd.Series(["CD8 T cells", "Megakaryocytes"])).tolist() == ["T cells", "Platelets"]
    assert to_coarse_celltypist("Tem/Effector helper T cells") == "T cells"
    assert to_coarse_celltypist("Non-classical monocytes") == "FCGR3A+ Monocytes"
    assert to_coarse_celltypist("Classical monocytes") == "CD14+ Monocytes"
    assert to_coarse_celltypist("CD16+ NK cells") == "NK cells"
    assert to_coarse_celltypist("Naive B cells") == "B cells"
    assert to_coarse_celltypist("pDC") == "Dendritic cells"
    assert to_coarse_celltypist("DC2") == "Dendritic cells"
    assert to_coarse_celltypist("Megakaryocytes/platelets") == "Platelets"
