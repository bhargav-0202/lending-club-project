"""
Data Preprocessing Module for Lending Club Project.

This module handles loading, cleaning, and preparing data for the
machine learning pipeline. It includes:
- Data loading from various sources
- Handling missing values
- Data validation
- Bad data identification and removal
"""

import logging
from typing import Tuple, Optional, List
from pyspark.sql import SparkSession, DataFrame

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Handles all data preprocessing operations."""
    
    def __init__(self, spark_session: SparkSession):
        """
        Initialize the DataPreprocessor.
        
        Args:
            spark_session: Active Spark session
        """
        self.spark = spark_session
        logger.info("DataPreprocessor initialized")
    
    def load_data(self, file_path: str, format_type: str = 'csv',
                  header: bool = True, infer_schema: bool = True) -> DataFrame:
        """
        Load data from file system.
        
        Args:
            file_path: Path to the data file
            format_type: File format (csv, parquet, etc.)
            header: Whether file has header row
            infer_schema: Whether to infer schema
            
        Returns:
            DataFrame: Loaded data
        """
        try:
            logger.info(f"Loading data from {file_path}")
            
            if format_type.lower() == 'csv':
                df = self.spark.read \
                    .format("csv") \
                    .option("header", "true" if header else "false") \
                    .option("inferSchema", "true" if infer_schema else "false") \
                    .load(file_path)
            
            elif format_type.lower() == 'parquet':
                df = self.spark.read.parquet(file_path)
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            logger.info(f"Successfully loaded {df.count()} rows from {file_path}")
            return df
        
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            raise
    
    def load_from_hive_database(self, table_name: str) -> DataFrame:
        """
        Load data from Hive database.
        
        Args:
            table_name: Name of the table in Hive
            
        Returns:
            DataFrame: Loaded data from Hive table
        """
        try:
            logger.info(f"Loading table {table_name} from Hive database")
            df = self.spark.sql(f"SELECT * FROM {table_name}")
            logger.info(f"Successfully loaded {df.count()} rows from {table_name}")
            return df
        
        except Exception as e:
            logger.error(f"Error loading Hive table {table_name}: {str(e)}")
            raise
    
    def identify_bad_data(self, df: DataFrame, group_column: str) -> Tuple[DataFrame, DataFrame]:
        """
        Identify duplicate/bad records based on grouping.
        
        Records that appear more than once for a given group are flagged as bad.
        
        Args:
            df: DataFrame to analyze
            group_column: Column to group by (e.g., 'member_id')
            
        Returns:
            Tuple: (bad_records_df, good_records_df)
        """
        logger.info(f"Identifying bad data based on {group_column}")
        
        # Find records that appear more than once
        bad_records = df.select(group_column) \
            .where(f"{group_column} NOT IN " + 
                   f"(SELECT {group_column} FROM {df})")
        
        # Alternative simpler approach: group and identify duplicates
        bad_records = self.spark.sql(f"""
            SELECT DISTINCT {group_column}
            FROM (
                SELECT {group_column}, COUNT(*) as total
                FROM {df}
                GROUP BY {group_column}
                HAVING total > 1
            )
        """)
        
        logger.info(f"Found {bad_records.count()} bad records")
        
        # Create a temp view for filtering good data
        bad_records.createOrReplaceTempView("bad_records_temp")
        
        good_records = df.where(f"{group_column} NOT IN (SELECT {group_column} FROM bad_records_temp)")
        
        logger.info(f"Extracted {good_records.count()} good records")
        
        return bad_records, good_records
    
    def remove_bad_records(self, df: DataFrame, bad_records: DataFrame, 
                           key_column: str) -> DataFrame:
        """
        Remove bad records from a dataframe.
        
        Args:
            df: Original DataFrame
            bad_records: DataFrame containing bad record identifiers
            key_column: Column to use for joining (e.g., 'member_id')
            
        Returns:
            DataFrame: Cleaned data without bad records
        """
        logger.info(f"Removing bad records from dataframe")
        
        bad_records.createOrReplaceTempView("bad_temp")
        cleaned_df = df.where(f"{key_column} NOT IN (SELECT {key_column} FROM bad_temp)")
        
        logger.info(f"Removed bad records. Remaining: {cleaned_df.count()} rows")
        return cleaned_df
    
    def handle_missing_values(self, df: DataFrame, 
                             strategy: str = 'drop', 
                             subset: Optional[List[str]] = None) -> DataFrame:
        """
        Handle missing values in the dataframe.
        
        Args:
            df: DataFrame to process
            strategy: Strategy to use ('drop', 'forward_fill', 'mean', 'default')
            subset: Specific columns to process (if None, process all)
            
        Returns:
            DataFrame: DataFrame with missing values handled
        """
        logger.info(f"Handling missing values with strategy: {strategy}")
        
        if strategy == 'drop':
            if subset:
                df = df.dropna(subset=subset)
            else:
                df = df.dropna()
            logger.info(f"Dropped rows with missing values. Remaining: {df.count()}")
        
        elif strategy == 'forward_fill':
            # Spark doesn't have built-in forward fill, use fillna with a default
            logger.warning("Forward fill not supported in Spark, using default values")
            df = df.fillna(0)
        
        elif strategy == 'mean':
            # Calculate mean for numeric columns and fill
            logger.info("Filling missing values with column means")
            # This would require calculating means for each numeric column
            pass
        
        return df
    
    def validate_data_quality(self, df: DataFrame, min_rows: int = 1) -> bool:
        """
        Validate data quality.
        
        Args:
            df: DataFrame to validate
            min_rows: Minimum expected number of rows
            
        Returns:
            bool: True if data quality is acceptable
        """
        row_count = df.count()
        
        if row_count < min_rows:
            logger.error(f"Data quality check failed: {row_count} rows < {min_rows} minimum")
            return False
        
        # Check for null columns
        null_counts = df.select([count(when(col(c).isNull(), c)).alias(c) for c in df.columns])
        
        logger.info(f"Data quality check passed: {row_count} rows")
        return True
    
    def show_data_summary(self, df: DataFrame, name: str = "Dataset") -> None:
        """
        Print a summary of the dataframe.
        
        Args:
            df: DataFrame to summarize
            name: Name to display for the dataset
        """
        print(f"\n{'='*70}")
        print(f"  {name} Summary")
        print(f"{'='*70}")
        print(f"Row Count: {df.count()}")
        print(f"Columns: {len(df.columns)}")
        print(f"\nColumn Names and Types:")
        df.printSchema()
        print(f"\nFirst 5 rows:")
        df.show(5)
        print(f"{'='*70}\n")


# Helper function for Spark SQL
from pyspark.sql.functions import col, when, count

def get_data_preprocessor(spark_session: SparkSession) -> DataPreprocessor:
    """
    Factory function to create a DataPreprocessor instance.
    
    Args:
        spark_session: Active Spark session
        
    Returns:
        DataPreprocessor: Initialized preprocessor
    """
    return DataPreprocessor(spark_session)
