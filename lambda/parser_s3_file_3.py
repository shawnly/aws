import json
import boto3
import yaml  # This needs to be installed as a dependency

def parse_s3_yaml(bucket, file_key):
    """
    Download and parse a YAML file from S3, extract repository, tag values, 
    and check if it's a DSS test.
    
    Args:
        bucket (str): S3 bucket name
        file_key (str): S3 object key (path to the YAML file)
        
    Returns:
        dict: Dictionary containing repository, tag, and dss_test_only flag
    
    Raises:
        Exception: Any errors that occur during S3 operations or YAML parsing
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download YAML file from S3
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        yaml_content = response['Body'].read().decode('utf-8')
        
        # Parse YAML content
        yaml_data = yaml.safe_load(yaml_content)
        
        # Set default values
        repository = None
        tag = None
        dss_test_only = False
        
        # Extract repository and tag values if they exist
        if yaml_data and isinstance(yaml_data, dict):
            metadata = yaml_data.get('metadata', {})
            if isinstance(metadata, dict):
                repository = metadata.get('repository')
                tag = metadata.get('tag')
            
            # Check if suite_type is "suites.interuss.dss.all_tests"
            v1 = yaml_data.get('v1', {})
            if isinstance(v1, dict):
                action = v1.get('action', {})
                if isinstance(action, dict):
                    test_suite = action.get('test_suite', {})
                    if isinstance(test_suite, dict):
                        suite_type = test_suite.get('suite_type')
                        dss_test_only = suite_type == "suites.interuss.dss.all_tests"
        
        # Return extracted data
        return {
            'repository': repository,
            'tag': tag,
            'dss_test_only': dss_test_only
        }
        
    except Exception as e:
        print(f"Error in parse_s3_yaml: {str(e)}")
        raise Exception(f"Failed to parse S3 YAML file: {str(e)}")

def lambda_handler(event, context):
    """
    Example Lambda handler that uses the parse_s3_yaml function.
    
    Args:
        event (dict): Lambda event data, should contain:
            - bucket: S3 bucket name
            - key: S3 object key (path to the YAML file)
        context (object): Lambda context object
        
    Returns:
        dict: Response containing parsed YAML data
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
        
        # Call the YAML parsing function
        yaml_data = parse_s3_yaml(bucket, file_key)
        
        # Return the parsed data
        return {
            'statusCode': 200,
            'body': json.dumps(yaml_data)
        }
        
    except Exception as e:
        # Handle errors
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        }

# Example of how to use the function in another context
def another_function(bucket, file_key):
    """
    Example of how to use the parse_s3_yaml function in another context.
    """
    try:
        yaml_data = parse_s3_yaml(bucket, file_key)
        
        # Do something with the parsed data
        repository = yaml_data['repository']
        tag = yaml_data['tag']
        dss_test_only = yaml_data['dss_test_only']
        
        # Process data further...
        
        return {
            'success': True,
            'data': yaml_data
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }