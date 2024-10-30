# Initial token request
curl -X POST \
  https://your-domain-prefix.auth.region.amazoncognito.com/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H "Authorization: Basic $(echo -n your-client-id:your-client-secret | base64)" \
  -d "grant_type=client_credentials&scope=api/read api/write"

# Refresh token request (replace REFRESH_TOKEN with the actual refresh token)
curl -X POST \
  https://your-domain-prefix.auth.region.amazoncognito.com/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H "Authorization: Basic $(echo -n your-client-id:your-client-secret | base64)" \
  -d "grant_type=refresh_token&refresh_token=REFRESH_TOKEN"