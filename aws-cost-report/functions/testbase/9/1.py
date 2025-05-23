#!/usr/bin/env python3
"""
AWS Cost Report Generator
Generates monthly cost reports for AWS Organization and linked accounts.
"""

import boto3
import pandas as pd
import argparse
import os
from datetime import datetime, timedelta
from collections import defaultdict
import json

class AWSCostReporter:
    def __init__(self):
        self.ce_client = boto3.client('ce')
        self.report_dir = 'aws_cost_report'
        
    def ensure_directory(self, path):
        """Create directory if it doesn't exist"""
        os.makedirs(path, exist_ok=True)
    
    def get_linked_accounts(self, start_date, end_date):
        """Get all linked account IDs and names from cost data"""
        print("Discovering linked accounts from cost data...")
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'LINKED_ACCOUNT'
                    }
                ]
            )
            
            accounts = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    account_id = group['Keys'][0]
                    if account_id and account_id != 'NoLinkedAccount':
                        # Try to get account name from dimension attributes
                        account_name = group.get('Attributes', {}).get('description', f'Account-{account_id}')
                        accounts[account_id] = account_name
            
            print(f"Found {len(accounts)} linked accounts")
            return accounts
            
        except Exception as e:
            print(f"Error getting linked accounts: {e}")
            return {}
    
    def get_account_cost_by_service(self, account_id, start_date, end_date):
        """Get cost breakdown by service for a specific account"""
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
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
            
            cost_data = []
            for result in response['ResultsByTime']:
                period_start = result['TimePeriod']['Start']
                period_end = result['TimePeriod']['End']
                
                for group in result['Groups']:
                    service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                    
                    blended_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    unblended_cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    usage_quantity = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    cost_data.append({
                        'Period_Start': period_start,
                        'Period_End': period_end,
                        'Service': service_name,
                        'Blended_Cost': blended_cost,
                        'Unblended_Cost': unblended_cost,
                        'Usage_Quantity': usage_quantity,
                        'Currency': group['Metrics']['BlendedCost']['Unit']
                    })
            
            return cost_data
            
        except Exception as e:
            print(f"Error getting cost data for account {account_id}: {e}")
            return []
    
    def get_organization_cost_summary(self, start_date, end_date):
        """Get organization-wide cost summary by service"""
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            cost_data = []
            for result in response['ResultsByTime']:
                period_start = result['TimePeriod']['Start']
                period_end = result['TimePeriod']['End']
                
                for group in result['Groups']:
                    service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                    
                    blended_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    unblended_cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    cost_data.append({
                        'Period_Start': period_start,
                        'Period_End': period_end,
                        'Service': service_name,
                        'Blended_Cost': blended_cost,
                        'Unblended_Cost': unblended_cost,
                        'Currency': group['Metrics']['BlendedCost']['Unit']
                    })
            
            return cost_data
            
        except Exception as e:
            print(f"Error getting organization cost summary: {e}")
            return []
    
    def save_to_excel(self, data, filepath, sheet_name='Cost Report'):
        """Save data to Excel file"""
        try:
            df = pd.DataFrame(data)
            if not df.empty:
                # Sort by cost descending
                if 'Blended_Cost' in df.columns:
                    df = df.sort_values('Blended_Cost', ascending=False)
                
                # Format currency columns
                currency_columns = ['Blended_Cost', 'Unblended_Cost']
                for col in currency_columns:
                    if col in df.columns:
                        df[col] = df[col].round(2)
                
                # Create Excel writer with formatting
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                print(f"Saved report: {filepath}")
                return True
            else:
                print(f"No data to save for {filepath}")
                return False
                
        except Exception as e:
            print(f"Error saving to {filepath}: {e}")
            return False
    
    def generate_reports(self, start_date, end_date, account_id=None):
        """Generate cost reports"""
        print(f"Generating AWS cost reports from {start_date} to {end_date}")
        
        # Create main report directory
        self.ensure_directory(self.report_dir)
        
        # Date range for filename
        date_range = f"{start_date}_{end_date}"
        
        if account_id:
            # Generate report for specific account only
            print(f"Generating report for specific account: {account_id}")
            account_dir = os.path.join(self.report_dir, account_id)
            self.ensure_directory(account_dir)
            
            cost_data = self.get_account_cost_by_service(account_id, start_date, end_date)
            if cost_data:
                filename = f"aws_cost_report_{date_range}.xlsx"
                filepath = os.path.join(account_dir, filename)
                self.save_to_excel(cost_data, filepath, f'Account {account_id}')
            else:
                print(f"No cost data found for account {account_id}")
        else:
            # Generate reports for all accounts
            accounts = self.get_linked_accounts(start_date, end_date)
            
            if not accounts:
                print("No linked accounts found. Generating organization summary only.")
            
            # Generate individual account reports
            for account_id, account_name in accounts.items():
                print(f"Processing account: {account_id} ({account_name})")
                
                account_dir = os.path.join(self.report_dir, account_id)
                self.ensure_directory(account_dir)
                
                cost_data = self.get_account_cost_by_service(account_id, start_date, end_date)
                if cost_data:
                    filename = f"aws_cost_report_{date_range}.xlsx"
                    filepath = os.path.join(account_dir, filename)
                    self.save_to_excel(cost_data, filepath, f'Account {account_id}')
            
            # Generate organization summary report
            print("Generating organization cost summary...")
            org_cost_data = self.get_organization_cost_summary(start_date, end_date)
            if org_cost_data:
                org_filename = f"organization_cost_summary_{date_range}.xlsx"
                org_filepath = os.path.join(self.report_dir, org_filename)
                self.save_to_excel(org_cost_data, org_filepath, 'Organization Summary')
        
        print("Report generation completed!")

def main():
    parser = argparse.ArgumentParser(description='Generate AWS cost reports')
    parser.add_argument('--start-date', required=True, 
                       help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True,
                       help='End date in YYYY-MM-DD format')
    parser.add_argument('--account-id', 
                       help='Optional: Generate report for specific account ID only')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        return 1
    
    # Initialize reporter and generate reports
    try:
        reporter = AWSCostReporter()
        reporter.generate_reports(args.start_date, args.end_date, args.account_id)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())