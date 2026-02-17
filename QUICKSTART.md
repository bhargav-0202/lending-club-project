# Quick Start Guide

Get the Lending Club Loan Scoring project up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Java 8+ (for Spark)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Data

Place your data files in `data/raw/`:
- `customers.csv`
- `loans.csv`
- `loans_repayments.csv`
- `loans_defaulters_delinq.csv`
- `loans_defaulters_detail.csv`

**Don't have data?** Check the `notebooks/` directory for example analysis.

## Run the Pipeline

### Option 1: Basic Usage (CSV Files)

```bash
python main.py
```

### Option 2: Hive Database

```bash
python main.py --hive
```

### Option 3: Custom Output Path

```bash
python main.py --output-path data/processed/my_scores
```

## What Happens

The pipeline will:

1. ✅ **Load** your data (CSV or Hive)
2. ✅ **Clean** data by removing duplicates and bad records
3. ✅ **Score** loans based on 3 criteria:
   - Payment History (20%)
   - Default History (45%)
   - Financial Health (35%)
4. ✅ **Grade** loans A through F
5. ✅ **Report** on grade distribution and risk analysis
6. ✅ **Save** results to `data/processed/loan_scores/`

## View Results

```python
import pandas as pd

# Load the results
scores = pd.read_parquet('data/processed/loan_scores/')

# See the first few
print(scores.head())

# Check grade distribution
print(scores['loan_final_grade'].value_counts())

# Analyze by grade
print(scores.groupby('loan_final_grade')['loan_score'].describe())
```

## Next Steps

- 📖 Read [README.md](README.md) for comprehensive documentation
- 🔧 Check [DEVELOPMENT.md](DEVELOPMENT.md) for development guide
- 📓 Explore [notebooks/](notebooks/) for detailed analysis
- 🧪 Review [src/](src/) modules for implementation details

## Troubleshooting

### No data files found

**Error**: "No data files found in data/raw directory"

**Solution**: Ensure CSV files are in `data/raw/` with correct names

### PySpark not installed

**Error**: "PySpark is not installed"

**Solution**: Run `pip install pyspark>=3.0.0`

### Out of memory

**Error**: Java heap space error

**Solution**: Increase memory
```bash
export SPARK_DRIVER_MEMORY=8g
export SPARK_EXECUTOR_MEMORY=8g
python main.py
```

### Data appears invalid

**Error**: Wrong column names or missing data

**Solution**: 
1. Check your CSV column names match the code expectations
2. Verify data types are correct
3. Check for missing values

## Project Structure

```
Lending-Club-Project/
├── main.py                    # Entry point ⭐ RUN THIS
├── README.md                  # Full documentation
├── requirements.txt           # Dependencies
├── data/
│   ├── raw/                   # 📥 Put your data here
│   └── processed/             # 📤 Results saved here
├── src/                       # Core logic
└── outputs/                   # Models and plots
```

## Learning Resources

- **Lending Club Dataset**: Public dataset with 900K+ loans
- **Spark**: Distributed processing for big data
- **Python ML**: scikit-learn for advanced models

## Support

Having issues? Check:

1. [README.md](README.md) - Comprehensive guide
2. [DEVELOPMENT.md](DEVELOPMENT.md) - Developer guide
3. Notebook examples in [notebooks/](notebooks/)
4. Source code docstrings in [src/](src/)

## Success! 🎉

If you see this output, you're ready:

```
======================================================================
  PIPELINE EXECUTION COMPLETED
======================================================================

✓ Loan scoring completed successfully!
✓ Results saved to: data/processed/loan_scores
✓ Total loans scored: 10,000
```

Your loan scores are ready for analysis!
