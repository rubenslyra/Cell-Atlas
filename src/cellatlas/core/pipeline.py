"""
Pipeline orchestration following Open/Closed Principle (OCP).
Extensible pipeline using composition over inheritance.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from abc import ABC
import anndata

from .interfaces import IDataLoader, IPreprocessor, IClusterer, IAnnotator


@dataclass
class PipelineStep:
    """Represents a single step in the pipeline."""
    name: str
    handler: callable
    enabled: bool = True


class Pipeline:
    """
    Orchestrates the complete scRNA-seq analysis pipeline.
    Follows Dependency Inversion Principle - depends on abstractions.
    """
    
    def __init__(self, 
                 loader: IDataLoader = None,
                 preprocessor: IPreprocessor = None,
                 clusterer: IClusterer = None,
                 annotator: IAnnotator = None):
        self.loader = loader
        self.preprocessor = preprocessor
        self.clusterer = clusterer
        self.annotator = annotator
        self._history: List[Dict[str, Any]] = []
    
    def run(self, source: str = None) -> anndata.AnnData:
        """Execute the complete pipeline."""
        adata = None
        
        if self.loader and source:
            adata = self.loader.load(source)
            self._log_step("load", adata)
        
        if self.preprocessor and adata is not None:
            adata = self.preprocessor.preprocess(adata)
            self._log_step("preprocess", adata)
        
        if self.clusterer and adata is not None:
            adata = self.clusterer.cluster(adata)
            self._log_step("cluster", adata)
        
        if self.annotator and adata is not None:
            adata = self.annotator.annotate(adata)
            self._log_step("annotate", adata)
        
        return adata
    
    def _log_step(self, step_name: str, adata: anndata.AnnData):
        """Log pipeline step execution."""
        self._history.append({
            "step": step_name,
            "n_obs": adata.n_obs,
            "n_vars": adata.n_vars
        })
    
    @property
    def history(self) -> List[Dict[str, Any]]:
        """Get pipeline execution history."""
        return self._history.copy()
