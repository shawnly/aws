import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional

# Initialize a DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Table names
XSV_CLIENT_TABLE = 'xsv_client'
XSV_S3_UPLOAD_EVENT_TABLE = 'xsv_s3_upload_event'

# XSV Client Table Operations

def get_client(client_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a client item from the xsv_client table.

    Args:
        client_id (str): The client ID to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The client item if found, None otherwise.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    try:
        response = table.get_item(Key={'client_id': client_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error retrieving client: {e.response['Error']['Message']}")
        return None

def get_client_attributes(client_id: str, attributes: List[str]) -> Optional[Dict[str, Any]]:
    """
    Retrieve specific attributes of a client from the xsv_client table.

    Args:
        client_id (str): The client ID to retrieve.
        attributes (List[str]): List of attribute names to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary of requested attributes if found, None otherwise.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    projection_expression = ', '.join(attributes)
    try:
        response = table.get_item(
            Key={'client_id': client_id},
            ProjectionExpression=projection_expression
        )
        return response.get('Item')
    except ClientError as e:
        print(f"Error retrieving client attributes: {e.response['Error']['Message']}")
        return None

def put_client(client_id: str, attributes: Dict[str, Any]) -> bool:
    """
    Put a new item or replace an existing item in the xsv_client table.

    Args:
        client_id (str): The client ID of the item.
        attributes (Dict[str, Any]): A dictionary of attribute names and values to put.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    table = dynamodb.Table(XSV_CLIENT_TABLE)
    item = {'client_id': client_id, **attributes}
    try:
        table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"Error putting client item: {e.response['Error']['Message']}")
        return False

# XSV S3 Upload Event Table Operations

def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an event item from the xsv_s3_upload_event table.

    Args:
        event_id (str): The event ID to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The event item if found, None otherwise.
    """
    table = dynamodb.Table(XSV_S3_UPLOAD_EVENT_TABLE)
    try:
        response = table.get_item(Key={'event_id': event_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error retrieving event: {e.response['Error']['Message']}")
        return None

def get_event_attributes(event_id: str, attributes: List[str]) -> Optional[Dict[str, Any]]:
    """
    Retrieve specific attributes of an event from the xsv_s3_upload_event table.

    Args:
        event_id (str): The event ID to retrieve.
        attributes (List[str]): List of attribute names to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary of requested attributes if found, None otherwise.
    """
    table = dynamodb.Table(XSV_S3_UPLOAD_EVENT_TABLE)
    projection_expression = ', '.join(attributes)
    try:
        response = table.get_item(
            Key={'event_id': event_id},
            ProjectionExpression=projection_expression
        )
        return response.get('Item')
    except ClientError as e:
        print(f"Error retrieving event attributes: {e.response['Error']['Message']}")
        return None

def put_event(event_id: str, attributes: Dict[str, Any]) -> bool:
    """
    Put a new item or replace an existing item in the xsv_s3_upload_event table.

    Args:
        event_id (str): The event ID of the item.
        attributes (Dict[str, Any]): A dictionary of attribute names and values to put.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    table = dynamodb.Table(XSV_S3_UPLOAD_EVENT_TABLE)
    item = {'event_id': event_id, **attributes}
    try:
        table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"Error putting event item: {e.response['Error']['Message']}")
        return False