import boto3
import pandas as pd
import argparse
import os
from datetime import datetime

# Initialize Cost Explorer client
ce_client = boto3.client('ce')

def get_linked_accounts():
    org_client = boto3.client('organizations')
    accounts = []
    paginator = org_client.get_paginator('list_accounts')
    for page in paginator.paginate():
        for acct in page['Accounts']:
            if acct['Status'] == 'ACTIVE':
                accounts.append(acct['Id'])
    return accounts

def get_cost_data(account_id, start_date, end_date):
    results = []
    next_token = None

    while True:
        response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['AmortizedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
            ],
            Filter={
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': [account_id]
                }
            },
            NextPageToken=next_token
        )
        results.extend(response['ResultsByTime'])
        next_token = response.get('NextPageToken')
        if not next_token:
            break

    # Get refunds (negative costs under "Refund")
    refund_response = ce_client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['AmortizedCost'],
        Filter={
            'And': [
                {
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': [account_id]
                    }
                },
                {
                    'Dimensions': {
                        'Key': 'RECORD_TYPE',
                        'Values': ['Refund']
                    }
                }
            ]
        }
    )

    return results, refund_response['ResultsByTime']

def write_to_excel(account_id, start_date, end_date, service_data, refund_data):
    rows = []
    for result in service_data:
        for group in result['Groups']:
            service = group['Keys'][0]
            amount = group['Metrics']['AmortizedCost']['Amount']
            rows.append({
                'StartDate': result['TimePeriod']['Start'],
                'EndDate': result['TimePeriod']['End'],
                'Service': service,
                'AmortizedCost': float(amount)
            })

    # Add refunds
    for result in refund_data:
        refund_amt = result['Total']['AmortizedCost']['Amount']
        if float(refund_amt) != 0:
            rows.append({
                'StartDate': result['TimePeriod']['Start'],
                'EndDate': result['TimePeriod']['End'],
                'Service': 'Refund',
                'AmortizedCost': float(refund_amt)
            })

    df = pd.DataFrame(rows)

    # Prepare file path
    year = start_date[:4]
    end_month = datetime.strptime(end_date, '%Y-%m-%d').strftime('%m')
    folder_path = f'aws_cost_reports/{account_id}/{year}/end-of-{end_month}'
    os.makedirs(folder_path, exist_ok=True)
    file_path = f"{folder_path}/aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx"
    df.to_excel(file_path, index=False)
    print(f"✅ Report saved: {file_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--account-id', help='Linked account ID (optional)')

    args = parser.parse_args()
    start_date = args.start_date
    end_date = args.end_date
    account_ids = [args.account_id] if args.account_id else get_linked_accounts()

    for account_id in account_ids:
        print(f"Fetching cost data for account {account_id}...")
        service_data, refund_data = get_cost_data(account_id, start_date, end_date)
        write_to_excel(account_id, start_date, end_date, service_data, refund_data)

if __name__ == '__main__':
    main()
