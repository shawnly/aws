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
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"Retrieving cost data from {start_date_str} to {end_date_str}...")
        
        # Basic cost query by service
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
                }
            ]
        )
        
        # Process data 
        cost_data = []
        for result in response['ResultsByTime']:
            period = result['TimePeriod']['Start']
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                unit = group['Metrics']['UnblendedCost']['Unit']
                
                cost_data.append({
                    'Service': service,
                    'Period': period,
                    'Cost': cost,
                    'Unit': unit
                })
        
        # Handle empty results
        if not cost_data:
            print("No cost data found for the specified period.")
            return generate_mock_data(start_date, end_date)
        
        # Convert to DataFrame
        df = pd.DataFrame(cost_data)
        
        print(f"Retrieved data for {len(df['Service'].unique())} services.")
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
    
    # Generate data
    cost_data = []
    
    # Base costs for services (to make data realistic)
    service_base_costs = {
        service: random.uniform(100, 2000) for service in services if not service.startswith("Refund")
    }
    
    # The refund will be a negative value (credit)
    service_base_costs["Refund: Service Credits"] = -random.uniform(200, 500)
    
    for date in date_list:
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
                'Period': date,
                'Cost': round(cost, 2),
                'Unit': 'USD'
            })
    
    return pd.DataFrame(cost_data)

def create_cost_dashboard(df, output_dir='aws_cost_report', 
                         start_date=None, end_date=None):
    """Create monthly cost charts by service"""
    
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
    
    # Get AWS account ID if available
    try:
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        print(f"AWS Account ID: {account_id}")
        account_suffix = f"_{account_id}"
    except Exception as e:
        print("Could not determine AWS Account ID. Using generic filenames.")
        account_id = "aws"
        account_suffix = ""
    
    # Save raw data to Excel
    excel_path = os.path.join(output_dir, f'aws_cost_data{account_suffix}{date_range_suffix}.xlsx')
    df.to_excel(excel_path, index=False)
    print(f"Raw data saved to: {excel_path}")
    
    # Print unique service names for debugging
    print("\nUnique service names in data:")
    for service in sorted(df['Service'].unique()):
        print(f"  - {service}")
    
    # Check for refund entries
    refund_entries = df[(df['Cost'] < 0) | (df['Service'].str.contains('refund|credit', case=False, na=False))]
    if not refund_entries.empty:
        print("\nRefund entries found:")
        for _, row in refund_entries.head(5).iterrows():
            print(f"  - {row['Service']}: ${row['Cost']:.2f} in {row['Period']}")
        if len(refund_entries) > 5:
            print(f"  ... and {len(refund_entries) - 5} more entries")
    else:
        print("\nNo refund entries found in the data")
    
    # Create pivot table
    pivot = df.pivot_table(
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
    fig.text(0.5, 0.95, f'AWS Monthly Cost by Service - {account_id}{date_range_text}', 
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
        bottom = np.zeros(len(months))  # Start at the bottom of the chart
        for service in neg_chart_data.index:
            values = neg_chart_data.loc[service].values
            ax.bar(range(len(months)), values, bottom=bottom, color=service_colors[service], 
                   label=f"Refund: {service}")
            bottom += values  # Update the bottom position for the next series
    
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
    
    # Adjust layout and save
    plt.subplots_adjust(bottom=0.2)  # Make room for the legend at the bottom
    plt.tight_layout(rect=[0, 0.05, 1, 0.85])  # Adjust layout to account for the stats at top and legend at bottom
    
    # Save the chart
    chart_file = os.path.join(output_dir, f'aws_cost_report{account_suffix}{date_range_suffix}.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {chart_file}")
    
    # Also save the data to Excel
    excel_file = os.path.join(output_dir, f'aws_cost_report{account_suffix}{date_range_suffix}.xlsx')
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
    
    OUTPUT_DIR = 'aws_cost_report'
    
    try:
        if args.use_mock:
            # Use mock data for testing
            print("Using mock data as requested...")
            df = generate_mock_data(start_date, end_date)
        else:
            # Get real AWS cost data
            df = get_aws_cost_data(start_date, end_date)
        
        # Create the dashboard
        create_cost_dashboard(df, OUTPUT_DIR, start_date, end_date)
        
        print("Report created successfully!")
        print(f"Files are available in the '{OUTPUT_DIR}' directory")
        
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
