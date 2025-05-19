#!/usr/bin/env python3
"""
AWS Cost Data Comparison Tool

This script compares raw cost data from AWS Cost Explorer with data from an exported AWS Cost and Usage Report (CUR)
to help identify discrepancies.
"""

import pandas as pd
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_data(raw_data_csv, aws_export_csv):
    """
    Load and prepare data from both sources for comparison.
    
    Args:
        raw_data_csv: Path to the raw cost data CSV from our extractor
        aws_export_csv: Path to the AWS exported CSV file
    
    Returns:
        Tuple of DataFrames (raw_df, aws_df)
    """
    print(f"Loading raw data from: {raw_data_csv}")
    raw_df = pd.read_csv(raw_data_csv)
    
    print(f"Loading AWS export data from: {aws_export_csv}")
    aws_df = pd.read_csv(aws_export_csv)
    
    print("\nRaw data from our extractor:")
    print(raw_df.head())
    print(f"Shape: {raw_df.shape}")
    
    print("\nAWS export data:")
    print(aws_df.head())
    print(f"Shape: {aws_df.shape}")
    
    return raw_df, aws_df

def prepare_aws_export_data(aws_df):
    """
    Prepare the AWS export data for comparison by identifying key columns.
    This function tries to automatically detect relevant columns in the AWS export.
    
    Args:
        aws_df: AWS export DataFrame
    
    Returns:
        Prepared DataFrame with standardized column names
    """
    # First, let's examine the columns to identify what we need
    print("\nAWS Export Columns:")
    for i, col in enumerate(aws_df.columns):
        print(f"{i}: {col}")
    
    # Try to automatically detect relevant columns
    date_columns = [col for col in aws_df.columns if any(keyword in col.lower() for keyword in ['date', 'time', 'period', 'month'])]
    service_columns = [col for col in aws_df.columns if any(keyword in col.lower() for keyword in ['service', 'product'])]
    cost_columns = [col for col in aws_df.columns if any(keyword in col.lower() for keyword in ['cost', 'charge', 'amount', 'spend'])]
    
    # If we can't automatically detect, ask the user
    if not date_columns:
        date_column_idx = int(input("Enter the index of the column that contains the date/month: "))
        date_columns = [aws_df.columns[date_column_idx]]
    
    if not service_columns:
        service_column_idx = int(input("Enter the index of the column that contains the service name: "))
        service_columns = [aws_df.columns[service_column_idx]]
    
    if not cost_columns:
        cost_column_idx = int(input("Enter the index of the column that contains the cost value: "))
        cost_columns = [aws_df.columns[cost_column_idx]]
    
    print(f"\nUsing date column: {date_columns[0]}")
    print(f"Using service column: {service_columns[0]}")
    print(f"Using cost column: {cost_columns[0]}")
    
    # Create a standardized DataFrame
    std_aws_df = pd.DataFrame({
        'month': aws_df[date_columns[0]],
        'service': aws_df[service_columns[0]],
        'aws_cost': aws_df[cost_columns[0]]
    })
    
    # Convert cost to numeric if it's not already
    std_aws_df['aws_cost'] = pd.to_numeric(std_aws_df['aws_cost'], errors='coerce')
    std_aws_df = std_aws_df.dropna(subset=['aws_cost'])
    
    return std_aws_df

def compare_data(raw_df, aws_df):
    """
    Compare the raw data from our extractor with the AWS export data.
    
    Args:
        raw_df: Raw data DataFrame from our extractor
        aws_df: AWS export DataFrame (already prepared)
    
    Returns:
        Tuple of (comparison_df, missing_services_df, monthly_comparison_df)
    """
    # Check which cost column to use from raw data
    if 'blended_cost' in raw_df.columns:
        raw_df['cost'] = raw_df['blended_cost']
    elif 'cost' not in raw_df.columns:
        raw_df['cost'] = raw_df['unblended_cost']
    
    # Standardize service names in both DataFrames
    def standardize_service(service):
        service = str(service).strip().lower()
        # Remove common prefixes
        for prefix in ['amazon ', 'aws ']:
            if service.startswith(prefix):
                service = service[len(prefix):]
        return service
    
    raw_df['std_service'] = raw_df['service'].apply(standardize_service)
    aws_df['std_service'] = aws_df['service'].apply(standardize_service)
    
    # Group by month and service and sum costs
    raw_grouped = raw_df.groupby(['month', 'std_service'])['cost'].sum().reset_index()
    aws_grouped = aws_df.groupby(['month', 'std_service'])['aws_cost'].sum().reset_index()
    
    # Merge the DataFrames to compare
    comparison = pd.merge(
        raw_grouped, 
        aws_grouped, 
        on=['month', 'std_service'], 
        how='outer',
        suffixes=('_raw', '_aws')
    )
    
    # Fill NaN values with 0
    comparison['cost'] = comparison['cost'].fillna(0)
    comparison['aws_cost'] = comparison['aws_cost'].fillna(0)
    
    # Calculate differences
    comparison['diff'] = comparison['aws_cost'] - comparison['cost']
    comparison['diff_percent'] = (comparison['diff'] / comparison['aws_cost'] * 100).fillna(0)
    
    # Monthly totals comparison
    raw_monthly = raw_df.groupby('month')['cost'].sum().reset_index()
    aws_monthly = aws_df.groupby('month')['aws_cost'].sum().reset_index()
    
    monthly_comparison = pd.merge(
        raw_monthly,
        aws_monthly,
        on='month',
        how='outer',
        suffixes=('_raw', '_aws')
    )
    
    monthly_comparison['diff'] = monthly_comparison['aws_cost'] - monthly_comparison['cost']
    monthly_comparison['diff_percent'] = (monthly_comparison['diff'] / monthly_comparison['aws_cost'] * 100).fillna(0)
    
    # Find missing services (those in AWS data but with low or zero values in raw data)
    missing_threshold = 0.1  # 10% difference threshold
    missing_services = comparison[
        (comparison['diff'] > 1.0) &  # $1 minimum difference to filter out tiny amounts
        (comparison['diff_percent'] > missing_threshold)
    ].sort_values(by='diff', ascending=False)
    
    return comparison, missing_services, monthly_comparison

def create_visualizations(comparison_df, missing_df, monthly_df, output_dir):
    """
    Create visualizations to help understand the discrepancies.
    
    Args:
        comparison_df: Service-level comparison DataFrame
        missing_df: Missing services DataFrame
        monthly_df: Monthly comparison DataFrame
        output_dir: Directory to save output files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Monthly totals comparison
    plt.figure(figsize=(12, 6))
    months = monthly_df['month']
    x = np.arange(len(months))
    width = 0.35
    
    plt.bar(x - width/2, monthly_df['cost'], width, label='Our Raw Data')
    plt.bar(x + width/2, monthly_df['aws_cost'], width, label='AWS Export')
    
    plt.xlabel('Month')
    plt.ylabel('Cost (USD)')
    plt.title('Monthly Cost Comparison')
    plt.xticks(x, months)
    plt.legend()
    
    for i, row in enumerate(monthly_df.itertuples()):
        diff_text = f"${row.diff:.2f}\n({row.diff_percent:.1f}%)"
        plt.text(i, max(row.cost, row.aws_cost) + 5, diff_text, ha='center')
    
    plt.savefig(os.path.join(output_dir, 'monthly_comparison.png'), dpi=300, bbox_inches='tight')
    
    # 2. Top missing services
    if not missing_df.empty:
        top_missing = missing_df.head(15)  # Top 15 missing services
        
        plt.figure(figsize=(12, 8))
        plt.barh(top_missing['std_service'], top_missing['diff'])
        plt.xlabel('Missing Cost (USD)')
        plt.ylabel('Service')
        plt.title('Top Missing Services')
        
        for i, row in enumerate(top_missing.itertuples()):
            plt.text(row.diff + 0.5, i, f"${row.diff:.2f} ({row.diff_percent:.1f}%)", va='center')
        
        plt.savefig(os.path.join(output_dir, 'missing_services.png'), dpi=300, bbox_inches='tight')
    
    # 3. Service distribution comparison for one month
    if len(monthly_df) > 0:
        latest_month = monthly_df['month'].iloc[-1]
        
        raw_month_data = comparison_df[comparison_df['month'] == latest_month].sort_values(by='cost', ascending=False)
        aws_month_data = comparison_df[comparison_df['month'] == latest_month].sort_values(by='aws_cost', ascending=False)
        
        # Top 10 services by cost
        raw_top10 = raw_month_data.head(10)
        aws_top10 = aws_month_data.head(10)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Our raw data
        ax1.pie(raw_top10['cost'], labels=raw_top10['std_service'], autopct='%1.1f%%', startangle=90)
        ax1.set_title(f'Our Raw Data - {latest_month}')
        
        # AWS export
        ax2.pie(aws_top10['aws_cost'], labels=aws_top10['std_service'], autopct='%1.1f%%', startangle=90)
        ax2.set_title(f'AWS Export - {latest_month}')
        
        plt.savefig(os.path.join(output_dir, 'service_distribution.png'), dpi=300, bbox_inches='tight')
    
    print(f"Visualizations saved to {output_dir}")

def export_results(comparison_df, missing_df, monthly_df, output_dir):
    """
    Export results to CSV files.
    
    Args:
        comparison_df: Service-level comparison DataFrame
        missing_df: Missing services DataFrame
        monthly_df: Monthly comparison DataFrame
        output_dir: Directory to save output files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Sort by difference (descending)
    comparison_sorted = comparison_df.sort_values(by='diff', ascending=False)
    
    # Export to CSV
    comparison_sorted.to_csv(os.path.join(output_dir, 'service_comparison.csv'), index=False)
    missing_df.to_csv(os.path.join(output_dir, 'missing_services.csv'), index=False)
    monthly_df.to_csv(os.path.join(output_dir, 'monthly_comparison.csv'), index=False)
    
    print(f"Results exported to {output_dir}")
    
    # Print summary to console
    print("\n=== SUMMARY ===")
    print(f"Total services analyzed: {len(comparison_df)}")
    print(f"Services with significant differences: {len(missing_df)}")
    
    if not monthly_df.empty:
        total_raw = monthly_df['cost'].sum()
        total_aws = monthly_df['aws_cost'].sum()
        diff = total_aws - total_raw
        diff_percent = (diff / total_aws * 100) if total_aws > 0 else 0
        
        print(f"\nTotal from our raw data: ${total_raw:.2f}")
        print(f"Total from AWS export: ${total_aws:.2f}")
        print(f"Difference: ${diff:.2f} ({diff_percent:.2f}%)")
    
    if not missing_df.empty:
        missing_total = missing_df['diff'].sum()
        print(f"\nTotal missing cost: ${missing_total:.2f}")
        print("\nTop missing services:")
        for i, row in missing_df.head(10).iterrows():
            print(f"  {row['std_service']}: ${row['diff']:.2f} ({row['diff_percent']:.2f}%)")

def main():
    parser = argparse.ArgumentParser(description='Compare AWS cost data')
    parser.add_argument('--raw-data', type=str, required=True,
                      help='Path to raw cost data CSV from our extractor')
    parser.add_argument('--aws-export', type=str, required=True,
                      help='Path to AWS exported CSV file')
    parser.add_argument('--output-dir', type=str, default='aws_cost_comparison',
                      help='Directory to save output files')
    
    args = parser.parse_args()
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, f"comparison_{timestamp}")
    
    # Load data
    raw_df, aws_df = load_data(args.raw_data, args.aws_export)
    
    # Prepare AWS export data
    std_aws_df = prepare_aws_export_data(aws_df)
    
    # Compare data
    comparison, missing_services, monthly_comparison = compare_data(raw_df, std_aws_df)
    
    # Create visualizations
    create_visualizations(comparison, missing_services, monthly_comparison, output_dir)
    
    # Export results
    export_results(comparison, missing_services, monthly_comparison, output_dir)

if __name__ == "__main__":
    main()