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
