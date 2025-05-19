#!/usr/bin/env python3
"""
AWS Raw Refund Data Extractor

This script extracts raw cost data with a focus on refunds from AWS Cost Explorer API
to help identify missing refund values that might cause discrepancies between
Cost Explorer API results and the AWS Console.
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

def get_raw_refund_data(account_id, start_date, end_date, output_dir="aws_raw_costs"):
    """
    Extract raw cost data with a focus on refunds directly from AWS Cost Explorer API.
    
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
    all_services_csv = os.path.join(output_path, f"{base_filename}_all_services.csv")
    refund_csv = os.path.join(output_path, f"{base_filename}_refunds.csv")
    monthly_csv = os.path.join(output_path, f"{base_filename}_monthly.csv")
    
    print(f"Extracting raw AWS cost data with focus on refunds for {account_id} from {start_date} to {end_date}...")
    
    # Prepare filter
    cost_filter = {}
    if account_id != 'all':
        cost_filter = {
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [account_id]
            }
        }
    
    # Get date ranges for monthly processing
    date_ranges = get_date_ranges(start_date, end_date)
    
    # Collect all data
    all_data = []
    refund_data = []
    monthly_data = []
    
    # Process month by month
    for date_range in date_ranges:
        month_start = date_range['start']
        month_end = date_range['end']
        month_name = date_range['month_name']
        
        print(f"Processing {month_name}...")
        
        # Get monthly totals first
        try:
            monthly_response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': month_start,
                    'End': month_end
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                Filter=cost_filter
            )
            
            # Process monthly response
            for period in monthly_response.get('ResultsByTime', []):
                metrics = period.get('Total', {})
                monthly_cost = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                
                monthly_data.append({
                    'month': month_name,
                    'start_date': month_start,
                    'end_date': month_end,
                    'blended_cost': monthly_cost
                })
        except Exception as e:
            print(f"Error getting monthly data for {month_name}: {str(e)}")
            continue
        
        # Now get the service breakdown with focus on refunds
        try:
            # Parameters for the API call
            params = {
                'TimePeriod': {
                    'Start': month_start,
                    'End': month_end
                },
                'Granularity': 'MONTHLY',
                'Metrics': ['BlendedCost'],
                'GroupBy': [
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                'Filter': cost_filter
            }
            
            # Make the API call
            next_token = None
            
            while True:
                # Add the next token if we have one
                if next_token:
                    params['NextPageToken'] = next_token
                
                response = ce_client.get_cost_and_usage(**params)
                
                # Process the response
                for period in response.get('ResultsByTime', []):
                    period_start = period.get('TimePeriod', {}).get('Start')
                    period_end = period.get('TimePeriod', {}).get('End')
                    
                    for group in period.get('Groups', []):
                        service = group.get('Keys', ['Unknown'])[0]
                        metrics = group.get('Metrics', {})
                        blended_cost = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                        
                        # Add to all services data
                        service_data = {
                            'month': month_name,
                            'start_date': period_start,
                            'end_date': period_end,
                            'service': service,
                            'blended_cost': blended_cost
                        }
                        all_data.append(service_data)
                        
                        # Check if this is a refund or credit
                        is_refund = ('refund' in service.lower() or 
                                     'credit' in service.lower() or
                                     blended_cost < 0)
                        
                        if is_refund:
                            refund_data.append(service_data)
                
                # Check if we have more pages
                next_token = response.get('NextPageToken')
                if not next_token:
                    break
            
            print(f"  Found {len(all_data)} services in {month_name}")
            print(f"  Found {len([d for d in refund_data if d['month'] == month_name])} potential refund entries in {month_name}")
            
        except Exception as e:
            print(f"Error getting service data for {month_name}: {str(e)}")
    
    # Write the data to CSV files
    # 1. All services
    if all_data:
        with open(all_services_csv, 'w', newline='') as csvfile:
            fieldnames = ['month', 'start_date', 'end_date', 'service', 'blended_cost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in all_data:
                writer.writerow(row)
            
        print(f"All services data saved to {all_services_csv}")
    
    # 2. Refund data
    if refund_data:
        with open(refund_csv, 'w', newline='') as csvfile:
            fieldnames = ['month', 'start_date', 'end_date', 'service', 'blended_cost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in refund_data:
                writer.writerow(row)
            
        print(f"Refund data saved to {refund_csv}")
        
        # Print refund summary
        print("\nRefund Summary:")
        refund_by_month = {}
        for row in refund_data:
            month = row['month']
            if month not in refund_by_month:
                refund_by_month[month] = 0
            refund_by_month[month] += row['blended_cost']
        
        for month, cost in sorted(refund_by_month.items()):
            print(f"  {month}: ${cost:.2f}")
    else:
        print("No refund data found!")
    
    # 3. Monthly data
    if monthly_data:
        with open(monthly_csv, 'w', newline='') as csvfile:
            fieldnames = ['month', 'start_date', 'end_date', 'blended_cost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in monthly_data:
                writer.writerow(row)
            
        print(f"Monthly totals saved to {monthly_csv}")
    
    # Also create a summary CSV showing what might be causing the discrepancies
    summary_csv = os.path.join(output_path, f"{base_filename}_summary.csv")
    
    # Calculate summary data
    summary_data = []
    for month in sorted(set(d['month'] for d in monthly_data)):
        month_total = next((d['blended_cost'] for d in monthly_data if d['month'] == month), 0)
        
        # Get all services for this month
        month_services = [d for d in all_data if d['month'] == month]
        services_total = sum(d['blended_cost'] for d in month_services)
        
        # Get refunds for this month
        month_refunds = [d for d in refund_data if d['month'] == month]
        refunds_total = sum(d['blended_cost'] for d in month_refunds)
        
        # Calculate the difference
        difference = month_total - services_total
        
        summary_data.append({
            'month': month,
            'month_total': month_total,
            'services_total': services_total,
            'refunds_total': refunds_total,
            'difference': difference,
            'difference_percent': (difference / month_total * 100) if month_total else 0
        })
    
    # Write summary to CSV
    if summary_data:
        with open(summary_csv, 'w', newline='') as csvfile:
            fieldnames = ['month', 'month_total', 'services_total', 'refunds_total', 'difference', 'difference_percent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in summary_data:
                writer.writerow(row)
            
        print(f"Summary data saved to {summary_csv}")
        
        # Print summary to console
        print("\nMonth Totals vs. Sum of Services:")
        for row in summary_data:
            print(f"  {row['month']}: Total=${row['month_total']:.2f}, Sum of Services=${row['services_total']:.2f}, " +
                  f"Refunds=${row['refunds_total']:.2f}, Difference=${row['difference']:.2f} ({row['difference_percent']:.2f}%)")
    
    print(f"\nRaw cost data extraction completed. Files saved to {output_path}")
    
    # Create a README file with instructions
    readme_file = os.path.join(output_path, "README.txt")
    with open(readme_file, 'w') as f:
        f.write("AWS Cost Data Raw Export\n")
        f.write("=======================\n\n")
        f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Date range: {start_date} to {end_date}\n\n")
        f.write("Files included:\n")
        f.write("1. *_all_services.csv - All services and their costs\n")
        f.write("2. *_refunds.csv - Just the refund/credit entries\n")
        f.write("3. *_monthly.csv - Monthly totals from the API\n")
        f.write("4. *_summary.csv - Comparison of monthly totals vs. sum of services\n\n")
        f.write("How to use this data:\n")
        f.write("1. Compare the refunds in *_refunds.csv with what you see in the AWS console\n")
        f.write("2. Check if any refund services are missing or have different amounts\n")
        f.write("3. Look at *_summary.csv to see if there's a consistent difference pattern\n")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Extract raw AWS refund data')
    parser.add_argument('--account', type=str, default='all',
                      help='AWS account ID to query (or "all" for all accounts)')
    parser.add_argument('--start-date', type=str, required=True,
                      help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, required=True,
                      help='End date in YYYY-MM-DD format')
    parser.add_argument('--output-dir', type=str, default='aws_raw_costs',
                      help='Directory to save output files')
    
    args = parser.parse_args()
    
    get_raw_refund_data(args.account, args.start_date, args.end_date, args.output_dir)

if __name__ == "__main__":
    main()