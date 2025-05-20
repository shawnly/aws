#!/bin/bash
# Simple script to create an Axios Lambda Layer

# Create directory structure
mkdir -p axios-layer/nodejs
cd axios-layer/nodejs

# Create package.json with Axios dependency
cat > package.json << EOL
{
  "name": "axios-layer",
  "version": "1.0.0",
  "description": "Lambda layer for Axios HTTP client",
  "dependencies": {
    "axios": "^1.6.5"
  }
}
EOL

# Install dependencies
npm install --production

# Go back and create zip file
cd ../..
zip -r axios-layer.zip axios-layer

echo "Layer created: axios-layer.zip"
echo "To upload to AWS, run:"
echo "aws lambda publish-layer-version --layer-name axios-layer --zip-file fileb://axios-layer.zip --compatible-runtimes nodejs16.x nodejs18.x nodejs20.x"