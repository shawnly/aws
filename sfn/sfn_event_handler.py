import json
import boto3
import logging

# Initialize SNS client and logger
sns_client = boto3.client('sns')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_sns_notification(status, execution_arn, state_machine_arn, sns_topic_arn):
    """
    Sends an SNS notification based on the Step Function execution status.

    Parameters:
    - status (str): The execution status of the Step Function (e.g., 'SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED_OUT').
    - execution_arn (str): The ARN of the Step Function execution.
    - state_machine_arn (str): The ARN of the Step Function state machine.
    - sns_topic_arn (str): The ARN of the SNS topic where the message will be sent.

    Raises:
    - Exception: If an error occurs when sending the SNS message.
    
    SNS message content:
    - If status is 'FAILED', 'ABORTED', or 'TIMED_OUT': "Step Function Execution Failed/Aborted/Timed Out"
    - If status is 'SUCCEEDED': "Step Function Execution Succeeded"

    Returns:
    - dict: A dictionary with the status code and result message.
    """
    try:
        # Map the status to the corresponding SNS message
        if status in ['FAILED', 'ABORTED', 'TIMED_OUT']:
            subject = f"Step Function Execution {status.capitalize()}"
            message = f"Step Function execution with ARN: {execution_arn} has {status.lower()}."
        elif status == 'SUCCEEDED':
            subject = "Step Function Execution Succeeded"
            message = f"Step Function execution with ARN: {execution_arn} has succeeded."
        else:
            logger.info("Unhandled status: %s", status)
            return {
                'statusCode': 200,
                'body': json.dumps('Unhandled status')
            }

        # Log message details
        logger.info("Sending SNS notification: %s", message)

        # Send the message to the SNS topic
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject=subject
        )

        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps(f"SNS notification sent for status: {status}")
        }

    except Exception as e:
        # Catch and log any exception that occurs
        logger.error("Error sending SNS notification: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing step function status change event')
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler function that processes Step Function execution status changes
    and calls the send_sns_notification function to send notifications to SNS.

    Parameters:
    - event (dict): The event triggering the function, which includes the Step Function status and execution details.
    - context (LambdaContext): The runtime information for the function.

    Expected event structure:
    {
        "detail": {
            "status": "SUCCEEDED | FAILED | ABORTED | TIMED_OUT",
            "executionArn": "<executionArn>",
            "stateMachineArn": "<stateMachineArn>"
        }
    }

    Returns:
    - dict: A dictionary with statusCode and message indicating success or failure.
    """
    try:
        # Extract the step function status and details from the event
        status = event.get('detail', {}).get('status')
        execution_arn = event.get('detail', {}).get('executionArn')
        state_machine_arn = event.get('detail', {}).get('stateMachineArn')

        # Validate if necessary details are present
        if not status or not execution_arn or not state_machine_arn:
            logger.error("Missing required event details")
            return {
                'statusCode': 400,
                'body': json.dumps('Missing required event details')
            }

        # Define your SNS topic ARN
        sns_topic_arn = '<Your-SNS-Topic-ARN>'  # Replace with your actual SNS Topic ARN

        # Call the function to send the SNS notification
        return send_sns_notification(status, execution_arn, state_machine_arn, sns_topic_arn)

    except Exception as e:
        # Catch any exceptions in the lambda_handler and log the error
        logger.error("Error in lambda_handler: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing Lambda event')
        }
