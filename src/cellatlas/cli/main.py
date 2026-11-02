"""
CLI entry point for Cell-Atlas pipeline.
"""
import argparse
import sys
from pathlib import Path

from ..core.config import Config
from ..data.loader import PBMC3kLoader
from ..analysis.preprocessing import Preprocessor
from ..analysis.clustering import LeidenClusterer
from ..analysis.annotation import CellTypeAnnotator


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Cell-Atlas: Reproducible scRNA-seq analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cellatlas download          Download PBMC3k dataset
  cellatlas preprocess       Run preprocessing pipeline
  cellatlas cluster          Run clustering analysis
  cellatlas annotate         Run cell type annotation
  cellatlas run-all          Run complete pipeline
        """
    )
    
    parser.add_argument('command', 
                       choices=['download', 'preprocess', 'cluster', 'annotate', 'run-all'],
                       help='Pipeline command to execute')
    parser.add_argument('--config', type=Path, help='Path to custom config file')
    
    args = parser.parse_args()
    config = Config()
    
    try:
        if args.command == 'download':
            loader = PBMC3kLoader(config)
            loader.load()
        
        elif args.command == 'preprocess':
            from ..utils.validators import DataValidator
            DataValidator.validate_file_exists(config.raw_path)
            loader = PBMC3kLoader(config)
            adata = loader.load(str(config.raw_path))
            preprocessor = Preprocessor(config)
            preprocessor.preprocess_and_save(adata)
        
        elif args.command == 'cluster':
            from ..utils.validators import DataValidator
            DataValidator.validate_file_exists(config.processed_path)
            import scanpy as sc
            adata = sc.read_h5ad(config.processed_path)
            clusterer = LeidenClusterer(config)
            clusterer.cluster_and_save(adata)
        
        elif args.command == 'annotate':
            from ..utils.validators import DataValidator
            DataValidator.validate_file_exists(config.clustered_path)
            import scanpy as sc
            adata = sc.read_h5ad(config.clustered_path)
            annotator = CellTypeAnnotator(config)
            annotator.annotate_and_save(adata)
        
        elif args.command == 'run-all':
            from ..utils.validators import DataValidator
            loader = PBMC3kLoader(config)
            adata = loader.load()
            preprocessor = Preprocessor(config)
            adata = preprocessor.preprocess_and_save(adata)
            clusterer = LeidenClusterer(config)
            adata = clusterer.cluster_and_save(adata)
            annotator = CellTypeAnnotator(config)
            adata = annotator.annotate_and_save(adata)
            print("\n🎉 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
