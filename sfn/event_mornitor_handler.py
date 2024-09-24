def lambda_handler(event, context):
    """
    Lambda handler function that retrieves the instance_id based on event_id and stops the EC2 instance.

    Parameters:
    - event: The event data passed to the Lambda function, expected to contain the event_id.
    - context: Runtime information for the Lambda function.

    Returns:
    - A JSON response indicating success or failure of the operation.
    """
    # Extract event_id from the event
    event_id = event.get('event_id')

    if not event_id:
        return {
            'statusCode': 400,
            'body': 'Missing required field: event_id'
        }

    # Step 1: Retrieve the instance_id using the event_id
    instance_id = retrieve_instance_id_by_event_id(event_id)

    if not instance_id:
        return {
            'statusCode': 404,
            'body': f"Instance ID not found for event_id {event_id}"
        }

    # Step 2: Stop the EC2 instance using the retrieved instance_id
    stop_result = stop_ec2_instance(instance_id)

    # Return the result of the stop operation
    if stop_result['status'] == 'success':
        return {
            'statusCode': 200,
            'body': f"Successfully stopped instance {instance_id}."
        }
    else:
        return {
            'statusCode': 500,
            'body': f"Error stopping instance: {stop_result['message']}"
        }
