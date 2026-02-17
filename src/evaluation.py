"""
Model Evaluation Module for Lending Club Project.

This module handles evaluation metrics, model assessment, and
performance analysis.
"""

import logging
from typing import Dict, List, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, when, avg, max, min

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Handles model evaluation and performance metrics."""
    
    def __init__(self, spark_session: SparkSession):
        """
        Initialize the ModelEvaluator.
        
        Args:
            spark_session: Active Spark session
        """
        self.spark = spark_session
        logger.info("ModelEvaluator initialized")
    
    def grade_distribution(self, loan_grade_df: DataFrame) -> Dict[str, int]:
        """
        Calculate distribution of loan grades.
        
        Args:
            loan_grade_df: DataFrame with assigned loan grades
            
        Returns:
            Dict: Grade distribution counts
        """
        logger.info("Calculating grade distribution...")
        
        distribution = loan_grade_df.groupBy('loan_final_grade').count().collect()
        
        grade_dist = {}
        for row in distribution:
            grade_dist[row.loan_final_grade] = row['count']
        
        logger.info(f"Grade distribution: {grade_dist}")
        
        return grade_dist
    
    def score_statistics(self, loan_grade_df: DataFrame) -> Dict[str, float]:
        """
        Calculate statistics for loan scores.
        
        Args:
            loan_grade_df: DataFrame with loan scores
            
        Returns:
            Dict: Score statistics (mean, min, max, etc.)
        """
        logger.info("Calculating score statistics...")
        
        stats = loan_grade_df.select(
            avg(col('loan_score')).alias('mean_score'),
            min(col('loan_score')).alias('min_score'),
            max(col('loan_score')).alias('max_score')
        ).collect()[0].asDict()
        
        logger.info(f"Score statistics: mean={stats['mean_score']:.2f}, "
                   f"min={stats['min_score']:.2f}, max={stats['max_score']:.2f}")
        
        return stats
    
    def grade_by_criteria(self, loan_grade_df: DataFrame) -> Dict[str, Dict]:
        """
        Analyze how different scoring criteria relate to final grade.
        
        Args:
            loan_grade_df: DataFrame with all scoring components
            
        Returns:
            Dict: Analysis of criteria by grade
        """
        logger.info("Analyzing grade by scoring criteria...")
        
        loan_grade_df.createOrReplaceTempView("grades")
        
        criteria_analysis = self.spark.sql("""
            SELECT 
                loan_final_grade,
                COUNT(*) as total_count,
                AVG(payment_history_pts) as avg_ph_pts,
                AVG(defaulters_history_pts) as avg_dh_pts,
                AVG(financial_health_pts) as avg_fh_pts,
                AVG(loan_score) as avg_total_score
            FROM grades
            GROUP BY loan_final_grade
            ORDER BY loan_final_grade
        """)
        
        analysis = {}
        for row in criteria_analysis.collect():
            analysis[row.loan_final_grade] = {
                'count': row.total_count,
                'avg_payment_history': round(row.avg_ph_pts, 2),
                'avg_defaulter_history': round(row.avg_dh_pts, 2),
                'avg_financial_health': round(row.avg_fh_pts, 2),
                'avg_total_score': round(row.avg_total_score, 2)
            }
        
        logger.info("Grade analysis by criteria completed")
        
        return analysis
    
    def high_risk_loans(self, loan_grade_df: DataFrame, threshold: str = 'D') -> DataFrame:
        """
        Identify high-risk loans (grades D, E, F).
        
        Args:
            loan_grade_df: DataFrame with assigned grades
            threshold: Grade threshold for high-risk (default: 'D')
            
        Returns:
            DataFrame: High-risk loans
        """
        logger.info(f"Identifying loans with grade >= {threshold} as high-risk...")
        
        high_risk = loan_grade_df.filter(
            col('loan_final_grade').isin(['D', 'E', 'F'])
        )
        
        count = high_risk.count()
        logger.info(f"Found {count} high-risk loans")
        
        return high_risk
    
    def low_risk_loans(self, loan_grade_df: DataFrame, threshold: str = 'B') -> DataFrame:
        """
        Identify low-risk loans (grades A, B).
        
        Args:
            loan_grade_df: DataFrame with assigned grades
            threshold: Grade threshold for low-risk (default: 'B')
            
        Returns:
            DataFrame: Low-risk loans
        """
        logger.info(f"Identifying loans with grade <= {threshold} as low-risk...")
        
        low_risk = loan_grade_df.filter(
            col('loan_final_grade').isin(['A', 'B'])
        )
        
        count = low_risk.count()
        logger.info(f"Found {count} low-risk loans")
        
        return low_risk
    
    def member_quality_summary(self, loan_grade_df: DataFrame) -> DataFrame:
        """
        Generate summary of loan quality per member (if multiple loans).
        
        Args:
            loan_grade_df: DataFrame with loan grades
            
        Returns:
            DataFrame: Member quality summary
        """
        logger.info("Generating member quality summary...")
        
        loan_grade_df.createOrReplaceTempView("loans_with_grade")
        
        member_summary = self.spark.sql("""
            SELECT 
                member_id,
                COUNT(DISTINCT loan_score) as total_loan_scores,
                AVG(loan_score) as avg_member_score,
                MIN(loan_score) as min_member_score,
                MAX(loan_score) as max_member_score,
                COLLECT_SET(loan_final_grade) as grades
            FROM loans_with_grade
            GROUP BY member_id
            ORDER BY avg_member_score DESC
        """)
        
        logger.info("Member quality summary generated")
        
        return member_summary
    
    def print_evaluation_report(self, loan_grade_df: DataFrame) -> None:
        """
        Print a comprehensive evaluation report.
        
        Args:
            loan_grade_df: DataFrame with loan grades and scores
        """
        print("\n" + "="*70)
        print("  LOAN SCORING MODEL - EVALUATION REPORT")
        print("="*70 + "\n")
        
        # Total records
        total = loan_grade_df.count()
        print(f"Total Records Evaluated: {total}\n")
        
        # Grade distribution
        print("Grade Distribution:")
        print("-" * 70)
        dist = self.grade_distribution(loan_grade_df)
        for grade in sorted(dist.keys()):
            count = dist[grade]
            pct = (count / total) * 100
            print(f"  Grade {grade}: {count:>6} loans ({pct:>5.2f}%)")
        print()
        
        # Score statistics
        print("Score Statistics:")
        print("-" * 70)
        stats = self.score_statistics(loan_grade_df)
        print(f"  Average Score:  {stats['mean_score']:>10.2f}")
        print(f"  Minimum Score:  {stats['min_score']:>10.2f}")
        print(f"  Maximum Score:  {stats['max_score']:>10.2f}")
        print()
        
        # Risk analysis
        print("Risk Analysis:")
        print("-" * 70)
        high_risk = self.high_risk_loans(loan_grade_df).count()
        low_risk = self.low_risk_loans(loan_grade_df).count()
        medium_risk = total - high_risk - low_risk
        
        print(f"  Low-Risk (A, B):     {low_risk:>6} loans ({(low_risk/total)*100:>5.2f}%)")
        print(f"  Medium-Risk (C):     {medium_risk:>6} loans ({(medium_risk/total)*100:>5.2f}%)")
        print(f"  High-Risk (D, E, F): {high_risk:>6} loans ({(high_risk/total)*100:>5.2f}%)")
        print()
        
        # Criteria analysis
        print("Average Scores by Grade:")
        print("-" * 70)
        analysis = self.grade_by_criteria(loan_grade_df)
        
        for grade in sorted(analysis.keys()):
            data = analysis[grade]
            print(f"\n  Grade {grade} (n={data['count']}):")
            print(f"    Payment History:    {data['avg_payment_history']:>8.2f}")
            print(f"    Defaulter History:  {data['avg_defaulter_history']:>8.2f}")
            print(f"    Financial Health:   {data['avg_financial_health']:>8.2f}")
            print(f"    Total Score:        {data['avg_total_score']:>8.2f}")
        
        print("\n" + "="*70 + "\n")
    
    def export_evaluation_metrics(self, loan_grade_df: DataFrame, 
                                 output_path: str) -> None:
        """
        Export evaluation metrics to a report file.
        
        Args:
            loan_grade_df: DataFrame with loan grades
            output_path: Path to save the report
        """
        logger.info(f"Exporting evaluation metrics to {output_path}")
        
        try:
            dist = self.grade_distribution(loan_grade_df)
            stats = self.score_statistics(loan_grade_df)
            
            report = f"""
LENDING CLUB PROJECT - LOAN SCORING EVALUATION REPORT
{'='*70}

SUMMARY STATISTICS
{'-'*70}
Total Loans Evaluated: {loan_grade_df.count()}
Average Score: {stats['mean_score']:.2f}
Minimum Score: {stats['min_score']:.2f}
Maximum Score: {stats['max_score']:.2f}

GRADE DISTRIBUTION
{'-'*70}
"""
            
            total = loan_grade_df.count()
            for grade in sorted(dist.keys()):
                count = dist[grade]
                pct = (count / total) * 100
                report += f"Grade {grade}: {count} loans ({pct:.2f}%)\n"
            
            report += f"\n{'='*70}\nReport Generated Successfully\n"
            
            with open(output_path, 'w') as f:
                f.write(report)
            
            logger.info(f"Evaluation report saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error exporting evaluation metrics: {str(e)}")
            raise


def get_model_evaluator(spark_session: SparkSession) -> ModelEvaluator:
    """
    Factory function to create a ModelEvaluator instance.
    
    Args:
        spark_session: Active Spark session
        
    Returns:
        ModelEvaluator: Initialized evaluator
    """
    return ModelEvaluator(spark_session)
