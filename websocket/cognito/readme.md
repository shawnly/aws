https://github.com/aws-samples/amazon-cognito-api-gateway/blob/main/custom-auth/lambda.py


# Replace these values with your own
CLIENT_ID="your_client_id"
CLIENT_SECRET="your_client_secret"
DOMAIN="your_domain_prefix.auth.region.amazoncognito.com"

# Get token using client credentials flow
curl -X POST \
  https://$DOMAIN/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET" \
  -H "Authorization: Basic $(echo -n $CLIENT_ID:$CLIENT_SECRET | base64)"


import requests
import base64

client_id = 'your_client_id'
client_secret = 'your_client_secret'
domain = 'your_domain_prefix.auth.region.amazoncognito.com'

# Create basic auth header
auth_header = base64.b64encode(
    f"{client_id}:{client_secret}".encode('utf-8')
).decode('utf-8')

# Request parameters
params = {
    'grant_type': 'client_credentials',
    'scope': 'api/read api/write'  # Request both scopes
}

# Make the request
response = requests.post(
    f'https://{domain}/oauth2/token',
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_header}'
    },
    data=params
)

print(response.json())