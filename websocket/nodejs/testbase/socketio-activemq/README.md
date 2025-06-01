how to install npm

brew install node
node -v
npm -v


mkdir socketio-activemq
cd socketio-activemq
npm init -y
npm install socket.io

how to debug with vscode



lsof -i :3000
kill -9

how to install activemq locally

docker pull rmohr/activemq

docker run -d --name activemq \
  -p 8161:8161 \            # Web UI
  -p 61616:61616 \          # OpenWire (Java clients)
  -p 61613:61613 \          # STOMP (Node.js clients)
  -e ACTIVEMQ_ADMIN_LOGIN=admin \
  -e ACTIVEMQ_ADMIN_PASSWORD=admin \
  rmohr/activemq

docker logs -f activemq

browser:
📍 http://localhost:8161
🔑 Login: admin / admin

docker stop activemq
docker rm activemq

socketio-activemq/
├── server.js             # Socket.IO server (producer)
├── client.html           # Web client to send messages
├── lib/
│   ├── mqSender.js       # Sends messages to ActiveMQ
│   └── mqConsumer.js     # NEW: Reads messages from ActiveMQ
├── consumer.js           # Starts the message reader
├── package.json