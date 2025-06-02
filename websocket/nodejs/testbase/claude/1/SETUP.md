# Complete Socket.IO ECS Project Files

## 🚀 Quick Setup Commands

```bash
# Create project directory
mkdir socketio-ecs-app
cd socketio-ecs-app

# Create directory structure
mkdir -p src public cloudformation scripts

# Make scripts executable after creating them
chmod +x scripts/*.sh
```

---

## 📄 **package.json**
```json
{
  "name": "socketio-ecs-app",
  "version": "1.0.0",
  "description": "Socket.IO application for ECS Fargate",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "dev": "node src/app.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "socket.io": "^4.7.2",
    "cors": "^2.8.5"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

---

## 📄 **src/app.js**
```javascript
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const path = require('path');

const app = express();
const server = createServer(app);

// Environment variables
const PORT = process.env.PORT || 3000;
const SERVER_NAME = process.env.SERVER_NAME || 'socketio-server';

// Trust proxy for ALB (important for HTTPS)
app.set('trust proxy', true);

// CORS configuration
app.use(cors());
app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname, '../public')));

// Health check route
app.get(`/${SERVER_NAME}/health`, (req, res) => {
  console.log('Health check requested');
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    server: SERVER_NAME,
    uptime: process.uptime(),
    protocol: req.protocol,
    secure: req.secure
  });
});

// Socket.IO setup with HTTPS/WSS support
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  },
  path: `/${SERVER_NAME}/socket.io/`,
  // Allow both HTTP and HTTPS connections
  allowEIO3: true,
  transports: ['websocket', 'polling']
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log(`User connected: ${socket.id}`);
  
  // Send welcome message
  socket.emit('message', {
    type: 'system',
    text: `Welcome to ${SERVER_NAME}! Connected via ${socket.conn.transport.name}`,
    timestamp: new Date().toISOString()
  });

  // Handle custom events
  socket.on('message', (data) => {
    console.log('Message received:', data);
    // Broadcast to all clients
    io.emit('message', {
      type: 'user',
      text: data.text,
      user: data.user || 'Anonymous',
      timestamp: new Date().toISOString()
    });
  });

  socket.on('disconnect', () => {
    console.log(`User disconnected: ${socket.id}`);
  });
});

// Start server
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Socket.IO server running on port ${PORT}`);
  console.log(`Server name: ${SERVER_NAME}`);
  console.log(`Health check: /${SERVER_NAME}/health`);
  console.log(`Socket path: /${SERVER_NAME}/socket.io/`);
  console.log('Ready for HTTPS/WSS connections through ALB');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});
```

---

## 📄 **public/index.html**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO Test Client</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
        .message { margin: 5px 0; }
        .system { color: #666; font-style: italic; }
        .user { color: #333; }
        input, button { padding: 10px; margin: 5px; }
        #messageInput { width: 300px; }
        .status { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .connected { color: green; }
        .disconnected { color: red; }
    </style>
</head>
<body>
    <h1>Socket.IO Test Client (HTTPS/WSS)</h1>
    <div id="status" class="status">Connecting...</div>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type a message...">
    <button onclick="sendMessage()">Send</button>

    <script src="/socket.io/socket.io.js"></script>
    <script>
        // Get server name from environment or use default
        const serverName = window.location.pathname.split('/')[1] || 'socketio-server';
        const statusDiv = document.getElementById('status');
        
        // Socket.IO connection - it will automatically use WSS if page is served over HTTPS
        const socket = io({
            path: `/${serverName}/socket.io/`,
            // Force websocket transport for better performance with HTTPS/WSS
            transports: ['websocket', 'polling'],
            // Automatically upgrade to websocket
            upgrade: true,
            // Connection timeout
            timeout: 20000
        });

        const messages = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');

        // Connection status handlers
        socket.on('connect', () => {
            statusDiv.innerHTML = `<span class="connected">✓ Connected via ${socket.io.engine.transport.name.toUpperCase()}</span>`;
            console.log('Connected to server');
        });

        socket.on('disconnect', () => {
            statusDiv.innerHTML = '<span class="disconnected">✗ Disconnected</span>';
            console.log('Disconnected from server');
        });

        socket.on('connect_error', (error) => {
            statusDiv.innerHTML = '<span class="disconnected">✗ Connection Error</span>';
            console.error('Connection error:', error);
        });

        // Transport upgrade handler
        socket.io.on('upgrade', () => {
            statusDiv.innerHTML = `<span class="connected">✓ Connected via ${socket.io.engine.transport.name.toUpperCase()}</span>`;
            console.log('Upgraded to', socket.io.engine.transport.name);
        });

        // Message handler
        socket.on('message', (data) => {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${data.type}`;
            messageElement.innerHTML = `<strong>${data.user || 'System'}:</strong> ${data.text} <small>(${new Date(data.timestamp).toLocaleTimeString()})</small>`;
            messages.appendChild(messageElement);
            messages.scrollTop = messages.scrollHeight;
        });

        function sendMessage() {
            const message = messageInput.value.trim();
            if (message) {
                socket.emit('message', {
                    text: message,
                    user: 'Test User'
                });
                messageInput.value = '';
            }
        }

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

---

## 📄 **Dockerfile**
```dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY src/ ./src/
COPY public/ ./public/

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Change ownership of the app directory
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "
    const http = require('http');
    const serverName = process.env.SERVER_NAME || 'socketio-server';
    const options = {
      host: 'localhost',
      port: process.env.PORT || 3000,
      path: \`/\${serverName}/health\`,
      timeout: 3000
    };
    const req = http.request(options, (res) => {
      if (res.statusCode === 200) {
        process.exit(0);
      } else {
        process.exit(1);
      }
    });
    req.on('error', () => process.exit(1));
    req.end();
  "

# Start the application
CMD ["npm", "start"]
```

---

## 📄 **.dockerignore**
```
node_modules
npm-debug.log
.git
.gitignore
README.md
cloudformation/
scripts/
.env
.env.local
```

---

## 📄 **cloudformation/infrastructure.yaml**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Socket.IO application on ECS Fargate with existing ALB integration'

Parameters:
  ProjectName:
    Type: String
    Default: 'socketio-app'
    Description: 'Name of the project'
  
  ServerName:
    Type: String
    Default: 'socketio-server'
    Description: 'Server name for routing'
  
  ImageTag:
    Type: String
    Default: 'latest'
    Description: 'Docker image tag to deploy'
  
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: 'Existing VPC ID where ECS will be deployed'
  
  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
    Description: 'Existing subnet IDs for ECS tasks'
  
  ExistingSecurityGroupId:
    Type: AWS::EC2::SecurityGroup::Id
    Description: 'Existing security group ID for ECS tasks'
  
  ExistingHTTPSListenerArn:
    Type: String
    Description: 'ARN of existing ALB HTTPS listener to add rules to'
  
  ListenerRulePriority:
    Type: Number
    Default: 100
    Description: 'Priority for ALB listener rule (must be unique in your ALB)'

Resources:
  # ECR Repository
  ECRRepository:
    Type: AWS::ECR::Repository
    Properties:
      RepositoryName: !Sub '${ProjectName}'
      LifecyclePolicy:
        LifecyclePolicyText: |
          {
            "rules": [
              {
                "rulePriority": 1,
                "description": "Keep last 10 images",
                "selection": {
                  "tagStatus": "tagged",
                  "countType": "imageCountMoreThan",
                  "countNumber": 10
                },
                "action": {
                  "type": "expire"
                }
              }
            ]
          }

  # CloudWatch Log Group
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/ecs/${ProjectName}'
      RetentionInDays: 7

  # Target Group for this specific application
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${ProjectName}-tg'
      Port: 3000
      Protocol: HTTP
      VpcId: !Ref VpcId
      TargetType: ip
      HealthCheckPath: !Sub '/${ServerName}/health'
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      Matcher:
        HttpCode: '200'
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-tg'

  # ALB Listener Rules for routing to this application
  HealthCheckListenerRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref ExistingHTTPSListenerArn
      Priority: !Ref ListenerRulePriority
      Conditions:
        - Field: path-pattern
          Values:
            - !Sub '/${ServerName}/health'
      Actions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  ApplicationListenerRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref ExistingHTTPSListenerArn
      Priority: !Sub '${ListenerRulePriority}1'
      Conditions:
        - Field: path-pattern
          Values:
            - !Sub '/${ServerName}/*'
      Actions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub '${ProjectName}-cluster'
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 1

  # ECS Task Definition
  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: !Sub '${ProjectName}-task'
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: '256'
      Memory: '512'
      ExecutionRoleArn: !Ref ECSExecutionRole
      TaskRoleArn: !Ref ECSTaskRole
      ContainerDefinitions:
        - Name: !Sub '${ProjectName}-container'
          Image: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRRepository}:${ImageTag}'
          Essential: true
          PortMappings:
            - ContainerPort: 3000
              Protocol: tcp
          Environment:
            - Name: NODE_ENV
              Value: production
            - Name: PORT
              Value: '3000'
            - Name: SERVER_NAME
              Value: !Ref ServerName
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs
          HealthCheck:
            Command:
              - CMD-SHELL
              - !Sub 'curl -f http://localhost:3000/${ServerName}/health || exit 1'
            Interval: 30
            Timeout: 5
            Retries: 3
            StartPeriod: 60

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    DependsOn: 
      - HealthCheckListenerRule
      - ApplicationListenerRule
    Properties:
      ServiceName: !Sub '${ProjectName}-service'
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      LaunchType: FARGATE
      DesiredCount: 2
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref ExistingSecurityGroupId
          Subnets: !Ref SubnetIds
          AssignPublicIp: ENABLED
      LoadBalancers:
        - ContainerName: !Sub '${ProjectName}-container'
          ContainerPort: 3000
          TargetGroupArn: !Ref TargetGroup
      HealthCheckGracePeriodSeconds: 120

  # IAM Roles
  ECSExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-execution-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
      Policies:
        - PolicyName: ECRAccessPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - ecr:GetAuthorizationToken
                  - ecr:BatchCheckLayerAvailability
                  - ecr:GetDownloadUrlForLayer
                  - ecr:BatchGetImage
                Resource: '*'

  ECSTaskRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-task-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: CloudWatchLogsPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*'

Outputs:
  ECRRepositoryURI:
    Description: 'ECR Repository URI'
    Value: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRRepository}'
    Export:
      Name: !Sub '${ProjectName}-ecr-uri'

  TargetGroupArn:
    Description: 'Target Group ARN for this application'
    Value: !Ref TargetGroup
    Export:
      Name: !Sub '${ProjectName}-target-group-arn'

  ECSClusterName:
    Description: 'ECS Cluster Name'
    Value: !Ref ECSCluster
    Export:
      Name: !Sub '${ProjectName}-cluster-name'

  ECSServiceName:
    Description: 'ECS Service Name'
    Value: !Ref ECSService
    Export:
      Name: !Sub '${ProjectName}-service-name'

  LogGroupName:
    Description: 'CloudWatch Log Group Name'
    Value: !Ref LogGroup

  HealthCheckPath:
    Description: 'Health check path for ALB rules'
    Value: !Sub '/${ServerName}/health'

  ApplicationPath:
    Description: 'Application path pattern for ALB rules'
    Value: !Sub '/${ServerName}/*'

  ListenerRulePriorities:
    Description: 'ALB Listener Rule Priorities Used'
    Value: !Sub '${ListenerRulePriority} and ${ListenerRulePriority}1'
```

---

## 📄 **scripts/build-and-push.sh**
```bash
#!/bin/bash

# Exit on any error
set -e

# Configuration
PROJECT_NAME="socketio-app"
AWS_REGION="us-east-1"
IMAGE_TAG=${1:-$(date +%Y%m%d-%H%M%S)}

echo "Building and pushing Docker image with tag: $IMAGE_TAG"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ECR repository URI
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME"

echo "ECR Repository URI: $ECR_REPO_URI"

# Login to ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

# Build Docker image
echo "Building Docker image..."
docker build -t $PROJECT_NAME:$IMAGE_TAG .
docker tag $PROJECT_NAME:$IMAGE_TAG $ECR_REPO_URI:$IMAGE_TAG
docker tag $PROJECT_NAME:$IMAGE_TAG $ECR_REPO_URI:latest

# Push to ECR
echo "Pushing image to ECR..."
docker push $ECR_REPO_URI:$IMAGE_TAG
docker push $ECR_REPO_URI:latest

echo "Image pushed successfully!"
echo "Image URI: $ECR_REPO_URI:$IMAGE_TAG"
echo ""
echo "To deploy this image, run:"
echo "./scripts/deploy.sh $IMAGE_TAG"
```

---

## 📄 **scripts/deploy.sh**
```bash
#!/bin/bash

# Exit on any error
set -e

# Configuration
PROJECT_NAME="socketio-app"
SERVER_NAME="socketio-server"
AWS_REGION="us-east-1"
STACK_NAME="$PROJECT_NAME-stack"
IMAGE_TAG=${1:-latest}

# Existing infrastructure parameters - SET THESE VALUES
VPC_ID=""
SUBNET_IDS=""
EXISTING_SECURITY_GROUP_ID=""
EXISTING_HTTPS_LISTENER_ARN=""
LISTENER_RULE_PRIORITY="100"

echo "Deploying CloudFormation stack: $STACK_NAME"
echo "Image tag: $IMAGE_TAG"
echo "Using existing infrastructure"

# Check if required parameters are set
if [ -z "$VPC_ID" ] || [ -z "$SUBNET_IDS" ] || [ -z "$EXISTING_SECURITY_GROUP_ID" ] || [ -z "$EXISTING_HTTPS_LISTENER_ARN" ]; then
    echo "ERROR: Please set all required existing infrastructure parameters in the script"
    echo ""
    echo "Required values:"
    echo 'VPC_ID="vpc-1234567890abcdef0"'
    echo 'SUBNET_IDS="subnet-12345678,subnet-87654321"'
    echo 'EXISTING_SECURITY_GROUP_ID="sg-1234567890abcdef0"'
    echo 'EXISTING_HTTPS_LISTENER_ARN="arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/50dc6c495c0c9188/80ac8a5b1234567"'
    echo 'LISTENER_RULE_PRIORITY="100"  # Must be unique in your ALB'
    echo ""
    echo "How to find these values:"
    echo "1. VPC_ID: EC2 Console > VPC > Your VPC ID"
    echo "2. SUBNET_IDS: EC2 Console > Subnets > Select your subnets"
    echo "3. EXISTING_SECURITY_GROUP_ID: EC2 Console > Security Groups > Your ECS security group"
    echo "4. EXISTING_HTTPS_LISTENER_ARN: EC2 Console > Load Balancers > Your ALB > Listeners tab > HTTPS listener ARN"
    echo "5. LISTENER_RULE_PRIORITY: Check existing rules in your ALB listener to pick unique priority"
    exit 1
fi

echo "Using existing infrastructure:"
echo "  VPC: $VPC_ID"
echo "  Subnets: $SUBNET_IDS"
echo "  Security Group: $EXISTING_SECURITY_GROUP_ID"
echo "  HTTPS Listener: $EXISTING_HTTPS_LISTENER_ARN"
echo "  Rule Priority: $LISTENER_RULE_PRIORITY"

# Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file cloudformation/infrastructure.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        ProjectName=$PROJECT_NAME \
        ServerName=$SERVER_NAME \
        ImageTag=$IMAGE_TAG \
        VpcId=$VPC_ID \
        SubnetIds=$SUBNET_IDS \
        ExistingSecurityGroupId=$EXISTING_SECURITY_GROUP_ID \
        ExistingHTTPSListenerArn=$EXISTING_HTTPS_LISTENER_ARN \
        ListenerRulePriority=$LISTENER_RULE_PRIORITY \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $AWS_REGION

echo "Deployment completed!"

# Get stack outputs
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo "Your Socket.IO application has been deployed and integrated with your existing ALB!"
echo "The application will be available at your ALB domain with these paths:"
echo "  Health Check: https://your-alb-domain/$SERVER_NAME/health"
echo "  Socket.IO App: https://your-alb-domain/$SERVER_NAME/"
echo ""
echo "ALB Listener Rules created with priorities: $LISTENER_RULE_PRIORITY and ${LISTENER_RULE_PRIORITY}1"
```

---

## 📄 **scripts/get-logs.sh**
```bash
#!/bin/bash

# Configuration
PROJECT_NAME="socketio-app"
AWS_REGION="us-east-1"
LOG_GROUP_NAME="/ecs/$PROJECT_NAME"

# Number of lines to fetch (default: 100)
LINES=${1:-100}

echo "Fetching last $LINES lines from CloudWatch logs..."
echo "Log Group: $LOG_GROUP_NAME"
echo ""

# Get recent log events
aws logs tail $LOG_GROUP_NAME \
    --since 1h \
    --follow \
    --region $AWS_REGION
```

---

## 📄 **README.md**
```markdown
# Socket.IO ECS Fargate Application

A Socket.IO application deployed on AWS ECS Fargate with existing ALB integration.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed
- Node.js 18+ (for local development)
- Existing AWS infrastructure (VPC, ALB with HTTPS listener, Security Groups)

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure your existing infrastructure:**
   Edit `scripts/deploy.sh` and set:
   - VPC_ID
   - SUBNET_IDS
   - EXISTING_SECURITY_GROUP_ID
   - EXISTING_HTTPS_LISTENER_ARN
   - LISTENER_RULE_PRIORITY

3. **Deploy:**
   ```bash
   # Make scripts executable
   chmod +x scripts/*.sh
   
   # Deploy infrastructure (creates ECR repo)
   ./scripts/deploy.sh
   
   # Build and push Docker image
   ./scripts/build-and-push.sh
   
   # Update service with your image
   ./scripts/deploy.sh latest
   ```

## Usage

### Local Development
```bash
npm start
```
Access at: http://localhost:3000/socketio-server/

### Production URLs
After deployment, access via your existing ALB:
- Health check: `https://your-alb-domain/socketio-server/health`
- Socket.IO app: `https://your-alb-domain/socketio-server/`

### Viewing Logs
```bash
./scripts/get-logs.sh
```

## Architecture

```
Internet -> Your Existing ALB -> ECS Fargate -> Socket.IO App
                                     |
                                     v
                               CloudWatch Logs
```
```

---

## 🚀 **Quick Setup Commands**

Copy and paste this to set up everything:

```bash
# Create project
mkdir socketio-ecs-app && cd socketio-ecs-app

# Create directories
mkdir -p src public cloudformation scripts

# Copy all the files above into their respective locations
# Then run:

npm install
chmod +x scripts/*.sh

# Edit scripts/deploy.sh with your infrastructure details
# Then deploy:
./scripts/deploy.sh
./scripts/build-and-push.sh
./scripts/deploy.sh latest
```

All files are ready to copy! Just create the directory structure and copy each file content into the correct location. Let me know if you need help with any specific file or setup step!