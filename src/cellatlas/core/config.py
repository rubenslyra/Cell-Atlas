"""
Configuration management following Single Responsibility Principle (SRP).
Centralized configuration with validation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, Union

PathLike = Union[str, Path]


@dataclass
class Config:
    """Central configuration for Cell-Atlas pipeline."""

    # Directories (relative paths are resolved against the current working directory)
    data_dir: Path = field(default_factory=lambda: Path("dados"))
    results_dir: Path = field(default_factory=lambda: Path("resultados"))
    figures_dir: Path = field(default_factory=lambda: Path("figuras"))

    # Data files
    raw_data: str = "pbmc3k.h5ad"
    processed_data: str = "pbmc3k_processado.h5ad"
    clustered_data: str = "pbmc3k_leiden.h5ad"
    annotated_data: str = "pbmc3k_anotado.h5ad"

    # Reproducibility
    random_state: int = 0

    # QC parameters
    min_genes_per_cell: int = 200
    max_genes_per_cell: int = 2500
    max_mito_percent: float = 5.0
    min_cells_per_gene: int = 3

    # Normalization
    target_sum: float = 1e4
    n_top_genes: int = 2000

    # Dimensionality reduction
    n_pcs: int = 10
    svd_solver: str = "arpack"

    # Clustering
    n_neighbors: int = 15
    resolutions: List[float] = field(default_factory=lambda: [0.2, 0.4, 0.6, 1.0])
    leiden_flavor: str = "igraph"
    leiden_n_iterations: int = 2

    # Annotation
    target_resolution: str = "leiden_0.6"
    min_annotation_score: float = 0.5
    marker_genes: Dict[str, List[str]] = field(default_factory=lambda: {
        "T cells": ["CD3E", "CD3D", "IL7R"],
        "B cells": ["MS4A1", "CD79A"],
        "CD14+ Monocytes": ["CD14", "LYZ"],
        "FCGR3A+ Monocytes": ["FCGR3A", "MS4A7"],
        "NK cells": ["GNLY", "NKG7"],
        "Dendritic cells": ["FCER1A", "CST3"],
        "Platelets": ["PPBP", "PF4"],
    })

    def __post_init__(self) -> None:
        """Normalize path fields and validate parameters (no filesystem side effects)."""
        self.data_dir = Path(self.data_dir)
        self.results_dir = Path(self.results_dir)
        self.figures_dir = Path(self.figures_dir)
        self.validate()

    # ------------------------------------------------------------------ #
    # Validation / filesystem
    # ------------------------------------------------------------------ #
    def validate(self) -> None:
        """Raise ``ValueError`` when parameters are inconsistent."""
        if self.min_genes_per_cell >= self.max_genes_per_cell:
            raise ValueError("min_genes_per_cell must be lower than max_genes_per_cell")
        if not 0 < self.max_mito_percent <= 100:
            raise ValueError("max_mito_percent must be in (0, 100]")
        if self.n_pcs < 2 or self.n_neighbors < 2:
            raise ValueError("n_pcs and n_neighbors must be >= 2")
        if not self.resolutions or any(r <= 0 for r in self.resolutions):
            raise ValueError("resolutions must be a non-empty list of positive numbers")

    def ensure_dirs(self) -> None:
        """Create output directories. Called explicitly by the CLI, never on import."""
        for directory in (self.data_dir, self.results_dir, self.figures_dir):
            directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "Config":
        """Build a Config from a dict, rejecting unknown keys (typos fail loudly)."""
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(values) - known)
        if unknown:
            raise ValueError(f"Unknown configuration keys: {', '.join(unknown)}")
        return cls(**dict(values))

    @classmethod
    def from_file(cls, path: PathLike) -> "Config":
        """Load configuration from a ``.toml`` or ``.json`` file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".json":
            values = json.loads(path.read_text(encoding="utf-8"))
        elif suffix == ".toml":
            try:
                import tomllib  # Python >= 3.11
            except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10
                import tomli as tomllib  # type: ignore[no-redef]
            with path.open("rb") as handle:
                values = tomllib.load(handle)
        else:
            raise ValueError(f"Unsupported config format '{suffix}' (use .toml or .json)")

        # Allow either a flat file or a [cellatlas] table.
        if "cellatlas" in values and isinstance(values["cellatlas"], dict):
            values = values["cellatlas"]
        return cls.from_mapping(values)

    # ------------------------------------------------------------------ #
    # Derived paths
    # ------------------------------------------------------------------ #
    @property
    def raw_path(self) -> Path:
        return self.data_dir / self.raw_data

    @property
    def processed_path(self) -> Path:
        return self.data_dir / self.processed_data

    @property
    def clustered_path(self) -> Path:
        return self.data_dir / self.clustered_data

    @property
    def annotated_path(self) -> Path:
        return self.data_dir / self.annotated_data
