import boto3
import pandas as pd
import argparse
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def parse_arguments():
    parser = argparse.ArgumentParser(description='Get AWS cost data for a specific account')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--account-id', required=True, help='AWS Account ID')
    return parser.parse_args()

def get_cost_and_usage(ce_client, start_date, end_date, account_id):
    """Get cost and usage data from AWS Cost Explorer"""
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=[
            'UnblendedCost',
            'NetUnblendedCost',  # Includes refunds
        ],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ],
        Filter={
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    )
    
    return response

def process_cost_data(response):
    """Process cost data into a DataFrame"""
    data = []
    
    for result in response['ResultsByTime']:
        time_period = result['TimePeriod']
        period_start = time_period['Start']
        period_end = time_period['End']
        
        for group in result['Groups']:
            service = group['Keys'][0]
            metrics = group['Metrics']
            
            unblended_cost = float(metrics['UnblendedCost']['Amount'])
            unblended_unit = metrics['UnblendedCost']['Unit']
            
            net_unblended_cost = float(metrics['NetUnblendedCost']['Amount'])
            net_unit = metrics['NetUnblendedCost']['Unit']
            
            # Calculate refund (if any)
            refund = net_unblended_cost - unblended_cost
            
            data.append({
                'PeriodStart': period_start,
                'PeriodEnd': period_end,
                'Service': service,
                'UnblendedCost': unblended_cost,
                'NetUnblendedCost': net_unblended_cost,
                'Refund': refund,
                'Currency': unblended_unit
            })
    
    # Add total row
    if data:
        total_unblended = sum(item['UnblendedCost'] for item in data)
        total_net = sum(item['NetUnblendedCost'] for item in data)
        total_refund = sum(item['Refund'] for item in data)
        currency = data[0]['Currency']
        
        data.append({
            'PeriodStart': data[0]['PeriodStart'],
            'PeriodEnd': data[0]['PeriodEnd'],
            'Service': 'TOTAL',
            'UnblendedCost': total_unblended,
            'NetUnblendedCost': total_net,
            'Refund': total_refund,
            'Currency': currency
        })
    
    return pd.DataFrame(data)

def save_to_excel(df, account_id, start_date, end_date):
    """Save data to Excel in the specified directory structure"""
    # Parse start and end dates
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Use the end date for folder structure
    year = end_dt.strftime('%Y')
    month = end_dt.strftime('%m')
    
    # Create directory structure
    output_dir = f"aws_cost_reports/{account_id}/{year}/end-of-{month}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Raw data file path
    raw_file_path = f"{output_dir}/aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx"
    
    # Save raw data
    with pd.ExcelWriter(raw_file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cost Details', index=False)
    
    # Create and save summary file
    summary_df = df[['Service', 'NetUnblendedCost', 'Currency']].copy()
    summary_file_path = f"{output_dir}/aws-cost-summary-{account_id}-{start_date}_to_{end_date}.xlsx"
    
    with pd.ExcelWriter(summary_file_path, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Service Cost Summary', index=False)
    
    return raw_file_path, summary_file_path

def main():
    args = parse_arguments()
    
    # Initialize Cost Explorer client
    ce_client = boto3.client('ce')
    
    # Get cost data
    response = get_cost_and_usage(ce_client, args.start_date, args.end_date, args.account_id)
    
    # Process data
    df = process_cost_data(response)
    
    # Save to Excel
    raw_path, summary_path = save_to_excel(df, args.account_id, args.start_date, args.end_date)
    
    print(f"Raw data saved to: {raw_path}")
    print(f"Summary saved to: {summary_path}")

if __name__ == "__main__":
    main()