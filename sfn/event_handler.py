import boto3
import json

dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')
sqs = boto3.client('sqs')

TABLE_NAME = 'ClientConcurrencyLimits'
STATE_MACHINE_ARN = 'arn:aws:states:REGION:ACCOUNT_ID:stateMachine:your-state-machine'
SQS_QUEUE_URL = 'https://sqs.REGION.amazonaws.com/ACCOUNT_ID/your-queue'

def lambda_handler(event, context):
    client_id = event['client_id']
    file_info = event['file_info']  # File information from S3 event
    table = dynamodb.Table(TABLE_NAME)
    
    # Fetch current executions and limit for the client
    response = table.get_item(Key={'client_id': client_id})
    
    if 'Item' not in response:
        return {"error": "Client not found"}
    
    item = response['Item']
    current_executions = item['current_executions']
    max_concurrent_executions = item['max_concurrent_executions']
    
    if current_executions < max_concurrent_executions:
        # Increment current executions
        table.update_item(
            Key={'client_id': client_id},
            UpdateExpression='SET current_executions = current_executions + :inc',
            ExpressionAttributeValues={':inc': 1}
        )
        
        # Trigger the Step Function
        stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(file_info)
        )
        
        return {"status": "Step Function started"}
    else:
        # If over limit, add the event to the SQS queue for later processing
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(event)  # Store the event with client_id and file_info
        )
        
        return {"status": "Queued for later processing"}
