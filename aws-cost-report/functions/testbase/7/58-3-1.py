import boto3
import os
import pandas as pd
import datetime
from dateutil.parser import parse
import argparse


class AWSCostDataRetriever:
    def __init__(self, output_dir="aws_cost_reports", start_date=None, end_date=None, use_mock_data=False):
        """
        Initialize the AWS Cost Data Retriever.
        
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
            'Amazon Route 53'
        ]
        
        self.mock_accounts = [
            {'id': '123456789012', 'name': 'Production Account'},
            {'id': '234567890123', 'name': 'Development Account'},
            {'id': '345678901234', 'name': 'Testing Account'},
            {'id': '456789012345', 'name': 'Staging Account'}
        ]
    
    def get_linked_accounts(self):
        """
        Get all linked accounts using Cost Explorer API or mock data.
        Returns a list of dictionaries with account IDs and names.
        """
        if self.use_mock_data:
            print("Using mock account data for testing")
            return self.mock_accounts
            
        accounts = []
        
        try:
            print("Retrieving linked accounts from AWS Cost Explorer API...")
            # Use Cost Explorer to get linked accounts
            response = self.ce_client.get_dimension_values(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
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
            
            # Handle pagination if needed
            next_token = response.get('NextPageToken')
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
    
    def get_account_cost_data(self, account_id, start_date, end_date):
        """Get cost data for a specific account and date range."""
        if self.use_mock_data:
            # Generate some mock data for testing
            import random
            random.seed(int(account_id) % 10000)
            
            services = []
            total_cost = 0
            
            for service in random.sample(self.mock_services, min(5, len(self.mock_services))):
                cost = random.uniform(100, 1000)
                services.append({'service': service, 'cost': cost})
                total_cost += cost
                
            return {
                'total_cost': total_cost,
                'services': services
            }
            
        try:
            # Get cost data for the account using AWS Cost Explorer API
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
            
            # Sort by cost (descending)
            services.sort(key=lambda x: x['cost'], reverse=True)
            
            # Calculate total cost by summing all service costs
            total_cost = sum(service['cost'] for service in services)
            
            return {
                'total_cost': total_cost,
                'services': services
            }
                
        except Exception as e:
            print(f"  Error getting cost data for account {account_id}: {str(e)}")
            return {
                'total_cost': 0,
                'services': []
            }
    
    def get_account_cost_data_by_month(self, account_id, date_ranges):
        """
        Get cost data for a specific account across multiple months.
        
        Args:
            account_id (str): AWS account ID
            date_ranges (list): List of date range dictionaries
        
        Returns:
            list: List of cost data dictionaries for each month
        """
        cost_data_by_month = []
        
        for i, date_range in enumerate(date_ranges):
            print(f"  Processing month {i+1}/{len(date_ranges)}: {date_range['month_name']}...")
            cost_data = self.get_account_cost_data(account_id, date_range['start'], date_range['end'])
            cost_data_by_month.append(cost_data)
            print(f"    Total cost: ${cost_data['total_cost']:.2f}, Services: {len(cost_data['services'])}")
            
        return cost_data_by_month
    
    def get_organization_cost_data(self, accounts, date_ranges):
        """
        Get cost data for the entire organization across multiple months.
        Returns a list of monthly cost data for all accounts.
        """
        monthly_cost_data = []
        
        for date_range in date_ranges:
            month = date_range['month_name']
            start = date_range['start']
            end = date_range['end']
            
            print(f"Processing month: {month} ({start} to {end})...")
            
            month_data = []
            
            if not self.use_mock_data:
                try:
                    # Try to get all account costs in a single API call (more efficient)
                    response = self.ce_client.get_cost_and_usage(
                        TimePeriod={
                            'Start': start,
                            'End': end
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
                    
                    if response.get('ResultsByTime') and response['ResultsByTime'][0].get('Groups'):
                        for group in response['ResultsByTime'][0]['Groups']:
                            account_id = group['Keys'][0]
                            cost = float(group['Metrics']['UnblendedCost']['Amount'])
                            
                            # Find account name
                            account_name = next((acc['name'] for acc in accounts if acc['id'] == account_id), 
                                              f"Account {account_id}")
                            
                            month_data.append({
                                'id': account_id,
                                'name': account_name,
                                'cost': cost
                            })
                        
                        # Sort by cost (descending)
                        month_data.sort(key=lambda x: x['cost'], reverse=True)
                        monthly_cost_data.append(month_data)
                        continue  # Skip the per-account approach if batch approach worked
                
                except Exception as e:
                    print(f"Error getting batch cost data: {e}")
                    print("Falling back to per-account queries...")
            
            # Fall back to per-account approach (or for mock data)
            account_costs = []
            for account in accounts:
                account_id = account['id']
                account_name = account['name']
                
                cost_data = self.get_account_cost_data(account_id, start, end)
                
                account_costs.append({
                    'id': account_id,
                    'name': account_name,
                    'cost': cost_data['total_cost']
                })
            
            # Sort by cost (descending)
            account_costs.sort(key=lambda x: x['cost'], reverse=True)
            monthly_cost_data.append(account_costs)
        
        return monthly_cost_data
    
    def save_account_cost_data(self, account_id, account_name, date_ranges, cost_data_by_month):
        """
        Save account cost data to a CSV file using the original script's directory structure.
        
        Args:
            account_id (str): AWS account ID
            account_name (str): AWS account name
            date_ranges (list): List of date range dictionaries
            cost_data_by_month (list): List of cost data dictionaries for each month
        
        Returns:
            str: Path to the CSV file
        """
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
        csv_file = os.path.join(
            output_path,
            f"aws-cost-report-{account_id}-{start_date}-{end_date}.csv"
        )
        
        # Prepare CSV data
        csv_data = []
        for i, month_data in enumerate(cost_data_by_month):
            month = date_ranges[i]['month_name']
            cost_data = month_data
            
            # Add row for total monthly cost
            csv_data.append({
                'month': month,
                'service': 'TOTAL',
                'cost': cost_data['total_cost']
            })
            
            # Add rows for each service
            for service_data in cost_data['services']:
                csv_data.append({
                    'month': month,
                    'service': service_data['service'],
                    'cost': service_data['cost']
                })
        
        # Save CSV data
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False)
        
        print(f"Account cost data saved to {csv_file}")
        return csv_file
    
    def save_organization_cost_data(self, accounts, date_ranges, monthly_cost_data):
        """
        Save organization-wide cost data to a CSV file using the original script's directory structure.
        
        Args:
            accounts (list): List of account dictionaries
            date_ranges (list): List of date range dictionaries
            monthly_cost_data (list): List of monthly cost data dictionaries
        
        Returns:
            str: Path to the CSV file
        """
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
        csv_file = os.path.join(
            output_path,
            f"aws-cost-summary-{start_date}-{end_date}.csv"
        )
        
        # Prepare CSV data
        csv_data = []
        for month_idx, month_data in enumerate(monthly_cost_data):
            month = date_ranges[month_idx]['month_name']
            
            for account_cost in month_data:
                csv_data.append({
                    'month': month,
                    'account_id': account_cost['id'],
                    'account_name': account_cost['name'],
                    'cost': account_cost['cost']
                })
        
        # Save CSV data
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False)
        
        print(f"Organization cost summary saved to {csv_file}")
        return csv_file
    
    def run(self):
        """Run the cost data retrieval process and save to CSV files."""
        print("Starting AWS cost data retrieval...")
        
        # Get all linked accounts
        accounts = self.get_linked_accounts()
        print(f"Found {len(accounts)} linked accounts")
        
        # Get date ranges
        date_ranges = self.get_date_ranges()
        print(f"Processing {len(date_ranges)} months from {date_ranges[0]['start']} to {date_ranges[-1]['end']}")
        
        # Get organization cost data
        print("\nRetrieving organization cost data...")
        monthly_org_data = self.get_organization_cost_data(accounts, date_ranges)
        
        # Save organization cost data
        org_csv = self.save_organization_cost_data(accounts, date_ranges, monthly_org_data)
        print(f"Organization data saved to {org_csv}")
        
        # Get and save individual account cost data
        print("\nRetrieving individual account cost data...")
        for i, account in enumerate(accounts):
            account_id = account['id']
            account_name = account['name']
            
            print(f"Account {i+1}/{len(accounts)}: {account_id} ({account_name})...")
            
            try:
                # Get cost data for each month
                cost_data_by_month = self.get_account_cost_data_by_month(account_id, date_ranges)
                
                # Skip accounts with no costs
                if all(month_data['total_cost'] == 0 for month_data in cost_data_by_month):
                    print(f"  Skipping - account has no costs for the selected period")
                    continue
                
                # Save account cost data
                account_csv = self.save_account_cost_data(account_id, account_name, date_ranges, cost_data_by_month)
            except Exception as e:
                print(f"  Error processing account {account_id}: {str(e)}")
                continue
            
            # Calculate progress
            progress = (i + 1) / len(accounts) * 100
            print(f"Progress: {progress:.1f}% ({i+1}/{len(accounts)} accounts)")
        
        print("\nAWS cost data retrieval completed!")
        print(f"Data saved to {self.output_dir} directory structure")
        
        return {
            "accounts": accounts,
            "date_ranges": date_ranges,
            "output_dir": self.output_dir
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AWS Cost Data Retriever')
    parser.add_argument('--start-date', type=str, required=True,
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, required=True,
                        help='End date in YYYY-MM-DD format')
    parser.add_argument('--mock', action='store_true',
                        help='Use mock data instead of real AWS API calls')
    parser.add_argument('--account', type=str,
                        help='Retrieve data for a specific account ID only')
    parser.add_argument('--output-dir', type=str, default='aws_cost_reports',
                        help='Output directory for cost reports')
    
    args = parser.parse_args()
    
    # Create and run the retriever
    retriever = AWSCostDataRetriever(
        output_dir=args.output_dir,
        start_date=args.start_date, 
        end_date=args.end_date,
        use_mock_data=args.mock
    )
    
    # If specific account is requested
    if args.account:
        print(f"Processing only account: {args.account}")
        # Get date ranges
        date_ranges = retriever.get_date_ranges()
        # Find account name or use generic placeholder
        accounts = retriever.get_linked_accounts()
        account_name = next((acc['name'] for acc in accounts if acc['id'] == args.account), f"Account {args.account}")
        # Get cost data for each month
        cost_data_by_month = retriever.get_account_cost_data_by_month(args.account, date_ranges)
        # Save account cost data
        account_csv = retriever.save_account_cost_data(args.account, account_name, date_ranges, cost_data_by_month)
        print(f"Account data saved to {account_csv}")
    else:
        # Run normal process for all accounts
        retriever.run()