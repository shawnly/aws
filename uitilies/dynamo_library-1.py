# dynamodb_lib.py

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')

# Define table names
XSV_CLIENT_TABLE = 'xsv_client'
SFN_EVENT_TABLE = 'sfn_event'

def query_client_by_id(client_id):
    """
    Query xsv_client table by client_id.

    Args:
        client_id (str): Client ID.

    Returns:
        dict: Client item.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    try:
        response = table.get_item(Key={'client_id': client_id})
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error querying client: {e}")
        return {}

def query_events_by_client_id(client_id):
    """
    Query sfn_event table by client_id.

    Args:
        client_id (str): Client ID.

    Returns:
        list: List of event items.
    """
    table = dynamodb.Table(SFN_EVENT_TABLE)
    try:
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('client_id').eq(client_id)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error querying events: {e}")
        return []

def put_client_item(client_item):
    """
    Put item into xsv_client table.

    Args:
        client_item (dict): Client item.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    try:
        table.put_item(Item=client_item)
        return True
    except ClientError as e:
        print(f"Error putting client item: {e}")
        return False

def put_event_item(event_item):
    """
    Put item into sfn_event table.

    Args:
        event_item (dict): Event item.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(SFN_EVENT_TABLE)
    try:
        table.put_item(Item=event_item)
        return True
    except ClientError as e:
        print(f"Error putting event item: {e}")
        return False

def update_client_item(client_id, update_expression, expression_attribute_values):
    """
    Update item in xsv_client table.

    Args:
        client_id (str): Client ID.
        update_expression (str): Update expression.
        expression_attribute_values (dict): Expression attribute values.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    try:
        table.update_item(
            Key={'client_id': client_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return True
    except ClientError as e:
        print(f"Error updating client item: {e}")
        return False

def update_event_item(event_id, update_expression, expression_attribute_values):
    """
    Update item in sfn_event table.

    Args:
        event_id (str): Event ID.
        update_expression (str): Update expression.
        expression_attribute_values (dict): Expression attribute values.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(SFN_EVENT_TABLE)
    try:
        table.update_item(
            Key={'event_id': event_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return True
    except ClientError as e:
        print(f"Error updating event item: {e}")
        return False

def query_client_by_id(client_id, attributes=None):
    """
    Query xsv_client table by client_id.

    Args:
        client_id (str): Client ID.
        attributes (list): List of attribute names to retrieve.

    Returns:
        dict: Client item.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    try:
        if attributes:
            response = table.get_item(
                Key={'client_id': client_id},
                ProjectionExpression=', '.join(attributes)
            )
        else:
            response = table.get_item(Key={'client_id': client_id})
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error querying client: {e}")
        return {}
    
    # Retrieve all attributes
    # client = query_client_by_id(client_id)
    # priority = client.get('priority_base')
    # sns_topic_arn = client.get('sns_topic_arn')
    # dns = client.get('client_dns')