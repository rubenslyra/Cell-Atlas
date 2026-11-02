"""
Configuration management following Single Responsibility Principle (SRP).
Centralized configuration with validation.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any


@dataclass
class Config:
    """Central configuration for Cell-Atlas pipeline."""
    
    # Directories
    data_dir: Path = field(default_factory=lambda: Path("dados"))
    results_dir: Path = field(default_factory=lambda: Path("resultados"))
    figures_dir: Path = field(default_factory=lambda: Path("figuras"))
    
    # Data files
    raw_data: str = "pbmc3k.h5ad"
    processed_data: str = "pbmc3k_processado.h5ad"
    clustered_data: str = "pbmc3k_leiden.h5ad"
    
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
    marker_genes: Dict[str, List[str]] = field(default_factory=lambda: {
        "T cells": ["CD3E", "CD3D", "TRAC"],
        "B cells": ["MS4A1", "CD79A"],
        "Monocytes": ["CD14", "LYZ"],
        "NK cells": ["NKG7", "GNLY"],
    })
    
    def __post_init__(self):
        """Ensure directories exist and validate parameters."""
        self.data_dir = Path(self.data_dir)
        self.results_dir = Path(self.results_dir)
        self.figures_dir = Path(self.figures_dir)
        
        for directory in [self.data_dir, self.results_dir, self.figures_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def raw_path(self) -> Path:
        return self.data_dir / self.raw_data
    
    @property
    def processed_path(self) -> Path:
        return self.data_dir / self.processed_data
    
    @property
    def clustered_path(self) -> Path:
        return self.data_dir / self.clustered_data
