"""
I/O helpers shared by every pipeline step.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Union

import anndata
import pandas as pd


def _to_object_strings(frame: pd.DataFrame) -> None:
    """Convert pandas nullable ``string`` columns/index to plain ``object`` in place.

    Files written by recent anndata/pandas may carry ``string[python]`` columns,
    which older anndata versions (< 0.12) refuse to write back.
    """
    for column in frame.columns:
        if isinstance(frame[column].dtype, pd.StringDtype):
            frame[column] = frame[column].astype(object)
    if isinstance(frame.index.dtype, pd.StringDtype):
        frame.index = frame.index.astype(object)


def write_h5ad(adata: anndata.AnnData, path: Union[str, Path]) -> Path:
    """Write ``adata`` atomically (temp file + rename) so a crash never leaves a corrupt .h5ad."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    _to_object_strings(adata.obs)
    _to_object_strings(adata.var)
    if adata.raw is not None:
        _to_object_strings(adata.raw.var)

    tmp = path.with_name(path.name + ".tmp")
    try:
        adata.write_h5ad(tmp)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return path
