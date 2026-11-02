"""
Core interfaces following Interface Segregation Principle (ISP).
All components depend on abstractions, not concrete implementations.
"""
from abc import ABC, abstractmethod
from typing import Any
import anndata


class IDataLoader(ABC):
    """Interface for data loading strategies."""
    
    @abstractmethod
    def load(self, source: str) -> anndata.AnnData:
        """Load data from source and return AnnData object."""
        pass


class IPreprocessor(ABC):
    """Interface for preprocessing pipelines."""
    
    @abstractmethod
    def preprocess(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Preprocess AnnData and return processed object."""
        pass


class IClusterer(ABC):
    """Interface for clustering algorithms."""
    
    @abstractmethod
    def cluster(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Cluster cells and return annotated AnnData."""
        pass


class IAnnotator(ABC):
    """Interface for cell type annotation."""
    
    @abstractmethod
    def annotate(self, adata: anndata.AnnData) -> anndata.AnnData:
        """Annotate clusters and return annotated AnnData."""
        pass


class IVisualizer(ABC):
    """Interface for visualization components."""
    
    @abstractmethod
    def plot(self, adata: anndata.AnnData, **kwargs) -> Any:
        """Generate visualization."""
        pass
