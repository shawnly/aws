import boto3
import pandas as pd
import os
from datetime import datetime

def get_cost_and_usage(start_date, end_date, account_id, region='us-east-1'):
    ce = boto3.client('ce', region_name=region)

    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['AmortizedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'}
        ],
        Filter={
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    )

    results = response['ResultsByTime'][0]
    data = []
    for group in results['Groups']:
        service = group['Keys'][0]
        cost = float(group['Metrics']['AmortizedCost']['Amount'])
        data.append({'Service': service, 'Cost': cost})
    
    return pd.DataFrame(data)


def get_refund_amount(start_date, end_date, account_id, region='us-east-1'):
    ce = boto3.client('ce', region_name=region)

    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['AmortizedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}
        ],
        Filter={
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    )

    refund = 0.0
    for group in response['ResultsByTime'][0]['Groups']:
        record_type = group['Keys'][0]
        amount = float(group['Metrics']['AmortizedCost']['Amount'])
        if record_type == 'Refund':
            refund += amount
    return refund


def export_to_excel(df, account_id, start_date, end_date):
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    year = start_dt.strftime('%Y')
    month_end = datetime.strptime(end_date, '%Y-%m-%d').strftime('%B').lower()
    dir_path = f'aws_cost_reports/{account_id}/{year}/end-of-{month_end}'
    os.makedirs(dir_path, exist_ok=True)
    
    file_path = f'{dir_path}/aws-cost-report-{account_id}-{start_date}_to_{end_date}.xlsx'
    df.to_excel(file_path, index=False)
    print(f"[✔] Report saved to: {file_path}")
    return file_path


def generate_summary(df, refund_amount):
    total_cost = df['Cost'].sum()
    adjusted_total = total_cost - refund_amount
    summary_df = pd.DataFrame([{
        'Total Before Refund': total_cost,
        'Refund Amount': refund_amount,
        'Total After Refund': adjusted_total
    }])
    return summary_df


def main(start_date, end_date, account_id):
    print("[...] Fetching service costs...")
    service_df = get_cost_and_usage(start_date, end_date, account_id)
    
    print("[...] Fetching refund amount...")
    refund = get_refund_amount(start_date, end_date, account_id)

    print("[...] Saving service cost report...")
    report_file = export_to_excel(service_df, account_id, start_date, end_date)

    print("[...] Creating summary report...")
    summary_df = generate_summary(service_df, refund)

    summary_file = report_file.replace('.xlsx', '-summary.xlsx')
    summary_df.to_excel(summary_file, index=False)
    print(f"[✔] Summary saved to: {summary_file}")


# Example usage
if __name__ == '__main__':
    # Replace with actual values or pass from CLI
    START_DATE = '2025-04-01'
    END_DATE = '2025-05-01'   # CE API requires end date to be exclusive
    ACCOUNT_ID = '123456789012'

    main(START_DATE, END_DATE, ACCOUNT_ID)
