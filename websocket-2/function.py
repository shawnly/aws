# src/connect/app.py
import json
import os
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    logger.info(f"New connection: {connection_id}")
    
    # Store connection ID in DynamoDB
    table.put_item(
        Item={
            'connectionId': connection_id
        }
    )
    
    return {
        'statusCode': 200,
        'body': 'Connected'
    }

# src/disconnect/app.py
import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    logger.info(f"Disconnecting: {connection_id}")
    
    # Remove connection ID from DynamoDB
    table.delete_item(
        Key={
            'connectionId': connection_id
        }
    )
    
    return {
        'statusCode': 200,
        'body': 'Disconnected'
    }

# src/message/app.py
import json
import os
import boto3
import logging
from boto3.dynamodb.conditions import Scan

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    
    # Create API Gateway management client
    client = boto3.client('apigatewaymanagementapi',
                         endpoint_url=f'https://{domain}/{stage}')
    
    # Get message from the WebSocket request
    body = json.loads(event['body'])
    message = body.get('message', '')
    
    logger.info(f"Received message from {connection_id}: {message}")
    
    # Get all connections
    connections = table.scan()['Items']
    
    # Broadcast message to all connected clients
    for connection in connections:
        try:
            client.post_to_connection(
                Data=json.dumps({
                    'message': message,
                    'from': connection_id
                }),
                ConnectionId=connection['connectionId']
            )
        except client.exceptions.GoneException:
            # Remove stale connections
            logger.warning(f"Removing stale connection: {connection['connectionId']}")
            table.delete_item(
                Key={'connectionId': connection['connectionId']}
            )
    
    return {
        'statusCode': 200,
        'body': 'Message sent'
    }

# requirements.txt
boto3==1.26.137
botocore==1.29.137