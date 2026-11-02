"""
Cell-Atlas
A reproducible, object-oriented single-cell RNA-seq analysis framework.
"""

__version__ = "0.1.0"
__author__ = "Cell-Atlas Team"

from .core.config import Config
from .core.pipeline import Pipeline

__all__ = ["Config", "Pipeline", "__version__"]
