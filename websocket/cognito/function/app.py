import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def connect_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    client_id = event['requestContext']['authorizer']['claims']['client_id']
    
    # Put connection ID and client ID into DynamoDB
    table.put_item(Item={'connection_id': connection_id, 'client_id': client_id})

    return {
        'statusCode': 200,
        'body': 'Connected.'
    }

def disconnect_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Remove connection from DynamoDB
    table.delete_item(Key={'connection_id': connection_id})
    
    return {
        'statusCode': 200,
        'body': 'Disconnected.'
    }
