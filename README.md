# Lending Club Loan Scoring Model

A production-grade machine learning project for automated loan score calculation and risk assessment using the Lending Club dataset.

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Dataset Description](#dataset-description)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Running the Pipeline](#running-the-pipeline)
- [Pipeline Steps](#pipeline-steps)
- [Results & Metrics](#results--metrics)
- [Technologies Used](#technologies-used)
- [Project Components](#project-components)
- [Output Files](#output-files)
- [Contributing](#contributing)

## 🎯 Problem Statement

This project solves the critical problem of **automated loan risk assessment and scoring** in the lending industry. The objective is to:

1. **Calculate comprehensive loan scores** based on multiple financial criteria
2. **Identify and classify loan risk levels** (A-F grades) to guide lending decisions
3. **Aggregate multiple scoring criteria** with weighted importance:
   - Payment History (20%)
   - Loan Default History (45%)
   - Financial Health (35%)
4. **Enable data-driven lending decisions** that reduce default risk and optimize portfolio performance

### Business Impact

- **Risk Mitigation**: Identify high-risk loans (grades D, E, F) for additional scrutiny
- **Portfolio Optimization**: Understand distribution of loan quality across the portfolio
- **Data-Driven Decisions**: Automated, repeatable scoring based on objective criteria
- **Regulatory Compliance**: Maintain audit trail of how scores were calculated

## 📊 Dataset Description

The project uses the **Lending Club dataset** with the following key tables:

### Primary Tables

| Table | Description | Key Columns |
|-------|-------------|------------|
| **Customers** | Customer profile information | member_id, age, home_ownership, grade, sub_grade, total_high_credit_limit |
| **Loans** | Loan details and status | loan_id, member_id, funded_amount, monthly_installment, loan_status |
| **Loans Repayments** | Payment history | loan_id, member_id, total_payment_received, last_payment_amount |
| **Loans Defaulters Delinq** | Delinquency records | member_id, delinq_2yrs (delinquencies in last 2 years) |
| **Loans Defaulters Detail** | Detailed default metrics | member_id, pub_rec (public records), pub_rec_bankruptcies, inq_last_6mths (inquiries) |

### Data Availability

**⚠️ Important**: Large raw datasets are not included in this repository to keep the project size manageable.

- **Raw Data** (`data/raw/`): Excluded (use your own Lending Club data)
- **Sample Data** (`data/sample/`): ✅ Included (15 rows per table for testing)
- **Processed Data** (`data/processed/`): Generated during pipeline execution

### Using Sample Data

The repository includes small sample datasets (15 rows each) in `data/sample/` for quick testing:

```bash
# Copy sample data to raw directory
cp data/sample/*.csv data/raw/

# Or update config to use sample data path
# Then run the pipeline
python main.py
```

**Sample files included:**
- `customers_sample.csv` - 15 customer records
- `loans_sample.csv` - 15 loan records
- `loans_repayments_sample.csv` - 15 repayment records
- `loans_defaulters_delinq_sample.csv` - 15 delinquency records
- `loans_defaulters_detail_sample.csv` - 15 defaulter detail records

### Using Full Dataset

For production use with the complete Lending Club dataset:

1. Download data from [Kaggle Lending Club](https://www.kaggle.com/datasets/wordsforthewise/lending-club)
2. Place CSV files in `data/raw/` directory
3. Ensure column names match the pipeline expectations
4. Run pipeline: `python main.py`

### Data Quality

The project includes a **data cleaning pipeline** that:
- Identifies bad/duplicate records
- Removes data quality issues
- Maintains referential integrity across tables
- Ensures valid loan scoring calculations

## 📁 Project Structure

```
Lending-Club-Project/
├── README.md                          # Project documentation
├── QUICKSTART.md                      # Quick start guide
├── DEVELOPMENT.md                     # Development guidelines
├── requirements.txt                   # Python dependencies
├── main.py                            # Entry point script
├── .gitignore                         # Git ignore rules
├── .env.example                       # Example environment config
│
├── data/
│   ├── raw/                           # Original datasets (git ignored)
│   ├── sample/                        # ✅ Sample data for testing (5-20 rows)
│   │   ├── customers_sample.csv
│   │   ├── loans_sample.csv
│   │   ├── loans_repayments_sample.csv
│   │   ├── loans_defaulters_delinq_sample.csv
│   │   └── loans_defaulters_detail_sample.csv
│   └── processed/                     # Cleaned and transformed data
│       └── loan_scores/               # Final scoring results
│
├── src/                               # Core application modules
│   ├── __init__.py
│   ├── config.py                      # Configuration management
│   ├── utils.py                       # Utility functions and constants
│   ├── data_preprocessing.py          # Data loading and cleaning
│   ├── feature_engineering.py         # Score calculation logic
│   ├── model_training.py              # Pipeline orchestration
│   └── evaluation.py                  # Model evaluation and metrics
│
├── notebooks/                         # Reference Jupyter notebooks
│   ├── 1.Lendingclub_datasets_generation.ipynb
│   ├── 2.lendingclub_customers_cleaned.ipynb
│   ├── 3.lendingclub_loans_cleaned.ipynb
│   ├── ... (other analysis notebooks)
│   └── 9.lendingclub_main_.ipynb
│
└── outputs/                           # Generated artifacts
    ├── models/                        # Saved models and scores
    └── plots/                         # Visualization outputs
```

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.8+**
- **Java 8+** (required for PySpark)
- **Apache Spark 3.0+** (optional, for distributed processing)

### Step 1: Clone or Download the Project

```bash
cd Lending-Club-Project
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Using venv
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Prepare Data

Place your data files in the `data/raw/` directory:
- `customers.csv` (or `.parquet`)
- `loans.csv` (or `.parquet`)
- `loans_repayments.csv` (or `.parquet`)
- `loans_defaulters_delinq.csv` (or `.parquet`)
- `loans_defaulters_detail.csv` (or `.parquet`)

**Alternative**: If using Hive database, adjust `main.py` table names to match your schema.

## ▶️ Running the Pipeline

### Basic Usage

```bash
# Run with CSV files
python main.py

# Run with Hive database (if available)
python main.py --hive

# Specify custom output path
python main.py --output-path data/processed/custom_scores

# View help
python main.py --help
```

### Expected Output

```
======================================================================
  LENDING CLUB LOAN SCORING MODEL
======================================================================

======================================================================
  LOADING DATA
======================================================================

...

======================================================================
  PIPELINE EXECUTION COMPLETED
======================================================================

✓ Loan scoring completed successfully!
✓ Results saved to: data/processed/loan_scores
✓ Total loans scored: 10,000
```

## 🔄 Pipeline Steps

### 1. Data Loading (`data_preprocessing.py`)
- Load data from CSV files or Hive database
- Validate schema and data types
- Display data summaries

### 2. Data Cleaning & Preprocessing
- **Identify bad records**: Detect duplicate/inconsistent records
- **Remove quality issues**: Exclude records that appear multiple times
- **Maintain integrity**: Ensure member IDs are consistent across tables
- **Validate quality**: Check minimum row counts and data consistency

### 3. Feature Engineering & Scoring (`feature_engineering.py`)

#### Criterion 1: Payment History (Weight: 20%)
Evaluates a customer's payment behavior:
- **Last Payment Points**: Based on payment amount vs. monthly installment
  - < 50% of installment: 100 pts
  - Full payment: 500 pts
  - Overpayment: 650-800 pts
- **Total Payment Points**: Based on total received vs. funded amount
  - ≥ 50% of funded: 650 pts
  - 0-50% of funded: 500 pts
  - No payment: 0 pts

#### Criterion 2: Loan Default History (Weight: 45%)
Evaluates default risk factors:
- **Delinquency Score**: Based on delinquencies in last 2 years
  - 0 delinquencies: 800 pts (excellent)
  - 1-2 delinquencies: 250 pts (bad)
  - 3-5 delinquencies: 100 pts (very bad)
  - > 5 delinquencies: 0 pts (unacceptable)
- **Public Records Score**: Based on public record history
- **Bankruptcy Score**: Based on bankruptcy history
- **Inquiry Score**: Based on credit inquiries in last 6 months

#### Criterion 3: Financial Health (Weight: 35%)
Evaluates financial stability:
- **Loan Status Score**: Current vs. Fully Paid vs. Charged Off
- **Home Ownership Score**: Own > Rent > Mortgage > Other
- **Credit Limit Utilization**: Loan size relative to available credit
- **Grade Score**: Customer's Lending Club grade (A1-G5)

#### Final Loan Score Calculation
```
Loan Score = (Payment History Pts × 0.20) 
           + (Default History Pts × 0.45) 
           + (Financial Health Pts × 0.35)
```

### 4. Grade Assignment
Scores are converted to letter grades:
- **Grade A**: Score > 2500 (Excellent)
- **Grade B**: 2000 < Score ≤ 2500 (Very Good)
- **Grade C**: 1500 < Score ≤ 2000 (Good)
- **Grade D**: 1000 < Score ≤ 1500 (Bad)
- **Grade E**: 750 < Score ≤ 1000 (Very Bad)
- **Grade F**: Score ≤ 750 (Unacceptable)

### 5. Evaluation & Reporting (`evaluation.py`)
- **Grade Distribution**: Count and percentage of each grade
- **Score Statistics**: Mean, min, max loan scores
- **Risk Analysis**: High-risk vs. low-risk loan identification
- **Criteria Analysis**: How each criterion contributes to final grades

## 📈 Results & Metrics

### Evaluation Report Output

The pipeline generates a comprehensive evaluation report including:

```
Total Records Evaluated: 10,000

Grade Distribution:
  Grade A:        2,500 loans (25.00%)
  Grade B:        3,000 loans (30.00%)
  Grade C:        2,500 loans (25.00%)
  Grade D:        1,200 loans (12.00%)
  Grade E:          600 loans (6.00%)
  Grade F:          200 loans (2.00%)

Score Statistics:
  Average Score:    1850.45
  Minimum Score:     150.00
  Maximum Score:    2890.50

Risk Analysis:
  Low-Risk (A, B):     5,500 loans (55.00%)
  Medium-Risk (C):     2,500 loans (25.00%)
  High-Risk (D, E, F): 2,000 loans (20.00%)
```

### Output Files

All results are saved to `data/processed/loan_scores/`:
- Parquet format for efficient querying
- Includes all scoring components:
  - `member_id`: Customer identifier
  - `payment_history_pts`: pts from criterion 1
  - `defaulters_history_pts`: pts from criterion 2
  - `financial_health_pts`: pts from criterion 3
  - `loan_score`: Final composite score
  - `loan_final_grade`: Letter grade (A-F)

## 💡 Technologies Used

| Category | Technology |
|----------|-----------|
| **Base** | Python 3.8+ |
| **Distributed Processing** | Apache Spark 3.0+ |
| **Data Manipulation** | PySpark DataFrame API |
| **Data Analysis** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn |
| **Visualization** | Matplotlib, Seaborn, Plotly |
| **Testing** | Pytest |
| **Code Quality** | Black, Flake8, MyPy |
| **Notebooks** | Jupyter/JupyterLab |

## 📚 Project Components

### `src/utils.py`
Utility functions and constants:
- Scoring point configurations
- Grade point boundaries
- Path helpers
- Logging utilities
- Data validation functions

### `src/data_preprocessing.py`
Data loading and cleaning:
- Load from CSV, Parquet, or Hive
- Bad record identification
- Data quality validation
- Missing value handling

### `src/feature_engineering.py`
Loan scoring logic:
- Payment history score calculation
- Default history score calculation
- Financial health score calculation
- Composite score calculation
- Grade assignment

### `src/model_training.py`
Pipeline orchestration:
- End-to-end pipeline execution
- Component coordination
- Result saving
- Result validation

### `src/evaluation.py`
Model evaluation:
- Grade distribution analysis
- Score statistics
- Risk-based segmentation
- Evaluation reporting

## 📤 Output Files

### Parquet Output
```
data/processed/loan_scores/
├── part-00000-*.parquet
├── part-00001-*.parquet
└── _SUCCESS
```

Can be opened in:
```python
import pandas as pd
scores = pd.read_parquet('data/processed/loan_scores/')
```

### Optional CSV Export
```python
# Export evaluation metrics
trainer.evaluator.export_evaluation_metrics(
    final_grades, 
    'outputs/evaluation_report.txt'
)
```

## 🔍 Development & Testing

### Run Tests
```bash
pytest tests/ -v --cov=src
```

### Code Quality Checks
```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## 📝 Jupyter Notebooks

The `notebooks/` directory contains reference notebooks for:
- Exploratory Data Analysis
- Dataset cleaning and preparation
- Feature analysis and visualization
- Score distribution analysis

These are for **reference only**. All production logic is in the `src/` modules.

## 🤝 Contributing

When contributing to this project:

1. Follow PEP 8 style guidelines
2. Add docstrings to all functions and classes
3. Write unit tests for new functionality
4. Update this README if adding features
5. Use type hints in function signatures
6. Create a new feature branch for changes

## 📋 Best Practices Implemented

✅ **Modular Design**: Separated concerns across modules
✅ **Comprehensive Docstrings**: All functions documented
✅ **Type Hints**: Function signatures include types
✅ **Error Handling**: Try-except blocks with logging
✅ **Configuration Management**: Centralized constants in utils
✅ **Logging**: Detailed execution logging
✅ **Factory Functions**: Consistent object creation
✅ **Factory Pattern**: Easier testing and dependency injection
✅ **Comments**: Inline explanations for complex logic
✅ **Path Handling**: Cross-platform path operations

## 🎓 Learning Outcomes

This project demonstrates:
- **Production ML Pipeline**: End-to-end workflow
- **Distributed Processing**: PySpark for big data
- **Data Engineering**: ETL pipeline design
- **Feature Engineering**: Score calculation logic
- **Code Quality**: Professional Python standards
- **Documentation**: Comprehensive project documentation


For issues or questions:
1. Check the README and docstrings
2. Review the notebook examples
3. Check the inline code comments
4. Examine the Spark and PySpark logs

## License

This project is provided as-is for educational and professional use.

##  Summary

This production-grade machine learning project provides:
- **Automated loan scoring** based on financial criteria
- **Risk assessment** for lending decisions
- **Scalable pipeline** using Apache Spark
- **Clean, modular code** suitable for professional environments
- **Comprehensive documentation** for maintainability
- **Best practices** in ML engineering and software development

**Status**: Production Ready ✅
**Last Updated**: 2026
**Python Version**: 3.8+
**Spark Version**: 3.0+
