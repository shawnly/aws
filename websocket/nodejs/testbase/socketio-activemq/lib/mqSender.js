// lib/mqSender.js
const stompit = require('stompit');

const connectOptions = {
  host: 'localhost',
  port: 61613,
  connectHeaders: {
    host: '/',
    login: 'admin',
    passcode: 'admin'
  }
};

function sendToQueue(queueName, message) {
  stompit.connect(connectOptions, (error, client) => {
    if (error) {
      return console.error('MQ connection error:', error.message);
    }

    const frame = client.send({
      destination: `/queue/${queueName}`,
      'content-type': 'application/json'
    });

    frame.write(JSON.stringify(message));
    frame.end();

    console.log(`📤 Sent message to /queue/${queueName}:`, message);

    client.disconnect();
  });
}

module.exports = { sendToQueue };
