import boto3
import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from dateutil.parser import parse
import calendar
from dateutil.relativedelta import relativedelta
import numpy as np
import argparse
import random
import time
import sys

class AWSCostReportGenerator:
    def __init__(self, output_dir="aws_cost_reports", start_date=None, end_date=None, use_mock_data=False):
        """
        Initialize the AWS Cost Report Generator.
        
        Args:
            output_dir (str): Base directory for output reports
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            use_mock_data (bool): Whether to use mock data instead of real AWS API calls
        """
        self.output_dir = output_dir
        self.start_date = start_date
        self.end_date = end_date
        self.use_mock_data = use_mock_data
        
        # AWS clients (only initialized if not using mock data)
        if not self.use_mock_data:
            self.ce_client = boto3.client('ce')  # Cost Explorer client
        
        # Colors for the top 9 services
        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # Mock data for testing
        self.mock_services = [
            'Amazon Elastic Compute Cloud - Compute',
            'Amazon Simple Storage Service',
            'Amazon Relational Database Service',
            'AWS Lambda',
            'Amazon CloudFront',
            'Amazon DynamoDB',
            'AWS WAF',
            'Amazon API Gateway',
            'Amazon Route 53',
            'Amazon CloudWatch',
            'Amazon Elastic Container Service',
            'Amazon Elastic Kubernetes Service',
            'Amazon Virtual Private Cloud',
            'AWS Data Transfer',
            'AWS Glue'
        ]
        
        self.mock_accounts = [
            {'id': '123456789012', 'name': 'Production Account'},
            {'id': '234567890123', 'name': 'Development Account'},
            {'id': '345678901234', 'name': 'Testing Account'},
            {'id': '456789012345', 'name': 'Staging Account'},
            {'id': '567890123456', 'name': 'Data Analytics Account'},
            {'id': '678901234567', 'name': 'Security Account'},
            {'id': '789012345678', 'name': 'ML Research Account'},
            {'id': '890123456789', 'name': 'IoT Services Account'},
            {'id': '901234567890', 'name': 'Legacy Systems Account'},
            {'id': '012345678901', 'name': 'Marketing Account'},
            {'id': '098765432109', 'name': 'Finance Account'},
            {'id': '987654321098', 'name': 'HR Account'}
        ]
    
    def get_linked_accounts(self):
        """
        Get all linked accounts using Cost Explorer API or mock data.
        """
        if self.use_mock_data:
            print("Using mock account data for testing")
            return self.mock_accounts
            
        accounts = []
        
        try:
            print("Retrieving linked accounts from AWS Cost Explorer API...")
            # Use Cost Explorer to get linked accounts - increase MaxResults to reduce pagination
            response = self.ce_client.get_dimension_values(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Dimension='LINKED_ACCOUNT',
                Context='COST_AND_USAGE',
                MaxResults=2000  # Request the maximum number of results in one call
            )
            
            # Extract account IDs
            for value in response.get('DimensionValues', []):
                account_id = value.get('Value')
                account_name = value.get('Attributes', {}).get('description', f"Account {account_id}")
                
                accounts.append({
                    'id': account_id,
                    'name': account_name
                })
            
            # We'll still check for pagination, but we've increased MaxResults to minimize it
            next_token = response.get('NextPageToken')
            if next_token:
                print("  Warning: Large number of accounts detected, retrieving additional pages...")
                while next_token:
                    response = self.ce_client.get_dimension_values(
                        TimePeriod={
                            'Start': self.start_date,
                            'End': self.end_date
                        },
                        Dimension='LINKED_ACCOUNT',
                        Context='COST_AND_USAGE',
                        MaxResults=2000,
                        NextPageToken=next_token
                    )
                    
                    for value in response.get('DimensionValues', []):
                        account_id = value.get('Value')
                        account_name = value.get('Attributes', {}).get('description', f"Account {account_id}")
                        
                        accounts.append({
                            'id': account_id,
                            'name': account_name
                        })
                    
                    next_token = response.get('NextPageToken')
            
            print(f"Retrieved {len(accounts)} accounts from AWS Cost Explorer API")
        
        except Exception as e:
            print(f"Error retrieving linked accounts: {str(e)}")
        
        return accounts
    
    def get_date_ranges(self):
        """Generate date ranges for the reports based on input dates."""
        date_ranges = []
        
        # Parse input dates
        start_dt = parse(self.start_date)
        end_dt = parse(self.end_date)
        
        # Create monthly date ranges
        current_month_start = start_dt.replace(day=1)
        
        while current_month_start <= end_dt:
            # Calculate month end (last day of month)
            if current_month_start.month == 12:
                next_month = current_month_start.replace(year=current_month_start.year + 1, month=1)
            else:
                next_month = current_month_start.replace(month=current_month_start.month + 1)
                
            month_end = next_month - datetime.timedelta(days=1)
            
            # Ensure we don't go past the end date
            month_end = min(month_end, end_dt)
            
            # Add the date range
            date_ranges.append({
                'start': current_month_start.strftime("%Y-%m-%d"),
                'end': month_end.strftime("%Y-%m-%d"),
                'year': month_end.strftime("%Y"),
                'month': month_end.strftime("%m"),
                'month_name': month_end.strftime("%b %Y")
            })
            
            # Move to next month
            current_month_start = next_month
            
        return date_ranges
    
    def get_cost_data(self, account_id, start_date, end_date, month_index=0):
        """Get cost data for a specific account and date range."""
        if self.use_mock_data:
            return self._generate_mock_cost_data(account_id, month_index)
            
        try:
            # Get cost and usage for both total and service breakdown in a single call
            # by using GroupBy with an empty list for total and then with SERVICE for breakdown
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': [account_id]
                    }
                },
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            # Check if we got any results
            if not response.get('ResultsByTime') or not response['ResultsByTime'][0].get('Groups'):
                # No data was returned - account might not have any costs
                return {
                    'total_cost': 0,
                    'services': []
                }
            
            # Parse service costs
            services = []
            for group in response['ResultsByTime'][0]['Groups']:
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                services.append({'service': service_name, 'cost': cost})
            
            # Sort by cost (descending) but make sure refunds come last
            # (since they have negative values, a simple sort would put them first)
            refund_services = [s for s in services if 'refund' in s['service'].lower()]
            other_services = [s for s in services if 'refund' not in s['service'].lower()]
            
            other_services.sort(key=lambda x: x['cost'], reverse=True)
            refund_services.sort(key=lambda x: x['cost'], reverse=True)
            
            sorted_services = other_services + refund_services
            
            # Calculate total cost by summing all service costs
            total_cost = sum(service['cost'] for service in services)
            
            return {
                'total_cost': total_cost,
                'services': sorted_services
            }
                
        except Exception as e:
            print(f"  Error getting cost data for account {account_id}: {str(e)}")
            return {
                'total_cost': 0,
                'services': []
            }
            
    def _generate_mock_cost_data(self, account_id, month_index=0):
        """Generate mock cost data for testing purposes."""
        # Use account_id and month as seeds for reproducible randomness
        seed = int(account_id) % 10000 + month_index * 100
        random.seed(seed)
        
        # Generate random total cost for the account based on account ID
        # Make some accounts more expensive than others for more realistic visualization
        base_cost = random.uniform(1000, 5000)
        
        # Add some monthly variation (costs tend to grow over time)
        month_factor = 1.0 + (month_index * 0.05)
        base_cost *= month_factor
        
        # Generate random services
        num_services = random.randint(5, 15)
        services = []
        
        # Get a subset of mock services
        selected_services = random.sample(self.mock_services, min(num_services, len(self.mock_services)))
        
        # Assign costs to services following a power law distribution (few services use most of the cost)
        total_cost = 0
        for i, service in enumerate(selected_services):
            # Power law distribution - first services get higher costs
            cost = base_cost * (0.5 ** i) * random.uniform(0.8, 1.2)
            services.append({'service': service, 'cost': cost})
            total_cost += cost
        
        # Sort by cost (descending)
        services.sort(key=lambda x: x['cost'], reverse=True)
        
        return {
            'total_cost': total_cost,
            'services': services
        }
    
    def generate_cost_report(self, account_id, account_name, date_ranges):
        """Generate cost report for a specific account across multiple date ranges."""
        print(f"  Generating report for account {account_id} ({account_name})")
        
        # Get year and month from the last date range for the output directory
        last_date_range = date_ranges[-1]
        
        # Create output directory
        output_path = os.path.join(
            self.output_dir,
            account_id,
            last_date_range['year'],
            f"end-of-{last_date_range['month']}",
        )
        os.makedirs(output_path, exist_ok=True)
        
        # Generate the report file name
        start_date = date_ranges[0]['start']
        end_date = date_ranges[-1]['end']
        output_file = os.path.join(
            output_path,
            f"aws-cost-report-{account_id}-{start_date}-{end_date}.png"
        )
        
        # Get cost data for each month
        monthly_cost_data = []
        for i, date_range in enumerate(date_ranges):
            print(f"    Processing month {i+1}/{len(date_ranges)}: {date_range['month_name']}...")
            cost_data = self.get_cost_data(account_id, date_range['start'], date_range['end'], i)
            monthly_cost_data.append({
                'month': date_range['month_name'],
                'cost_data': cost_data
            })
            print(f"      Total cost: ${cost_data['total_cost']:.2f}, Services: {len(cost_data['services'])}")
        
        # Skip generating a report if all months have zero cost
        if all(month_data['cost_data']['total_cost'] == 0 for month_data in monthly_cost_data):
            print(f"    Skipping report generation - account has no costs for the selected period")
            return None
        
        # Generate the report
        print(f"    Creating visualization...")
        self._create_multi_month_cost_report(
            account_id, 
            account_name, 
            monthly_cost_data, 
            output_file
        )
        
        # Generate CSV data
        csv_file = os.path.join(
            output_path,
            f"aws-cost-report-{account_id}-{start_date}-{end_date}.csv"
        )
        
        # Prepare CSV data
        csv_data = []
        for month_data in monthly_cost_data:
            month = month_data['month']
            cost_data = month_data['cost_data']
            
            for service_data in cost_data['services']:
                csv_data.append({
                    'month': month,
                    'service': service_data['service'],
                    'cost': service_data['cost']
                })
        
        # Save CSV data
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False)
        
        print(f"    Report saved to {output_file}")
        return output_file
        
    def _create_multi_month_cost_report(self, account_id, account_name, monthly_cost_data, output_file):
        """Create a cost report visualization with one bar per month."""
        # Set up the figure with improved proportions
        plt.figure(figsize=(16, 12))  # Wider figure to accommodate legend better
        
        # Create subplot with improved height ratios - less space for title/summary and more for chart
        gs = plt.GridSpec(3, 1, height_ratios=[0.4, 0.6, 5], hspace=0.4)
        title_ax = plt.subplot(gs[0])
        summary_ax = plt.subplot(gs[1])
        chart_ax = plt.subplot(gs[2])
        
        # Set the title at the very top
        plt.sca(title_ax)
        title_ax.axis('off')  # Hide the axes
        date_range = f"{monthly_cost_data[0]['month']} to {monthly_cost_data[-1]['month']}"
        plt.text(0.5, 0.5, f'AWS Cost Explorer Report - {account_name} ({account_id})\n{date_range}', 
                 fontsize=16, fontweight='bold', ha='center', va='center')
        
        # Switch to the chart axis for the main bar chart
        plt.sca(chart_ax)
        
        # Calculate total costs and refunds for each month
        for month_data in monthly_cost_data:
            # Process refunds separately
            refund_services = [s for s in month_data['cost_data']['services'] 
                              if s['service'].lower() == 'refund' or 'refund' in s['service'].lower()]
            other_services = [s for s in month_data['cost_data']['services'] 
                             if s['service'].lower() != 'refund' and 'refund' not in s['service'].lower()]
            
            # Calculate refund amount (should be negative)
            refund_amount = sum(s['cost'] for s in refund_services)
            
            # Calculate total without refunds
            total_without_refunds = sum(s['cost'] for s in other_services)
            
            # Store these calculations in the month_data
            month_data['refund_amount'] = refund_amount
            month_data['total_without_refunds'] = total_without_refunds
            month_data['other_services'] = other_services
        
        # Get all unique services across all months (excluding refunds)
        all_services = set()
        for month_data in monthly_cost_data:
            # Only include services with meaningful costs (more than $0.01) and exclude refunds
            services = [service['service'] for service in month_data['other_services'] 
                       if service['cost'] > 0.01 and 'refund' not in service['service'].lower()]
            all_services.update(services)
        
        # Calculate summary statistics
        total_cost = sum(month_data['cost_data']['total_cost'] for month_data in monthly_cost_data)
        avg_monthly_cost = total_cost / len(monthly_cost_data)
        service_count = len(all_services)
        
        # Convert to list and sort alphabetically (for consistent coloring)
        all_services = sorted(list(all_services))
        
        # Create a color map for services
        service_colors = {}
        for i, service in enumerate(all_services):
            service_colors[service] = self.colors[i % len(self.colors)]
        
        # Add a special color for refunds
        refund_color = '#FF5733'  # A reddish color for refunds
        
        # Prepare data for the stacked bar chart
        months = [data['month'] for data in monthly_cost_data]
        x_positions = np.arange(len(months))
        
        # Find maximum cost and refund to set y-axis scale properly
        max_positive_cost = max(month_data['total_without_refunds'] for month_data in monthly_cost_data)
        min_refund = min(month_data['refund_amount'] for month_data in monthly_cost_data)
        
        # Set y-axis to accommodate both costs and refunds
        plt.ylim(min_refund * 1.1, max_positive_cost * 1.1)  # Extra 10% margin
        
        # Add a horizontal line at y=0
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Increase bar width for better proportions
        bar_width = 0.65
        
        # Build the stacked bars for positive costs
        bottoms = np.zeros(len(months))
        handles = []  # For the legend
        
        # Process each month's data for positive costs (non-refunds)
        for month_idx, month_data in enumerate(monthly_cost_data):
            # Filter services with significant costs (more than $0.01)
            significant_services = [s for s in month_data['other_services'] 
                                   if s['cost'] > 0.01 and 'refund' not in s['service'].lower()]
            
            # Get the top 9 services for this month
            top_services = significant_services[:9]
            
            # Calculate the "Other" category if needed - sum services beyond top 9
            # and services with negligible costs (≤ $0.01)
            other_services_cost = sum(service['cost'] for service in month_data['other_services'][9:] 
                                     if 'refund' not in service['service'].lower())
            negligible_cost = sum(service['cost'] for service in month_data['other_services'] 
                                 if service['cost'] <= 0.01 and 'refund' not in service['service'].lower())
            other_services_cost += negligible_cost
            
            # Add the top services
            for service_data in top_services:
                service_name = service_data['service']
                cost = service_data['cost']
                
                # Draw the bar segment with wider width
                bar = plt.bar(month_idx, cost, width=bar_width, bottom=bottoms[month_idx], 
                             color=service_colors.get(service_name, 'gray'))
                
                # Add cost label in the middle of the segment if it's big enough
                if cost > max_positive_cost * 0.05:  # Only label if at least 5% of the maximum monthly cost
                    # Position the text in the middle of the segment
                    middle_y = bottoms[month_idx] + (cost / 2)
                    plt.text(month_idx, middle_y, f'${cost:.0f}', 
                            ha='center', va='center', fontsize=9, 
                            color='white', fontweight='bold')
                
                bottoms[month_idx] += cost
                
                # Add to legend handles only once
                if service_name not in [h.get_label() for h in handles]:
                    handles.append(plt.Rectangle((0,0), 1, 1, color=service_colors.get(service_name, 'gray'), 
                                               label=service_name))
            
            # Add "Other" category if needed
            if other_services_cost > 0.01:  # Only show "Other" if it's meaningful
                plt.bar(month_idx, other_services_cost, width=bar_width, bottom=bottoms[month_idx], color='#cccccc')
                
                # Add cost label for "Other" if it's big enough
                if other_services_cost > max_positive_cost * 0.05:
                    middle_y = bottoms[month_idx] + (other_services_cost / 2)
                    plt.text(month_idx, middle_y, f'${other_services_cost:.0f}', 
                            ha='center', va='center', fontsize=9, 
                            color='black', fontweight='bold')
                
                bottoms[month_idx] += other_services_cost
            
            # Add refund bars below x-axis
            refund_amount = month_data['refund_amount']
            if refund_amount < 0:  # Refunds should be negative
                plt.bar(month_idx, refund_amount, width=bar_width, bottom=0, color=refund_color)
                
                # Add refund label in the middle of the segment
                plt.text(month_idx, refund_amount/2, f'${refund_amount:.0f}', 
                        ha='center', va='center', fontsize=9, 
                        color='white', fontweight='bold')
                
                # Add to legend handles only once
                if 'Refund' not in [h.get_label() for h in handles]:
                    handles.append(plt.Rectangle((0,0), 1, 1, color=refund_color, label='Refund'))
            
            # Add NET total cost label at the top of the bar (including refunds)
            net_cost = month_data['cost_data']['total_cost']
            plt.text(month_idx, bottoms[month_idx] * 1.02, f'${net_cost:.2f}', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')
        
        # Set chart labels
        plt.ylabel('Cost (USD)', fontsize=12, fontweight='bold')
        plt.xticks(x_positions, months, rotation=45, fontsize=10, fontweight='bold')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add legend with better positioning and compact layout
        # Use a smaller font and more columns for a more compact legend
        plt.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.15),
                  ncol=5, fontsize=9, frameon=True, fancybox=True, shadow=True)
        
        # Now create the summary table in the middle
        plt.sca(summary_ax)
        summary_ax.axis('off')  # Hide the axes
        
        # Create a table for the summary stats - using the NET cost
        col_labels = ['Total Cost (Net)', 'Average Monthly Cost', 'Service Count']
        table_data = [
            [f'${total_cost:.2f}', f'${avg_monthly_cost:.2f}', f'{service_count}']
        ]
        
        # Create a table that spans 60% of the width
        table = plt.table(cellText=table_data, colLabels=col_labels, loc='center', 
                        cellLoc='center', colColours=['#f2f2f2']*3)
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 1.5)  # Make the table taller
        
        # Add padding around the plot areas
        plt.subplots_adjust(bottom=0.28, left=0.1, right=0.9, top=0.9)
        
        # Save the figure using the output_file parameter
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Report saved to {output_file}")


    def generate_organization_summary(self, accounts, date_ranges):
        """Generate a summary report for the entire organization across multiple months."""
        print("Generating organization summary...")
        
        # Get year and month from the last date range for the output directory
        last_date_range = date_ranges[-1]
        
        # Create output directory
        output_path = os.path.join(
            self.output_dir,
            "organization_summary",
            last_date_range['year'],
            f"end-of-{last_date_range['month']}",
        )
        os.makedirs(output_path, exist_ok=True)
        
        # Generate the report file name
        start_date = date_ranges[0]['start']
        end_date = date_ranges[-1]['end']
        output_file = os.path.join(
            output_path,
            f"aws-cost-summary-{start_date}-{end_date}.png"
        )
        
        # Optimize by getting costs for all accounts in one API call if possible
        # Only fall back to per-account calls if this fails
        try:
            print("Attempting to get cost data for all accounts in a single API call...")
            monthly_summary_data = []
            
            for i, date_range in enumerate(date_ranges):
                month_date = date_range['month_name']
                
                # Get costs for all accounts in a single API call
                response = self.ce_client.get_cost_and_usage(
                    TimePeriod={
                        'Start': date_range['start'],
                        'End': date_range['end']
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {
                            'Type': 'DIMENSION',
                            'Key': 'LINKED_ACCOUNT'
                        }
                    ]
                )
                
                # Process the response
                account_costs = []
                if response.get('ResultsByTime') and response['ResultsByTime'][0].get('Groups'):
                    for group in response['ResultsByTime'][0]['Groups']:
                        account_id = group['Keys'][0]
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        
                        # Find the account name from our accounts list
                        account_name = next((acc['name'] for acc in accounts if acc['id'] == account_id), f"Account {account_id}")
                        
                        account_costs.append({
                            'id': account_id,
                            'name': account_name,
                            'cost': cost
                        })
                
                # Sort by cost (descending)
                account_costs.sort(key=lambda x: x['cost'], reverse=True)
                
                monthly_summary_data.append({
                    'month': month_date,
                    'account_costs': account_costs
                })
                
            print(f"Successfully retrieved costs for all accounts in one API call")
            
        except Exception as e:
            print(f"Failed to get all costs in one call: {str(e)}")
            print("Falling back to per-account data retrieval (slower method)...")
            
            # Fall back to the original method of getting costs per account
            monthly_summary_data = []
            
            for i, date_range in enumerate(date_ranges):
                month_date = date_range['month_name']
                
                # Get cost data for all accounts for this month
                account_costs = []
                for account in accounts:
                    cost_data = self.get_cost_data(account['id'], date_range['start'], date_range['end'], i)
                    account_costs.append({
                        'id': account['id'],
                        'name': account['name'],
                        'cost': cost_data['total_cost']
                    })
                
                # Sort by cost (descending)
                account_costs.sort(key=lambda x: x['cost'], reverse=True)
                
                monthly_summary_data.append({
                    'month': month_date,
                    'account_costs': account_costs
                })
        
        # Create the summary visualization
        print("Creating organization summary visualization...")
        self._create_multi_month_organization_summary(
            monthly_summary_data,
            output_file
        )
        
        # Generate CSV data
        csv_file = os.path.join(
            output_path,
            f"aws-cost-summary-{start_date}-{end_date}.csv"
        )
        
        # Prepare CSV data
        csv_data = []
        for month_data in monthly_summary_data:
            month = month_data['month']
            
            for account in month_data['account_costs']:
                csv_data.append({
                    'month': month,
                    'account_id': account['id'],
                    'account_name': account['name'],
                    'cost': account['cost']
                })
        
        # Save CSV data
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False)
        
        print(f"Organization summary completed and saved to {output_file}")
        return output_file
        
    def _create_multi_month_organization_summary(self, monthly_summary_data, output_file):
        """Create an organization summary visualization with one bar per month."""
        # Set up the figure with improved proportions
        plt.figure(figsize=(16, 12))  # Wider figure to accommodate legend better
        
        # Create subplot with improved height ratios
        gs = plt.GridSpec(3, 1, height_ratios=[0.4, 0.6, 5], hspace=0.4)
        title_ax = plt.subplot(gs[0])
        summary_ax = plt.subplot(gs[1])
        chart_ax = plt.subplot(gs[2])
        
        # Set the title at the very top
        plt.sca(title_ax)
        title_ax.axis('off')  # Hide the axes
        date_range = f"{monthly_summary_data[0]['month']} to {monthly_summary_data[-1]['month']}"
        plt.text(0.5, 0.5, f'AWS Organization Cost Summary\n{date_range}', 
                 fontsize=16, fontweight='bold', ha='center', va='center')
        
        # Switch to the chart axis for the main bar chart
        plt.sca(chart_ax)
        
        # Get all accounts across all months with significant costs (>$0.01)
        all_accounts = set()
        for month_data in monthly_summary_data:
            # Only include accounts with meaningful costs
            accounts = [(account['id'], account['name']) for account in month_data['account_costs'] 
                       if account['cost'] > 0.01]
            all_accounts.update(accounts)
        
        # Calculate summary statistics
        total_cost = sum(sum(account['cost'] for account in month_data['account_costs']) 
                         for month_data in monthly_summary_data)
        avg_monthly_cost = total_cost / len(monthly_summary_data)
        account_count = len(all_accounts)
        
        # Convert to list and sort by account ID
        all_accounts = sorted(list(all_accounts), key=lambda x: x[0])
        
        # Create a color map for accounts
        account_colors = {}
        for i, (account_id, _) in enumerate(all_accounts):
            account_colors[account_id] = self.colors[i % len(self.colors)]
        
        # Prepare data for the stacked bar chart
        months = [data['month'] for data in monthly_summary_data]
        x_positions = np.arange(len(months))
        
        # Increase bar width for better proportions
        bar_width = 0.65
        
        # Build the stacked bars
        bottoms = np.zeros(len(months))
        handles = []  # For the legend
        
        # Set up the y-axis to have a good scale
        max_monthly_cost = max(sum(account['cost'] for account in month_data['account_costs']) 
                              for month_data in monthly_summary_data)
        plt.ylim(0, max_monthly_cost * 1.1)  # Add 10% margin at the top
        
        # Process each month's data
        for month_idx, month_data in enumerate(monthly_summary_data):
            # Filter accounts with significant costs
            significant_accounts = [acc for acc in month_data['account_costs'] if acc['cost'] > 0.01]
            
            # Get the top 9 accounts for this month
            top_accounts = significant_accounts[:9]
            
            # Calculate the "Other" category if needed
            other_accounts_cost = sum(account['cost'] for account in month_data['account_costs'][9:] 
                                     if account['cost'] > 0.01)
            negligible_cost = sum(account['cost'] for account in month_data['account_costs'] 
                                if account['cost'] <= 0.01)
            other_accounts_cost += negligible_cost
            
            # Add the top accounts
            for account in top_accounts:
                account_id = account['id']
                account_name = account['name']
                cost = account['cost']
                
                # Draw the bar segment with wider width
                bar = plt.bar(month_idx, cost, width=bar_width, bottom=bottoms[month_idx], 
                             color=account_colors.get(account_id, 'gray'))
                
                # Add cost label in the middle of the segment if it's big enough
                if cost > max_monthly_cost * 0.05:  # Only label if at least 5% of the maximum monthly cost
                    # Position the text in the middle of the segment
                    middle_y = bottoms[month_idx] + (cost / 2)
                    plt.text(month_idx, middle_y, f'${cost:.0f}', 
                            ha='center', va='center', fontsize=9, 
                            color='white', fontweight='bold')
                
                bottoms[month_idx] += cost
                
                # Add to legend handles only once
                legend_label = f"{account_name} ({account_id})"
                if legend_label not in [h.get_label() for h in handles]:
                    handles.append(plt.Rectangle((0,0), 1, 1, color=account_colors.get(account_id, 'gray'), 
                                               label=legend_label))
            
            # Add "Other" category if needed
            if other_accounts_cost > 0.01:  # Only show "Other" if it's meaningful
                plt.bar(month_idx, other_accounts_cost, width=bar_width, bottom=bottoms[month_idx], color='#cccccc')
                
                # Add cost label for "Other" if it's big enough
                if other_accounts_cost > max_monthly_cost * 0.05:
                    middle_y = bottoms[month_idx] + (other_accounts_cost / 2)
                    plt.text(month_idx, middle_y, f'${other_accounts_cost:.0f}', 
                            ha='center', va='center', fontsize=9,
                            color='black', fontweight='bold')
                
                bottoms[month_idx] += other_accounts_cost
                
                # Add to legend handles only once
                if 'Other Accounts' not in [h.get_label() for h in handles]:
                    handles.append(plt.Rectangle((0,0), 1, 1, color='#cccccc', label='Other Accounts'))
            
            # Add total cost label on top of the bar
            month_total_cost = sum(account['cost'] for account in month_data['account_costs'])
            plt.text(month_idx, bottoms[month_idx] * 1.02, f'${month_total_cost:.2f}', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Set chart labels
        plt.ylabel('Cost (USD)', fontsize=12, fontweight='bold')
        plt.xticks(x_positions, months, rotation=45, fontsize=10, fontweight='bold')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add legend with better positioning
        # Use more columns for the organization view legend to keep it compact
        plt.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.15),
                  ncol=4, fontsize=9, frameon=True, fancybox=True, shadow=True)
        
        # Now create the summary table in the middle
        plt.sca(summary_ax)
        summary_ax.axis('off')  # Hide the axes
        
        # Create a table for the summary stats
        col_labels = ['Total Cost', 'Average Monthly Cost', 'Account Count']
        table_data = [
            [f'${total_cost:.2f}', f'${avg_monthly_cost:.2f}', f'{account_count}']
        ]
        
        table = plt.table(cellText=table_data, colLabels=col_labels, loc='center', 
                         cellLoc='center', colColours=['#f2f2f2']*3)
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 1.5)  # Make the table taller
        
        # Add padding around the plot areas
        plt.subplots_adjust(bottom=0.28, left=0.1, right=0.9, top=0.9)
        
        # Save the figure using the output_file parameter
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Organization summary saved to {output_file}")

    def run(self):
        """Run the cost report generation process."""
        start_time = time.time()
        print("Starting AWS cost report generation...")
        
        # Get all linked accounts
        print("Retrieving linked accounts...")
        accounts = self.get_linked_accounts()
        print(f"Found {len(accounts)} linked accounts")
        
        # Get date ranges
        date_ranges = self.get_date_ranges()
        print(f"Processing {len(date_ranges)} months from {date_ranges[0]['start']} to {date_ranges[-1]['end']}")
        
        # Generate organization summary
        org_time_start = time.time()
        self.generate_organization_summary(accounts, date_ranges)
        org_time_end = time.time()
        print(f"Organization summary completed in {org_time_end - org_time_start:.1f} seconds")
        
        # Ask user if they want to continue with individual account reports for large orgs
        if not self.use_mock_data and len(accounts) > 20:  # Only ask for very large organizations
            user_input = input(f"Found {len(accounts)} accounts. Generate individual account reports? (y/n): ").strip().lower()
            if user_input != 'y':
                print("Skipping individual account reports.")
                print(f"\nAWS cost report generation completed in {time.time() - start_time:.1f} seconds!")
                return
        
        # Generate individual account reports
        print("\nGenerating individual account reports...")
        for i, account in enumerate(accounts):
            account_start_time = time.time()
            print(f"Account {i+1}/{len(accounts)}: {account['id']} ({account['name']})...")
            try:
                self.generate_cost_report(account['id'], account['name'], date_ranges)
                print(f"  Completed in {time.time() - account_start_time:.1f} seconds")
            except Exception as e:
                print(f"  Error generating report for account {account['id']}: {str(e)}")
                continue
            
            # Add a progress indicator
            progress = (i + 1) / len(accounts) * 100
            print(f"Progress: {progress:.1f}% ({i+1}/{len(accounts)} accounts)")
        
        print(f"\nAWS cost report generation completed in {time.time() - start_time:.1f} seconds!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AWS Cost Report Generator')
    parser.add_argument('--start-date', type=str, required=True,
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, required=True,
                        help='End date in YYYY-MM-DD format')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock data instead of real AWS API calls')
    parser.add_argument('--account', type=str,
                        help='Generate report for a specific account ID only')
    
    args = parser.parse_args()
    
    # Create and run the generator with hardcoded output directory
    output_dir = "aws_cost_reports"
    generator = AWSCostReportGenerator(
        output_dir=output_dir, 
        start_date=args.start_date, 
        end_date=args.end_date,
        use_mock_data=args.mock
    )
    
    # Check if we're only processing a specific account
    if args.account:
        print(f"Generating report for specific account: {args.account}")
        # Get date ranges
        date_ranges = generator.get_date_ranges()
        # Create a single-account list
        accounts = [{'id': args.account, 'name': f'Account {args.account}'}]
        # Generate just this account's report
        generator.generate_cost_report(args.account, f'Account {args.account}', date_ranges)
    else:
        # Run the normal process for all accounts
        generator.run()