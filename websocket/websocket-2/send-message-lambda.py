import os
import boto3
import json

# Initialize DynamoDB and API Gateway Management API clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
apigateway_management_api = boto3.client('apigatewaymanagementapi', 
                                         endpoint_url=os.environ['WEBSOCKET_API_URL'])

def lambda_handler(event, context):
    # You can retrieve the specific email address or any identifier from the event
    email_address = event.get("email_address", "example@example.com")
    
    # Get connection_id from DynamoDB for the given email address
    try:
        response = table.get_item(Key={'email-address': email_address})
        connection_id = response['Item']['connection_id']  # Assuming you store the connection ID with email
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error retrieving connection ID: {str(e)}"
        }

    # Construct the message to be sent to the client
    data = {
        "action": "email",
        "email-address": email_address,
        "xxxx": "other-parameters",
        "message": "hello from lambda"
    }

    try:
        # Send the message to the WebSocket client using the retrieved connection ID
        apigateway_management_api.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data)
        )
        return {
            'statusCode': 200,
            'body': f'Message sent to connection: {connection_id}'
        }

    except apigateway_management_api.exceptions.GoneException:
        return {
            'statusCode': 410,
            'body': f'Connection {connection_id} is no longer valid'
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error sending message: {str(e)}'
        }
