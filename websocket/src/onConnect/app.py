import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('WebSocketConnections')

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    
    table.put_item(
        Item={
            'ConnectionId': connection_id
        }
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Connected')