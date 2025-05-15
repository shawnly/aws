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
SERVICE_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
]

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
        
        # Check if end date is in the future
        if end_date > datetime.date.today():
            print(f"Warning: End date {end_date_str} is in the future.")
            print("AWS Cost Explorer may not have complete data for the current month.")
            
        return start_date, end_date
    
    except ValueError as e:
        print(f"Error with date format: {e}")
        print("Please use YYYY-MM-DD format")
        return None, None

def get_aws_cost_data(start_date, end_date):
    """Fetch AWS Cost Explorer data for the specified date range"""
    print("Fetching AWS Cost Explorer data...")
    
    try:
        # Create a Cost Explorer client
        ce_client = boto3.client('ce')
        
        # Format dates for AWS API
        # Make sure end date is at the end of the month to include all data
        if end_date.day != end_date.replace(day=28).day:  # Not already end of month
            # Set to the first day of next month, then subtract one day
            next_month = end_date.replace(day=1) + relativedelta(months=1)
            end_date = next_month - datetime.timedelta(days=1)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"Retrieving cost data from {start_date_str} to {end_date_str}...")
        
        # First try to get cost by RECORD_TYPE to find refunds explicitly
        try:
            print("Querying by RECORD_TYPE dimension...")
            record_response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date_str,
                    'End': end_date_str
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'RECORD_TYPE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'LINKED_ACCOUNT'
                    }
                ]
            )
            
            # Process RECORD_TYPE data to find refunds
            refund_data = []
            for result in record_response['ResultsByTime']:
                period = result['TimePeriod']['Start']
                end = result['TimePeriod']['End']
                
                for group in result['Groups']:
                    record_type, account = group['Keys']
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    unit = group['Metrics']['UnblendedCost']['Unit']
                    
                    # Check if this is a refund record
                    if record_type.lower() in ('refund', 'credit'):
                        print(f"  Found record_type={record_type}, cost=${cost:.2f} in period {period}")
                        refund_data.append({
                            'Service': f"Refund: {record_type}",
                            'Account': account,
                            'Period': period,
                            'Cost': cost,
                            'Unit': unit
                        })
            
            print(f"Found {len(refund_data)} refund entries from RECORD_TYPE query.")
        
        except Exception as e:
            print(f"RECORD_TYPE query failed: {str(e)}")
            refund_data = []
        
        # Then try to get all cost data by service
        print("Retrieving costs by SERVICE and LINKED_ACCOUNT...")
        service_response = ce_client.get_cost_and_usage(
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
        
        # Process service data
        service_data = []
        service_refund_count = 0
        
        for result in service_response['ResultsByTime']:
            period = result['TimePeriod']['Start']
            end = result['TimePeriod']['End']
            
            # For debugging - show the time periods we're getting from AWS
            print(f"Processing data for period: {period} to {end}")
            
            for group in result['Groups']:
                service, account = group['Keys']
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                unit = group['Metrics']['UnblendedCost']['Unit']
                
                # Check if this is likely a refund based on name or negative cost
                is_refund = (cost < 0 or 
                             'refund' in service.lower() or 
                             'credit' in service.lower())
                
                if is_refund:
                    service_refund_count += 1
                    print(f"  Found service refund: {service}, ${cost:.2f} in period {period}")
                    
                    # For refunds, mark them clearly
                    service_name = f"Refund: {service}" if not service.startswith("Refund") else service
                else:
                    service_name = service
                
                service_data.append({
                    'Service': service_name,
                    'Account': account,
                    'Period': period,
                    'Cost': cost,
                    'Unit': unit
                })
        
        print(f"Found {service_refund_count} refund entries from SERVICE query.")
        
        # Combine both data sources
        all_data = refund_data + service_data
        
        # Handle empty results
        if not all_data:
            print("No cost data found for the specified period.")
            return generate_mock_data(start_date, end_date)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        # Remove any duplicates (might have been added by both queries)
        df = df.drop_duplicates()
        
        print(f"Combined data has {len(df)} rows for {len(df['Service'].unique())} services across {len(df['Account'].unique())} accounts.")
        
        # Additional check for refunds in the raw data
        refund_check = df[(df['Cost'] < 0) | 
                          (df['Service'].str.contains('refund', case=False, na=False)) |
                          (df['Service'].str.contains('credit', case=False, na=False))]
        
        if not refund_check.empty:
            print("\nRefunds/credits found in combined data:")
            for _, row in refund_check.iterrows():
                print(f"  {row['Period']}: {row['Service']} = ${row['Cost']:.2f} for account {row['Account']}")
            print(f"Total refund entries: {len(refund_check)}")
        else:
            print("\nNo refunds or credits found in the retrieved data.")
        
        # Count refunds by month
        if not refund_check.empty:
            refund_by_month = refund_check.groupby('Period')['Cost'].agg(['count', 'sum'])
            print("\nRefund totals by month:")
            for period, row in refund_by_month.iterrows():
                count = row['count']
                total = row['sum']
                print(f"  {period}: {count} refunds totaling ${total:.2f}")
                
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
    
    # Create mock services
    services = [
        'Amazon Elastic Compute Cloud',
        'Amazon Simple Storage Service',
        'Amazon RDS Service',
        'AWS Lambda',
        'Amazon DynamoDB',
        'AWS CloudTrail',
        'Amazon CloudWatch',
        'Amazon Route 53',
        'AWS Key Management Service',
        'Amazon CloudFront'
    ]
    
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
                    'Unit': 'USD'
                })
    
    return pd.DataFrame(cost_data)

def create_cost_dashboard(df, output_dir='aws_cost_report', 
                         start_date=None, end_date=None, account_id=None):
    """Create monthly cost charts by service"""
    
    # Create base output directory
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
    
    # Set up account-specific directory and labels
    if account_id == "summary":
        # For summary report
        account_label = "All Accounts"
        report_dir = os.path.join(output_dir, "summary")
    elif account_id:
        # For individual account reports
        account_label = f"Account {account_id}"
        report_dir = os.path.join(output_dir, account_id)
    else:
        # Fallback (shouldn't happen)
        account_label = "AWS"
        report_dir = output_dir
    
    # Create account-specific directory
    os.makedirs(report_dir, exist_ok=True)
    
    # Save raw data to Excel
    excel_path = os.path.join(report_dir, f'aws_cost_data{date_range_suffix}.xlsx')
    df.to_excel(excel_path, index=False)
    print(f"Raw data saved to: {excel_path}")
    
    # Print unique service names for debugging
    print("\nUnique service names in data:")
    for service in sorted(df['Service'].unique()):
        print(f"  - {service}")
    
    # Check for refund entries
    refund_entries = df[(df['Cost'] < 0) | 
                       (df['Service'].str.contains('refund', case=False, na=False)) |
                       (df['Service'].str.contains('credit', case=False, na=False))]
    
    if not refund_entries.empty:
        print(f"\nRefund entries for {account_label}:")
        
        # Group by month to count refunds per month
        refund_by_month = refund_entries.groupby('Period')['Cost'].agg(['count', 'sum'])
        for period, row in refund_by_month.iterrows():
            count = row['count']
            total = row['sum']
            print(f"  - {period}: {count} refunds totaling ${total:.2f}")
    else:
        print("\nNo refund entries found in the data")
    
    # Create pivot table
    pivot = df.pivot_table(
        index='Service',
        columns='Period',
        values='Cost',
        aggfunc='sum'
    ).fillna(0)
    
    # Sort by total cost (absolute value to account for refunds)
    pivot['Total'] = pivot.sum(axis=1)
    pivot['AbsTotal'] = pivot['Total'].abs()  # Use absolute total for sorting
    pivot = pivot.sort_values('AbsTotal', ascending=False)
    pivot = pivot.drop('AbsTotal', axis=1)  # Remove the abs column after sorting
    
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
    positive_data = pd.DataFrame(index=pivot.index, columns=date_columns)
    negative_data = pd.DataFrame(index=pivot.index, columns=date_columns)
    
    # Zero out negative values in positive data and vice versa
    for col in date_columns:
        for idx in pivot.index:
            if col in pivot.columns:  # Check if column exists
                val = pivot.loc[idx, col] if idx in pivot.index and col in pivot.columns else 0
                positive_data.loc[idx, col] = max(val, 0)  # Only positive values
                negative_data.loc[idx, col] = min(val, 0)  # Only negative values
    
    # For debugging - print all negative values
    print("\nNegative values in the pivot table:")
    for col in date_columns:
        for idx in pivot.index:
            if col in pivot.columns and pivot.loc[idx, col] < 0:
                print(f"  {idx} in {col}: ${pivot.loc[idx, col]:.2f}")
    
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
    pos_chart_data = positive_data.copy()
    neg_chart_data = negative_data.copy()
    
    # Get top services for positive data, group the rest as 'Other'
    top_n_services = 8
    if len(pos_chart_data) > top_n_services:
        # Sort by absolute value to get top services by magnitude
        # First ensure all values are numeric
        service_totals = pos_chart_data.sum(axis=1)
        service_totals = pd.to_numeric(service_totals, errors='coerce').fillna(0).abs()
        
        # Debug
        print("\nService totals for sorting:")
        for service, total in service_totals.items():
            print(f"  {service}: {total}")
        
        # Get top services and handle empty results gracefully
        if not service_totals.empty:
            # Sort by value and take top N
            top_services = service_totals.sort_values(ascending=False).head(top_n_services).index.tolist()
        else:
            top_services = []
            
        print(f"Selected top services: {top_services}")
        
        # Create copies with only top services
        if top_services:
            top_pos_data = pos_chart_data.loc[top_services].copy()
            
            # Aggregate remaining services as 'Other'
            other_services = [s for s in pos_chart_data.index if s not in top_services]
            if other_services:
                other_pos_sum = pos_chart_data.loc[other_services].sum()
                top_pos_data.loc['Other'] = other_pos_sum
            
            pos_chart_data = top_pos_data
        # If no top services, keep original data
    
    # For debug - count how many services have negative values
    neg_service_count = 0
    for service in pivot.index:
        has_neg = False
        for col in date_columns:
            if service in pivot.index and col in pivot.columns and pivot.loc[service, col] < 0:
                has_neg = True
                break
        if has_neg:
            neg_service_count += 1
    
    print(f"Found {neg_service_count} services with negative values")
    
    # List all services with negative values
    print("Services with negative values:")
    for service in pivot.index:
        for col in date_columns:
            if service in pivot.index and col in pivot.columns and pivot.loc[service, col] < 0:
                print(f"  {service} has ${pivot.loc[service, col]:.2f} in {col}")
                break  # Just print the first negative value for each service
    
    # Keep all negative services (refunds) separate - don't group them
    # Only keep rows with at least one negative value
    services_with_negatives = []
    for service, row in neg_chart_data.iterrows():
        if (row < 0).any():
            services_with_negatives.append(service)
    
    print(f"Found {len(services_with_negatives)} services with negative values for chart")
    print("Services with negatives for chart:")
    for service in services_with_negatives:
        print(f"  {service}")
    
    neg_chart_data = neg_chart_data.loc[services_with_negatives] if services_with_negatives else pd.DataFrame()
    
    # Format month labels
    months = sorted(pos_chart_data.columns)
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
    fig.text(0.5, 0.95, f'AWS Monthly Cost by Service - {account_label}{date_range_text}', 
            ha='center', fontsize=16, weight='bold')
    
    # Create a top stats row with 3 columns
    stats_y_pos = 0.9
    # Total Cost
    fig.text(0.17, stats_y_pos, f"Total Cost: ${total_cost:,.2f}", 
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
    # Monthly Average
    fig.text(0.5, stats_y_pos, f"Monthly Average: ${monthly_avg:,.2f}", 
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
    # Service Count
    fig.text(0.83, stats_y_pos, f"Unique Services: {unique_services}", 
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', alpha=0.7))
    
    # Adjust the main plot position to make room for the stats
    plt.subplots_adjust(top=0.85)
    
    # Assign colors to services
    service_colors = {}
    
    # Assign colors to positive data services
    for i, service in enumerate(pos_chart_data.index):
        if service == 'Other':
            service_colors[service] = '#CCCCCC'  # Gray for Other
        else:
            # Use modulo to cycle through colors if we have more services than colors
            color_idx = i % len(SERVICE_COLORS)
            service_colors[service] = SERVICE_COLORS[color_idx]
    
    # Assign red color variations to negative data services
    red_colors = ['#FF0000', '#CC0000', '#990000', '#660000']
    for i, service in enumerate(neg_chart_data.index):
        color_idx = i % len(red_colors)
        service_colors[service] = red_colors[color_idx]
    
    # Plot positive data
    if not pos_chart_data.empty:
        pos_chart_data.T.plot(kind='bar', stacked=True, ax=ax, 
                              color=[service_colors[s] for s in pos_chart_data.index])
    
    # Plot negative data (if any)
    if not neg_chart_data.empty:
        # Convert to numeric and ensure it's a proper numpy array of floats
        bottom = np.zeros(len(months))
        for service in neg_chart_data.index:
            # Convert values to numeric, ensuring they're floats
            values = neg_chart_data.loc[service].values
            numeric_values = np.array([float(val) if isinstance(val, (int, float)) else 0.0 for val in values])
            
            # Debug information
            print(f"Plotting negative values for {service}: {numeric_values}")
            
            # Create a bar plot for this service
            ax.bar(range(len(months)), numeric_values, bottom=bottom, color=service_colors[service], 
                   label=f"Refund: {service}")
            
            # Update bottom position - make sure it's numeric
            bottom = bottom + numeric_values  # Element-wise addition of numpy arrays
    
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
                # Get the value and convert it safely to float
                try:
                    cost_val = neg_chart_data.loc[service, month]
                    cost = float(cost_val) if isinstance(cost_val, (int, float)) else 0.0
                except (ValueError, TypeError):
                    cost = 0.0
                
                if cost < 0:  # Only process negative values
                    # Position the label in the middle of the negative segment
                    y_pos = bottom[j] + cost/2
                    ax.text(j, y_pos, f'${int(cost):,}', 
                            ha='center', va='center', fontsize=9, color='white',
                            weight='bold')
                
                # Update the bottom - ensure it's numeric
                bottom[j] += cost
    
    # Handle the case where a month has only negative values (all refunds)
    if not pos_chart_data.empty:
        max_pos = max(pos_chart_data.sum())
    else:
        max_pos = 1  # Default if no positive values
    
    # Add total labels on top of each bar
    for i, month in enumerate(months):
        pos_total = pos_chart_data[month].sum() if not pos_chart_data.empty else 0
        neg_total = neg_chart_data[month].sum() if not neg_chart_data.empty else 0
        total = pos_total + neg_total
        
        # Position above the highest positive value or at a minimum height if all negative
        if pos_total > 0:
            label_y = pos_total + (max_pos * 0.02)
        else:
            label_y = max_pos * 0.05  # Position slightly above zero
        
        ax.text(i, label_y, f'${int(total):,}', 
               ha='center', fontsize=10, fontweight='bold')
    
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
    
    # Adjust layout and save
    plt.subplots_adjust(bottom=0.2)  # Make room for the legend at the bottom
    plt.tight_layout(rect=[0, 0.05, 1, 0.85])  # Adjust layout to account for the stats at top and legend at bottom
    
    # Save the chart
    chart_file = os.path.join(report_dir, f'aws_cost_report{date_range_suffix}.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {chart_file}")
    
    # Also save the data to Excel
    excel_file = os.path.join(report_dir, f'aws_cost_report{date_range_suffix}.xlsx')
    with pd.ExcelWriter(excel_file) as writer:
        excel_pivot.to_excel(writer, sheet_name='Services')
        
        # Create a summary sheet
        summary_df = pd.DataFrame({
            'Metric': ['Total Cost', 'Monthly Average', 'Unique Services'],
            'Value': [f"${total_cost:,.2f}", f"${monthly_avg:,.2f}", unique_services]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Raw data
        df.to_excel(writer, sheet_name='Raw_Data', index=False)
    
    print(f"Data saved to: {excel_file}")
    plt.close()

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Validate dates
    start_date, end_date = validate_dates(args.start_date, args.end_date)
    if not start_date or not end_date:
        print("Invalid date range. Exiting.")
        return
    
    BASE_OUTPUT_DIR = 'aws_cost_report'
    
    try:
        if args.use_mock:
            # Use mock data for testing
            print("Using mock data as requested...")
            df = generate_mock_data(start_date, end_date)
        else:
            # Get real AWS cost data
            df = get_aws_cost_data(start_date, end_date)
        
        # Get unique account IDs
        accounts = df['Account'].unique()
        
        # Create individual reports for each account
        for account in accounts:
            print(f"\nCreating report for account: {account}")
            # Filter data for this account
            account_df = df[df['Account'] == account]
            
            # Create dashboard for this account
            create_cost_dashboard(account_df, BASE_OUTPUT_DIR, start_date, end_date, account)
        
        # Create a summary report across all accounts
        print("\nCreating summary report across all accounts...")
        create_cost_dashboard(df, BASE_OUTPUT_DIR, start_date, end_date, "summary")
        
        print("\nAll reports created successfully!")
        print(f"Files are available in the '{BASE_OUTPUT_DIR}' directory, organized by account")
        
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
