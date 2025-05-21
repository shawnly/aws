import boto3
import pandas as pd
import os
import argparse
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Get AWS cost data for a specific account')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--account-id', required=True, nargs='+', help='One or more AWS Account IDs')
    return parser.parse_args()

def get_cost_data(start_date, end_date, account_id):
    client = boto3.client('ce')
    response = client.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        Filter={
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        },
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )
    return response

def save_account_cost_report(account_id, start_date, end_date, response):
    year = start_date[:4]
    month = end_date[5:7]
    folder_path = f'aws_cost_reports/{account_id}/{year}/end-of-{month}'
    os.makedirs(folder_path, exist_ok=True)
    file_path = f'{folder_path}/aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx'

    rows = []
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            amount = group['Metrics']['UnblendedCost']['Amount']
            rows.append({
                'Account ID': account_id,
                'Start Date': start_date,
                'End Date': end_date,
                'Service': service,
                'Cost ($)': float(amount),
                'Result Start': result['TimePeriod']['Start'],
                'Result End': result['TimePeriod']['End']
            })

    df = pd.DataFrame(rows)
    df.to_excel(file_path, index=False)
    return df

def generate_summary_report(all_dataframes, start_date, end_date):
    summary_df = pd.concat(all_dataframes)
    summary = summary_df.groupby('Service')['Cost ($)'].sum().reset_index()
    summary.sort_values(by='Cost ($)', ascending=False, inplace=True)

    output_file = f'aws_cost_reports/summary-cost-report-{start_date}_to_{end_date}.xlsx'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    summary.to_excel(output_file, index=False)

def main():
    args = parse_arguments()
    start_date = args.start_date
    end_date = args.end_date
    account_ids = args.account_id

    all_data = []
    for account_id in account_ids:
        print(f"Processing account {account_id}...")
        response = get_cost_data(start_date, end_date, account_id)
        df = save_account_cost_report(account_id, start_date, end_date, response)
        all_data.append(df)

    generate_summary_report(all_data, start_date, end_date)
    print("✅ Reports generated successfully.")

if __name__ == '__main__':
    main()
