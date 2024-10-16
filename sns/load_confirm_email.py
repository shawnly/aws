import boto3
import requests
from botocore.exceptions import ClientError

sns_client = boto3.client('sns')

email_list = ['email1@example.com', 'email2@example.com', 'email3@example.com']

for email in email_list:
    try:
        subscription_arn = sns_client.subscribe(
            TopicArn='your_sns_topic_arn',
            Protocol='email',
            Endpoint=email
        )

        response = sns_client.get_subscription_attributes(
            SubscriptionArn=subscription_arn
        )
        confirmation_url = response['Attributes']['SubscriptionArn']

        print(f"Confirmation URL for {email}: {confirmation_url}")

        # Automatically confirm the subscription
        confirmation_response = requests.get(confirmation_url)
        if confirmation_response.status_code == 200:
            print(f"Subscription confirmed for {email}")
        else:
            print(f"Error confirming subscription for {email}: {confirmation_response.text}")

    except ClientError as e:
        print(f"Error subscribing {email}: {e}")