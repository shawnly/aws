const stompit = require('stompit');

const connectOptions = {
  host: process.env.MQ_HOST || 'localhost',
  port: parseInt(process.env.MQ_PORT || '61613'),
  connectHeaders: {
    host: '/',
    login: process.env.MQ_USER || 'admin',
    passcode: process.env.MQ_PASSWORD || 'admin'
  }
};

const QUEUE_NAME = process.env.MQ_QUEUE || 'websocket';

function sendToQueue(queueNameOverride, message) {
  const queue = queueNameOverride || QUEUE_NAME;

  stompit.connect(connectOptions, (error, client) => {
    if (error) {
      console.error('❌ MQ connection error:', error.message);
      return;
    }

    const frame = client.send({
      destination: `/queue/${queue}`,
      'content-type': 'application/json'
    });

    frame.write(JSON.stringify(message));
    frame.end();

    console.log(`📤 Sent to /queue/${queue}:`, message);
    client.disconnect();
  });
}

module.exports = { sendToQueue };
