import json

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    print(f"New connection: {connection_id}")
    # Optional: Store connection ID (e.g., in DynamoDB) for later use
    return {
        'statusCode': 200,
        'body': json.dumps('Connected')
    }
