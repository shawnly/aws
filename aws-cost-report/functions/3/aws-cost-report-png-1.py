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
        # First get overall top services to determine which ones to group later
        top_services_response = ce_client.get_cost_and_usage(
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
                }
            ]
        )
        
        # Process to find top services
        service_totals = {}
        for result in top_services_response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                service_totals[service] = service_totals.get(service, 0) + cost
        
        # Sort services by total cost and get top 8
        sorted_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
        top_8_services = [service for service, cost in sorted_services[:8]]
        
        # Now get detailed cost data with account breakdown
        # We'll use the GroupBy filter to get top services separately and group the rest
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
        
        # Process data, grouping non-top services as "Other"
        cost_data = []
        for result in response['ResultsByTime']:
            period = result['TimePeriod']['Start']
            
            for group in result['Groups']:
                service, account = group['Keys']
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                unit = group['Metrics']['UnblendedCost']['Unit']
                
                # Group non-top services as "Other" (except refunds which we'll keep separate)
                if service not in top_8_services and not service.lower().startswith("refund"):
                    service_to_use = "Other"
                else:
                    service_to_use = service
                
                cost_data.append({
                    'Service': service_to_use,
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
            print("Using account IDs only. This is normal if your credentials don't have Organizations access.")
            # Just use account ID as the name
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
    services = list(AWS_SERVICE_COLORS.keys())[:9]  # Take first 9 services
    
    # Add a refund service
    services.append("Refund: Service Credits")
    
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
        service: random.uniform(100, 2000) for service in services if not service.startswith("Refund")
    }
    
    # The refund will be a negative value (credit)
    service_base_costs["Refund: Service Credits"] = -random.uniform(200, 500)
    
    for date in date_list:
        for account in accounts:
            # Add normal service costs
            for service in services:
                # Create some variation in costs
                month_index = date_list.index(date)
                trend_factor = 1.0 + (month_index * 0.05)  # 5% growth trend
                variation = random.uniform(0.8, 1.2) * trend_factor
                
                # For refunds, we want them to be negative and not grow with the trend
                if service.startswith("Refund"):
                    # Refunds only appear in some months (not every month)
                    if random.random() > 0.3:  # 70% chance of having a refund in a given month
                        base_cost = service_base_costs[service]
                        # Slight variation in refund amount
                        cost = base_cost * random.uniform(0.8, 1.2)
                    else:
                        continue  # Skip this month for refunds
                else:
                    base_cost = service_base_costs[service]
                    cost = base_cost * variation
                
                cost_data.append({
                    'Service': service,
                    'Account': account,
                    'Period': date,
                    'Cost': round(cost, 2),
                    'Unit': 'USD',
                    'AccountName': f"Account {account[-4:]}"  # Mock account name
                })
    
    # Group non-top services as "Other" (except refunds)
    df = pd.DataFrame(cost_data)
    
    # Get top 8 services by total cost (excluding refunds)
    non_refund_services = df[~df['Service'].str.startswith('Refund')]
    service_totals = non_refund_services.groupby('Service')['Cost'].sum()
    top_services = service_totals.nlargest(8).index.tolist()
    
    # Create a new dataframe with grouped services
    processed_data = []
    for _, row in df.iterrows():
        service = row['Service']
        
        # Keep refunds separate, group others
        if service.startswith('Refund'):
            service_to_use = service
        elif service in top_services:
            service_to_use = service
        else:
            service_to_use = "Other"
        
        new_row = row.copy()
        new_row['Service'] = service_to_use
        processed_data.append(new_row)
    
    return pd.DataFrame(processed_data)

def create_cost_report_per_account(df, output_dir='aws_cost_report', 
                                  start_date=None, end_date=None):
    """Create monthly cost charts for each account with summary statistics"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Format date range for display
    date_range_text = ""
    if start_date and end_date:
        date_range_text = f" ({start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')})"
    
    # Format date range for filenames
    if start_date and end_date:
        date_range_suffix = f"_{start_date.strftime('%Y%m')}_to_{end_date.strftime('%Y%m')}"
    else:
        date_range_suffix = ""
    
    # Save raw data to Excel
    excel_path = os.path.join(output_dir, f'aws_cost_data{date_range_suffix}.xlsx')
    df.to_excel(excel_path, index=False)
    print(f"Raw data saved to: {excel_path}")
    
    # Print unique service names for debugging
    print("\nUnique service names in data:")
    for service in sorted(df['Service'].unique()):
        print(f"  - {service}")
    
    # Check for refund entries
    refund_entries = df[df['Service'].str.contains('refund', case=False, na=False)]
    if not refund_entries.empty:
        print("\nRefund entries found:")
        for _, row in refund_entries.head(5).iterrows():
            print(f"  - {row['Service']}: ${row['Cost']:.2f} in {row['Period']} for account {row['Account']}")
        if len(refund_entries) > 5:
            print(f"  ... and {len(refund_entries) - 5} more entries")
    else:
        print("\nNo refund entries found in the data")
    
    # Create summary report for all accounts
    create_summary_report(df, output_dir, date_range_text, start_date, end_date)
    
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
        
        # Reorder columns to put Total after Service and before the months
        # First, get all columns except 'Total'
        date_columns = [col for col in pivot.columns if col != 'Total']
        
        # Sort date columns chronologically
        date_columns.sort()
        
        # Create new column order with Total second
        ordered_columns = ['Total'] + date_columns
        
        # Reorder the pivot table
        pivot = pivot[ordered_columns]
        
        # Separate positive and negative values for better visualization
        positive_data = pivot.copy()
        negative_data = pivot.copy()
        
        # Zero out negative values in positive data and vice versa
        for col in ordered_columns:
            positive_data[col] = positive_data[col].apply(lambda x: max(x, 0))
            negative_data[col] = negative_data[col].apply(lambda x: min(x, 0))
        
        # Create a copy with formatted month names for Excel export
        excel_pivot = pivot.copy()
        
        # Format column names for better readability in Excel
        column_mapping = {'Total': 'Total'}
        for col in date_columns:
            if '-' in col:
                parts = col.split('-')
                if len(parts) >= 2:
                    # Convert from YYYY-MM-DD to Month YYYY format
                    month_num = int(parts[1])
                    year = parts[0]
                    month_name = datetime.date(2000, month_num, 1).strftime('%B')
                    column_mapping[col] = f"{month_name} {year}"
        
        # Rename columns in the Excel export copy
        excel_pivot = excel_pivot.rename(columns=column_mapping)
        
        # Calculate summary statistics
        total_cost = pivot['Total'].sum()
        num_months = len(pivot.columns) - 1  # Exclude total column
        monthly_avg = total_cost / num_months if num_months > 0 else 0
        unique_services = len(pivot.index)
        
        # Exclude Total column for chart
        pos_chart_data = positive_data.drop('Total', axis=1).copy()
        neg_chart_data = negative_data.drop('Total', axis=1).copy()
        
        # Get top services for positive data, group the rest as 'Other'
        top_n_services = 8
        if len(pos_chart_data) > top_n_services:
            # Sort by absolute value to get top services by magnitude
            service_totals = pos_chart_data.sum(axis=1).abs()
            top_services = service_totals.nlargest(top_n_services).index.tolist()
            
            # Create copies with only top services
            top_pos_data = pos_chart_data.loc[top_services].copy()
            
            # Aggregate remaining services as 'Other'
            other_services = [s for s in pos_chart_data.index if s not in top_services]
            if other_services:
                other_pos_sum = pos_chart_data.loc[other_services].sum()
                top_pos_data.loc['Other'] = other_pos_sum
            
            pos_chart_data = top_pos_data
        
        # Keep all negative services (refunds) separate - don't group them
        # Only keep rows with at least one negative value
        services_with_negatives = []
        for service, row in neg_chart_data.iterrows():
            if (row < 0).any():
                services_with_negatives.append(service)
        
        neg_chart_data = neg_chart_data.loc[services_with_negatives] if services_with_negatives else pd.DataFrame()
        
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
                    # Convert from MM/YYYY to Month YYYY format
                    month_num = int(parts[1])
                    year = parts[0]
                    month_name = datetime.date(2000, month_num, 1).strftime('%b')
                    month_labels.append(f"{month_name} {year}")
                else:
                    month_labels.append(month)
            else:
                month_labels.append(month)
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Add summary statistics at the top
        fig.text(0.5, 0.95, f'AWS Monthly Cost by Service - {account_name}{date_range_text}', 
                ha='center', fontsize=16, weight='bold')
        
        # Create a top stats row with 3 columns
        stats_y_pos = 0.9
        # Total Cost
        fig.text(0.17, stats_y_pos, f"Total Cost\n${total_cost:,.2f}", 
                ha='center', fontsize=12, weight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
        # Monthly Average
        fig.text(0.5, stats_y_pos, f"Monthly Average\n${monthly_avg:,.2f}", 
                ha='center', fontsize=12, weight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
        # Service Count
        fig.text(0.83, stats_y_pos, f"Unique Services\n{unique_services}", 
                ha='center', fontsize=12, weight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
        
        # Adjust the main plot position to make room for the stats
        plt.subplots_adjust(top=0.85)
        
        # Create the stacked bar chart
        ax = chart_data.T.plot(kind='bar', stacked=True, figsize=(14, 8), color=colors)
        
        # Add debugging for refund values
        print("\nDebugging service values:")
        for service in chart_data.index:
            if service.startswith('Refund'):
                print(f"Refund service: {service}")
                print(f"Values: {chart_data.loc[service].values}")
                
        # Add labels inside each segment of the stacked bar
        bottom_values = np.zeros(len(chart_data.columns))
        for i, service in enumerate(chart_data.index):
            for j, month in enumerate(chart_data.columns):
                cost = chart_data.loc[service, month]
                
                # Special handling for negative values (refunds)
                if cost < 0:
                    # Draw a red label below the axis for refunds
                    ax.text(j, bottom_values[j] + cost/2, f'${int(cost):,}', 
                            ha='center', va='center', fontsize=9, color='white',
                            weight='bold', bbox=dict(facecolor='red', alpha=0.7, pad=1))
                    # Don't add this to the bottom values since it's negative
                    continue
                    
                # Only add label if the segment is large enough to be visible
                if cost > max(chart_data.T.sum(axis=1)) * 0.05:  # 5% threshold for visibility
                    # Calculate the position (middle of the segment)
                    y_pos = bottom_values[j] + cost/2
                    # Choose text color based on segment darkness
                    text_color = 'white' if cost > max(chart_data.T.sum(axis=1)) * 0.1 else 'black'
                    ax.text(j, y_pos, f'${int(cost):,}', 
                            ha='center', va='center', fontsize=9, color=text_color)
                bottom_values[j] += cost
        
        # Add labels inside each segment of the stacked bar (for positive values)
        if not pos_chart_data.empty:
            bottom_values = np.zeros(len(months))
            for service in pos_chart_data.index:
                for j, month in enumerate(months):
                    cost = pos_chart_data.loc[service, month]
                    # Only add label if the segment is large enough to be visible
                    if cost > max(pos_chart_data.sum()) * 0.05:  # 5% threshold for visibility
                        # Calculate the position (middle of the segment)
                        y_pos = bottom_values[j] + cost/2
                        # Choose text color based on segment darkness
                        text_color = 'white' if cost > max(pos_chart_data.sum()) * 0.1 else 'black'
                        ax.text(j, y_pos, f'${int(cost):,}', 
                                ha='center', va='center', fontsize=9, color=text_color)
                    bottom_values[j] += cost
        
        # Add labels for negative values
        if not neg_chart_data.empty:
            bottom = np.zeros(len(months))
            for service in neg_chart_data.index:
                for j, month in enumerate(months):
                    cost = neg_chart_data.loc[service, month]
                    if cost < 0:  # Only process negative values
                        # Position the label in the middle of the negative segment
                        y_pos = bottom[j] + cost/2
                        ax.text(j, y_pos, f'${int(cost):,}', 
                                ha='center', va='center', fontsize=9, color='white',
                                weight='bold')
                    bottom[j] += cost
        
        # Add total labels on top of each bar
        for i, month in enumerate(months):
            pos_total = pos_chart_data[month].sum()
            neg_total = neg_chart_data[month].sum() if not neg_chart_data.empty else 0
            total = pos_total + neg_total
            
            # Position above the highest positive value
            ax.text(i, pos_total + (max(pos_chart_data.sum()) * 0.02), 
                   f'${int(total):,}', ha='center', fontsize=10, fontweight='bold')
        
        # Format the chart
        ax.set_ylabel('Cost (USD)', fontsize=12)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_xticklabels(month_labels, rotation=0)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add commas and dollar signs to y-axis
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x:,.0f}'))
        
        # Ensure y-axis extends below zero for negative values
        if not neg_chart_data.empty:
            y_min = neg_chart_data.values.min() * 1.1  # Add 10% padding
            y_max = ax.get_ylim()[1]
            ax.set_ylim(y_min, y_max)
        
        # Move legend to bottom and make it horizontal
        handles, labels = ax.get_legend_handles_labels()
        
        # If we have too many services, limit the legend to the most important ones
        if len(labels) > 12:
            # Keep top positive services and any refunds
            keep_services = list(pos_chart_data.index[:7])  # Top 7 positive
            if 'Other' in pos_chart_data.index:
                keep_services.append('Other')
            
            # Add any refund services
            for service in neg_chart_data.index:
                keep_services.append(service)
            
            # Filter the handles and labels
            filtered_handles = []
            filtered_labels = []
            for i, label in enumerate(labels):
                if label in keep_services or 'Refund' in label:
                    filtered_handles.append(handles[i])
                    filtered_labels.append(label)
            
            handles, labels = filtered_handles, filtered_labels
        
        # Place the legend at the bottom
        ax.legend(handles, labels, title='Services', loc='upper center', 
                  bbox_to_anchor=(0.5, -0.15), ncol=min(len(labels), 4), 
                  frameon=True, fontsize=10)
        
        # Format date range for filenames
        if start_date and end_date:
            date_range_suffix = f"_{start_date.strftime('%Y%m')}_to_{end_date.strftime('%Y%m')}"
        else:
            date_range_suffix = ""
        
        # Adjust layout and save
        plt.subplots_adjust(bottom=0.2)  # Make room for the legend at the bottom
        plt.tight_layout(rect=[0, 0.05, 1, 0.85])  # Adjust layout to account for the stats at top and legend at bottom
        chart_file = os.path.join(output_dir, f'aws_cost_report_{account}{date_range_suffix}.png')
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"Chart saved to: {chart_file}")
        
        # Also save the account data to Excel
        account_excel = os.path.join(output_dir, f'aws_cost_report_{account}{date_range_suffix}.xlsx')
        with pd.ExcelWriter(account_excel) as writer:
            excel_pivot.to_excel(writer, sheet_name='Services')
            
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

def create_summary_report(df, output_dir, date_range_text, start_date=None, end_date=None):
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
    
    # Reorder columns to put Total after Service and before the months
    # First, get all columns except 'Total'
    date_columns = [col for col in pivot.columns if col != 'Total']
    
    # Sort date columns chronologically
    date_columns.sort()
    
    # Create new column order with Total second
    ordered_columns = ['Total'] + date_columns
    
    # Reorder the pivot table
    pivot = pivot[ordered_columns]
    
    # Create a copy with formatted month names for Excel export
    excel_pivot = pivot.copy()
    
    # Format column names for better readability in Excel
    column_mapping = {'Total': 'Total'}
    for col in date_columns:
        if '-' in col:
            parts = col.split('-')
            if len(parts) >= 2:
                # Convert from YYYY-MM-DD to Month YYYY format
                month_num = int(parts[1])
                year = parts[0]
                month_name = datetime.date(2000, month_num, 1).strftime('%B')
                column_mapping[col] = f"{month_name} {year}"
    
    # Rename columns in the Excel export copy
    excel_pivot = excel_pivot.rename(columns=column_mapping)
    
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
                # Convert from MM/YYYY to Month YYYY format
                month_num = int(parts[1])
                year = parts[0]
                month_name = datetime.date(2000, month_num, 1).strftime('%b')
                month_labels.append(f"{month_name} {year}")
            else:
                month_labels.append(month)
        else:
            month_labels.append(month)
    
    # Top services by cost
    top_services = df.groupby('Service')['Cost'].sum().sort_values(ascending=False).head(5)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(14, 10))
    
    # Add summary title and statistics at the top
    fig.text(0.5, 0.95, f'AWS Monthly Cost Summary{date_range_text}', 
            ha='center', fontsize=16, weight='bold')
    
    # Create a top stats row with 3 columns
    stats_y_pos = 0.9
    # Total Cost
    fig.text(0.17, stats_y_pos, f"Total Cost\n${total_cost:,.2f}", 
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
    # Monthly Average
    fig.text(0.5, stats_y_pos, f"Monthly Average\n${monthly_avg:,.2f}", 
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
    # Account and Service Count
    fig.text(0.83, stats_y_pos, f"Accounts: {num_accounts}\nServices: {unique_services}", 
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
    
    # Define grid for multiple charts with adjusted positioning
    gs = fig.add_gridspec(2, 2, height_ratios=[2, 1], top=0.85)
    
    # Main chart - Monthly cost by account
    ax1 = fig.add_subplot(gs[0, :])
    chart_data = pivot.drop('Total', axis=1)
    
    # Ensure chronological order for chart data
    chart_data = chart_data[sorted(chart_data.columns)]
    
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
    ax1.set_ylabel('Cost (USD)', fontsize=12)
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_xticklabels(month_labels, rotation=0)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'${x:,.0f}'))
    
    # Move legend to bottom and make it horizontal
    ax1.legend(title='Accounts', loc='upper center', bbox_to_anchor=(0.5, -0.15), 
              ncol=min(len(chart_data.index), 4), frameon=True, fontsize=10)
    
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
    
    # Format date range for filenames
    if start_date and end_date:
        date_range_suffix = f"_{start_date.strftime('%Y%m')}_to_{end_date.strftime('%Y%m')}"
    else:
        date_range_suffix = ""
    
    # Adjust layout and save
    plt.subplots_adjust(bottom=0.2)  # Make room for the legend at the bottom
    plt.tight_layout(rect=[0, 0.05, 1, 0.85])  # Adjust layout to account for the stats at top and legend at bottom
    chart_file = os.path.join(output_dir, f'aws_cost_summary{date_range_suffix}.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"Summary chart saved to: {chart_file}")
    
    # Save summary data to Excel
    summary_excel = os.path.join(output_dir, f'aws_cost_summary{date_range_suffix}.xlsx')
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
        
        # Add a clarification about the dates in the report
        print("\nNote about AWS Cost Explorer dates:")
        print("AWS Cost Explorer reports billing data by month starting on the 1st of each month.")
        print("For example, 'November 2024' represents costs from November 1st to November 30th.")
        print("These dates align with AWS's billing cycle, not when the data was retrieved.\n")
        
    except Exception as e:
        print(f"Error creating reports: {str(e)}")
        
        # For debugging
        import traceback
        with open('error_log.txt', 'w') as f:
            f.write(traceback.format_exc())
        
        print("Error details saved to 'error_log.txt'")

if __name__ == "__main__":
    main()