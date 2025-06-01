const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { sendToQueue } = require('./lib/mqSender');

const app = express();
const PORT = process.env.PORT || 3000;
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*";
const SOCKET_IO_PATH = process.env.SOCKET_IO_PATH || "/socket.io";
const HEALTH_CHECK_PATH = process.env.HEALTH_CHECK_PATH || "/health";

app.get(HEALTH_CHECK_PATH, (req, res) => res.status(200).send('OK'));

const server = http.createServer(app);

const io = new Server(server, {
  path: SOCKET_IO_PATH,
  cors: {
    origin: ALLOWED_ORIGIN,
    methods: ["GET", "POST"],
    credentials: true
  },
  transports: ["websocket"]
});

io.on('connection', (socket) => {
  console.log(`✅ Client connected: ${socket.id}`);
  socket.on('message', (data) => {
    const enriched = {
      ...data,
      socketId: socket.id,
      timestamp: new Date().toISOString(),
      environment: process.env.ENVIRONMENT || 'dev'
    };
    console.log('📥 Message received:', enriched);
    sendToQueue(null, enriched);
  });
  socket.on('disconnect', (reason) => {
    console.log(`❌ Client disconnected: ${socket.id}, Reason: ${reason}`);
  });
});

server.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
