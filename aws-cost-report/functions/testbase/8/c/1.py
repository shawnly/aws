import boto3
import pandas as pd
import os
from datetime import datetime, timedelta
import argparse
from dateutil.relativedelta import relativedelta

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate AWS Cost Reports')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--account-id', required=False, help='Specific AWS account ID (optional)')
    return parser.parse_args()

def get_all_linked_accounts(ce_client):
    """Get all linked accounts in the organization"""
    accounts = []
    paginator = ce_client.get_paginator('get_dimension_values')
    
    for page in paginator.paginate(
        TimePeriod={
            'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'End': datetime.now().strftime('%Y-%m-%d')
        },
        Dimension='LINKED_ACCOUNT'
    ):
        for value in page['DimensionValues']:
            accounts.append(value['Value'])
    
    return accounts

def get_cost_and_usage(ce_client, start_date, end_date, account_id=None):
    """Get cost and usage data from Cost Explorer"""
    filters = {
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['*']
        }
    }
    
    if account_id:
        filters['Dimensions'] = {
            'Key': 'LINKED_ACCOUNT',
            'Values': [account_id]
        }

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['AmortizedCost', 'UnblendedCost', 'UsageQuantity'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ],
        Filter=filters
    )
    
    return response

def process_cost_data(response, account_id):
    """Process the cost data into a DataFrame"""
    results = []
    
    for period in response['ResultsByTime']:
        start_date = period['TimePeriod']['Start']
        end_date = period['TimePeriod']['End']
        
        for group in period['Groups']:
            service_name = group['Keys'][0]
            metrics = group['Metrics']
            
            amortized_cost = float(metrics['AmortizedCost']['Amount'])
            unblended_cost = float(metrics['UnblendedCost']['Amount'])
            usage_quantity = float(metrics['UsageQuantity']['Amount'])
            
            # Calculate refund (negative costs represent refunds/credits)
            refund = 0
            if amortized_cost < 0:
                refund = abs(amortized_cost)
                
            results.append({
                'Account ID': account_id,
                'Start Date': start_date,
                'End Date': end_date,
                'Service Name': service_name,
                'Amortized Cost ($)': amortized_cost,
                'Unblended Cost ($)': unblended_cost,
                'Usage Quantity': usage_quantity,
                'Refund ($)': refund
            })
    
    return pd.DataFrame(results)

def save_to_excel(df, account_id, start_date, end_date):
    """Save DataFrame to Excel file in the specified directory structure"""
    # Extract year and month from end_date
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    year = end_date_obj.strftime('%Y')
    month = end_date_obj.strftime('%m')
    
    # Create directory structure
    directory = f"aws_cost_reports/{account_id}/{year}/end-of-{month}"
    os.makedirs(directory, exist_ok=True)
    
    # Create filename
    filename = f"{directory}/aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx"
    
    # Save to Excel
    df.to_excel(filename, index=False)
    print(f"Report saved to {filename}")
    
    return filename

def main():
    args = parse_arguments()
    start_date = args.start_date
    end_date = args.end_date
    account_id = args.account_id
    
    # Initialize Cost Explorer client
    ce_client = boto3.client('ce')
    
    if account_id:
        # Generate report for specific account
        print(f"Generating cost report for account {account_id}...")
        response = get_cost_and_usage(ce_client, start_date, end_date, account_id)
        df = process_cost_data(response, account_id)
        save_to_excel(df, account_id, start_date, end_date)
    else:
        # Generate reports for all linked accounts
        print("Generating cost reports for all linked accounts...")
        accounts = get_all_linked_accounts(ce_client)
        
        for account in accounts:
            print(f"Processing account {account}...")
            response = get_cost_and_usage(ce_client, start_date, end_date, account)
            df = process_cost_data(response, account)
            save_to_excel(df, account, start_date, end_date)
        
        # Additionally, create a consolidated report for all accounts
        print("Generating consolidated report for all accounts...")
        all_accounts_response = get_cost_and_usage(ce_client, start_date, end_date)
        df_all = process_cost_data(all_accounts_response, "consolidated")
        save_to_excel(df_all, "consolidated", start_date, end_date)
    
    print("All reports generated successfully!")

if __name__ == "__main__":
    main()