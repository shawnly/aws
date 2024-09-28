import os
import boto3

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')

def get_table(table_name):
    """
    Get the DynamoDB table object.

    :param table_name: Name of the DynamoDB table.
    :return: Table resource object.
    """
    return dynamodb.Table(table_name)

def get_item(table_name, primary_key, primary_key_value):
    """
    Get an item from the DynamoDB table using the primary key.

    :param table_name: Name of the DynamoDB table.
    :param primary_key: Name of the primary key attribute.
    :param primary_key_value: Value of the primary key.
    :return: The retrieved item as a dictionary, or None if not found.
    """
    table = get_table(table_name)
    try:
        response = table.get_item(Key={primary_key: primary_key_value})
        return response.get('Item', None)
    except Exception as e:
        print(f"Error fetching item: {e}")
        return None

def get_item_attributes(table_name, primary_key, primary_key_value, attributes):
    """
    Get specific attributes from an item in the DynamoDB table.

    :param table_name: Name of the DynamoDB table.
    :param primary_key: Name of the primary key attribute.
    :param primary_key_value: Value of the primary key.
    :param attributes: List of attribute names to retrieve.
    :return: A dictionary containing the requested attributes, or None if not found.
    """
    table = get_table(table_name)
    try:
        response = table.get_item(
            Key={primary_key: primary_key_value},
            ProjectionExpression=", ".join(attributes)
        )
        return response.get('Item', None)
    except Exception as e:
        print(f"Error fetching attributes: {e}")
        return None

def put_item(table_name, primary_key, primary_key_value, attributes):
    """
    Insert or update an item in the DynamoDB table.

    :param table_name: Name of the DynamoDB table.
    :param primary_key: Name of the primary key attribute.
    :param primary_key_value: Value of the primary key.
    :param attributes: Dictionary of attribute names and their corresponding values to insert/update.
    :return: The response from DynamoDB.
    """
    table = get_table(table_name)
    try:
        item = {primary_key: primary_key_value}
        item.update(attributes)
        response = table.put_item(Item=item)
        return response
    except Exception as e:
        print(f"Error putting item: {e}")
        return None
