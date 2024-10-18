import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
apigw_management = boto3.client('apigatewaymanagementapi')
table = dynamodb.Table('WebSocketConnections')  # Replace with your table name

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    route_key = event['requestContext']['routeKey']

    # Handle WebSocket connection establishment
    if route_key == '$connect':
        return handle_connect(connection_id)

    # Handle WebSocket disconnection
    elif route_key == '$disconnect':
        return handle_disconnect(connection_id)

    # Handle default route (message sending)
    elif route_key == '$default':
        return handle_default(event, connection_id)

    # Handle EC2-triggered event (incoming message)
    elif route_key == 'sendmessage':
        payload = json.loads(event['body'])
        return handle_ec2_message(payload)

def handle_connect(connection_id):
    """Store connection_id in DynamoDB when a WebSocket client connects."""
    try:
        table.put_item(Item={'connection_id': connection_id})
        return {
            'statusCode': 200,
            'body': 'Connection established'
        }
    except ClientError as e:
        print(f"Error saving connection ID: {e}")
        return {
            'statusCode': 500,
            'body': 'Failed to connect'
        }

def handle_disconnect(connection_id):
    """Remove connection_id from DynamoDB when a WebSocket client disconnects."""
    try:
        table.delete_item(Key={'connection_id': connection_id})
        return {
            'statusCode': 200,
            'body': 'Connection closed'
        }
    except ClientError as e:
        print(f"Error deleting connection ID: {e}")
        return {
            'statusCode': 500,
            'body': 'Failed to disconnect'
        }

def handle_default(event, connection_id):
    """Handle messages sent from the WebSocket client."""
    message = json.loads(event['body'])
    return {
        'statusCode': 200,
        'body': f"Received: {message['data']} from {connection_id}"
    }

def handle_ec2_message(payload):
    """Handle messages sent from EC2 (via Lambda invocation) and send to WebSocket clients."""
    try:
        # Get the target connection ID from DynamoDB
        response = table.scan()
        items = response.get('Items', [])

        # Send message to all connected clients
        for item in items:
            target_connection_id = item['connection_id']
            post_to_connection(target_connection_id, payload['message'])

        return {
            'statusCode': 200,
            'body': 'Message sent to WebSocket clients'
        }
    except ClientError as e:
        print(f"Error sending message: {e}")
        return {
            'statusCode': 500,
            'body': 'Failed to send message'
        }

def post_to_connection(connection_id, message):
    """Post a message to the WebSocket connection."""
    try:
        apigw_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'message': message})
        )
    except ClientError as e:
        print(f"Error posting message to connection {connection_id}: {e}")
        try:
            table.delete_item(Key={'connection_id': connection_id})
        except ClientError as delete_error:
            print(f"Error deleting connection ID: {delete_error}")
