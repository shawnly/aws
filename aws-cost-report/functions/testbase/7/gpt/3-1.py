import boto3
import pandas as pd
import argparse
import os
from datetime import datetime

# Initialize Cost Explorer client
ce_client = boto3.client('ce')

def get_accounts_from_cost_explorer(start_date, end_date):
    accounts = []
    response = ce_client.get_dimension_values(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Dimension='LINKED_ACCOUNT',
        Context='COST_AND_USAGE',
        MaxResults=2000
    )
    for value in response.get('DimensionValues', []):
        account_id = value.get('Value')
        account_name = value.get('Attributes', {}).get('description', f"Account {account_id}")
        accounts.append({
            'id': account_id,
            'name': account_name
        })
    return accounts

def get_cost_data(account_id, start_date, end_date):
    response = ce_client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['AmortizedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
        Filter={
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    )
    service_results = response['ResultsByTime']

    # Get refunds
    refund_response = ce_client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['AmortizedCost'],
        Filter={
            'And': [
                {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [account_id]}},
                {'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Refund']}}
            ]
        }
    )
    refund_results = refund_response['ResultsByTime']

    return service_results, refund_results

def write_to_excel(account_id, account_name, start_date, end_date, service_data, refund_data):
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

    # Save to file path
    year = start_date[:4]
    end_month = datetime.strptime(end_date, '%Y-%m-%d').strftime('%m')
    folder_path = f'aws_cost_reports/{account_id}/{year}/end-of-{end_month}'
    os.makedirs(folder_path, exist_ok=True)
    filename = f"aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx"
    file_path = os.path.join(folder_path, filename)
    df.to_excel(file_path, index=False)
    print(f"✅ {account_name} ({account_id}) report saved: {file_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--account-id', help='Specific account ID (optional)')

    args = parser.parse_args()
    start_date = args.start_date
    end_date = args.end_date

    if args.account_id:
        accounts = [{'id': args.account_id, 'name': f"Account {args.account_id}"}]
    else:
        accounts = get_accounts_from_cost_explorer(start_date, end_date)

    for acct in accounts:
        print(f"📊 Fetching cost data for {acct['name']} ({acct['id']})...")
        service_data, refund_data = get_cost_data(acct['id'], start_date, end_date)
        write_to_excel(acct['id'], acct['name'], start_date, end_date, service_data, refund_data)

if __name__ == '__main__':
    main()
