import json
import boto3

def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event['body'])
    message = body.get('message', 'No message')

    # Setup API Gateway Management API
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    apigw_client = boto3.client('apigatewaymanagementapi', endpoint_url=f"https://{domain_name}/{stage}")

    try:
        apigw_client.post_to_connection(
            ConnectionId=connection_id,
            Data=message.encode('utf-8')
        )
        print(f"Message sent: {message}")
    except apigw_client.exceptions.GoneException:
        print(f"Connection {connection_id} is gone")

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed')
    }
