import boto3
import json

sfn_client = boto3.client('stepfunctions')
sqs_client = boto3.client('sqs')

# Define your Step Function ARN and SQS URL
STEP_FUNCTION_ARN = 'arn:aws:states:region:account-id:stateMachine:yourStepFunction'
SQS_URL = 'https://sqs.region.amazonaws.com/account-id/your-queue-name'

def lambda_handler(event, context):
    # Poll SQS queue for a message
    response = sqs_client.receive_message(
        QueueUrl=SQS_URL,
        MaxNumberOfMessages=1,  # Only one message at a time
        WaitTimeSeconds=5
    )
    
    if 'Messages' in response:
        message = response['Messages'][0]
        message_body = json.loads(message['Body'])
        receipt_handle = message['ReceiptHandle']

        # Extract S3 details from message and trigger the Step Function
        bucket_name = message_body['detail']['bucket']['name']
        object_key = message_body['detail']['object']['key']

        start_step_function(bucket_name, object_key)

        # Delete the message from SQS after processing
        sqs_client.delete_message(
            QueueUrl=SQS_URL,
            ReceiptHandle=receipt_handle
        )
        print(f"Processed {object_key} from SQS and deleted message.")
    else:
        print("No messages in SQS.")

def start_step_function(bucket_name, object_key):
    # Start Step Function with the S3 details
    response = sfn_client.start_execution(
        stateMachineArn=STEP_FUNCTION_ARN,
        input=json.dumps({
            'bucket_name': bucket_name,
            'object_key': object_key
        })
    )
    print(f"Started Step Function for {object_key}")

def get_sqs_message_count():
    # Get the number of messages in the queue
    response = sqs_client.get_queue_attributes(
        QueueUrl=SQS_URL,
        AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
    )
    
    # Extract the number of messages
    num_available_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    num_in_flight_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])

    print(f"Messages available for processing: {num_available_messages}")
    print(f"Messages currently being processed: {num_in_flight_messages}")

    return num_available_messages, num_in_flight_messages

# Call the function to check the SQS message count
# available, in_flight = get_sqs_message_count()