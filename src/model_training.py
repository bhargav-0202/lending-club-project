"""
Model Training Module for Lending Club Project.

This module orchestrates the complete machine learning pipeline,
including data loading, preprocessing, feature engineering,
and model evaluation.
"""

import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
from pyspark.sql import SparkSession, DataFrame

from .data_preprocessing import DataPreprocessor
from .feature_engineering import FeatureEngineer
from .evaluation import ModelEvaluator
from .utils import print_section_header

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Orchestrates the complete ML pipeline for loan scoring."""
    
    def __init__(self, spark_session: SparkSession):
        """
        Initialize the ModelTrainer with all required components.
        
        Args:
            spark_session: Active Spark session
        """
        self.spark = spark_session
        self.preprocessor = DataPreprocessor(spark_session)
        self.feature_engineer = FeatureEngineer(spark_session)
        self.evaluator = ModelEvaluator(spark_session)
        logger.info("ModelTrainer initialized")
    
    def load_data(self, data_paths: Dict[str, str]) -> Dict[str, DataFrame]:
        """
        Load all required datasets.
        
        Args:
            data_paths: Dictionary mapping data type to file path
                       (e.g., {'customers': 'path/to/customers.csv'})
            
        Returns:
            Dict: Dictionary of loaded DataFrames
        """
        print_section_header("LOADING DATA")
        
        loaded_data = {}
        
        try:
            for data_type, path in data_paths.items():
                logger.info(f"Loading {data_type} from {path}")
                df = self.preprocessor.load_data(
                    path, 
                    format_type='parquet' if path.endswith('parquet') else 'csv'
                )
                loaded_data[data_type] = df
                self.preprocessor.show_data_summary(df, f"{data_type.title()} Data")
        
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
        
        return loaded_data
    
    def load_from_hive(self, table_names: Dict[str, str]) -> Dict[str, DataFrame]:
        """
        Load data directly from Hive database tables.
        
        Args:
            table_names: Dictionary mapping logical name to Hive table name
                        (e.g., {'customers': 'itv022692_lending_club.customers'})
            
        Returns:
            Dict: Dictionary of loaded DataFrames
        """
        print_section_header("LOADING DATA FROM HIVE")
        
        loaded_data = {}
        
        try:
            for data_type, table_name in table_names.items():
                logger.info(f"Loading {data_type} from Hive table {table_name}")
                df = self.preprocessor.load_from_hive_database(table_name)
                loaded_data[data_type] = df
                self.preprocessor.show_data_summary(df, f"{data_type.title()} Data")
        
        except Exception as e:
            logger.error(f"Error loading from Hive: {str(e)}")
            raise
        
        return loaded_data
    
    def preprocess_data(self, loaded_data: Dict[str, DataFrame]) -> Tuple[Dict[str, DataFrame], DataFrame]:
        """
        Preprocess all loaded data.
        
        Args:
            loaded_data: Dictionary of raw DataFrames
            
        Returns:
            Tuple: (cleaned_data dict, bad_records DataFrame)
        """
        print_section_header("PREPROCESSING DATA")
        
        cleaned_data = {}
        bad_records = None
        
        try:
            # Identify bad data from customers table
            if 'customers' in loaded_data:
                logger.info("Identifying bad customer records...")
                bad_records, cleaned_customers = self.preprocessor.identify_bad_data(
                    loaded_data['customers'], 
                    'member_id'
                )
                cleaned_data['customers'] = cleaned_customers
            
            # Remove bad records from remaining datasets
            for data_type, df in loaded_data.items():
                if data_type == 'customers':
                    continue
                
                logger.info(f"Cleaning {data_type} by removing bad records...")
                cleaned_df = self.preprocessor.remove_bad_records(
                    df, 
                    bad_records, 
                    'member_id'
                )
                cleaned_data[data_type] = cleaned_df
                self.preprocessor.show_data_summary(cleaned_df, f"Cleaned {data_type.title()}")
        
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            raise
        
        return cleaned_data, bad_records
    
    def engineer_features(self, cleaned_data: Dict[str, DataFrame], 
                         bad_records: DataFrame) -> DataFrame:
        """
        Perform feature engineering and calculate loan scores.
        
        Args:
            cleaned_data: Dictionary of cleaned DataFrames
            bad_records: DataFrame with bad records
            
        Returns:
            DataFrame: Final loan scores with grades
        """
        print_section_header("FEATURE ENGINEERING & LOAN SCORING")
        
        try:
            # Calculate payment history score
            ph_df = self.feature_engineer.calculate_payment_history_score(
                cleaned_data.get('repayments'),
                cleaned_data.get('loans'),
                bad_records
            )
            
            # Calculate defaulter history score
            ldh_df = self.feature_engineer.calculate_defaulter_history_score(
                cleaned_data.get('defaulters_delinq'),
                cleaned_data.get('defaulters_detail'),
                ph_df,
                bad_records
            )
            
            # Calculate financial health score
            fh_df = self.feature_engineer.calculate_financial_health_score(
                cleaned_data.get('loans'),
                cleaned_data.get('customers'),
                ldh_df,
                bad_records
            )
            
            # Calculate composite score
            loan_score_df = self.feature_engineer.calculate_composite_loan_score(fh_df)
            
            # Assign grades
            final_grades = self.feature_engineer.assign_loan_grade(loan_score_df)
            
            print(f"Generated loan scores for {final_grades.count()} loans")
            
            return final_grades
        
        except Exception as e:
            logger.error(f"Error in feature engineering: {str(e)}")
            raise
    
    def evaluate_model(self, final_grades: DataFrame) -> Dict:
        """
        Evaluate the loan scoring model.
        
        Args:
            final_grades: DataFrame with final scores and grades
            
        Returns:
            Dict: Evaluation metrics
        """
        print_section_header("MODEL EVALUATION")
        
        try:
            self.evaluator.print_evaluation_report(final_grades)
            
            metrics = {
                'grade_distribution': self.evaluator.grade_distribution(final_grades),
                'score_statistics': self.evaluator.score_statistics(final_grades),
                'grade_criteria_analysis': self.evaluator.grade_by_criteria(final_grades),
            }
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise
    
    def save_results(self, final_grades: DataFrame, output_path: str, 
                    format_type: str = 'parquet') -> None:
        """
        Save final model results.
        
        Args:
            final_grades: DataFrame with final scores and grades
            output_path: Path to save results
            format_type: Format to save in ('parquet' or 'csv')
        """
        print_section_header("SAVING RESULTS")
        
        try:
            output_dir = Path(output_path)
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving final grades to {output_path} ({format_type} format)")
            
            if format_type.lower() == 'parquet':
                final_grades.write \
                    .format("parquet") \
                    .mode("overwrite") \
                    .option("path", str(output_path)) \
                    .save()
            
            elif format_type.lower() == 'csv':
                final_grades.write \
                    .format("csv") \
                    .option("header", "true") \
                    .mode("overwrite") \
                    .option("path", str(output_path)) \
                    .save()
            
            logger.info(f"Successfully saved results to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise
    
    def run_pipeline(self, 
                    hive_tables: Optional[Dict[str, str]] = None,
                    data_paths: Optional[Dict[str, str]] = None,
                    output_path: Optional[str] = None) -> Tuple[DataFrame, Dict]:
        """
        Execute the complete ML pipeline.
        
        Args:
            hive_tables: Hive table names (alternative to data_paths)
            data_paths: File paths to data (alternative to hive_tables)
            output_path: Path to save results
            
        Returns:
            Tuple: (final_grades DataFrame, evaluation metrics dict)
        """
        print_section_header("LENDING CLUB LOAN SCORING - COMPLETE PIPELINE")
        
        try:
            # Load data
            if hive_tables:
                loaded_data = self.load_from_hive(hive_tables)
            elif data_paths:
                loaded_data = self.load_data(data_paths)
            else:
                raise ValueError("Either hive_tables or data_paths must be provided")
            
            # Preprocess
            cleaned_data, bad_records = self.preprocess_data(loaded_data)
            
            # Feature engineering
            final_grades = self.engineer_features(cleaned_data, bad_records)
            
            # Evaluate
            metrics = self.evaluate_model(final_grades)
            
            # Save results
            if output_path:
                self.save_results(final_grades, output_path, format_type='parquet')
            
            logger.info("Pipeline execution completed successfully")
            
            return final_grades, metrics
        
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise


def get_model_trainer(spark_session: SparkSession) -> ModelTrainer:
    """
    Factory function to create a ModelTrainer instance.
    
    Args:
        spark_session: Active Spark session
        
    Returns:
        ModelTrainer: Initialized trainer
    """
    return ModelTrainer(spark_session)
