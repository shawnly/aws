# ECS Fargate + Socket.IO + ActiveMQ

This project deploys a parameterized Socket.IO WebSocket server on AWS ECS Fargate. The service relays incoming messages to ActiveMQ via STOMP and supports deployment of multiple logical services using path-based routing (e.g., /serviceA, /serviceB).

## Features

- WebSocket communication via Socket.IO
- Message forwarding to ActiveMQ
- Dynamic service path (e.g., `/serviceA/socket.io`)
- Health check path (e.g., `/serviceA/health`)
- Logging to CloudWatch
- ALB forwarding rule for path-based routing

## File Structure

```
ecs-fargate-socketio/
├── server.js
├── Dockerfile
├── package.json
├── lib/
│   └── mqSender.js
├── cloudformation/
│   └── ecs-fargate-socketio.yaml
├── README.md
└── build-push-deploy.sh
```

## Deployment Steps

1. Set required parameters in `build-push-deploy.sh`.
2. Build and push the Docker image to ECR.
3. Deploy the stack using AWS CloudFormation.
