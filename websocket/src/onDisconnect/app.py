import json

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    print(f"Connection disconnected: {connection_id}")
    # Optional: Remove connection ID from storage (e.g., in DynamoDB)
    return {
        'statusCode': 200,
        'body': json.dumps('Disconnected')
    }
