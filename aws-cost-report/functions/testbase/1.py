import boto3
import json

def list_aws_accounts():
    """
    Lists AWS accounts in the organization with their IDs and names.
    Prints raw response and account details.
    """
    # Create a client for the AWS Organizations service
    org_client = boto3.client('organizations')
    
    try:
        # Get accounts (without pagination)
        response = org_client.list_accounts()
        
        # Print the entire raw response
        print("Raw API Response:")
        print(json.dumps(response, indent=2, default=str))
        print("\n" + "-" * 50 + "\n")
        
        # Process and print each account's details
        print("Account Details:")
        for account in response.get('Accounts', []):
            print("\nAccount Information:")
            print(json.dumps(account, indent=2, default=str))
            
        # Extract and return just ID and name
        accounts = []
        for account in response.get('Accounts', []):
            accounts.append({
                'AccountId': account.get('Id'),
                'AccountName': account.get('Name')
            })
                
        return accounts
        
    except Exception as e:
        print(f"Error fetching AWS accounts: {e}")
        return []

if __name__ == "__main__":
    # Get the list of AWS accounts
    aws_accounts = list_aws_accounts()
    
    # Print the summarized results
    print("\n" + "-" * 50)
    print("\nSummarized Account List:")
    print(f"Total accounts found: {len(aws_accounts)}")
    print(f"{'Account ID':<24} {'Account Name':<40}")
    print("-" * 64)
    
    for account in aws_accounts:
        print(f"{account['AccountId']:<24} {account['AccountName']:<40}")