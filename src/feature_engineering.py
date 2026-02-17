"""
Feature Engineering Module for Lending Club Project.

This module handles creation of new features and transformations
for the machine learning pipeline, including loan score calculation.
"""

import logging
from typing import Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when, coalesce

from .utils import SCORE_POINTS, GRADE_POINTS, SCORE_WEIGHTS

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Handles all feature engineering operations."""
    
    def __init__(self, spark_session: SparkSession):
        """
        Initialize the FeatureEngineer.
        
        Args:
            spark_session: Active Spark session
        """
        self.spark = spark_session
        self.score_points = SCORE_POINTS
        self.grade_points = GRADE_POINTS
        self.weights = SCORE_WEIGHTS
        logger.info("FeatureEngineer initialized")
    
    def calculate_payment_history_score(self, 
                                       repayments_df: DataFrame,
                                       loans_df: DataFrame,
                                       bad_records: DataFrame) -> DataFrame:
        """
        Calculate payment history score (Criterion 1).
        
        Evaluates based on:
        - Last payment amount vs monthly installment
        - Total payment received vs funded amount
        
        Args:
            repayments_df: Loan repayments data
            loans_df: Loans data
            bad_records: Bad records to exclude
            
        Returns:
            DataFrame: Payment history scores
        """
        logger.info("Calculating payment history score...")
        
        bad_records.createOrReplaceTempView("bad_customers")
        repayments_df.createOrReplaceTempView("repayments")
        loans_df.createOrReplaceTempView("loans")
        
        ph_df = self.spark.sql(f"""
            SELECT 
                c.member_id,
                CASE 
                    WHEN p.last_payment_amount < (c.monthly_installment * 0.5) 
                        THEN {self.score_points['very_bad']}
                    WHEN p.last_payment_amount >= (c.monthly_installment * 0.5) 
                        AND p.last_payment_amount < c.monthly_installment 
                        THEN {self.score_points['very_bad']}
                    WHEN p.last_payment_amount = c.monthly_installment 
                        THEN {self.score_points['good']}
                    WHEN p.last_payment_amount > c.monthly_installment 
                        AND p.last_payment_amount <= (c.monthly_installment * 1.50) 
                        THEN {self.score_points['very_good']}
                    WHEN p.last_payment_amount > (c.monthly_installment * 1.50) 
                        THEN {self.score_points['excellent']}
                    ELSE {self.score_points['unacceptable']}
                END AS last_payment_pts,
                CASE 
                    WHEN p.total_payment_received >= (c.funded_amount * 0.50) 
                        THEN {self.score_points['very_good']}
                    WHEN p.total_payment_received < (c.funded_amount * 0.50) 
                        AND p.total_payment_received > 0 
                        THEN {self.score_points['good']}
                    WHEN p.total_payment_received = 0 
                        OR p.total_payment_received IS NULL 
                        THEN {self.score_points['unacceptable']}
                END AS total_payment_pts
            FROM repayments p
            INNER JOIN loans c ON c.loan_id = p.loan_id
            WHERE c.member_id NOT IN (SELECT member_id FROM bad_customers)
        """)
        
        ph_df.createOrReplaceTempView("ph_pts")
        logger.info("Payment history score calculated successfully")
        
        return ph_df
    
    def calculate_defaulter_history_score(self,
                                         defaulters_delinq_df: DataFrame,
                                         defaulters_detail_df: DataFrame,
                                         ph_df: DataFrame,
                                         bad_records: DataFrame) -> DataFrame:
        """
        Calculate loan defaulter history score (Criterion 2).
        
        Evaluates based on:
        - Delinquency history (2 years)
        - Public records
        - Bankruptcies
        - Inquiries in last 6 months
        
        Args:
            defaulters_delinq_df: Delinquency data
            defaulters_detail_df: Detailed defaulter records
            ph_df: Payment history DataFrame
            bad_records: Bad records to exclude
            
        Returns:
            DataFrame: Defaulter history scores combined with payment history
        """
        logger.info("Calculating defaulter history score...")
        
        bad_records.createOrReplaceTempView("bad_customers")
        defaulters_delinq_df.createOrReplaceTempView("delinq_data")
        defaulters_detail_df.createOrReplaceTempView("defaulter_detail")
        ph_df.createOrReplaceTempView("ph_pts")
        
        ldh_df = self.spark.sql(f"""
            SELECT 
                p.*,
                CASE 
                    WHEN d.delinq_2yrs = 0 THEN {self.score_points['excellent']}
                    WHEN d.delinq_2yrs BETWEEN 1 AND 2 THEN {self.score_points['bad']}
                    WHEN d.delinq_2yrs BETWEEN 3 AND 5 THEN {self.score_points['very_bad']}
                    WHEN d.delinq_2yrs > 5 OR d.delinq_2yrs IS NULL 
                        THEN {self.grade_points['unacceptable']}
                END AS delinq_pts,
                CASE 
                    WHEN l.pub_rec = 0 THEN {self.score_points['excellent']}
                    WHEN l.pub_rec BETWEEN 1 AND 2 THEN {self.score_points['bad']}
                    WHEN l.pub_rec BETWEEN 3 AND 5 THEN {self.score_points['very_bad']}
                    WHEN l.pub_rec > 5 OR l.pub_rec IS NULL 
                        THEN {self.score_points['very_bad']}
                END AS public_records_pts,
                CASE 
                    WHEN l.pub_rec_bankruptcies = 0 THEN {self.score_points['excellent']}
                    WHEN l.pub_rec_bankruptcies BETWEEN 1 AND 2 THEN {self.score_points['bad']}
                    WHEN l.pub_rec_bankruptcies BETWEEN 3 AND 5 THEN {self.score_points['very_bad']}
                    WHEN l.pub_rec_bankruptcies > 5 OR l.pub_rec_bankruptcies IS NULL 
                        THEN {self.score_points['very_bad']}
                END AS public_bankruptcies_pts,
                CASE 
                    WHEN l.inq_last_6mths = 0 THEN {self.score_points['excellent']}
                    WHEN l.inq_last_6mths BETWEEN 1 AND 2 THEN {self.score_points['bad']}
                    WHEN l.inq_last_6mths BETWEEN 3 AND 5 THEN {self.score_points['very_bad']}
                    WHEN l.inq_last_6mths > 5 OR l.inq_last_6mths IS NULL 
                        THEN {self.score_points['unacceptable']}
                END AS enq_pts
            FROM defaulter_detail l
            INNER JOIN delinq_data d ON d.member_id = l.member_id
            INNER JOIN ph_pts p ON p.member_id = l.member_id
            WHERE l.member_id NOT IN (SELECT member_id FROM bad_customers)
        """)
        
        ldh_df.createOrReplaceTempView("ldh_ph_pts")
        logger.info("Defaulter history score calculated successfully")
        
        return ldh_df
    
    def calculate_financial_health_score(self,
                                        loans_df: DataFrame,
                                        customers_df: DataFrame,
                                        ldh_df: DataFrame,
                                        bad_records: DataFrame) -> DataFrame:
        """
        Calculate financial health score (Criterion 3).
        
        Evaluates based on:
        - Loan status
        - Home ownership
        - Credit limit utilization
        - Grade and sub-grade
        
        Args:
            loans_df: Loans data
            customers_df: Customer data
            ldh_df: Defaulter history DataFrame
            bad_records: Bad records to exclude
            
        Returns:
            DataFrame: Financial health scores with all previous scores
        """
        logger.info("Calculating financial health score...")
        
        bad_records.createOrReplaceTempView("bad_customers")
        loans_df.createOrReplaceTempView("loans")
        customers_df.createOrReplaceTempView("customers")
        ldh_df.createOrReplaceTempView("ldh_ph_pts")
        
        fh_df = self.spark.sql(f"""
            SELECT 
                ldef.*,
                CASE 
                    WHEN LOWER(l.loan_status) LIKE '%fully paid%' 
                        THEN {self.score_points['excellent']}
                    WHEN LOWER(l.loan_status) LIKE '%current%' 
                        THEN {self.score_points['good']}
                    WHEN LOWER(l.loan_status) LIKE '%in grace period%' 
                        THEN {self.score_points['bad']}
                    WHEN LOWER(l.loan_status) LIKE '%late (16-30 days)%' 
                        OR LOWER(l.loan_status) LIKE '%late (31-120 days)%' 
                        THEN {self.score_points['very_bad']}
                    WHEN LOWER(l.loan_status) LIKE '%charged off%' 
                        THEN {self.score_points['unacceptable']}
                    ELSE {self.score_points['unacceptable']}
                END AS loan_status_pts,
                CASE 
                    WHEN LOWER(a.home_ownership) LIKE '%own%' 
                        THEN {self.score_points['excellent']}
                    WHEN LOWER(a.home_ownership) LIKE '%rent%' 
                        THEN {self.score_points['good']}
                    WHEN LOWER(a.home_ownership) LIKE '%mortgage%' 
                        THEN {self.score_points['bad']}
                    WHEN LOWER(a.home_ownership) LIKE '%any%' 
                        OR a.home_ownership IS NULL 
                        THEN {self.score_points['very_bad']}
                END AS home_pts,
                CASE 
                    WHEN l.funded_amount <= (a.total_high_credit_limit * 0.10) 
                        THEN {self.score_points['excellent']}
                    WHEN l.funded_amount > (a.total_high_credit_limit * 0.10) 
                        AND l.funded_amount <= (a.total_high_credit_limit * 0.20) 
                        THEN {self.score_points['very_good']}
                    WHEN l.funded_amount > (a.total_high_credit_limit * 0.20) 
                        AND l.funded_amount <= (a.total_high_credit_limit * 0.30) 
                        THEN {self.score_points['good']}
                    WHEN l.funded_amount > (a.total_high_credit_limit * 0.30) 
                        AND l.funded_amount <= (a.total_high_credit_limit * 0.50) 
                        THEN {self.score_points['bad']}
                    WHEN l.funded_amount > (a.total_high_credit_limit * 0.50) 
                        AND l.funded_amount <= (a.total_high_credit_limit * 0.70) 
                        THEN {self.score_points['very_bad']}
                    WHEN l.funded_amount > (a.total_high_credit_limit * 0.70) 
                        THEN {self.score_points['unacceptable']}
                    ELSE {self.score_points['unacceptable']}
                END AS credit_limit_pts,
                CASE 
                    WHEN a.grade = 'A' AND a.sub_grade = 'A1' 
                        THEN {self.score_points['excellent']}
                    WHEN a.grade = 'A' AND a.sub_grade = 'A2' 
                        THEN ({self.score_points['excellent']} * 0.95)
                    WHEN a.grade = 'A' AND a.sub_grade = 'A3' 
                        THEN ({self.score_points['excellent']} * 0.90)
                    WHEN a.grade = 'A' AND a.sub_grade = 'A4' 
                        THEN ({self.score_points['excellent']} * 0.85)
                    WHEN a.grade = 'A' AND a.sub_grade = 'A5' 
                        THEN ({self.score_points['excellent']} * 0.80)
                    WHEN a.grade = 'B' AND a.sub_grade = 'B1' 
                        THEN {self.score_points['very_good']}
                    WHEN a.grade = 'B' AND a.sub_grade IN ('B2', 'B3', 'B4', 'B5') 
                        THEN {self.score_points['very_good']} * 0.90
                    WHEN a.grade = 'C' AND a.sub_grade = 'C1' 
                        THEN {self.score_points['good']}
                    WHEN a.grade = 'C' AND a.sub_grade IN ('C2', 'C3', 'C4', 'C5') 
                        THEN {self.score_points['good']} * 0.90
                    WHEN a.grade = 'D' AND a.sub_grade = 'D1' 
                        THEN {self.score_points['bad']}
                    WHEN a.grade = 'D' AND a.sub_grade IN ('D2', 'D3', 'D4', 'D5') 
                        THEN {self.score_points['bad']} * 0.90
                    WHEN a.grade = 'E' AND a.sub_grade = 'E1' 
                        THEN {self.score_points['very_bad']}
                    WHEN a.grade = 'E' AND a.sub_grade IN ('E2', 'E3', 'E4', 'E5') 
                        THEN {self.score_points['very_bad']} * 0.90
                    WHEN a.grade IN ('F', 'G') 
                        THEN {self.score_points['unacceptable']}
                    ELSE 0
                END AS grade_pts
            FROM ldh_ph_pts ldef
            INNER JOIN loans l ON ldef.member_id = l.member_id
            INNER JOIN customers a ON a.member_id = ldef.member_id
            WHERE ldef.member_id NOT IN (SELECT member_id FROM bad_customers)
        """)
        
        fh_df.createOrReplaceTempView("fh_ldh_ph_pts")
        logger.info("Financial health score calculated successfully")
        
        return fh_df
    
    def calculate_composite_loan_score(self, fh_df: DataFrame) -> DataFrame:
        """
        Calculate final composite loan score from all three criteria.
        
        Weights:
        - Payment History: 20%
        - Defaulter History: 45%
        - Financial Health: 35%
        
        Args:
            fh_df: Financial health DataFrame with all criteria scores
            
        Returns:
            DataFrame: Final loan scores
        """
        logger.info("Calculating composite loan score...")
        
        fh_df.createOrReplaceTempView("fh_ldh_ph_pts")
        
        loan_score = self.spark.sql(f"""
            SELECT 
                member_id,
                ((last_payment_pts + total_payment_pts) * {self.weights['payment_history']}) 
                    AS payment_history_pts,
                ((delinq_pts + public_records_pts + public_bankruptcies_pts + enq_pts) * {self.weights['defaulters_history']}) 
                    AS defaulters_history_pts,
                ((loan_status_pts + home_pts + credit_limit_pts + grade_pts) * {self.weights['financial_health']}) 
                    AS financial_health_pts
            FROM fh_ldh_ph_pts
        """)
        
        # Calculate total score
        final_loan_score = loan_score.withColumn(
            'loan_score',
            col('payment_history_pts') + col('defaulters_history_pts') + col('financial_health_pts')
        )
        
        logger.info("Composite loan score calculated successfully")
        
        return final_loan_score
    
    def assign_loan_grade(self, loan_score_df: DataFrame) -> DataFrame:
        """
        Assign letter grades (A-F) based on loan scores.
        
        Grade boundaries:
        - A: > 2500 (Very Good)
        - B: > 2000 and <= 2500
        - C: > 1500 and <= 2000
        - D: > 1000 and <= 1500
        - E: > 750 and <= 1000
        - F: <= 750
        
        Args:
            loan_score_df: DataFrame with loan scores
            
        Returns:
            DataFrame: Scores with assigned grades
        """
        logger.info("Assigning loan grades...")
        
        loan_score_df.createOrReplaceTempView("loan_score_eval")
        
        loan_grade = self.spark.sql(f"""
            SELECT 
                ls.*,
                CASE 
                    WHEN loan_score > {self.grade_points['very_good']} THEN 'A'
                    WHEN loan_score <= {self.grade_points['very_good']} 
                        AND loan_score > {self.grade_points['good']} THEN 'B'
                    WHEN loan_score <= {self.grade_points['good']} 
                        AND loan_score > {self.grade_points['bad']} THEN 'C'
                    WHEN loan_score <= {self.grade_points['bad']} 
                        AND loan_score > {self.grade_points['very_bad']} THEN 'D'
                    WHEN loan_score <= {self.grade_points['very_bad']} 
                        AND loan_score > {self.grade_points['unacceptable']} THEN 'E'
                    WHEN loan_score <= {self.grade_points['unacceptable']} THEN 'F'
                END AS loan_final_grade
            FROM loan_score_eval ls
        """)
        
        logger.info("Loan grades assigned successfully")
        
        return loan_grade


def get_feature_engineer(spark_session: SparkSession) -> FeatureEngineer:
    """
    Factory function to create a FeatureEngineer instance.
    
    Args:
        spark_session: Active Spark session
        
    Returns:
        FeatureEngineer: Initialized feature engineer
    """
    return FeatureEngineer(spark_session)
