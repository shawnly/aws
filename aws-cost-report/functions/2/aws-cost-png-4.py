import boto3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import os
import argparse
from matplotlib.ticker import FuncFormatter

# Define colors for AWS services
AWS_SERVICE_COLORS = {
    'Amazon Elastic Compute Cloud': '#FF9900',  # EC2 - Orange
    'Amazon Simple Storage Service': '#3B48CC',  # S3 - Blue
    'Amazon RDS Service': '#2E73B8',  # RDS - Light Blue
    'AWS Lambda': '#FF5252',  # Lambda - Red
    'Amazon DynamoDB': '#5A45AA',  # DynamoDB - Purple
    'AWS CloudTrail': '#2ECC71',  # CloudTrail - Green
    'Amazon CloudWatch': '#3498DB',  # CloudWatch - Sky Blue
    'Amazon Route 53': '#F39C12',  # Route 53 - Yellow
    'AWS Key Management Service': '#9B59B6',  # KMS - Violet
    'Amazon CloudFront': '#1ABC9C',  # CloudFront - Teal
    'Amazon ElastiCache': '#E74C3C',  # ElastiCache - Dark Red
    'Amazon SageMaker': '#8E44AD',  # SageMaker - Dark Purple
    'Other': '#CCCCCC'  # Gray for aggregated services
}

def parse_args():
    """Parse command line arguments for date range"""
    parser = argparse.ArgumentParser(description='Generate AWS Cost Reports')
    
    # Get default dates
    today = datetime.date.today()
    six_months_ago = today - relativedelta(months=6)
    
    parser.add_argument(
        '--start-date', 
        type=str,
        default=six_months_ago.strftime('%Y-%m-%d'),
        help='Start date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        '--end-date', 
        type=str,
        default=today.strftime('%Y-%m-%d'),
        help='End date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        '--use-mock', 
        action='store_true',
        help='Use mock data instead of real AWS data'
    )
    
    return parser.parse_args()

def validate_dates(start_date_str, end_date_str):
    """Validate and parse date strings"""
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if start_date >= end_date:
            print("Error: Start date must be before end date")
            return None, None
            
        # Check that date range isn't too long (AWS typically limits to 1 year)
        date_range = relativedelta(end_date, start_date)
        months_diff = date_range.years * 12 + date_range.months
        
        if months_diff > 12:
            print("Warning: Date range exceeds 12 months, which may not be supported by AWS Cost Explorer.")
            print(f"Proceeding with date range: {months_diff} months")
            
        return start_date, end_date
    
    except ValueError as e:
        print(f"Error with date format: {e}")
        print("Please use YYYY-MM-DD format")
        return None, None

def get_aws_cost_data(start_date, end_date):
    """Fetch AWS Cost Explorer data for the specified date range"""
    print("Fetching AWS Cost Explorer data...")
    
    # Create a Cost Explorer client
    ce_client = boto3.client('ce')
    
    # Format dates for AWS API
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"Retrieving cost data from {start_date_str} to {end_date_str}...")
    
    try:
        # Get cost by service and linked account
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date_str,
                'End': end_date_str
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                },
                {
                    'Type': 'DIMENSION',
                    'Key': 'LINKED_ACCOUNT'
                }
            ]
        )
        
        # Process data
        cost_data = []
        for result in response['ResultsByTime']:
            period = result['TimePeriod']['Start']
            
            for group in result['Groups']:
                service, account = group['Keys']
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                unit = group['Metrics']['UnblendedCost']['Unit']
                
                cost_data.append({
                    'Service': service,
                    'Account': account,
                    'Period': period,
                    'Cost': cost,
                    'Unit': unit
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(cost_data)
        
        # Add account names if available
        try:
            # Try to get account names
            org_client = boto3.client('organizations')
            accounts = org_client.list_accounts()
            
            # Create mapping of account ID to name
            account_names = {}
            for acc in accounts['Accounts']:
                account_id = acc['Id']
                account_name = acc['Name']
                account_names[account_id] = account_name
            
            # Add account names to the dataframe
            def get_account_name(account_id):
                return account_names.get(account_id, account_id)
            
            df['AccountName'] = df['Account'].apply(get_account_name)
            
        except Exception as e:
            # If we can't get account names, just use the account IDs
            print(f"Note: Could not retrieve account names: {str(e)}")
            print("Using account IDs only")
            df['AccountName'] = df['Account']
        
        print(f"Retrieved data for {len(df['Service'].unique())} services " +
              f"and {len(df['Account'].unique())} accounts.")
        
        return df
    
    except Exception as e:
        print(f"Error retrieving AWS cost data: {str(e)}")
        # For debugging - save the error
        with open('aws_error.txt', 'w') as f:
            f.write(str(e))
        
        # Fall back to mock data if there's an error
        print("Falling back to mock data for testing purposes.")
        return generate_mock_data(start_date, end_date)

def generate_mock_data(start_date, end_date):
    """Generate mock AWS cost data for testing within date range"""
    import random
    
    print("Generating mock AWS cost data (for testing)...")
    
    # Create date range by month
    current_date = start_date.replace(day=1)
    end_month = end_date.replace(day=1)
    date_list = []
    
    while current_date <= end_month:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += relativedelta(months=1)
    
    # Create mock services (subset of AWS_SERVICE_COLORS)
    services = list(AWS_SERVICE_COLORS.keys())[:10]  # Take first 10 services
    
    # Create mock accounts
    accounts = [
        '123456789012',
        '234567890123',
        '345678901234'
    ]
    
    # Generate data
    cost_data = []
    
    # Base costs for services (to make data realistic)
    service_base_costs = {
        service: random.uniform(100, 2000) for service in services
    }
    
    for date in date_list:
        for account in accounts:
            for service in services:
                # Create some variation in costs
                month_index = date_list.index(date)
                trend_factor = 1.0 + (month_index * 0.05)  # 5% growth trend
                variation = random.uniform(0.8, 1.2) * trend_factor
                cost = service_base_costs[service] * variation
                
                cost_data.append({
                    'Service': service,
                    'Account': account,
                    'Period': date,
                    'Cost': round(cost, 2),
                    'Unit': 'USD',
                    'AccountName': f"Account {account[-4:]}"  # Mock account name
                })
    
    return pd.DataFrame(cost_data)

def create_cost_report_per_account(df, output_dir='aws_cost_report', 
                                  start_date=None, end_date=None):
    """Create monthly cost charts for each account with summary statistics"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Format date range for display
    date_range_text = ""
    if start_date and end_date:
        date_range_text = f" ({start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')})"
    
    # Save raw data to Excel
    excel_path = os.path.join(output_dir, 'aws_cost_data.xlsx')
    df.to_excel(excel_path, index=False)
    print(f"Raw data saved to: {excel_path}")
    
    # Create summary report for all accounts
    create_summary_report(df, output_dir, date_range_text)
    
    # Get list of accounts
    accounts = df['Account'].unique()
    
    for account in accounts:
        print(f"Creating report for account: {account}")
        # Filter data for this account
        account_df = df[df['Account'] == account]
        
        # Get account name if available
        if 'AccountName' in account_df.columns:
            account_name = account_df['AccountName'].iloc[0]
        else:
            account_name = account
        
        # Create pivot table
        pivot = account_df.pivot_table(
            index='Service',
            columns='Period',
            values='Cost',
            aggfunc='sum'
        ).fillna(0)
        
        # Sort by total cost
        pivot['Total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values('Total', ascending=False)
        
        # Calculate summary statistics
        total_cost = pivot['Total'].sum()
        num_months = len(pivot.columns) - 1  # Exclude total column
        monthly_avg = total_cost / num_months if num_months > 0 else 0
        unique_services = len(pivot.index)
        
        # Exclude Total column for chart
        chart_data = pivot.drop('Total', axis=1)
        
        # Get top services, group the rest as 'Other'
        top_n_services = 8
        if len(chart_data) > top_n_services:
            top_services = chart_data.iloc[:top_n_services]
            other_services = chart_data.iloc[top_n_services:].sum()
            chart_data = top_services.copy()
            chart_data.loc['Other'] = other_services
        
        # Get colors for services
        colors = []
        for service in chart_data.index:
            if service == 'Other':
                colors.append(AWS_SERVICE_COLORS['Other'])
            else:
                colors.append(AWS_SERVICE_COLORS.get(service, '#AAAAAA'))
        
        # Format month labels
        months = chart_data.columns
        month_labels = []
        for month in months:
            if '-' in month:
                parts = month.split('-')
                if len(parts) >= 2:
                    month_labels.append(f"{parts[1]}/{parts[0][-2:]}")  # MM/YY format
                else:
                    month_labels.append(month)
            else:
                month_labels.append(month)
        
        # Create the figure with two subplots (main chart and summary box)
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Create the stacked bar chart
        chart_data.T.plot(kind='bar', stacked=True, ax=ax, color=colors)
        
        # Add labels inside each segment of the stacked bar
        bottom_values = np.zeros(len(chart_data.columns))
        for i, service in enumerate(chart_data.index):
            for j, month in enumerate(chart_data.columns):
                cost = chart_data.loc[service, month]
                # Only add label if the segment is large enough to be visible
                if cost > max(chart_data.T.sum(axis=1)) * 0.05:  # 5% threshold for visibility
                    # Calculate the position (middle of the segment)
                    y_pos = bottom_values[j] + cost/2
                    # Choose text color based on segment darkness
                    text_color = 'white' if cost > max(chart_data.T.sum(axis=1)) * 0.1 else 'black'
                    ax.text(j, y_pos, f'${int(cost):,}', 
                            ha='center', va='center', fontsize=9, color=text_color)
                bottom_values[j] += cost
        
        # Add total labels on top of each bar
        for i, total in enumerate(chart_data.T.sum(axis=1)):
            ax.text(i, total + (max(chart_data.T.sum(axis=1)) * 0.02), f'${int(total):,}', 
                   ha='center', fontsize=10, fontweight='bold')
        
        # Format the chart
        ax.set_title(f'AWS Monthly Cost by Service - {account_name}{date_range_text}', fontsize=16)
        ax.set_ylabel('Cost (USD)', fontsize=12)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_xticklabels(month_labels, rotation=0)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add commas and dollar signs to y-axis
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x:,.0f}'))
        
        # Add summary statistics box
        summary_text = (
            f"Summary Statistics:\n"
            f"Total Cost: ${total_cost:,.2f}\n"
            f"Monthly Average: ${monthly_avg:,.2f}\n"
            f"Unique Services: {unique_services}"
        )
        
        # Position the text box in the upper right corner
        props = dict(boxstyle='round', facecolor='white', alpha=0.7)
        ax.text(0.02, 0.97, summary_text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=props)
        
        # Add legend
        ax.legend(title='Services', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adjust layout and save
        plt.tight_layout()
        chart_file = os.path.join(output_dir, f'aws_cost_report_{account}.png')
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"Chart saved to: {chart_file}")
        
        # Also save the account data to Excel
        account_excel = os.path.join(output_dir, f'aws_cost_report_{account}.xlsx')
        with pd.ExcelWriter(account_excel) as writer:
            pivot.to_excel(writer, sheet_name='Services')
            
            # Create a summary sheet
            summary_df = pd.DataFrame({
                'Metric': ['Total Cost', 'Monthly Average', 'Unique Services'],
                'Value': [f"${total_cost:,.2f}", f"${monthly_avg:,.2f}", unique_services]
            })
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Raw data
            account_df.to_excel(writer, sheet_name='Raw_Data', index=False)
        
        print(f"Account data saved to: {account_excel}")
        plt.close()

def create_summary_report(df, output_dir, date_range_text):
    """Create a summary report across all accounts"""
    print("Creating summary report across all accounts...")
    
    # Group by Account and Period to get monthly totals per account
    summary = df.groupby(['Account', 'Period'])['Cost'].sum().reset_index()
    
    # Add account names if available
    if 'AccountName' in df.columns:
        # Get mapping of Account ID to AccountName
        account_names = df[['Account', 'AccountName']].drop_duplicates().set_index('Account')['AccountName']
        summary['AccountName'] = summary['Account'].map(account_names)
    else:
        summary['AccountName'] = summary['Account']
    
    # Create pivot table for the chart
    pivot = summary.pivot_table(
        index='AccountName',
        columns='Period',
        values='Cost',
        aggfunc='sum'
    ).fillna(0)
    
    # Sort by total cost
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=False)
    
    # Calculate overall summary statistics
    total_cost = pivot['Total'].sum()
    num_months = len(pivot.columns) - 1  # Exclude total column
    monthly_avg = total_cost / num_months if num_months > 0 else 0
    num_accounts = len(pivot.index)
    unique_services = len(df['Service'].unique())
    
    # Format month labels
    months = [col for col in pivot.columns if col != 'Total']
    month_labels = []
    for month in months:
        if '-' in month:
            parts = month.split('-')
            if len(parts) >= 2:
                month_labels.append(f"{parts[1]}/{parts[0][-2:]}")  # MM/YY format
            else:
                month_labels.append(month)
        else:
            month_labels.append(month)
    
    # Top services by cost
    top_services = df.groupby('Service')['Cost'].sum().sort_values(ascending=False).head(5)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(14, 10))
    
    # Define grid for multiple charts
    gs = fig.add_gridspec(2, 2, height_ratios=[2, 1])
    
    # Main chart - Monthly cost by account
    ax1 = fig.add_subplot(gs[0, :])
    chart_data = pivot.drop('Total', axis=1)
    chart_data.T.plot(kind='bar', stacked=True, ax=ax1)
    
    # Add labels inside each segment of the stacked bar
    bottom_values = np.zeros(len(chart_data.columns))
    for i, account in enumerate(chart_data.index):
        for j, month in enumerate(chart_data.columns):
            cost = chart_data.loc[account, month]
            # Only add label if the segment is large enough to be visible
            if cost > max(chart_data.T.sum(axis=1)) * 0.05:  # 5% threshold for visibility
                # Calculate the position (middle of the segment)
                y_pos = bottom_values[j] + cost/2
                # Choose text color based on segment darkness
                text_color = 'white' if cost > max(chart_data.T.sum(axis=1)) * 0.1 else 'black'
                ax1.text(j, y_pos, f'${int(cost):,}', 
                        ha='center', va='center', fontsize=9, color=text_color)
            bottom_values[j] += cost
    
    # Add total labels on top of each bar
    for i, total in enumerate(chart_data.T.sum(axis=1)):
        ax1.text(i, total + (max(chart_data.T.sum(axis=1)) * 0.02), f'${int(total):,}', 
               ha='center', fontsize=10, fontweight='bold')
    
    # Format the chart
    ax1.set_title(f'AWS Monthly Cost by Account{date_range_text}', fontsize=16)
    ax1.set_ylabel('Cost (USD)', fontsize=12)
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_xticklabels(month_labels, rotation=0)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x:,.0f}'))
    ax1.legend(title='Accounts', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Total by account chart
    ax2 = fig.add_subplot(gs[1, 0])
    pivot['Total'].sort_values().plot(kind='barh', ax=ax2)
    ax2.set_title('Total Cost by Account', fontsize=14)
    ax2.set_xlabel('Cost (USD)', fontsize=12)
    ax2.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x:,.0f}'))
    
    # Add value labels to the bars
    for i, v in enumerate(pivot['Total']):
        ax2.text(v + (max(pivot['Total']) * 0.02), i, f'${int(v):,}', va='center')
    
    # Top services chart
    ax3 = fig.add_subplot(gs[1, 1])
    top_services.plot(kind='pie', ax=ax3, autopct='%1.1f%%', startangle=90)
    ax3.set_title('Top 5 Services by Cost', fontsize=14)
    ax3.set_ylabel('')
    
    # Add summary box
    summary_text = (
        f"Summary Statistics:\n"
        f"Total Cost: ${total_cost:,.2f}\n"
        f"Monthly Average: ${monthly_avg:,.2f}\n"
        f"Number of Accounts: {num_accounts}\n"
        f"Unique Services: {unique_services}"
    )
    
    # Position the text box in the upper right corner of main chart
    props = dict(boxstyle='round', facecolor='white', alpha=0.7)
    ax1.text(0.02, 0.97, summary_text, transform=ax1.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    
    # Adjust layout and save
    plt.tight_layout()
    chart_file = os.path.join(output_dir, 'aws_cost_summary.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"Summary chart saved to: {chart_file}")
    
    # Save summary data to Excel
    summary_excel = os.path.join(output_dir, 'aws_cost_summary.xlsx')
    with pd.ExcelWriter(summary_excel) as writer:
        pivot.to_excel(writer, sheet_name='Monthly_By_Account')
        
        # Top services sheet
        top_services.reset_index().rename(columns={'Cost': 'Total Cost'}).to_excel(
            writer, sheet_name='Top_Services', index=False)
        
        # Create a summary sheet
        summary_df = pd.DataFrame({
            'Metric': ['Total Cost', 'Monthly Average', 'Number of Accounts', 'Unique Services'],
            'Value': [f"${total_cost:,.2f}", f"${monthly_avg:,.2f}", num_accounts, unique_services]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"Summary data saved to: {summary_excel}")
    plt.close()

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Validate dates
    start_date, end_date = validate_dates(args.start_date, args.end_date)
    if not start_date or not end_date:
        print("Invalid date range. Exiting.")
        return
    
    OUTPUT_DIR = 'aws_cost_report'
    
    try:
        if args.use_mock:
            # Use mock data for testing
            print("Using mock data as requested...")
            df = generate_mock_data(start_date, end_date)
        else:
            # Get real AWS cost data
            df = get_aws_cost_data(start_date, end_date)
        
        # Create reports for each account
        create_cost_report_per_account(df, OUTPUT_DIR, start_date, end_date)
        
        print("All reports created successfully!")
        print(f"Reports are available in the '{OUTPUT_DIR}' directory")
        
    except Exception as e:
        print(f"Error creating reports: {str(e)}")
        
        # For debugging
        import traceback
        with open('error_log.txt', 'w') as f:
            f.write(traceback.format_exc())
        
        print("Error details saved to 'error_log.txt'")

if __name__ == "__main__":
    main()