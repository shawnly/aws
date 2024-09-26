import boto3
from botocore.exceptions import ClientError

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Function to put a client item into xsv_client table
def put_xsv_client(client_id, priority_base, sns_topic_arn, client_dns):
    table = dynamodb.Table('xsv_client')
    response = table.put_item(
        Item={
            'client_id': client_id,
            'priority_base': priority_base,
            'sns_topic_arn': sns_topic_arn,
            'client_dns': client_dns
        }
    )
    return response

# Function to update the status of an event in the sfn_event table
def update_sfn_event(event_id, event_status, instance_id):
    table = dynamodb.Table('sfn_event')
    response = table.update_item(
        Key={
            'event_id': event_id
        },
        UpdateExpression="SET event_status = :status, instance_id = :instance",
        ExpressionAttributeValues={
            ':status': event_status,
            ':instance': instance_id
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

# Function to get the priority_base attribute from the xsv_client table by client_id
def get_priority_by_client_id(client_id):
    table = dynamodb.Table('xsv_client')
    try:
        response = table.get_item(
            Key={
                'client_id': client_id
            },
            AttributesToGet=['priority_base']  # Specify only the attribute you want
        )
        
        if 'Item' in response:
            return response['Item']['priority_base']
        else:
            return None  # Client ID not found
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")
        return None
