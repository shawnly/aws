import boto3

# Initialize SNS client
sns = boto3.client('sns', region_name='your-region')  # Replace with your region

# List of email addresses to confirm
email_addresses = ['email1@example.com', 'email2@example.com', ...]

# Your SNS topic ARN
topic_arn = 'your-topic-arn'

# Subscribe and confirm each email address
for email in email_addresses:
    try:
        # Subscribe email address
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        subscription_arn = response['SubscriptionArn']
        print(f'Subscribed {email}. Subscription ARN: {subscription_arn}')

        # Get subscription confirmation status
        status_response = sns.get_subscription_attributes(
            SubscriptionArn=subscription_arn
        )
        status = status_response['Attributes']['SubscriptionStatus']

        # Confirm subscription if not already confirmed
        if status != 'Confirmed':
            # Get confirmation token from email (manually or using an email parsing library)
            # For demonstration purposes, assume you have the token
            confirmation_token = 'your-confirmation-token'

            # Confirm subscription
            sns.confirm_subscription(
                TopicArn=topic_arn,
                Token=confirmation_token,
                AuthenticateOnUnsubscribe='true'
            )
            print(f'Confirmed subscription for {email}')
        else:
            print(f'{email} already confirmed')
    except Exception as e:
        print(f'Error processing {email}: {str(e)}')
    