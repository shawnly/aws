import boto3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse
import os
from dateutil.relativedelta import relativedelta

def get_monthly_costs_by_account(start_date, end_date, granularity='MONTHLY', metrics=['UnblendedCost']):
    """
    Get monthly costs for each linked account using the Cost Explorer API.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        granularity (str): Time granularity (DAILY, MONTHLY, etc.)
        metrics (list): List of cost metrics to retrieve
        
    Returns:
        dict: Dictionary containing cost data organized by account
    """
    client = boto3.client('ce')
    
    # Get list of linked accounts
    accounts_response = client.get_dimension_values(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Dimension='LINKED_ACCOUNT'
    )
    
    accounts = [(item['Value'], item.get('Name', item['Value'])) 
                for item in accounts_response['DimensionValues']]
    
    results_by_account = {}
    
    # For each account, get cost data
    for account_id, account_name in accounts:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity=granularity,
            Metrics=metrics,
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
        
        results_by_account[f"{account_id} ({account_name})"] = response
    
    return results_by_account

def process_cost_data(results_by_account):
    """
    Process the raw cost data into a more usable format.
    
    Args:
        results_by_account (dict): Raw cost data from Cost Explorer API
        
    Returns:
        dict: Processed cost data by account
    """
    processed_data = {}
    
    for account, data in results_by_account.items():
        account_data = []
        
        for time_period in data['ResultsByTime']:
            period_start = time_period['TimePeriod']['Start']
            
            for group in time_period['Groups']:
                service = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                unit = group['Metrics']['UnblendedCost']['Unit']
                
                account_data.append({
                    'Date': period_start,
                    'Service': service,
                    'Amount': amount,
                    'Unit': unit
                })
        
        # Create DataFrame for this account
        df = pd.DataFrame(account_data)
        if not df.empty:
            # Summarize by date and service
            df_pivot = df.pivot_table(
                index='Date', 
                columns='Service', 
                values='Amount', 
                aggfunc='sum'
            ).fillna(0)
            
            processed_data[account] = df_pivot
    
    return processed_data

def generate_visualizations(processed_data, output_dir='cost_reports'):
    """
    Generate visualizations from the processed cost data.
    
    Args:
        processed_data (dict): Processed cost data by account
        output_dir (str): Directory to save the visualizations
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for account, df in processed_data.items():
        # Clean account name for filename
        account_clean = account.replace(' ', '_').replace('(', '').replace(')', '')
        
        # Create monthly total costs
        monthly_total = df.sum(axis=1)
        monthly_total.name = 'Total'
        
        # Get top services by cost
        service_totals = df.sum()
        top_services = service_totals.nlargest(10).index.tolist()
        
        # Create a DataFrame with top services and 'Other'
        top_df = df[top_services].copy()
        top_df['Other'] = df.drop(columns=top_services).sum(axis=1)
        
        # Generate stacked bar chart
        plt.figure(figsize=(12, 8))
        top_df.plot(kind='bar', stacked=True, figsize=(12, 8))
        plt.title(f'Monthly AWS Costs - {account}')
        plt.xlabel('Month')
        plt.ylabel('Cost (USD)')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(title='AWS Services', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Save visualization
        plt.savefig(f'{output_dir}/{account_clean}_monthly_costs.png', dpi=300)
        plt.close()
        
        # Save data to CSV
        top_df.to_csv(f'{output_dir}/{account_clean}_monthly_costs.csv')
        
        # Generate simple report
        with open(f'{output_dir}/{account_clean}_report.txt', 'w') as f:
            f.write(f"AWS Cost Report for {account}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Monthly Costs:\n")
            for date, cost in monthly_total.items():
                f.write(f"  {date}: ${cost:.2f}\n")
            
            f.write("\nTop Services by Cost:\n")
            for service, cost in service_totals.nlargest(10).items():
                percentage = (cost / service_totals.sum()) * 100
                f.write(f"  {service}: ${cost:.2f} ({percentage:.1f}%)\n")
            
            f.write(f"\nTotal Cost: ${service_totals.sum():.2f}\n")

def main():
    parser = argparse.ArgumentParser(description='Generate AWS Cost Explorer reports')
    parser.add_argument('--months', type=int, default=6, 
                        help='Number of months to include in the report')
    parser.add_argument('--output', type=str, default='cost_reports',
                        help='Output directory for reports')
    parser.add_argument('--granularity', type=str, default='MONTHLY',
                        choices=['DAILY', 'MONTHLY'], 
                        help='Time granularity for the report')
    
    args = parser.parse_args()
    
    # Calculate date range
    end_date = datetime.now().replace(day=1) - timedelta(days=1)
    start_date = (end_date - relativedelta(months=args.months-1)).replace(day=1)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"Generating AWS cost reports from {start_str} to {end_str}")
    
    # Get cost data
    results = get_monthly_costs_by_account(start_str, end_str, args.granularity)
    
    # Process data
    processed_data = process_cost_data(results)
    
    # Generate visualizations and reports
    generate_visualizations(processed_data, args.output)
    
    print(f"Reports generated in '{args.output}' directory")

if __name__ == "__main__":
    main()