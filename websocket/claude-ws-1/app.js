// authorizer/app.js
const AWS = require('aws-sdk');
const cognito = new AWS.CognitoIdentityServiceProvider();

exports.handler = async (event) => {
  try {
    const token = event.headers.Authorization;
    
    if (!token) {
      throw new Error('No authorization token provided');
    }

    // Verify the JWT token with Cognito
    const params = {
      AccessToken: token
    };

    try {
      await cognito.getUser(params).promise();
      
      return {
        isAuthorized: true,
        context: {
          // Additional context if needed
        }
      };
    } catch (error) {
      console.error('Token verification failed:', error);
      return {
        isAuthorized: false
      };
    }
  } catch (error) {
    console.error('Authorization failed:', error);
    return {
      isAuthorized: false
    };
  }
};