// websocket-client.js
const WebSocket = require('ws');
const axios = require('axios');
const querystring = require('querystring');

class CognitoWebSocketClient {
  constructor(config) {
    this.config = {
      cognitoDomain: config.cognitoDomain,  // e.g., 'https://your-domain.auth.region.amazoncognito.com'
      clientId: config.clientId,
      clientSecret: config.clientSecret,
      websocketUrl: config.websocketUrl,    // e.g., 'wss://xxxx.execute-api.region.amazonaws.com/prod'
      username: config.username,
      password: config.password
    };
    
    this.ws = null;
    this.token = null;
    this.refreshToken = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.messageHandlers = new Map();
  }

  async connect() {
    try {
      if (!this.token) {
        await this.authenticate();
      }
      
      await this.establishWebSocketConnection();
    } catch (error) {
      console.error('Connection error:', error);
      throw error;
    }
  }

  async authenticate() {
    try {
      const auth = Buffer.from(`${this.config.clientId}:${this.config.clientSecret}`).toString('base64');
      
      const tokenResponse = await axios({
        method: 'post',
        url: `${this.config.cognitoDomain}/oauth2/token`,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': `Basic ${auth}`
        },
        data: querystring.stringify({
          grant_type: 'password',
          username: this.config.username,
          password: this.config.password,
          scope: 'openid'
        })
      });

      this.token = tokenResponse.data.access_token;
      this.refreshToken = tokenResponse.data.refresh_token;
      
      // Set timer to refresh token before it expires
      const expiresIn = (tokenResponse.data.expires_in - 300) * 1000; // Refresh 5 minutes before expiry
      setTimeout(() => this.refreshTokens(), expiresIn);
      
    } catch (error) {
      console.error('Authentication error:', error);
      throw error;
    }
  }

  async refreshTokens() {
    try {
      const auth = Buffer.from(`${this.config.clientId}:${this.config.clientSecret}`).toString('base64');
      
      const tokenResponse = await axios({
        method: 'post',
        url: `${this.config.cognitoDomain}/oauth2/token`,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': `Basic ${auth}`
        },
        data: querystring.stringify({
          grant_type: 'refresh_token',
          refresh_token: this.refreshToken
        })
      });

      this.token = tokenResponse.data.access_token;
      
      // If the WebSocket is connected, reconnect with new token
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        await this.reconnect();
      }
      
      // Set next token refresh
      const expiresIn = (tokenResponse.data.expires_in - 300) * 1000;
      setTimeout(() => this.refreshTokens(), expiresIn);
      
    } catch (error) {
      console.error('Token refresh error:', error);
      // If refresh fails, try full authentication
      await this.authenticate();
    }
  }

  async establishWebSocketConnection() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.config.websocketUrl, {
        headers: {
          'Authorization': this.token
        }
      });

      this.ws.on('open', () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      });

      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      });

      this.ws.on('close', async (code, reason) => {
        console.log(`WebSocket closed: ${code} - ${reason}`);
        if (code === 4001 || reason.includes('token expired')) {
          await this.handleTokenExpiration();
        } else if (this.reconnectAttempts < this.maxReconnectAttempts) {
          await this.reconnect();
        }
      });

      this.ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      });
    });
  }

  async handleTokenExpiration() {
    try {
      await this.authenticate();
      await this.reconnect();
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
  }

  async reconnect() {
    if (this.ws) {
      this.ws.close();
    }
    
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    try {
      await this.establishWebSocketConnection();
    } catch (error) {
      console.error('Reconnection failed:', error);
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => this.reconnect(), 5000); // Wait 5 seconds before retrying
      }
    }
  }

  // Add a message handler for specific message types
  on(messageType, handler) {
    this.messageHandlers.set(messageType, handler);
  }

  // Handle incoming messages
  handleMessage(message) {
    if (message.type && this.messageHandlers.has(message.type)) {
      this.messageHandlers.get(message.type)(message);
    }
  }

  // Send a message through the WebSocket
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  // Close the WebSocket connection
  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

module.exports = CognitoWebSocketClient;