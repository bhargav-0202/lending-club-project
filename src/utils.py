"""
Utility functions for the Lending Club Project.

This module contains helper functions and constants used across
the entire ML pipeline.
"""

import logging
from typing import Any, Dict, Optional
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Scoring points configuration
SCORE_POINTS = {
    'unacceptable': 0,
    'very_bad': 100,
    'bad': 250,
    'good': 500,
    'very_good': 650,
    'excellent': 800,
}

# Grade points configuration
GRADE_POINTS = {
    'unacceptable': 750,
    'very_bad': 1000,
    'bad': 1500,
    'good': 2000,
    'very_good': 2500,
}

# Weighting factors for loan score calculation (must sum to 1.0)
SCORE_WEIGHTS = {
    'payment_history': 0.20,        # 20%
    'defaulters_history': 0.45,     # 45%
    'financial_health': 0.35,       # 35%
}


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


def get_project_paths() -> Dict[str, Path]:
    """
    Get standardized project directory paths.
    
    Returns:
        Dict: Dictionary containing all project directory paths
    """
    root = Path(__file__).parent.parent
    paths = {
        'root': root,
        'data_raw': root / 'data' / 'raw',
        'data_processed': root / 'data' / 'processed',
        'notebooks': root / 'notebooks',
        'outputs': root / 'outputs',
        'models': root / 'outputs' / 'models',
        'plots': root / 'outputs' / 'plots',
    }
    return paths


def ensure_directories_exist(paths: Dict[str, Path]) -> None:
    """
    Ensure all required directories exist.
    
    Args:
        paths: Dictionary of directory paths
        
    Raises:
        ConfigurationError: If directories cannot be created
    """
    try:
        for key, path in paths.items():
            if 'raw' in key or 'processed' in key or key == 'notebooks':
                # Skip raw/processed/notebooks as they're expected to exist
                continue
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {path}")
    except Exception as e:
        raise ConfigurationError(f"Failed to create directories: {str(e)}")


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Log function calls with parameters for debugging.
    
    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters
    """
    params_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"Calling {func_name}({params_str})")


def validate_dataframe_columns(df: Any, required_columns: list) -> bool:
    """
    Validate that a dataframe contains required columns.
    
    Args:
        df: The dataframe to validate
        required_columns: List of required column names
        
    Returns:
        bool: True if all columns exist, False otherwise
    """
    if not hasattr(df, 'columns'):
        logger.error("Input object does not have 'columns' attribute")
        return False
    
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing columns: {missing_cols}")
        return False
    
    return True


def save_output(data: Any, output_path: Path, format_type: str = 'parquet') -> None:
    """
    Save processed data to disk.
    
    Args:
        data: Data to save (DataFrame or similar)
        output_path: Path where to save
        format_type: Format to save in ('parquet', 'csv', etc.)
        
    Raises:
        ConfigurationError: If save operation fails
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type.lower() == 'parquet':
            data.write.mode("overwrite").parquet(str(output_path))
        elif format_type.lower() == 'csv':
            data.write.mode("overwrite").option("header", "true").csv(str(output_path))
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        logger.info(f"Successfully saved output to {output_path}")
    except Exception as e:
        raise ConfigurationError(f"Failed to save output: {str(e)}")


def print_section_header(title: str) -> None:
    """
    Print a formatted section header for console output.
    
    Args:
        title: Section title to print
    """
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")
