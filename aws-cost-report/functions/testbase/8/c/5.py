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

def get_all_linked_accounts(ce_client, start_date, end_date):
    """Get all linked accounts in the organization with their names"""
    accounts = []
    
    # Use get_dimension_values directly
    response = ce_client.get_dimension_values(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Dimension='LINKED_ACCOUNT',
        Context='COST_AND_USAGE',
        MaxResults=2000
    )
    
    # Extract account IDs and names
    for value in response.get('DimensionValues', []):
        account_id = value.get('Value')
        account_name = value.get('Attributes', {}).get('description', f"Account {account_id}")
        
        accounts.append({
            'id': account_id,
            'name': account_name
        })
    
    # Check if there's a NextToken for pagination
    while 'NextToken' in response:
        response = ce_client.get_dimension_values(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Dimension='LINKED_ACCOUNT',
            Context='COST_AND_USAGE',
            MaxResults=2000,
            NextToken=response['NextToken']
        )
        
        for value in response.get('DimensionValues', []):
            account_id = value.get('Value')
            account_name = value.get('Attributes', {}).get('description', f"Account {account_id}")
            
            accounts.append({
                'id': account_id,
                'name': account_name
            })
    
    return accounts

def get_cost_and_usage(ce_client, start_date, end_date, account_id=None):
    """Get cost and usage data from Cost Explorer with pagination"""
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

    # Initial request
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
    
    # Store all results
    all_results = response
    
    # Handle pagination if there's a NextToken
    while 'NextToken' in response:
        next_token = response['NextToken']
        
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
            Filter=filters,
            NextToken=next_token
        )
        
        # Append the groups from each paginated response to the original results
        for i, period in enumerate(response['ResultsByTime']):
            all_results['ResultsByTime'][i]['Groups'].extend(period['Groups'])
    
    return all_results

def get_organization_cost_by_service(ce_client, start_date, end_date):
    """Get organization-wide cost aggregated by service with pagination"""
    # Initial request
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
        ]
    )
    
    # Store all results
    all_results = response
    
    # Handle pagination if there's a NextToken
    while 'NextToken' in response:
        next_token = response['NextToken']
        
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
            NextToken=next_token
        )
        
        # Append the groups from each paginated response to the original results
        for i, period in enumerate(response['ResultsByTime']):
            all_results['ResultsByTime'][i]['Groups'].extend(period['Groups'])
    
    return all_results

def process_cost_data(response, account_id, account_name):
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
                'Account Name': account_name,
                'Start Date': start_date,
                'End Date': end_date,
                'Service Name': service_name,
                'Amortized Cost ($)': amortized_cost,
                'Unblended Cost ($)': unblended_cost,
                'Usage Quantity': usage_quantity,
                'Refund ($)': refund
            })
    
    return pd.DataFrame(results)

def process_organization_summary(response):
    """Process the organization summary cost data into a DataFrame"""
    results = []
    
    for period in response['ResultsByTime']:
        start_date = period['TimePeriod']['Start']
        end_date = period['TimePeriod']['End']
        month_year = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m')
        
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
                'Month': month_year,
                'Start Date': start_date,
                'End Date': end_date,
                'Service Name': service_name,
                'Total Amortized Cost ($)': amortized_cost,
                'Total Unblended Cost ($)': unblended_cost,
                'Total Usage Quantity': usage_quantity,
                'Total Refund ($)': refund
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

def save_organization_summary(df, start_date, end_date):
    """Save organization summary to Excel file"""
    # Extract year and month from end_date
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    year = end_date_obj.strftime('%Y')
    month = end_date_obj.strftime('%m')
    
    # Create directory structure
    directory = f"aws_cost_reports/organization_summary/{year}/end-of-{month}"
    os.makedirs(directory, exist_ok=True)
    
    # Create filename
    filename = f"{directory}/aws-organization-summary-{start_date}_to_{end_date}.xlsx"
    
    # Save to Excel
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        # Save detailed data to first sheet
        df.to_excel(writer, sheet_name='Service Details', index=False)
        
        # Create a pivot table summarizing total costs by service across all months
        pivot_df = df.pivot_table(
            index=['Service Name'],
            values=['Total Amortized Cost ($)', 'Total Unblended Cost ($)', 'Total Refund ($)'],
            aggfunc='sum'
        ).reset_index()
        
        # Sort by highest cost
        pivot_df = pivot_df.sort_values('Total Amortized Cost ($)', ascending=False)
        
        # Add total row at the bottom
        total_row = {
            'Service Name': 'TOTAL',
            'Total Amortized Cost ($)': pivot_df['Total Amortized Cost ($)'].sum(),
            'Total Unblended Cost ($)': pivot_df['Total Unblended Cost ($)'].sum(),
            'Total Refund ($)': pivot_df['Total Refund ($)'].sum()
        }
        pivot_df = pd.concat([pivot_df, pd.DataFrame([total_row])], ignore_index=True)
        
        # Save to second sheet
        pivot_df.to_excel(writer, sheet_name='Service Summary', index=False)
        
        # Create pivot table by month and service
        monthly_pivot = df.pivot_table(
            index=['Service Name'],
            columns=['Month'],
            values=['Total Amortized Cost ($)'],
            aggfunc='sum'
        )
        
        # Flatten the multi-index
        monthly_pivot.columns = [f"{col[1]} ({col[0]})" for col in monthly_pivot.columns]
        monthly_pivot = monthly_pivot.reset_index()
        
        # Save to third sheet
        monthly_pivot.to_excel(writer, sheet_name='Monthly Breakdown', index=False)
        
        # Format the Excel file
        workbook = writer.book
        
        # Add some cell formats
        currency_format = workbook.add_format({'num_format': '$#,##0.00'})
        total_format = workbook.add_format({
            'bold': True, 
            'num_format': '$#,##0.00', 
            'bg_color': '#D9D9D9'  # Light gray background
        })
        
        # Get the worksheet objects
        worksheet2 = writer.sheets['Service Summary']
        
        # Set column widths and formats for the Service Summary sheet
        worksheet2.set_column('A:A', 30)  # Service Name
        worksheet2.set_column('B:D', 18, currency_format)  # Cost columns
        
        # Highlight the total row
        total_row_index = len(pivot_df) + 1  # Add 1 for header row
        worksheet2.set_row(total_row_index - 1, None, total_format)
    
    print(f"Organization summary report saved to {filename}")
    return filename

def main():
    args = parse_arguments()
    start_date = args.start_date
    end_date = args.end_date
    account_id = args.account_id
    
    # Initialize Cost Explorer client
    ce_client = boto3.client('ce')
    
    # Generate organization summary report regardless of whether a specific account is specified
    print("Generating organization-wide summary report by service...")
    org_response = get_organization_cost_by_service(ce_client, start_date, end_date)
    org_df = process_organization_summary(org_response)
    save_organization_summary(org_df, start_date, end_date)
    
    if account_id:
        # Generate report for specific account
        print(f"Generating cost report for account {account_id}...")
        
        # Get account name for the specific account ID
        accounts = get_all_linked_accounts(ce_client, start_date, end_date)
        account_info = next((acc for acc in accounts if acc['id'] == account_id), None)
        
        if account_info:
            account_name = account_info['name']
        else:
            account_name = f"Account {account_id}"
            
        response = get_cost_and_usage(ce_client, start_date, end_date, account_id)
        df = process_cost_data(response, account_id, account_name)
        save_to_excel(df, account_id, start_date, end_date)
    else:
        # Get all linked accounts with their names
        print("Getting all linked accounts...")
        accounts = get_all_linked_accounts(ce_client, start_date, end_date)
        
        # Generate reports for all linked accounts
        print("Generating cost reports for all linked accounts...")
        all_dfs = []
        
        for account in accounts:
            account_id = account['id']
            account_name = account['name']
            
            print(f"Processing account {account_id} ({account_name})...")
            response = get_cost_and_usage(ce_client, start_date, end_date, account_id)
            df = process_cost_data(response, account_id, account_name)
            save_to_excel(df, account_id, start_date, end_date)
            all_dfs.append(df)
        
        # Create a consolidated report by combining all dataframes
        if all_dfs:
            print("Generating consolidated report for all accounts...")
            df_consolidated = pd.concat(all_dfs, ignore_index=True)
            save_to_excel(df_consolidated, "consolidated", start_date, end_date)
        else:
            print("No account data found.")
    
    print("All reports generated successfully!")

if __name__ == "__main__":
    main()