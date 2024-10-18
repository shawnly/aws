const AWS = require('aws-sdk');
// const dotenv = require('dotenv');

// Load environment variables from .env file
// dotenv.config();
// Set the AWS region (optional if set in environment variables)
AWS.config.update({ region: 'us-east-1' });

const lambda = new AWS.Lambda();

const invokeLambda = async (message) => {
  const params = {
    FunctionName: process.env.LAMBDA_FUNCTION_NAME, // Replace with your Lambda function name
    InvocationType: 'RequestResponse', // Synchronous invocation
    Payload: JSON.stringify({ message })  // Send the message payload
  };

  try {
    const data = await lambda.invoke(params).promise();
    console.log('Lambda function invoked successfully:', JSON.parse(data.Payload));
  } catch (err) {
    console.error('Error invoking Lambda:', err);
  }
};

// Example dynamic message
// const message = 'Hello from EC2 to WebSocket!';
const message = {
    action: 'sendMessage',
    data: 'Hello WebSocket from EC2!'
  };

// Invoke Lambda to send message to WebSocket clients
invokeLambda(message);
