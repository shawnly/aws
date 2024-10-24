import os
import boto3
import json

# Initialize the API Gateway management API client
client = boto3.client('apigatewaymanagementapi', 
                      endpoint_url=os.environ['WEBSOCKET_API_URL'])

def lambda_handler(event, context):
    # The WebSocket connection ID is required to send messages back to the client
    connection_id = event['requestContext']['connectionId']
    
    try:
        # Parse the received WebSocket message
        body = json.loads(event['body'])
        action = body.get('action')

        if action == 'ping':
            # If the action is 'ping', respond with a 'pong'
            response = {
                'action': 'pong'
            }
            send_message_to_client(connection_id, response)

        else:
            # Handle other actions (such as 'email') here
            print(f"Received action: {action}")
            # You can add other actions here as needed, such as handling emails.

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Action processed successfully'})
        }

    except Exception as e:
        print(f"Error processing message: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def send_message_to_client(connection_id, message):
    """Send a message to the WebSocket client using connection_id"""
    try:
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        print(f"Sent message to connection {connection_id}: {message}")
    except client.exceptions.GoneException:
        print(f"Connection {connection_id} is gone")
    except Exception as e:
        print(f"Failed to send message: {e}")
