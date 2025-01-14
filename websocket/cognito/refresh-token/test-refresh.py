import requests
import base64
import time
import json

class CognitoAuth:
    def __init__(self, domain, client_id, client_secret):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = f"https://{domain}/oauth2/token"
        
    def _get_basic_auth_header(self):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
        return f"Basic {auth_bytes.decode('utf-8')}"
    
    def get_initial_tokens(self):
        """Get initial access token and refresh token"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': self._get_basic_auth_header()
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'api/read api/write'
        }
        
        response = requests.post(self.token_endpoint, headers=headers, data=data)
        return response.json()
    
    def refresh_tokens(self, refresh_token):
        """Get new access token using refresh token"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': self._get_basic_auth_header()
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(self.token_endpoint, headers=headers, data=data)
        return response.json()

def decode_jwt(token):
    """Decode JWT token without verification (for demonstration)"""
    parts = token.split('.')
    if len(parts) != 3:
        return None
    
    payload = parts[1]
    # Add padding if needed
    padding = len(payload) % 4
    if padding:
        payload += '=' * (4 - padding)
    
    decoded = base64.b64decode(payload.replace('-', '+').replace('_', '/'))
    return json.loads(decoded)

def main():
    # Replace these with your values
    domain = "your-domain-prefix.auth.region.amazoncognito.com"
    client_id = "your-client-id"
    client_secret = "your-client-secret"
    
    auth = CognitoAuth(domain, client_id, client_secret)
    
    # Get initial tokens
    print("Getting initial tokens...")
    initial_tokens = auth.get_initial_tokens()
    print("\nInitial Tokens Response:")
    print(json.dumps(initial_tokens, indent=2))
    
    if 'access_token' in initial_tokens:
        decoded_token = decode_jwt(initial_tokens['access_token'])
        print("\nDecoded Access Token:")
        print(json.dumps(decoded_token, indent=2))
    
    # Wait a bit to demonstrate refresh
    print("\nWaiting 5 seconds before refreshing token...")
    time.sleep(5)
    
    # Refresh the token
    if 'refresh_token' in initial_tokens:
        print("\nRefreshing tokens...")
        refreshed_tokens = auth.refresh_tokens(initial_tokens['refresh_token'])
        print("\nRefreshed Tokens Response:")
        print(json.dumps(refreshed_tokens, indent=2))
        
        if 'access_token' in refreshed_tokens:
            decoded_refreshed_token = decode_jwt(refreshed_tokens['access_token'])
            print("\nDecoded Refreshed Access Token:")
            print(json.dumps(decoded_refreshed_token, indent=2))
    else:
        print("\nNo refresh token available in initial response")

if __name__ == "__main__":
    main()