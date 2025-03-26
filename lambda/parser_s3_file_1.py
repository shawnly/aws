import json
import boto3
import yaml  # This needs to be installed as a dependency

def lambda_handler(event, context):
    """
    Lambda function to download a YAML file from S3, parse it, and extract 
    repository, tag values, and check if it's a DSS test.
    
    Args:
        event (dict): Lambda event data, should contain:
            - bucket: S3 bucket name
            - key: S3 object key (path to the YAML file)
        context (object): Lambda context object
        
    Returns:
        dict: Response containing repository, tag values, and dss_test_only flag
    """
    try:
        # Get S3 bucket and file key from the event
        bucket = event.get('bucket')
        file_key = event.get('key')
        
        if not bucket or not file_key:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Missing required parameters: bucket and key'
                })
            }
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download YAML file from S3
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        yaml_content = response['Body'].read().decode('utf-8')
        
        # Parse YAML content
        yaml_data = yaml.safe_load(yaml_content)
        
        # Extract repository and tag values
        repository = yaml_data.get('metadata', {}).get('repository')
        tag = yaml_data.get('metadata', {}).get('tag')
        
        # Check if suite_type is "suites.interuss.dss.all_tests"
        suite_type = yaml_data.get('v1', {}).get('action', {}).get('test_suite', {}).get('suite_type')
        dss_test_only = suite_type == "suites.interuss.dss.all_tests"
        
        # Prepare and return response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'repository': repository,
                'tag': tag,
                'dss_test_only': dss_test_only
            })
        }
        
    except Exception as e:
        # Handle errors
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        }