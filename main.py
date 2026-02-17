#!/usr/bin/env python3
"""
Main entry point for the Lending Club Loan Scoring Project.

This script orchestrates the complete ML pipeline:
1. Load data (from files or Hive database)
2. Preprocess and clean data
3. Engineer features and calculate loan scores
4. Evaluate model performance
5. Save results

Usage:
    python main.py [--hive] [--output-path PATH]

Example:
    # Run with Hive database
    python main.py --hive
    
    # Run with CSV files
    python main.py
    
    # Run with custom output path
    python main.py --output-path data/processed/loan_scores
"""

import argparse
import logging
import sys
from pathlib import Path

try:
    from pyspark.sql import SparkSession
except ImportError:
    print("ERROR: PySpark is not installed. Please install it using: pip install pyspark")
    sys.exit(1)

from src.model_training import ModelTrainer
from src.utils import get_project_paths, ensure_directories_exist, print_section_header

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_spark_session() -> SparkSession:
    """
    Create and configure a Spark session.
    
    Returns:
        SparkSession: Configured Spark session
    """
    logger.info("Creating Spark session...")
    
    try:
        spark = SparkSession \
            .builder \
            .appName("LendingClubLoanScoring") \
            .config('spark.driver.memory', '4g') \
            .config('spark.executor.memory', '4g') \
            .getOrCreate()
        
        logger.info("Spark session created successfully")
        return spark
    
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise


def load_data_from_csv(trainer: ModelTrainer, data_dir: Path) -> tuple:
    """
    Load data from CSV files.
    
    Args:
        trainer: ModelTrainer instance
        data_dir: Path to data directory
        
    Returns:
        Tuple: (final_grades DataFrame, metrics dictionary)
    """
    print_section_header("LOADING DATA FROM CSV FILES")
    
    # Define paths to CSV/parquet files
    # Adjust these paths based on your actual data location
    data_paths = {
        'customers': str(data_dir / 'raw' / 'customers.csv'),
        'loans': str(data_dir / 'raw' / 'loans.csv'),
        'repayments': str(data_dir / 'raw' / 'loans_repayments.csv'),
        'defaulters_delinq': str(data_dir / 'raw' / 'loans_defaulters_delinq.csv'),
        'defaulters_detail': str(data_dir / 'raw' / 'loans_defaulters_detail.csv'),
    }
    
    # Filter out paths that don't exist
    available_paths = {}
    for data_type, path in data_paths.items():
        if Path(path).exists():
            available_paths[data_type] = path
            logger.info(f"Found data file: {path}")
        else:
            logger.warning(f"Data file not found: {path}")
    
    if not available_paths:
        logger.warning("No data files found in data/raw directory")
        print("\n" + "="*70)
        print("  DATA NOT FOUND")
        print("="*70)
        print("\nPlease ensure you have the following files in data/raw/:")
        print("  - customers.csv (or .parquet)")
        print("  - loans.csv (or .parquet)")
        print("  - loans_repayments.csv (or .parquet)")
        print("  - loans_defaulters_delinq.csv (or .parquet)")
        print("  - loans_defaulters_detail.csv (or .parquet)")
        print("\nOr use --hive flag to load from Hive database")
        print("="*70 + "\n")
        
        return None, None
    
    return trainer.run_pipeline(data_paths=available_paths)


def load_data_from_hive(trainer: ModelTrainer) -> tuple:
    """
    Load data from Hive database.
    
    Args:
        trainer: ModelTrainer instance
        
    Returns:
        Tuple: (final_grades DataFrame, metrics dictionary)
    """
    print_section_header("LOADING DATA FROM HIVE DATABASE")
    
    # Define Hive table names (adjust database name as needed)
    hive_tables = {
        'customers': 'itv022692_lending_club.customers_new',
        'loans': 'itv022692_lending_club.loans',
        'repayments': 'itv022692_lending_club.loans_repayments',
        'defaulters_delinq': 'itv022692_lending_club.loans_defaulters_delinq_new',
        'defaulters_detail': 'itv022692_lending_club.loans_defaulters_detail_rec_enq_new',
    }
    
    return trainer.run_pipeline(hive_tables=hive_tables)


def main():
    """Main execution function."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Lending Club Loan Scoring ML Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--hive',
        action='store_true',
        help='Load data from Hive database instead of CSV files'
    )
    
    parser.add_argument(
        '--output-path',
        default='data/processed/loan_scores',
        help='Path to save output results (default: data/processed/loan_scores)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file (not yet implemented)'
    )
    
    args = parser.parse_args()
    
    try:
        # Print welcome message
        print_section_header("LENDING CLUB LOAN SCORING MODEL")
        print("Production-Grade Machine Learning Pipeline\n")
        
        # Get project paths
        paths = get_project_paths()
        ensure_directories_exist(paths)
        
        logger.info("Project paths initialized")
        logger.info(f"Project root: {paths['root']}")
        
        # Create Spark session
        spark = create_spark_session()
        
        # Create model trainer
        trainer = ModelTrainer(spark)
        
        # Load and process data
        if args.hive:
            logger.info("Using Hive database as data source")
            final_grades, metrics = load_data_from_hive(trainer)
        else:
            logger.info("Using CSV files as data source")
            final_grades, metrics = load_data_from_csv(trainer, paths['data_raw'].parent)
        
        # If data loading was successful
        if final_grades is not None:
            # Save results
            output_path = args.output_path
            trainer.save_results(final_grades, output_path, format_type='parquet')
            
            # Print completion message
            print_section_header("PIPELINE EXECUTION COMPLETED")
            print(f"\n✓ Loan scoring completed successfully!")
            print(f"✓ Results saved to: {output_path}")
            print(f"✓ Total loans scored: {final_grades.count()}\n")
            
            logger.info("Pipeline execution completed successfully")
        else:
            print("\nPipeline execution failed - data not available")
            logger.error("Pipeline execution failed - data not available")
            sys.exit(1)
        
        # Close Spark session
        spark.stop()
        logger.info("Spark session closed")
        
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print_section_header("ERROR")
        print(f"\nAn error occurred: {str(e)}")
        print("\nFor more details, check the logs above.")
        print("="*70 + "\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
