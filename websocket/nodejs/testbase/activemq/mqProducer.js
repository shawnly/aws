// mq producer
const { Client } = require('@stomp/stompjs');
const WebSocket = require('websocket').w3cwebsocket;

const BROKER_URL = 'wss://your-broker-name.mq.us-west-2.amazonaws.com:61614';
const MQ_USER = 'admin';
const MQ_PASSWORD = 'your-password';
const QUEUE_NAME = '/queue/your-queue-name';

const client = new Client({
  brokerURL: BROKER_URL,
  connectHeaders: {
    login: MQ_USER,
    passcode: MQ_PASSWORD,
  },
  debug: (str) => {
    console.log(`🧭 ${str}`);
  },
  reconnectDelay: 5000,
  heartbeatIncoming: 4000,
  heartbeatOutgoing: 4000,
  webSocketFactory: () => new WebSocket(BROKER_URL)
});

client.onConnect = () => {
  console.log('✅ Connected to ActiveMQ');

  const message = {
    type: 'notification',
    from: 'node-producer',
    timestamp: new Date().toISOString(),
    text: 'Hello from producer!'
  };

  client.publish({
    destination: QUEUE_NAME,
    body: JSON.stringify(message),
    headers: { persistent: 'true' }
  });

  console.log('📤 Message sent:', message);

  client.deactivate(); // close connection after sending
};

client.onStompError = (frame) => {
  console.error('❌ STOMP Error:', frame.headers['message']);
  console.error('Details:', frame.body);
};

client.activate();
