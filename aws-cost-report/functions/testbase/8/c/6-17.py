import boto3
import pandas as pd
import os
from datetime import datetime, timedelta
import argparse
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import seaborn as sns
import numpy as np
from collections import defaultdict

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

def create_cost_visualization(df, title, account_id, start_date, end_date, is_organization=False):
    """Create AWS Cost Explorer style visualization with refunds and cost amounts on segments"""
    # Set up the style to look like AWS Cost Explorer
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Prepare data for visualization
    if is_organization:
        cost_column = 'Total Amortized Cost ($)'
        service_column = 'Service Name'
        month_column = 'Month'
    else:
        cost_column = 'Amortized Cost ($)'
        service_column = 'Service Name'
        # Create month column from start date
        df['Month'] = pd.to_datetime(df['Start Date']).dt.strftime('%Y-%m')
        month_column = 'Month'
    
    # Separate positive costs and refunds
    df_positive = df[df[cost_column] >= 0].copy()
    df_refunds = df[df[cost_column] < 0].copy()
    
    # Group positive costs by month and service
    monthly_costs = df_positive.groupby([month_column, service_column])[cost_column].sum().reset_index()
    
    # Group refunds by month (aggregate all refunds together)
    monthly_refunds = df_refunds.groupby(month_column)[cost_column].sum().reset_index()
    monthly_refunds['Service_Category'] = 'Refunds/Credits'
    
    # Get top 9 services overall for positive costs
    top_services = df_positive.groupby(service_column)[cost_column].sum().nlargest(9).index.tolist()
    
    # Create "Others" category for remaining services
    monthly_costs['Service_Category'] = monthly_costs[service_column].apply(
        lambda x: x if x in top_services else 'Others'
    )
    
    # Regroup with the new category
    monthly_summary = monthly_costs.groupby([month_column, 'Service_Category'])[cost_column].sum().reset_index()
    
    # Pivot the data for stacked bar chart
    pivot_data = monthly_summary.pivot(index=month_column, columns='Service_Category', values=cost_column).fillna(0)
    
    # Sort columns by total cost (descending), but keep 'Others' at the end
    column_totals = pivot_data.sum().sort_values(ascending=False)
    if 'Others' in column_totals.index:
        others_total = column_totals['Others']
        column_totals = column_totals.drop('Others')
        column_totals['Others'] = others_total
    
    pivot_data = pivot_data[column_totals.index]
    
    # Create refunds pivot data
    refunds_pivot = monthly_refunds.set_index(month_column)[cost_column] if not monthly_refunds.empty else pd.Series(dtype=float)
    
    # Ensure all months are represented in refunds data
    all_months = pivot_data.index
    refunds_data = pd.Series(index=all_months, dtype=float).fillna(0)
    for month in refunds_pivot.index:
        if month in refunds_data.index:
            refunds_data[month] = refunds_pivot[month]
    
    # Create the figure with subplots for table and chart
    fig = plt.figure(figsize=(14, 10))
    
    # Create table subplot (positioned between title and chart)
    table_ax = plt.subplot2grid((10, 1), (1, 0), rowspan=1)
    table_ax.axis('off')  # Hide axes for table
    
    # Create main chart subplot (takes most of the space below table)
    ax = plt.subplot2grid((10, 1), (3, 0), rowspan=7)
    
    # Calculate summary statistics for the table
    total_cost = df[cost_column].sum()
    
    # Calculate number of months in the date range
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    months_diff = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    if months_diff == 0:
        months_diff = 1  # At least 1 month
    
    average_monthly_cost = total_cost / months_diff
    
    # Count total unique services (regardless of cost)
    service_count = len(df[service_column].unique())
    
    # Table data
    table_data = [
        ['Total Cost', 'Average Monthly Cost', 'Total Services'],
        [f'${total_cost:,.2f}', f'${average_monthly_cost:,.2f}', f'{service_count}']
    ]
    
    # Create table with same width as chart
    table = table_ax.table(cellText=table_data, 
                          cellLoc='center',
                          loc='center',
                          bbox=[0, 0.1, 1, 0.8])  # Full width to match chart
    
    # Style the table with light colors
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.5)
    
    # Style header row (first row) - light blue
    for i in range(3):
        table[(0, i)].set_facecolor('#E8F4FD')  # Very light blue
        table[(0, i)].set_text_props(weight='bold', color='#2C5282')  # Dark blue text
        table[(0, i)].set_edgecolor('#D1E7F5')  # Light blue border
    
    # Style data row (second row) - very light gray
    for i in range(3):
        table[(1, i)].set_facecolor('#F8F9FA')  # Very light gray
        table[(1, i)].set_text_props(weight='bold', color='#2D3748')  # Dark gray text
        table[(1, i)].set_edgecolor('#E2E8F0')  # Light gray border
    
    # Define colors - AWS-like color scheme
    colors = [
        '#FF9900',  # AWS Orange
        '#146EB4',  # AWS Blue
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Light Blue
        '#96CEB4',  # Green
        '#FECA57',  # Yellow
        '#FF9FF3',  # Pink
        '#54A0FF',  # Blue
        '#C7ECEE'   # Light Gray for Others
    ]
    
    # Create stacked bar chart for positive costs
    bottom = np.zeros(len(pivot_data.index))
    bars = []
    
    for i, service in enumerate(pivot_data.columns):
        color = colors[i % len(colors)]
        service_costs = pivot_data[service].values
        bars.append(ax.bar(range(len(pivot_data.index)), service_costs, bottom=bottom, 
                          label=service, color=color, alpha=0.8))
        
        # Add cost amounts on each segment - SIMPLIFIED APPROACH
        for j, cost in enumerate(service_costs):
            if cost > 50:  # Show amounts for costs over $50
                segment_center = bottom[j] + cost / 2
                
                # Use white text for most segments, black for very light colors
                if service in ['Amazon Elastic Load Balancing', 'Amazon EC2 Container Registry (ECR)', 'Others']:
                    text_color = 'black'
                    text_effects = [path_effects.withStroke(linewidth=3, foreground='white')]
                else:
                    text_color = 'white'
                    text_effects = [path_effects.withStroke(linewidth=2, foreground='black')]
                
                ax.text(j, segment_center, f'${cost:,.2f}', 
                       ha='center', va='center', fontsize=10, 
                       fontweight='bold', color=text_color,
                       path_effects=text_effects)
        
        bottom += service_costs
    
    # Add refunds as negative bars (green)
    if not refunds_data.empty and refunds_data.abs().sum() > 0:
        refund_bars = ax.bar(range(len(refunds_data.index)), refunds_data.values, 
                            label='Refunds/Credits', color='#00D084', alpha=0.8)
        
        # Add refund amounts on the negative bars
        for j, refund in enumerate(refunds_data.values):
            if refund < 0:  # Only show label if there's actual refund
                ax.text(j, refund / 2, f'-${abs(refund):,.2f}', 
                       ha='center', va='center', fontsize=8, 
                       fontweight='bold', color='white')
    
    # Calculate net total for each month (positive costs + refunds)
    net_totals = pivot_data.sum(axis=1) + refunds_data
    
    # Add net total labels on top of each bar
    for i, (month, net_total) in enumerate(net_totals.items()):
        positive_total = pivot_data.loc[month].sum()
        if positive_total > 0:
            # Position label above the positive part
            ax.text(i, positive_total + positive_total * 0.01, f'Net: ${net_total:,.2f}', 
                   ha='center', va='bottom', fontweight='bold', fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    # Customize the chart
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Cost (USD)', fontsize=12, fontweight='bold')
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
    
    # Set x-axis labels to month names (horizontal)
    ax.set_xticks(range(len(pivot_data.index)))
    ax.set_xticklabels(pivot_data.index, rotation=0)
    
    # Add horizontal line at y=0 for reference
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
    
    # Customize legend - move to bottom with 4 columns
    ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', fontsize=10, ncol=4)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, axis='y')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the chart
    chart_directory = get_chart_directory(account_id, end_date)
    os.makedirs(chart_directory, exist_ok=True)
    
    chart_filename = f"{chart_directory}/aws-cost-chart-{account_id}-{start_date}_to_{end_date}.png"
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Cost visualization saved to {chart_filename}")
    return chart_filename

def get_chart_directory(account_id, end_date):
    """Get the directory path for saving charts"""
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    year = end_date_obj.strftime('%Y')
    month = end_date_obj.strftime('%m')
    
    if account_id == "organization_summary":
        return f"aws_cost_reports/organization_summary/{year}/end-of-{month}/charts"
    else:
        return f"aws_cost_reports/{account_id}/{year}/end-of-{month}/charts"

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
    
    # Create organization-wide visualization
    print("Creating organization cost visualization...")
    create_cost_visualization(
        org_df, 
        f"AWS Organization Cost by Service ({start_date} to {end_date})",
        "organization_summary",
        start_date,
        end_date,
        is_organization=True
    )
    
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
        
        # Create visualization for specific account
        print(f"Creating cost visualization for account {account_id}...")
        create_cost_visualization(
            df,
            f"AWS Cost by Service - {account_name} ({start_date} to {end_date})",
            account_id,
            start_date,
            end_date,
            is_organization=False
        )
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
            
            # Create visualization for each account
            print(f"Creating cost visualization for account {account_id}...")
            create_cost_visualization(
                df,
                f"AWS Cost by Service - {account_name} ({start_date} to {end_date})",
                account_id,
                start_date,
                end_date,
                is_organization=False
            )
        
        # Create a consolidated report by combining all dataframes
        if all_dfs:
            print("Generating consolidated report for all accounts...")
            df_consolidated = pd.concat(all_dfs, ignore_index=True)
            save_to_excel(df_consolidated, "consolidated", start_date, end_date)
            
            # Create visualization for consolidated data
            print("Creating consolidated cost visualization...")
            create_cost_visualization(
                df_consolidated,
                f"AWS Consolidated Cost by Service ({start_date} to {end_date})",
                "consolidated",
                start_date,
                end_date,
                is_organization=False
            )
        else:
            print("No account data found.")
    
    print("All reports and visualizations generated successfully!")

if __name__ == "__main__":
    main()