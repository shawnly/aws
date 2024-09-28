# dynamodb_lib.py

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')

def get_client(table_name, client_id):
    """
    Get client item from xsv_client table.

    Args:
        table_name (str): Client table name.
        client_id (str): Client ID.

    Returns:
        dict: Client item.
    """
    table = dynamodb.Table(table_name)
    try:
        response = table.get_item(Key={'client_id': client_id})
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error getting client: {e}")
        return {}

def get_client_attributes(table_name, client_id, attributes):
    """
    Get specific client attributes from xsv_client table.

    Args:
        table_name (str): Client table name.
        client_id (str): Client ID.
        attributes (list): List of attribute names.

    Returns:
        dict: Client attributes.
    """
    table = dynamodb.Table(table_name)
    try:
        projection_expression = ', '.join(attributes)
        response = table.get_item(
            Key={'client_id': client_id},
            ProjectionExpression=projection_expression
        )
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error getting client attributes: {e}")
        return {}

def put_client_item(table_name, client_id, attributes):
    """
    Put client item into xsv_client table.

    Args:
        table_name (str): Client table name.
        client_id (str): Client ID.
        attributes (dict): Client attributes.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(table_name)
    try:
        item = {'client_id': client_id}
        item.update(attributes)
        table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"Error putting client item: {e}")
        return False

def update_client_item(table_name, client_id, update_expression, expression_attribute_values):
    """
    Update client item in xsv_client table.

    Args:
        table_name (str): Client table name.
        client_id (str): Client ID.
        update_expression (str): Update expression.
        expression_attribute_values (dict): Expression attribute values.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(table_name)
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

def get_s3_upload_event(table_name, event_id):
    """
    Get S3 upload event item from xsv_s3_upload_event table.

    Args:
        table_name (str): Event table name.
        event_id (str): Event ID.

    Returns:
        dict: Event item.
    """
    table = dynamodb.Table(table_name)
    try:
        response = table.get_item(Key={'event_id': event_id})
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error getting event: {e}")
        return {}

def get_s3_upload_event_attributes(table_name, event_id, attributes):
    """
    Get specific S3 upload event attributes from xsv_s3_upload_event table.

    Args:
        table_name (str): Event table name.
        event_id (str): Event ID.
        attributes (list): List of attribute names.

    Returns:
        dict: Event attributes.
    """
    table = dynamodb.Table(table_name)
    try:
        projection_expression = ', '.join(attributes)
        response = table.get_item(
            Key={'event_id': event_id},
            ProjectionExpression=projection_expression
        )
        return response.get('Item', {})
    except ClientError as e:
        print(f"Error getting event attributes: {e}")
        return {}

def put_s3_upload_event_item(table_name, event_id, attributes):
    """
    Put S3 upload event item into xsv_s3_upload_event table.

    Args:
        table_name (str): Event table name.
        event_id (str): Event ID.
        attributes (dict): Event attributes.

    Returns:
        bool: True if successful, False otherwise.
    """
    table = dynamodb.Table(table_name)
    try:
        item = {'event_id': event_id}
        item.update(attributes)
        table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"Error putting event item: {e}")
        return False

def update_s3_upload_event_item(table_name, event_id, update_expression, expression_attribute_values):
    """
    Update S3 upload event item in xsv_s3