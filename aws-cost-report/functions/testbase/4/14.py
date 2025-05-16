def generate_multi_month_report(account_id, account_name, months_data, output_dir_base="aws_cost_reports", use_mock=False):
    """
    Generate a consolidated report showing costs across multiple months
    
    Args:
        account_id: AWS account ID
        account_name: AWS account name
        months_data: List of tuples (year, month, dataframe)
        output_dir_base: Base output directory
        use_mock: Whether this is mock data
        
    Returns:
        Boolean indicating success
    """
    try:
        if not months_data:
            print(f"No cost data available for account {account_id} ({account_name}) for any month")
            return False
            
        # Sort months chronologically
        months_data.sort(key=lambda x: (x[0], x[1]))  # Sort by year, then month
        
        # Create a list of month labels for x-axis
        month_labels = [f"{calendar.month_abbr[m]}-{y}" for y, m, _ in months_data]
        
        # Identify top services across all months
        all_services = set()
        for _, _, df in months_data:
            all_services.update(df['Service'].unique())
        
        # Get top 9 services by total cost across all months
        service_totals = {}
        for _, _, df in months_data:
            for service, amount in zip(df['Service'], df['Amount']):
                service_totals[service] = service_totals.get(service, 0) + amount
                
        top_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
        if len(top_services) > 9:
            top_services = top_services[:9]
            top_service_names = [service for service, _ in top_services]
            has_other = True
        else:
            top_service_names = [service for service, _ in top_services]
            has_other = False
            
        # Prepare data for stacked bar chart
        stacked_data = []
        for year, month, df in months_data:
            month_data = {'month': f"{calendar.month_abbr[month]}-{year}"}
            
            # Add amounts for top services
            for service in top_service_names:
                service_amount = df[df['Service'] == service]['Amount'].sum() if service in df['Service'].values else 0
                month_data[service] = service_amount
                
            # Add 'Other' category if needed
            if has_other:
                other_amount = sum(df[~df['Service'].isin(top_service_names)]['Amount'])
                month_data['Other'] = other_amount
                
            stacked_data.append(month_data)
            
        # Convert to DataFrame for easier plotting
        plot_df = pd.DataFrame(stacked_data)
        
        # Get date range for filename
        first_month = months_data[0]
        last_month = months_data[-1]
        start_date = datetime.date(first_month[0], first_month[1], 1)
        end_date = get_month_date_range(last_month[0], last_month[1])[1]
        
        # Create directory for multi-month report using the last month's date for folder structure
        # This follows the requested format: aws_cost_reports/account_id/year/month/
        output_dir = f"{output_dir_base}/{account_id}/{last_month[0]}/{last_month[1]:02d}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the report filename
        filename = f"aws-cost-report-{account_id}-{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"
        
        # Create visualization
        plt.figure(figsize=(15, 10))
        
        # Create a list of colors for the services
        colors = plt.cm.tab10(range(10))  # Using tab10 colormap which has 10 distinct colors
        
        # Create the stacked bar chart
        bottom = np.zeros(len(plot_df))
        x_positions = np.arange(len(plot_df))
        
        # Plot each service as a segment in the stacked bars
        services_to_plot = top_service_names + (['Other'] if has_other else [])
        
        # Store positions for labels
        label_positions = {}
        
        for i, service in enumerate(services_to_plot):
            if service in plot_df.columns:
                # Plot the bar segment
                bars = plt.bar(x_positions, plot_df[service], bottom=bottom, 
                               label=service, color=colors[i % len(colors)])
                
                # Calculate middle positions for labels
                segment_heights = plot_df[service].values
                midpoints = bottom + segment_heights/2
                
                # Save the positions for this service's labels
                label_positions[service] = (x_positions, midpoints, segment_heights)
                
                # Update the bottom for the next service
                bottom += segment_heights
        
        # Calculate totals for each month
        monthly_totals = []
        for _, _, df in months_data:
            monthly_totals.append(df['Amount'].sum())
        
        # Add labels to each segment
        for service, (x_pos, y_pos, heights) in label_positions.items():
            for i, (x, y, h) in enumerate(zip(x_pos, y_pos, heights)):
                # Only add label if the segment is large enough
                if h > max(monthly_totals) * 0.03:  # Only label segments that are at least 3% of the max total
                    # Format: $XXX if < 1000, $X.XK if >= 1000
                    if h < 1000:
                        label = f"${h:.0f}"
                    else:
                        label = f"${h/1000:.1f}K"
                    plt.text(x, y, label, ha='center', va='center', fontsize=9, 
                             color='white' if h > max(monthly_totals) * 0.05 else 'black')
        
        # Add total labels on top of each bar
        for i, total in enumerate(monthly_totals):
            if total < 1000:
                label = f"${total:.0f}"
            elif total < 1000000:
                label = f"${total/1000:.1f}K"
            else:
                label = f"${total/1000000:.1f}M"
            
            plt.text(x_positions[i], bottom[i] + (max(monthly_totals) * 0.02), label, 
                     ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Add labels and legend
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Cost (USD)', fontsize=12)
        plt.title(f'Monthly AWS Costs by Service', fontsize=16)
        plt.legend(title='AWS Services', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Set x-ticks to month labels
        plt.xticks(x_positions, plot_df['month'])
        
        # Add grid lines for better readability
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add some padding above the bars for total labels
        y_max = max(monthly_totals) * 1.1
        plt.ylim(0, y_max)
        
        # Add title and account info
        mode_label = " [MOCK DATA]" if use_mock else ""
        plt.suptitle(f'AWS Cost Report{mode_label} - Account: {account_id} ({account_name})\n'
                    f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}', 
                    fontsize=16)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.9, right=0.85)
        
        # Save the figure
        plt.savefig(f"{output_dir}/{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save the data to CSV
        plot_df.to_csv(f"{output_dir}/{filename}.csv", index=False)
        
        print(f"Generated multi-month report for account {account_id} ({account_name}) for period {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        return True
        
    except Exception as e:
        print(f"Error generating multi-month report for account {account_id} ({account_name}): {str(e)}")
        import traceback
        traceback.print_exc()
        return Falseimport boto3
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import os
import calendar
from dateutil.relativedelta import relativedelta
import argparse
import random
import json
import numpy as np

def get_linked_accounts(use_mock=False):
    """Get all linked accounts in the AWS Organization or use current account if not in an organization"""
    if use_mock:
        # Return mock account data
        mock_accounts = [
            {'id': '123456789012', 'name': 'Development Account'},
            {'id': '234567890123', 'name': 'Production Account'},
            {'id': '345678901234', 'name': 'Staging Account'},
            {'id': '456789012345', 'name': 'Data Analytics Account'},
            {'id': '567890123456', 'name': 'Machine Learning Account'}
        ]
        return mock_accounts
    
    try:
        # Try to get accounts from AWS Organizations
        org_client = boto3.client('organizations')
        
        accounts = []
        paginator = org_client.get_paginator('list_accounts')
        
        for page in paginator.paginate():
            for account in page['Accounts']:
                if account['Status'] == 'ACTIVE':
                    accounts.append({
                        'id': account['Id'],
                        'name': account['Name']
                    })
        
        return accounts
    except Exception as e:
        # If Organizations API fails (e.g., account not in an organization),
        # use the current account
        try:
            sts_client = boto3.client('sts')
            identity = sts_client.get_caller_identity()
            account_id = identity['Account']
            
            # Try to get account alias
            iam_client = boto3.client('iam')
            try:
                response = iam_client.list_account_aliases()
                account_name = response['AccountAliases'][0] if response['AccountAliases'] else f"Account {account_id}"
            except:
                account_name = f"Account {account_id}"
            
            print(f"No organization found. Using current account: {account_id} ({account_name})")
            return [{'id': account_id, 'name': account_name}]
            
        except Exception as inner_e:
            print(f"Failed to get current account: {str(inner_e)}")
            print("Using a default account ID. Please specify your actual account ID with --account.")
            return [{'id': '123456789012', 'name': 'Current Account'}]

def get_month_date_range(year, month):
    """Get start and end dates for a given month"""
    first_day = datetime.date(year, month, 1)
    
    # Get the last day of the month
    if month == 12:
        last_day = datetime.date(year, month, 31)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    return first_day, last_day

def get_cost_data(account_id, start_date, end_date, use_mock=False):
    """Get cost data for an account for the specified date range"""
    if use_mock:
        # Generate mock cost data
        aws_services = [
            'Amazon Elastic Compute Cloud', 'AWS Lambda', 'Amazon Simple Storage Service',
            'Amazon Relational Database Service', 'Amazon DynamoDB', 'Amazon CloudFront',
            'AWS Key Management Service', 'Amazon Elastic Container Service', 'Amazon Route 53',
            'Amazon Simple Queue Service', 'Amazon Simple Notification Service', 'AWS CloudTrail',
            'Amazon Virtual Private Cloud', 'AWS Glue', 'Amazon API Gateway'
        ]
        
        # Generate 10-15 random services
        num_services = random.randint(10, 15)
        selected_services = random.sample(aws_services, num_services)
        
        # Base amount between $500 and $5000
        base_amount = random.uniform(500, 5000)
        total = 0
        
        groups = []
        for service in selected_services:
            # Random amount following a power law distribution for realism
            amount = base_amount * random.uniform(0.01, 1) ** 2
            total += amount
            
            groups.append({
                'Keys': [service],
                'Metrics': {
                    'UnblendedCost': {
                        'Amount': str(amount),
                        'Unit': 'USD'
                    }
                }
            })
        
        mock_response = {
            'GroupDefinitions': [
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            'ResultsByTime': [
                {
                    'TimePeriod': {
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': (end_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    },
                    'Total': {
                        'UnblendedCost': {
                            'Amount': str(total),
                            'Unit': 'USD'
                        }
                    },
                    'Groups': groups
                }
            ]
        }
        
        return mock_response
    
    # Real AWS API call
    ce_client = boto3.client('ce')
    
    # Check if we need to filter by linked account
    # If the current account is the same as the requested account, don't filter
    try:
        sts_client = boto3.client('sts')
        current_account = sts_client.get_caller_identity()['Account']
        use_filter = current_account != account_id
    except:
        use_filter = True
    
    # Base parameters
    params = {
        'TimePeriod': {
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': (end_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        },
        'Granularity': 'MONTHLY',
        'Metrics': ['UnblendedCost'],
        'GroupBy': [
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    }
    
    # Add filter only if needed (when looking at child accounts from organization master)
    if use_filter:
        params['Filter'] = {
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    
    response = ce_client.get_cost_and_usage(**params)
    return response

def process_cost_data(cost_data):
    """Process the cost data into a pandas DataFrame"""
    results = []
    
    for time_period in cost_data['ResultsByTime']:
        for group in time_period['Groups']:
            service = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            results.append({
                'Service': service,
                'Amount': amount
            })
    
    # If there are no results, return an empty DataFrame
    if not results:
        return pd.DataFrame(columns=['Service', 'Amount'])
        
    df = pd.DataFrame(results)
    return df

def generate_cost_report(account_id, account_name, year, month, use_mock=False, output_dir_base="aws_cost_reports"):
    """Generate cost report for an account for a specific month"""
    start_date, end_date = get_month_date_range(year, month)
    
    try:
        # Get cost data
        cost_data = get_cost_data(account_id, start_date, end_date, use_mock)
        df = process_cost_data(cost_data)
        
        # If DataFrame is empty, return without creating a report
        if df.empty:
            print(f"No cost data available for account {account_id} ({account_name}) for {year}-{month:02d}")
            return False
        
        # Sort by amount and get top 9 services, grouping the rest as 'Other'
        df = df.sort_values(by='Amount', ascending=False)
        
        if len(df) > 9:
            top_services = df.iloc[:9].copy()
            other_amount = df.iloc[9:]['Amount'].sum()
            
            # Add 'Other' category
            other_row = pd.DataFrame([{'Service': 'Other', 'Amount': other_amount}])
            final_df = pd.concat([top_services, other_row], ignore_index=True)
        else:
            final_df = df
        
        # Create output directory
        output_dir = f"{output_dir_base}/{account_id}/{year}/{end_date.month:02d}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the report filename
        filename = f"aws-cost-report-{account_id}-{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Bar chart
        plt.subplot(1, 2, 1)
        bars = plt.bar(['Cost'], [final_df['Amount'].sum()], color='steelblue', width=0.4)
        plt.title(f'Total Cost: ${final_df["Amount"].sum():.2f}')
        plt.ylabel('Cost (USD)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Pie chart
        plt.subplot(1, 2, 2)
        plt.pie(final_df['Amount'], labels=final_df['Service'], autopct='%1.1f%%', 
                startangle=90, shadow=False, 
                explode=[0.05] * len(final_df))
        plt.axis('equal')
        plt.title(f'Service Distribution - {calendar.month_name[month]} {year}')
        
        # Add title and account info
        mode_label = " [MOCK DATA]" if use_mock else ""
        plt.suptitle(f'AWS Cost Report{mode_label} - Account: {account_id} ({account_name})\n'
                    f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}', 
                    fontsize=16)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.85)
        
        # Save the figure
        plt.savefig(f"{output_dir}/{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save the data to CSV
        final_df.to_csv(f"{output_dir}/{filename}.csv", index=False)
        
        # Save raw response data for debugging
        if use_mock:
            with open(f"{output_dir}/{filename}-raw.json", 'w') as f:
                json.dump(cost_data, f, indent=2, default=str)
        
        print(f"Generated report for account {account_id} ({account_name}) for {year}-{month:02d}")
        return True
        
    except Exception as e:
        print(f"Error generating report for account {account_id} ({account_name}) for {year}-{month:02d}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate AWS cost reports for all linked accounts')
    parser.add_argument('--months', type=int, default=1, help='Number of past months to generate reports for')
    parser.add_argument('--account', type=str, help='Specific account ID to generate reports for (optional)')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of AWS API calls')
    parser.add_argument('--output-dir', type=str, default='aws_cost_reports', help='Base output directory')
    parser.add_argument('--single-account', action='store_true', help='Force single account mode (use current account)')
    parser.add_argument('--multi-month', action='store_true', help='Generate a consolidated report with multiple months')
    args = parser.parse_args()
    
    # Get accounts
    try:
        if args.single_account and not args.mock:
            # Force single account mode
            sts_client = boto3.client('sts')
            identity = sts_client.get_caller_identity()
            account_id = identity['Account']
            
            # Try to get account alias
            iam_client = boto3.client('iam')
            try:
                response = iam_client.list_account_aliases()
                account_name = response['AccountAliases'][0] if response['AccountAliases'] else f"Account {account_id}"
            except:
                account_name = f"Account {account_id}"
            
            accounts = [{'id': account_id, 'name': account_name}]
            print(f"Using single account mode with account: {account_id} ({account_name})")
        else:
            # Get linked accounts or current account if not in organization
            accounts = get_linked_accounts(use_mock=args.mock)
        
        print(f"Found {len(accounts)} account(s)" + (" (mock data)" if args.mock else ""))
    except Exception as e:
        print(f"Error getting accounts: {str(e)}")
        if not args.mock:
            print("Consider using --mock flag for testing or --single-account to use current account only")
        return
    
    # Filter accounts if specified
    if args.account:
        accounts = [account for account in accounts if account['id'] == args.account]
        if not accounts:
            print(f"Account {args.account} not found")
            return
    
    # Get date ranges for reports
    today = datetime.date.today()
    months_to_process = []
    
    for i in range(args.months):
        # Calculate month that is i months ago
        target_date = today - relativedelta(months=i)
        months_to_process.append((target_date.year, target_date.month))
    
    # Generate reports
    total_reports = 0
    
    # If multi-month is enabled, collect data for all months before generating consolidated report
    if args.multi_month:
        for account in accounts:
            account_data = []
            for year, month in months_to_process:
                try:
                    start_date, end_date = get_month_date_range(year, month)
                    cost_data = get_cost_data(account['id'], start_date, end_date, use_mock=args.mock)
                    df = process_cost_data(cost_data)
                    
                    if not df.empty:
                        account_data.append((year, month, df))
                except Exception as e:
                    print(f"Error getting data for account {account['id']} ({account['name']}) for {year}-{month:02d}: {str(e)}")
            
            if account_data:
                success = generate_multi_month_report(
                    account['id'], 
                    account['name'], 
                    account_data,
                    output_dir_base=args.output_dir,
                    use_mock=args.mock
                )
                if success:
                    total_reports += 1
    
    # Generate individual monthly reports unless only multi-month is needed
    if not args.multi_month:
        for account in accounts:
            for year, month in months_to_process:
                success = generate_cost_report(
                    account['id'], 
                    account['name'], 
                    year, 
                    month, 
                    use_mock=args.mock,
                    output_dir_base=args.output_dir
                )
                if success:
                    total_reports += 1
    
    print(f"Generated {total_reports} reports")
    
    if args.mock:
        print("\nNOTE: Reports were generated with mock data for debugging purposes.")
    
    print(f"Check the {args.output_dir} directory for the generated reports.")

if __name__ == "__main__":
    main()
