"""
Data validation following Single Responsibility Principle.
"""
from pathlib import Path
from typing import List
import anndata


class DataValidator:
    """Validates data integrity and pipeline prerequisites."""
    
    @staticmethod
    def validate_file_exists(file_path: Path) -> bool:
        """Check if file exists."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return True
    
    @staticmethod
    def validate_adata(adata: anndata.AnnData) -> bool:
        """Validate AnnData object basic integrity."""
        if adata.n_obs == 0 or adata.n_vars == 0:
            raise ValueError("AnnData has zero observations or variables")
        return True
    
    @staticmethod
    def validate_prerequisites(required_files: List[Path]) -> bool:
        """Validate all prerequisite files exist."""
        missing = []
        for f in required_files:
            if not f.exists():
                missing.append(str(f))
        if missing:
            raise FileNotFoundError(f"Missing required files: {', '.join(missing)}")
        return True
