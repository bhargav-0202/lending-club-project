"""
Lending Club Loan Scoring Project

A production-grade machine learning pipeline for automated loan scoring
and risk assessment using the Lending Club dataset.

Modules:
    - utils: Utility functions and constants
    - data_preprocessing: Data loading and cleaning
    - feature_engineering: Loan scoring calculations
    - model_training: Pipeline orchestration
    - evaluation: Model evaluation and metrics

Author: Data Science Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Data Science Team"

from .utils import (
    SCORE_POINTS,
    GRADE_POINTS,
    SCORE_WEIGHTS,
    get_project_paths,
    ensure_directories_exist,
)

__all__ = [
    "SCORE_POINTS",
    "GRADE_POINTS",
    "SCORE_WEIGHTS",
    "get_project_paths",
    "ensure_directories_exist",
]
