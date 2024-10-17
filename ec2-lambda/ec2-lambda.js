const AWS = require('aws-sdk');

// Set the AWS region (optional if set in environment variables)
AWS.config.update({ region: 'us-east-1' });

// Create a Lambda service object
const lambda = new AWS.Lambda();

const params = {
  FunctionName: 'my-lambda-function', // Replace with your Lambda function name
  InvocationType: 'RequestResponse',  // 'RequestResponse' for sync invocation
  Payload: JSON.stringify({ key1: 'value1', key2: 'value2' })  // Send any data you want
};

lambda.invoke(params, function (err, data) {
  if (err) {
    console.log('Error', err);
  } else {
    console.log('Success', data.Payload);
  }
});
