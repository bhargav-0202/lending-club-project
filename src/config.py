"""
Configuration module for Lending Club Project.

Contains configuration for different environments and execution modes.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"
PLOTS_DIR = OUTPUTS_DIR / "plots"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Spark configuration
SPARK_CONFIG = {
    'spark.app.name': 'LendingClubLoanScoring',
    'spark.driver.memory': os.getenv('SPARK_DRIVER_MEMORY', '4g'),
    'spark.executor.memory': os.getenv('SPARK_EXECUTOR_MEMORY', '4g'),
    'spark.sql.shuffle.partitions': os.getenv('SPARK_SHUFFLE_PARTITIONS', '200'),
}

# Data configuration
DATA_CONFIG = {
    'bad_record_threshold': 1,  # Records appearing more than once are bad
    'min_rows_threshold': 1,    # Minimum rows for data quality check
}

# Feature engineering weights (must sum to 1.0)
FEATURE_WEIGHTS = {
    'payment_history': 0.20,
    'defaulters_history': 0.45,
    'financial_health': 0.35,
}

# Grade thresholds (score boundaries)
GRADE_THRESHOLDS = {
    'A': 2500,
    'B': 2000,
    'C': 1500,
    'D': 1000,
    'E': 750,
    'F': 0,
}

# Hive database configuration
HIVE_CONFIG = {
    'database': os.getenv('HIVE_DATABASE', 'itv022692_lending_club'),
    'tables': {
        'customers': 'customers_new',
        'loans': 'loans',
        'repayments': 'loans_repayments',
        'defaulters_delinq': 'loans_defaulters_delinq_new',
        'defaulters_detail': 'loans_defaulters_detail_rec_enq_new',
    }
}

# CSV file names (in data/raw directory)
CSV_CONFIG = {
    'customers': 'customers.csv',
    'loans': 'loans.csv',
    'repayments': 'loans_repayments.csv',
    'defaulters_delinq': 'loans_defaulters_delinq.csv',
    'defaulters_detail': 'loans_defaulters_detail.csv',
}

# Output configuration
OUTPUT_CONFIG = {
    'format': 'parquet',  # 'parquet' or 'csv'
    'mode': 'overwrite',
    'partitions': 4,
}

# Development vs Production
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configuration by environment
ENVIRONMENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    'development': {
        'log_level': 'DEBUG',
        'spark_shuffle_partitions': '200',
    },
    'production': {
        'log_level': 'INFO',
        'spark_shuffle_partitions': '1000',
    },
}


def get_config(env: str = None) -> Dict[str, Any]:
    """
    Get configuration for the specified environment.
    
    Args:
        env: Environment name ('development' or 'production')
        
    Returns:
        Dict: Configuration dictionary
    """
    if env is None:
        env = ENVIRONMENT
    
    config = {
        'project_root': PROJECT_ROOT,
        'data_dir': DATA_DIR,
        'raw_data_dir': RAW_DATA_DIR,
        'processed_data_dir': PROCESSED_DATA_DIR,
        'outputs_dir': OUTPUTS_DIR,
        'models_dir': MODELS_DIR,
        'plots_dir': PLOTS_DIR,
        'spark': SPARK_CONFIG,
        'data': DATA_CONFIG,
        'weights': FEATURE_WEIGHTS,
        'grades': GRADE_THRESHOLDS,
        'hive': HIVE_CONFIG,
        'csv': CSV_CONFIG,
        'output': OUTPUT_CONFIG,
    }
    
    # Apply environment-specific overrides
    if env in ENVIRONMENT_CONFIGS:
        env_config = ENVIRONMENT_CONFIGS[env]
        for key, value in env_config.items():
            if key in config:
                config[key] = value
    
    return config


def validate_config() -> bool:
    """
    Validate configuration settings.
    
    Returns:
        bool: True if all validations pass
    """
    # Verify weighted sum to 1.0
    weight_sum = sum(FEATURE_WEIGHTS.values())
    if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point errors
        print(f"ERROR: Feature weights sum to {weight_sum}, must equal 1.0")
        return False
    
    # Verify grade thresholds are in descending order
    thresholds = list(GRADE_THRESHOLDS.values())
    if thresholds != sorted(thresholds, reverse=True):
        print("ERROR: Grade thresholds must be in descending order")
        return False
    
    return True


if __name__ == '__main__':
    config = get_config()
    print("Configuration loaded successfully")
    if validate_config():
        print("Configuration validation passed")
    else:
        print("Configuration validation failed")
