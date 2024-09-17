def process_sqs_queue(client_id):
    # Fetch next message from SQS queue
    messages = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=1
    )
    
    if 'Messages' in messages:
        for message in messages['Messages']:
            event = json.loads(message['Body'])
            file_info = event['file_info']
            
            # Start Step Function for the next file in the queue
            stepfunctions.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=json.dumps(file_info)
            )
            
            # Remove the message from the queue after processing
            sqs.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
            
            # Increment current executions for the client
            table.update_item(
                Key={'client_id': client_id},
                UpdateExpression='SET current_executions = current_executions + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
def step_function_completed(client_id):
    # Decrement the execution count in DynamoDB after a Step Function completes
    table.update_item(
        Key={'client_id': client_id},
        UpdateExpression='SET current_executions = current_executions - :dec',
        ExpressionAttributeValues={':dec': 1}
    )
    
    # Process the SQS queue to start the next file for this client
    process_sqs_queue(client_id)
