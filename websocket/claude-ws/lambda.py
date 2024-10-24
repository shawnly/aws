# src/connect.py
import os
import json
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    logger.info("Connect event: %s", json.dumps(event))
    connection_id = event['requestContext']['connectionId']
    
    try:
        # Store connection ID
        table.put_item(
            Item={
                'connectionId': connection_id
            }
        )
        logger.info("Successfully connected: %s", connection_id)
        return {
            'statusCode': 200,
            'body': json.dumps('Connected')
        }
    except Exception as e:
        logger.error("Connection error: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Connection error')
        }

# src/disconnect.py
import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    logger.info("Disconnect event: %s", json.dumps(event))
    connection_id = event['requestContext']['connectionId']
    
    try:
        # Remove connection ID
        table.delete_item(
            Key={
                'connectionId': connection_id
            }
        )
        logger.info("Successfully disconnected: %s", connection_id)
        return {
            'statusCode': 200,
            'body': json.dumps('Disconnected')
        }
    except Exception as e:
        logger.error("Disconnection error: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Disconnection error')
        }

# src/message.py
import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    logger.info("Message event: %s", json.dumps(event))
    
    connection_id = event['requestContext']['connectionId']
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    
    # Create API Gateway management client
    client = boto3.client('apigatewaymanagementapi',
                         endpoint_url=f'https://{domain}/{stage}')
    
    try:
        # Get message from the body
        body = json.loads(event['body'])
        message = body.get('message', '')
        
        logger.info("Processing message: %s", message)
        
        # Get all connections
        connections = table.scan()['Items']
        logger.info("Found %d connections", len(connections))
        
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
                logger.info("Message sent to %s", connection['connectionId'])
            except client.exceptions.GoneException:
                logger.warning("Connection %s is gone, removing", connection['connectionId'])
                # Remove stale connections
                table.delete_item(
                    Key={'connectionId': connection['connectionId']}
                )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Message sent')
        }
    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing message')
        }

# src/default.py
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info("Default route event: %s", json.dumps(event))
    return {
        'statusCode': 200,
        'body': json.dumps('Message received on default route')
    }