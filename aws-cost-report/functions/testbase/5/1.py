import boto3
import json

# Replace with your AWS credentials and region
aws_region = "your_region"
aws_access_key = "your_access_key"
aws_secret_key = "your_secret_key"

# Initialize the Cost Explorer client
ce_client = boto3.client('ce', region_name=aws_region,
                         aws_access_key_id=aws_access_key,
                         aws_secret_access_key=aws_secret_key)

# Define the time period (e.g., current month)
start_date = "2025-05-01"
end_date = "2025-06-01"

# Specify the cost type as Amortized
cost_type = "Amortized"

# Get cost data using the API
response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date,
        'End': end_date
    },
    Granularity="DAILY",  # You can also use MONTHLY
    CostTypes=[
        cost_type
    ],
    # Add filters (e.g., Service) if needed
    # Dimensions={}  # Example: {"key": "SERVICE"}
    # ... other parameters as needed
)

# Process the response (example: extract costs and save to a file)
if response['ResultsByTime']:
    with open('amortized_costs.csv', 'w') as csv_file:
        csv_file.write('Date,Service,Cost\n')  # CSV header

        for result in response['ResultsByTime']:
            for item in result['Cost']:
                # Extract data from the JSON (example)
                date = result['TimePeriod']['Start']
                service = item['Service']
                cost = item['AmortizedCost']

                # Write to the CSV file
                csv_file.write(f"{date},{service},{cost}\n")

    print(f"Amortized cost data exported to 'amortized_costs.csv'")
else:
    print("No cost data found for the specified period.")
