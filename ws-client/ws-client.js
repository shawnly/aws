const axios = require('axios');
const WebSocket = require('ws');

const COGNITO_URL = 'https://my-auth-domain.auth.us-east-1.amazonaws.com/oauth2/token';
const CLIENT_ID = 'your_client_id';
const CLIENT_SECRET = 'your_client_secret';
const WEBSOCKET_URL = 'wss://9vjthlsd9f.execute-api.us-east-1.amazonaws.com/prod';

// const COGNITO_URL = 'https://my-auth-domain.auth.region.amazonaws.com/oauth2/token';
// const CLIENT_ID = 'your_client_id';
// const CLIENT_SECRET = 'your_client_secret';
// const WEBSOCKET_URL = 'wss://your-websocket-endpoint';

let accessToken = null;

// Function to get a new access token from Cognito
async function getAccessToken() {
    try {
        const response = await axios.post(COGNITO_URL, new URLSearchParams({
            grant_type: 'client_credentials',
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        }), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });

        accessToken = response.data.access_token;
        console.log('New access token obtained');
        return accessToken;
    } catch (error) {
        console.error('Failed to get access token:', error.message);
        throw error;
    }
}

// Function to connect to WebSocket
function connectWebSocket() {
    if (!accessToken) {
        console.error('Access token is missing');
        return;
    }

    const ws = new WebSocket(WEBSOCKET_URL, {
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    });

    ws.on('open', () => {
        console.log('Connected to WebSocket');
    });

    ws.on('message', (message) => {
        console.log('Received message:', message);
    });

    ws.on('error', async (error) => {
        console.error('WebSocket error:', error.message);

        // Check if the error is due to token expiration
        if (error.message.includes('403') || error.message.includes('token expired')) {
            console.log('Token expired. Fetching new token and reconnecting...');
            try {
                await getAccessToken();
                connectWebSocket(); // Attempt reconnection with a new token
            } catch (error) {
                console.error('Failed to refresh token:', error.message);
            }
        }
    });

    ws.on('close', (code, reason) => {
        console.log(`WebSocket closed: ${code} - ${reason}`);
        // Optionally attempt to reconnect with a new token
    });
}

// Main function to initialize the connection
async function init() {
    try {
        await getAccessToken();
        connectWebSocket();
    } catch (error) {
        console.error('Initialization failed:', error.message);
    }
}

// Start the WebSocket connection process
init();
