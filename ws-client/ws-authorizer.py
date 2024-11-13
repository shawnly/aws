# authorizer/app.py
import json
import time
import os
import boto3
import jwt
import requests
from jwt.algorithms import RSAAlgorithm
from typing import Dict, Any

class TokenVerifier:
    def __init__(self, region: str, user_pool_id: str):
        self.region = region
        self.user_pool_id = user_pool_id
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self.jwks = None
        self._load_jwks()

    def _load_jwks(self) -> None:
        """Load the JSON Web Key Set from Cognito"""
        jwks_url = f"{self.issuer}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        self.jwks = response.json()

    def _get_public_key(self, kid: str) -> str:
        """Get the public key that matches the kid"""
        key_data = next((key for key in self.jwks['keys'] if key['kid'] == kid), None)
        if not key_data:
            raise ValueError('Public key not found')
        return RSAAlgorithm.from_jwk(json.dumps(key_data))

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify the JWT token and return the claims"""
        try:
            # Decode the token header to get the key ID (kid)
            header = jwt.get_unverified_header(token)
            kid = header['kid']

            # Get the public key
            public_key = self._get_public_key(kid)

            # Verify the token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={
                    'verify_exp': True,
                    'verify_iss': True,
                    'verify_aud': True
                },
                issuer=self.issuer
            )

            return claims

        except jwt.ExpiredSignatureError:
            raise ValueError('Token has expired')
        except jwt.InvalidTokenError as e:
            raise ValueError(f'Invalid token: {str(e)}')
        except Exception as e:
            raise ValueError(f'Token verification failed: {str(e)}')

def generate_policy(principal_id: str, effect: str, resource: str) -> Dict[str, Any]:
    """Generate the IAM policy for the WebSocket connection"""
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for WebSocket authorization"""
    try:
        # Get the token from the Authorization header
        auth_header = event.get('headers', {}).get('Authorization')
        if not auth_header:
            raise ValueError('Authorization header is missing')

        # Remove 'Bearer ' if present
        token = auth_header.replace('Bearer ', '')

        # Initialize the token verifier
        verifier = TokenVerifier(
            region=os.environ['AWS_REGION'],
            user_pool_id=os.environ['USER_POOL_ID']
        )

        # Verify the token
        claims = verifier.verify_token(token)

        # Generate the IAM policy
        method_arn = event['methodArn']
        policy = generate_policy(
            principal_id=claims['sub'],
            effect='Allow',
            resource=method_arn
        )

        # Add additional context if needed
        policy['context'] = {
            'username': claims.get('username', ''),
            'email': claims.get('email', ''),
            'scope': claims.get('scope', '')
        }

        return policy

    except ValueError as e:
        print(f"Authorization error: {str(e)}")
        raise Exception('Unauthorized')
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise Exception('Internal Server Error')