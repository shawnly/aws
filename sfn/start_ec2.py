import boto3
from botocore.exceptions import ClientError

# Initialize boto3 clients outside the handler to avoid re-initializing them on every Lambda invocation
ec2_client = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')

# DynamoDB table name
sfn_event_table = dynamodb.Table('sfn_event_table')  # Replace with your actual DynamoDB table name

def insert_into_dynamodb(instance_id, client_id):
    """
    Inserts the instance_id and client_id into the DynamoDB table.
    
    Parameters:
    - instance_id: The EC2 instance ID to be stored in DynamoDB as a string.
    - client_id: The client ID to be stored in DynamoDB as a string.

    Returns:
    - A dictionary containing the result of the DynamoDB operation (success or error).
    """
    try:
        # Ensure instance_id and client_id are strings
        dynamodb_response = sfn_event_table.put_item(
            Item={
                'instance_id': str(instance_id),  # Ensure instance_id is a string
                'client_id': str(client_id)       # Ensure client_id is a string
            }
        )
        print(f"Successfully added instance_id {instance_id} and client_id {client_id} to DynamoDB")
        return {
            'status': 'success',
            'instance_id': instance_id,
            'client_id': client_id
        }
    except ClientError as e:
        error_message = f"Failed to insert into DynamoDB: {e}"
        print(error_message)
        return {
            'status': 'error',
            'message': error_message
        }

def start_ec2_and_update_dynamodb(launch_template_id, launch_template_version, client_id):
    """
    Starts an EC2 instance using a launch template, retrieves the instance ID,
    and inserts the instance ID and client ID into DynamoDB.

    Parameters:
    - launch_template_id: The ID of the EC2 launch template to use for starting the instance.
    - launch_template_version: The version of the EC2 launch template.
    - client_id: The client ID to be stored in DynamoDB along with the EC2 instance ID.

    Returns:
    - A dictionary containing the instance ID and client ID on success, or an error message on failure.
    """

    # Step 1: Define special tag
    special_tag_key = 'SpecialTagKey'
    special_tag_value = 'SpecialTagValue'

    try:
        # Step 2: Launch EC2 instance using the provided launch template and add the special tag
        response = ec2_client.run_instances(
            LaunchTemplate={
                'LaunchTemplateId': launch_template_id,
                'Version': launch_template_version
            },
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': special_tag_key,
                            'Value': special_tag_value
                        }
                    ]
                }
            ]
        )

        # Step 3: Retrieve the instance ID from the response
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Successfully launched EC2 instance with ID: {instance_id}")

        # Step 4: Insert the instance ID and client ID into DynamoDB using the new function
        dynamodb_result = insert_into_dynamodb(instance_id, client_id)

        return dynamodb_result

    except ClientError as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        return {
            'status': 'error',
            'message': error_message
        }

def lambda_handler(event, context):
    """
    Lambda handler function that receives the event payload and triggers the
    start_ec2_and_update_dynamodb function.

    Parameters:
    - event: The event payload received by the Lambda function. It should contain the
      required parameters like 'launch_template_id', 'launch_template_version', and 'client_id'.
    - context: Lambda context object (not used in this function).

    Returns:
    - The result from the start_ec2_and_update_dynamodb function.
    """
    # Extract parameters from the event
    launch_template_id = event.get('launch_template_id', 'your-launch-template-id')  # Default ID for testing
    launch_template_version = event.get('launch_template_version', '1')  # Default to version 1 for testing
    client_id = event.get('client_id', '123456')  # Default client ID for testing

    # Call the function to start EC2 and update DynamoDB
    result = start_ec2_and_update_dynamodb(launch_template_id, launch_template_version, client_id)

    # Return the result to the caller
    return result
