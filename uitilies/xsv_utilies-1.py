import boto3
import os
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Get table names from Lambda environment variables
CLIENT_TABLE_NAME = os.environ.get('XSV_CLIENT_TABLE')
UPLOAD_EVENT_TABLE_NAME = os.environ.get('XSV_S3_UPLOAD_EVENT_TABLE')

# Helper function to get DynamoDB table resource
def get_table(table_name):
    """Return a DynamoDB table resource."""
    return dynamodb.Table(table_name)


# -----------------------------------
# xsv_client Table Functions
# -----------------------------------

def get_client(client_id):
    """
    Retrieve the entire client record from the xsv_client table using client_id.
    
    :param client_id: The unique client_id (primary key) of the client.
    :return: A dictionary representing the client record if found, otherwise None.
    """
    table = get_table(CLIENT_TABLE_NAME)
    
    try:
        response = table.get_item(Key={'client_id': client_id})
        return response.get('Item', None)
    except ClientError as e:
        print(f"Error fetching client record: {e.response['Error']['Message']}")
        return None


def get_client_attributes(client_id, attributes):
    """
    Retrieve specific attributes for a client from the xsv_client table.
    
    :param client_id: The unique client_id of the client.
    :param attributes: List of attribute names to retrieve (e.g., ['sns_topic_arn', 'client_name']).
    :return: A dictionary with the requested attributes, or None if the client is not found.
    """
    table = get_table(CLIENT_TABLE_NAME)
    
    try:
        response = table.get_item(
            Key={'client_id': client_id},
            ProjectionExpression=", ".join(attributes)
        )
        return response.get('Item', None)
    except ClientError as e:
        print(f"Error fetching client attributes: {e.response['Error']['Message']}")
        return None


def put_client(client_id, attributes):
    """
    Insert or update a client record in the xsv_client table.
    
    :param client_id: The unique client_id of the client.
    :param attributes: A dictionary of attribute-value pairs to insert or update.
    :return: True if the operation was successful, otherwise False.
    """
    table = get_table(CLIENT_TABLE_NAME)
    attributes['client_id'] = client_id  # Ensure client_id is part of the item
    
    try:
        table.put_item(Item=attributes)
        return True
    except ClientError as e:
        print(f"Error putting client item: {e.response['Error']['Message']}")
        return False


# -----------------------------------
# xsv_s3_upload_event_table Functions
# -----------------------------------

def get_upload_event(event_id):
    """
    Retrieve the entire event record from the xsv_s3_upload_event_table using event_id.
    
    :param event_id: The unique event_id (primary key) of the event.
    :return: A dictionary representing the event record if found, otherwise None.
    """
    table = get_table(UPLOAD_EVENT_TABLE_NAME)
    
    try:
        response = table.get_item(Key={'event_id': event_id})
        return response.get('Item', None)
    except ClientError as e:
        print(f"Error fetching upload event record: {e.response['Error']['Message']}")
        return None


def get_upload_event_attributes(event_id, attributes):
    """
    Retrieve specific attributes for an upload event from the xsv_s3_upload_event_table.
    
    :param event_id: The unique event_id of the upload event.
    :param attributes: List of attribute names to retrieve (e.g., ['event_status', 's3_key']).
    :return: A dictionary with the requested attributes, or None if the event is not found.
    """
    table = get_table(UPLOAD_EVENT_TABLE_NAME)
    
    try:
        response = table.get_item(
            Key={'event_id': event_id},
            ProjectionExpression=", ".join(attributes)
        )
        return response.get('Item', None)
    except ClientError as e:
        print(f"Error fetching upload event attributes: {e.response['Error']['Message']}")
        return None


def put_upload_event(event_id, attributes):
    """
    Insert or update an event record in the xsv_s3_upload_event_table.
    
    :param event_id: The unique event_id of the event.
    :param attributes: A dictionary of attribute-value pairs to insert or update.
    :return: True if the operation was successful, otherwise False.
    """
    table = get_table(UPLOAD_EVENT_TABLE_NAME)
    attributes['event_id'] = event_id  # Ensure event_id is part of the item
    
    try:
        table.put_item(Item=attributes)
        return True
    except ClientError as e:
        print(f"Error putting upload event item: {e.response['Error']['Message']}")
        return False
