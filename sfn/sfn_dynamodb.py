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

