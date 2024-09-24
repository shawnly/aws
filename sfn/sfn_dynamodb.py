import boto3
from botocore.exceptions import ClientError

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')

def update_event_in_dynamodb(event_id, client_id, instance_id):
    """
    Updates the DynamoDB table with client_id and instance_id for the given event_id.

    Parameters:
    - event_id (str): The unique identifier for the event. This is the primary key in the DynamoDB table.
    - client_id (str): The ID of the client to be updated in the DynamoDB table.
    - instance_id (str): The EC2 instance ID to be updated in the DynamoDB table.

    Returns:
    - A dictionary indicating the success or failure of the operation.
    """
    table_name = 'sfn_event_table'  # Your DynamoDB table name
    sfn_event_table = dynamodb.Table(table_name)

    try:
        # Update DynamoDB item with event_id as the primary key
        response = sfn_event_table.update_item(
            Key={
                'event_id': event_id  # Primary key
            },
            UpdateExpression="SET client_id = :c, instance_id = :i",
            ExpressionAttributeValues={
                ':c': client_id,  # Value for client_id
                ':i': instance_id  # Value for instance_id
            },
            ReturnValues="UPDATED_NEW"  # Returns the updated attributes
        )

        # Print success message for debugging or monitoring
        print(f"Successfully updated event {event_id} with client_id {client_id} and instance_id {instance_id}")

        # Return a success response
        return {
            'status': 'success',
            'updatedAttributes': response['Attributes']
        }

    except ClientError as e:
        # Handle any client errors (e.g., table does not exist, insufficient permissions)
        error_message = f"Failed to update DynamoDB: {e.response['Error']['Message']}"
        print(error_message)
        return {
            'status': 'error',
            'message': error_message
        }

# Example usage in Lambda function
def lambda_handler(event, context):
    """
    Lambda handler function to update DynamoDB with event details.

    Parameters:
    - event: The event data passed to the Lambda function, expected to contain event_id, client_id, and instance_id.
    - context: Runtime information for the Lambda function.

    Returns:
    - A JSON response indicating success or failure.
    """
    # Extract parameters from the event input
    event_id = event.get('event_id')
    client_id = event.get('client_id')
    instance_id = event.get('instance_id')

    # Validate that required fields are provided
    if not event_id or not client_id or not instance_id:
        return {
            'statusCode': 400,
            'body': 'Missing required fields: event_id, client_id, and instance_id are required.'
        }

    # Call the function to update DynamoDB
    update_result = update_event_in_dynamodb(event_id, client_id, instance_id)

    # Return the result of the DynamoDB update operation
    if update_result['status'] == 'success':
        return {
            'statusCode': 200,
            'body': f"Successfully updated event {event_id} with client_id {client_id} and instance_id {instance_id}."
        }
    else:
        return {
            'statusCode': 500,
            'body': f"Error updating DynamoDB: {update_result['message']}"
        }



import boto3
from botocore.exceptions import ClientError

# Initialize the DynamoDB resource and EC2 client
dynamodb = boto3.resource('dynamodb')
ec2 = boto3.client('ec2')

def retrieve_instance_id_by_event_id(event_id):
    """
    Retrieves the instance_id from the DynamoDB table for a given event_id.

    Parameters:
    - event_id (str): The unique identifier for the event (primary key in DynamoDB).

    Returns:
    - A string with the instance_id if found, otherwise an error message.
    """
    table_name = 'sfn_event_table'  # DynamoDB table name
    sfn_event_table = dynamodb.Table(table_name)
    
    try:
        # Query the DynamoDB table to get the instance_id for the given event_id
        response = sfn_event_table.get_item(
            Key={
                'event_id': event_id  # Primary key
            }
        )

        # Check if the item is present in the response
        if 'Item' in response:
            instance_id = response['Item'].get('instance_id')
            print(f"Successfully retrieved instance_id {instance_id} for event_id {event_id}")
            return instance_id
        else:
            raise ValueError(f"No item found for event_id {event_id}")

    except ClientError as e:
        # Handle errors from the DynamoDB operation
        error_message = f"Failed to retrieve instance_id for event_id {event_id}: {e.response['Error']['Message']}"
        print(error_message)
        return None

    except ValueError as ve:
        # Handle case where no item is found
        print(str(ve))
        return None


def stop_ec2_instance(instance_id):
    """
    Stops an EC2 instance based on the provided instance_id.

    Parameters:
    - instance_id (str): The EC2 instance ID that should be stopped.

    Returns:
    - A dictionary indicating the success or failure of the stop operation.
    """
    try:
        # Stop the EC2 instance
        response = ec2.stop_instances(
            InstanceIds=[instance_id]
        )
        
        # Retrieve the current state of the instance after stop call
        stopping_state = response['StoppingInstances'][0]['CurrentState']['Name']
        print(f"Successfully stopped instance {instance_id}. Current state: {stopping_state}")
        
        return {
            'status': 'success',
            'message': f"Instance {instance_id} is now in {stopping_state} state."
        }

    except ClientError as e:
        # Handle errors during the EC2 stop operation
        error_message = f"Failed to stop instance {instance_id}: {e.response['Error']['Message']}"
        print(error_message)
        return {
            'status': 'error',
            'message': error_message
        }
