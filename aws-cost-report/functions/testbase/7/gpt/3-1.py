import boto3
import argparse
import os
import pandas as pd
from datetime import datetime
from collections import defaultdict

def parse_arguments():
    parser = argparse.ArgumentParser(description='Get AWS cost data for linked accounts.')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--account-id', required=False, help='AWS Linked Account ID (optional)')
    return parser.parse_args()

def get_linked_accounts():
    org_client = boto3.client('organizations')
    accounts = []
    paginator = org_client.get_paginator('list_accounts')
    for page in paginator.paginate():
        for acct in page['Accounts']:
            if acct['Status'] == 'ACTIVE':
                accounts.append(acct['Id'])
    return accounts

def get_cost_data(start_date, end_date, account_id=None):
    ce_client = boto3.client('ce')
    filter_obj = {
        "Dimensions": {
            "Key": "LINKED_ACCOUNT",
            "Values": [account_id]
        }
    } if account_id else None

    results = defaultdict(list)
    response = ce_client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['AmortizedCost', 'UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
        Filter=filter_obj
    )

    for result in response['ResultsByTime']:
        time_period = result['TimePeriod']
        for group in result['Groups']:
            service = group['Keys'][0]
            amortized = float(group['Metrics']['AmortizedCost']['Amount'])
            unblended = float(group['Metrics']['UnblendedCost']['Amount'])
            results['Start'].append(time_period['Start'])
            results['End'].append(time_period['End'])
            results['Service'].append(service)
            results['AmortizedCost'].append(amortized)
            results['UnblendedCost'].append(unblended)

    return pd.DataFrame(results)

def save_to_excel(df, account_id, start_date, end_date):
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    month = end_dt.strftime('%B').lower()
    year = end_dt.strftime('%Y')
    out_dir = f'aws_cost_reports/{account_id}/{year}/end-of-{month}'
    os.makedirs(out_dir, exist_ok=True)
    file_name = f'aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx'
    file_path = os.path.join(out_dir, file_name)
    df.to_excel(file_path, index=False)
    print(f'Report saved to: {file_path}')

def main():
    args = parse_arguments()
    account_ids = [args.account_id] if args.account_id else get_linked_accounts()
    for account_id in account_ids:
        print(f'Generating report for account {account_id}')
        df = get_cost_data(args.start_date, args.end_date, account_id)
        save_to_excel(df, account_id, args.start_date, args.end_date)

if __name__ == '__main__':
    main()
