// npm install ws nodemailer

const WebSocket = require('ws');
const nodemailer = require('nodemailer');

// WebSocket URL and mail server details
const WEBSOCKET_URL = 'wss://your-websocket-api-id.execute-api.region.amazonaws.com/Prod';
const MAIL_SERVER = 'mail-server.xxx.com';
const MAIL_PORT = 25;
const MAIL_USERNAME = 'admin';
const MAIL_PASSWORD = 'your-password'; // if your mail server requires authentication

// Set up nodemailer transport for sending emails
const transporter = nodemailer.createTransport({
  host: MAIL_SERVER,
  port: MAIL_PORT,
  secure: false, // true for 465, false for other ports (e.g., 25)
  auth: {
    user: MAIL_USERNAME,
    pass: MAIL_PASSWORD
  }
});

// Function to send email
function sendEmail(toEmail, messageBody) {
  const mailOptions = {
    from: MAIL_USERNAME,
    to: toEmail,
    subject: 'Message from WebSocket',
    text: messageBody
  };

  transporter.sendMail(mailOptions, (error, info) => {
    if (error) {
      return console.log(`Failed to send email: ${error}`);
    }
    console.log(`Email sent to ${toEmail}: ${info.response}`);
  });
}

// Set up WebSocket client
const ws = new WebSocket(WEBSOCKET_URL);

// WebSocket event listeners
ws.on('open', function open() {
  console.log('WebSocket connection established');
});

ws.on('message', function incoming(data) {
  try {
    // Parse the received message (assumed to be in JSON format)
    const parsedMessage = JSON.parse(data);
    const action = parsedMessage.action;
    const emailAddress = parsedMessage['email-address'];
    const emailMessage = parsedMessage.message;

    // Check if the action is 'email'
    if (action === 'email' && emailAddress && emailMessage) {
      console.log(`Action: ${action}, Sending email to: ${emailAddress}`);
      sendEmail(emailAddress, emailMessage);
    }
  } catch (error) {
    console.error(`Error parsing message: ${error}`);
  }
});

ws.on('close', function close() {
  console.log('WebSocket connection closed');
});

ws.on('error', function error(err) {
  console.error(`WebSocket error: ${err}`);
});
