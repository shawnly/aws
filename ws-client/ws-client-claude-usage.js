// usage-example.js
const CognitoWebSocketClient = require('./websocket-client');

async function main() {
  const client = new CognitoWebSocketClient({
    cognitoDomain: 'https://your-domain.auth.region.amazoncognito.com',
    clientId: 'your-client-id',
    clientSecret: 'your-client-secret',
    websocketUrl: 'wss://xxxx.execute-api.region.amazonaws.com/prod',
    username: 'user@example.com',
    password: 'password123'
  });

  // Add message handlers
  client.on('message', (message) => {
    console.log('Received message:', message);
  });

  client.on('notification', (message) => {
    console.log('Received notification:', message);
  });

  try {
    // Connect to WebSocket
    await client.connect();

    // Send a message
    client.send({
      type: 'message',
      content: 'Hello, WebSocket!'
    });

  } catch (error) {
    console.error('Error:', error);
  }
}

main();