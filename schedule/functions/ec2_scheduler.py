import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_tagged_ec2_instances(tag_key, tag_value, event_id):
    ec2 = boto3.client('ec2')
    instances = []
    
    # Get EC2 instances with matching tags
    response = ec2.describe_instances(
        Filters=[
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': f'tag:event', 'Values': [event_id]}
        ]
    )
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    
    return instances

def start_instances(instance_ids):
    if not instance_ids:
        logger.info("No EC2 instances to start")
        return
        
    ec2 = boto3.client('ec2')
    ec2.start_instances(InstanceIds=instance_ids)
    logger.info(f"Started EC2 instances: {instance_ids}")

def stop_instances(instance_ids):
    if not instance_ids:
        logger.info("No EC2 instances to stop")
        return
        
    ec2 = boto3.client('ec2')
    ec2.stop_instances(InstanceIds=instance_ids)
    logger.info(f"Stopped EC2 instances: {instance_ids}")

def lambda_handler(event, context):
    action = event['action']  # 'start' or 'stop'
    tag_key = event['tag_key']  # 'scheduled'
    tag_value = event['tag_value']  # 'true'
    event_id = event['event_id']  # '101'
    
    try:
        instance_ids = get_tagged_ec2_instances(tag_key, tag_value, event_id)
        
        if action == 'start':
            start_instances(instance_ids)
        elif action == 'stop':
            stop_instances(instance_ids)
        
        return {
            'statusCode': 200,
            'body': f"Successfully {action}ed EC2 instances"
        }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e