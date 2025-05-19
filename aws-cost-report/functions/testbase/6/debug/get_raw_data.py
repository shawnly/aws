#!/usr/bin/env python3
"""
AWS Raw Cost Data Extractor

This script extracts raw cost data directly from AWS Cost Explorer API with minimal processing
to ensure all cost values are captured. It's specifically designed to help debug discrepancies
between Cost Explorer API results and the AWS Console.
"""

import boto3
import csv
import os
import datetime
import argparse
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

def get_date_ranges(start_date, end_date):
    """Generate monthly date ranges between start and end dates."""
    date_ranges = []
    
    # Parse input dates
    start_dt = parse(start_date)
    end_dt = parse(end_date)
    
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

def get_raw_cost_data(account_id, start_date, end_date, output_dir="aws_raw_costs"):
    """
    Extract raw cost data directly from AWS Cost Explorer API with minimal processing.
    
    Args:
        account_id: AWS account ID to query (or 'all' for all accounts)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Directory to save output files
    """
    # Create AWS client
    ce_client = boto3.client('ce')
    
    # Create output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"raw_data_{timestamp}")
    os.makedirs(output_path, exist_ok=True)
    
    # Base CSV filename
    base_filename = f"raw_cost_data_{start_date}_{end_date}"
    if account_id != 'all':
        base_filename = f"account_{account_id}_{base_filename}"
    
    # Setup output files
    cost_csv = os.path.join(output_path, f"{base_filename}.csv")
    metrics_csv = os.path.join(output_path, f"{base_filename}_metrics.csv")
    monthly_csv = os.path.join(output_path, f"{base_filename}_monthly.csv")
    
    print(f"Extracting raw AWS cost data for {account_id} from {start_date} to {end_date}...")
    
    # Prepare filter
    cost_filter = {}
    if account_id != 'all':
        cost_filter = {
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    
    # Get monthly data first (without service breakdown)
    try:
        print("Getting monthly totals with all metrics...")
        monthly_response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost', 'BlendedCost', 'AmortizedCost', 'NetAmortizedCost', 'NetUnblendedCost'],
            Filter=cost_filter
        )
        
        # Write monthly totals to CSV
        with open(monthly_csv, 'w', newline='') as csvfile:
            fieldnames = ['month_start', 'month_end', 'unblended_cost', 'blended_cost', 'amortized_cost', 
                         'net_amortized_cost', 'net_unblended_cost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for period in monthly_response.get('ResultsByTime', []):
                metrics = period.get('Total', {})
                row = {
                    'month_start': period.get('TimePeriod', {}).get('Start'),
                    'month_end': period.get('TimePeriod', {}).get('End'),
                    'unblended_cost': float(metrics.get('UnblendedCost', {}).get('Amount', 0)),
                    'blended_cost': float(metrics.get('BlendedCost', {}).get('Amount', 0)),
                    'amortized_cost': float(metrics.get('AmortizedCost', {}).get('Amount', 0)) if 'AmortizedCost' in metrics else 0,
                    'net_amortized_cost': float(metrics.get('NetAmortizedCost', {}).get('Amount', 0)) if 'NetAmortizedCost' in metrics else 0,
                    'net_unblended_cost': float(metrics.get('NetUnblendedCost', {}).get('Amount', 0)) if 'NetUnblendedCost' in metrics else 0
                }
                writer.writerow(row)
            
        print(f"Monthly totals saved to {monthly_csv}")
        
    except Exception as e:
        print(f"Error getting monthly data: {str(e)}")
    
    # Now get the detailed data with service breakdown
    try:
        print("Getting detailed cost data with service breakdown...")
        
        # Use NextPageToken to get all results since there could be many services
        next_token = None
        all_data = []
        metrics_data = []
        
        # Get date ranges for monthly processing
        date_ranges = get_date_ranges(start_date, end_date)
        
        # Process month by month to avoid issues with too many results
        for date_range in date_ranges:
            month_start = date_range['start']
            month_end = date_range['end']
            month_name = date_range['month_name']
            
            print(f"Processing {month_name}...")
            
            # Get the metrics first for this month
            metrics_response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': month_start,
                    'End': month_end
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'BlendedCost', 'AmortizedCost', 'NetAmortizedCost', 'NetUnblendedCost'],
                Filter=cost_filter
            )
            
            # Process metrics response
            for period in metrics_response.get('ResultsByTime', []):
                metrics = period.get('Total', {})
                metrics_data.append({
                    'month': month_name,
                    'start_date': month_start,
                    'end_date': month_end,
                    'unblended_cost': float(metrics.get('UnblendedCost', {}).get('Amount', 0)),
                    'blended_cost': float(metrics.get('BlendedCost', {}).get('Amount', 0)),
                    'amortized_cost': float(metrics.get('AmortizedCost', {}).get('Amount', 0)) if 'AmortizedCost' in metrics else 0,
                    'net_amortized_cost': float(metrics.get('NetAmortizedCost', {}).get('Amount', 0)) if 'NetAmortizedCost' in metrics else 0,
                    'net_unblended_cost': float(metrics.get('NetUnblendedCost', {}).get('Amount', 0)) if 'NetUnblendedCost' in metrics else 0
                })
            
            # Now get the service breakdown
            next_token = None
            while True:
                # Parameters for the API call
                params = {
                    'TimePeriod': {
                        'Start': month_start,
                        'End': month_end
                    },
                    'Granularity': 'MONTHLY',
                    'Metrics': ['UnblendedCost', 'BlendedCost'],
                    'GroupBy': [
                        {
                            'Type': 'DIMENSION',
                            'Key': 'SERVICE'
                        }
                    ],
                    'Filter': cost_filter
                }
                
                # Add the next token if we have one
                if next_token:
                    params['NextPageToken'] = next_token
                
                # Make the API call
                response = ce_client.get_cost_and_usage(**params)
                
                # Process the response
                for period in response.get('ResultsByTime', []):
                    period_start = period.get('TimePeriod', {}).get('Start')
                    period_end = period.get('TimePeriod', {}).get('End')
                    
                    for group in period.get('Groups', []):
                        service = group.get('Keys', ['Unknown'])[0]
                        metrics = group.get('Metrics', {})
                        
                        all_data.append({
                            'month': month_name,
                            'start_date': period_start,
                            'end_date': period_end,
                            'service': service,
                            'unblended_cost': float(metrics.get('UnblendedCost', {}).get('Amount', 0)),
                            'blended_cost': float(metrics.get('BlendedCost', {}).get('Amount', 0))
                        })
                
                # Check if we have more pages
                next_token = response.get('NextPageToken')
                if not next_token:
                    break
        
        # Write the detailed data to CSV
        if all_data:
            with open(cost_csv, 'w', newline='') as csvfile:
                fieldnames = ['month', 'start_date', 'end_date', 'service', 'unblended_cost', 'blended_cost']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in all_data:
                    writer.writerow(row)
                
            print(f"Detailed cost data saved to {cost_csv}")
        
        # Write metrics data to CSV
        if metrics_data:
            with open(metrics_csv, 'w', newline='') as csvfile:
                fieldnames = ['month', 'start_date', 'end_date', 'unblended_cost', 'blended_cost', 
                             'amortized_cost', 'net_amortized_cost', 'net_unblended_cost']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in metrics_data:
                    writer.writerow(row)
                
            print(f"Metrics data saved to {metrics_csv}")
        
    except Exception as e:
        print(f"Error getting detailed data: {str(e)}")
    
    print(f"Raw cost data extraction completed. Files saved to {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Extract raw AWS cost data')
    parser.add_argument('--account', type=str, default='all',
                      help='AWS account ID to query (or "all" for all accounts)')
    parser.add_argument('--start-date', type=str, required=True,
                      help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, required=True,
                      help='End date in YYYY-MM-DD format')
    parser.add_argument('--output-dir', type=str, default='aws_raw_costs',
                      help='Directory to save output files')
    
    args = parser.parse_args()
    
    get_raw_cost_data(args.account, args.start_date, args.end_date, args.output_dir)

if __name__ == "__main__":
    main()