# Development Guide

This guide provides instructions for developing and extending the Lending Club Loan Scoring Project.

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Lending-Club-Project
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Development Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy jupyter
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
# Create .pre-commit-config.yaml for automated checks
```

## Project Structure Overview

```
src/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── utils.py                 # Utility functions
├── data_preprocessing.py     # Data loading and cleaning
├── feature_engineering.py    # Scoring calculations
├── model_training.py         # Pipeline orchestration
└── evaluation.py             # Model evaluation
```

## Coding Standards

### Python Style Guide

Follow **PEP 8** with these additional guidelines:

```python
# ✅ DO: Clear, descriptive names
def calculate_payment_history_score(repayments_df, loans_df):
    """Calculate payment history score based on repayment patterns."""
    pass

# ❌ DON'T: Unclear abbreviations
def calc_ph_score(rdf, ldf):
    pass

# ✅ DO: Comprehensive docstrings
def preprocess_data(raw_data):
    """
    Preprocess raw data for modeling.
    
    Args:
        raw_data: Input DataFrame with raw records
        
    Returns:
        DataFrame: Cleaned data ready for modeling
        
    Raises:
        ValueError: If data validation fails
    """
    pass

# ✅ DO: Type hints
def load_data(filepath: str, format_type: str = 'csv') -> DataFrame:
    pass

# ❌ DON'T: Missing types
def load_data(filepath, format_type='csv'):
    pass
```

### Import Organization

```python
# Standard library
import logging
from pathlib import Path
from typing import Dict, Optional

# Third-party libraries
import pandas as pd
from pyspark.sql import SparkSession

# Local imports
from .utils import get_project_paths
from .config import DATA_CONFIG
```

## Adding New Features

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Feature with Tests

```bash
# Create test file
touch tests/test_new_feature.py

# Write tests first (TDD approach)
# Then implement feature
# Run tests
pytest tests/test_new_feature.py -v
```

### 3. Code Quality Checks

```bash
# Format code
black src/

# Lint code  
flake8 src/ --max-line-length=100

# Type checking
mypy src/ --no-implicit-optional

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### 4. Submit Pull Request

Document your changes:
- What problem does this solve?
- How does it work?
- What tests were added?
- Any breaking changes?

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_data_preprocessing.py

# Run with coverage report
pytest --cov=src --cov-report=html

# Run in verbose mode
pytest -v

# Run specific test
pytest tests/test_data_preprocessing.py::TestDataPreprocessor::test_load_data
```

### Writing Tests

```python
import pytest
from src.data_preprocessing import DataPreprocessor

class TestDataPreprocessor:
    """Tests for DataPreprocessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.spark = SparkSession.builder.appName("test").getOrCreate()
        self.preprocessor = DataPreprocessor(self.spark)
    
    def test_load_data_csv(self):
        """Test loading CSV data."""
        df = self.preprocessor.load_data('path/to/data.csv')
        assert df.count() > 0
        assert 'member_id' in df.columns
    
    def test_bad_data_identification(self):
        """Test bad data identification."""
        bad_records, good_records = self.preprocessor.identify_bad_data(
            test_df, 'member_id'
        )
        assert bad_records.count() > 0
```

## Documentation

### Function Documentation

Every function must have:

```python
def calculate_score(df: DataFrame, weights: Dict[str, float]) -> DataFrame:
    """
    Calculate composite loan score.
    
    This function combines multiple scoring criteria using the provided
    weights to produce a final loan score.
    
    Args:
        df: DataFrame with scoring components
        weights: Dictionary mapping criteria to weights (must sum to 1.0)
        
    Returns:
        DataFrame: Input DataFrame with 'loan_score' column added
        
    Raises:
        ValueError: If weights don't sum to 1.0
        
    Example:
        >>> weights = {'ph': 0.2, 'dh': 0.45, 'fh': 0.35}
        >>> result = calculate_score(df, weights)
        >>> result.select('loan_score').show()
    """
```

### Class Documentation

```python
class LoanScorer:
    """
    Calculates loan scores based on financial criteria.
    
    This class encapsulates all logic for calculating composite loan scores
    from multiple financial criteria with configurable weights.
    
    Attributes:
        weights (Dict[str, float]): Scoring criteria weights
        grades (Dict[str, int]): Grade threshold boundaries
        
    Example:
        >>> scorer = LoanScorer(spark)
        >>> scores = scorer.calculate_scores(data)
    """
```

## Performance Optimization

### Spark Performance Tips

```python
# ✅ DO: Use partitioning
df.repartition(10).write.parquet(output_path)

# ❌ DON'T: Process unpartitioned data
df.write.parquet(output_path)

# ✅ DO: Select necessary columns early
df.select(['member_id', 'score']).write.parquet(...)

# ❌ DON'T: Select all columns
df.write.parquet(...)

# ✅ DO: Use caching for reused DataFrames
df = df.cache()
result1 = df.filter(...)
result2 = df.groupBy(...)

# ❌ DON'T: Recompute same DataFrame
result1 = df.filter(...)
result2 = df.groupBy(...)  # Recomputes df
```

## Debugging

### Enable Detailed Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In your code:
logger = logging.getLogger(__name__)
logger.debug(f"Processing {df.count()} records")
```

### Spark UI

```python
spark = SparkSession.builder \
    .config('spark.ui.port', '4040') \
    .getOrCreate()

# Access Spark UI at http://localhost:4040
```

### Inspect DataFrames

```python
# Display schema
df.printSchema()

# Show first rows
df.show(5)

# Get statistics
df.describe().show()

# Check for nulls
df.select([count(when(col(c).isNull(), c)).alias(c) for c in df.columns]).show()
```

## Release Process

### Version Management

Update version in:
- `src/__init__.py`
- `setup.py` (if exists)
- `README.md`

### Creating a Release

```bash
# Tag the release
git tag -a v1.1.0 -m "Release version 1.1.0"

# Push tag
git push origin v1.1.0
```

## Common Issues and Solutions

### Issue: PySpark NotImplementedError
**Solution**: Update PySpark version
```bash
pip install --upgrade pyspark
```

### Issue: Spark Session Already Running
**Solution**: Stop the session first
```python
spark.stop()
spark = SparkSession.builder.getOrCreate()
```

### Issue: Out of Memory
**Solution**: Increase memory allocation
```bash
export SPARK_DRIVER_MEMORY=8g
export SPARK_EXECUTOR_MEMORY=8g
```

## Resources

- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Apache Spark SQL Documentation](https://spark.apache.org/sql/)

## Contact

For questions or suggestions, please open an issue in the repository.
