# AWS Cost Reporter

A Python tool that generates AWS cost reports and visualizations for organization accounts using the AWS Cost Explorer API.

## Features

- Organization-wide cost reports by service
- Individual account cost breakdowns
- Professional AWS Cost Explorer-style charts
- Excel reports with multiple sheets
- Automatic handling of refunds/credits

## Setup

### 1. Install Python Environment
```bash
# Create conda environment
conda create -n aws-cost-py11 python=3.11
conda activate aws-cost-py11

# Install dependencies
conda install -c conda-forge pandas numpy matplotlib seaborn openpyxl python-dateutil xlsxwriter
pip install boto3
```

### 2. Configure AWS
```bash
aws configure
# Enter your AWS credentials with Cost Explorer permissions
```

## Requirements.txt
```text
boto3>=1.26.0
pandas>=1.5.0
numpy>=1.21.0
openpyxl>=3.0.10
xlsxwriter>=3.0.3
python-dateutil>=2.8.2
matplotlib>=3.6.0
seaborn>=0.11.2
```

## Usage

```bash
# Generate reports for all accounts
python aws_cost_reporter.py --start-date 2024-11-01 --end-date 2025-05-01

# Generate report for specific account
python aws_cost_reporter.py --start-date 2024-11-01 --end-date 2025-05-01 --account-id 123456789012
```

### Important Note
Use the 1st of the next month as end date for complete monthly data:
- For April 2025 data: `--end-date 2025-05-01`

## Output Files

```
aws_cost_reports/
├── organization_summary/2025/04/
│   ├── aws-organization-summary-{dates}.xlsx      # Costs by service
│   └── aws-cost-chart-organization_summary-{dates}.png
└── {account-id}/2025/04/
    ├── aws-cost-report-{account-id}-{dates}.xlsx
    └── aws-cost-chart-{account-id}-{dates}.png
```