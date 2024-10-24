# src/connect.py
import os
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Store connection ID
    table.put_item(
        Item={
            'connectionId': connection_id
        }
    )
    
    return {
        'statusCode': 200,
        'body': 'Connected'
    }

# src/disconnect.py
import os
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    # Remove connection ID
    table.delete_item(
        Key={
            'connectionId': connection_id
        }
    )
    
    return {
        'statusCode': 200,
        'body': 'Disconnected'
    }

# src/message.py
import os
import json
import boto3
from boto3.dynamodb.conditions import Scan

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    connection_id = event['requestContext']['connectionId']
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    
    # Create API Gateway management client
    client = boto3.client('apigatewaymanagementapi',
                         endpoint_url=f'https://{domain}/{stage}')
    
    # Get message from the body
    body = json.loads(event['body'])
    message = body.get('message', '')
    
    # Get all connections
    connections = table.scan()['Items']
    
    # Broadcast message to all connected clients
    for connection in connections:
        try:
            client.post_to_connection(
                Data=json.dumps({
                    'message': message,
                    'sender': connection_id
                }),
                ConnectionId=connection['connectionId']
            )
        except client.exceptions.GoneException:
            # Remove stale connections
            table.delete_item(
                Key={'connectionId': connection['connectionId']}
            )
    
    return {
        'statusCode': 200,
        'body': 'Message sent'
    }