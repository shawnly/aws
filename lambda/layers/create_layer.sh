#!/bin/bash

# Lambda Layer Builder Script
# Usage: ./build_layer.sh <layer_name>
# Example: ./build_layer.sh my-python-layer

set -e  # Exit on any error

# Check if layer name is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a layer name"
    echo "Usage: $0 <layer_name>"
    exit 1
fi

LAYER_NAME=$1
ZIP_FILE="${LAYER_NAME}.zip"

echo "Building Lambda layer: $LAYER_NAME"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in current directory"
    exit 1
fi

# Clean up any existing python directory and zip file
[ -d "python" ] && rm -rf python
[ -f "$ZIP_FILE" ] && rm -f "$ZIP_FILE"

# Create python directory and install packages
echo "Creating python directory and installing packages..."
mkdir python
pip install -r requirements.txt -t python/ --upgrade

# Clean up unnecessary files
echo "Cleaning up unnecessary files..."
find python/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find python/ -name "*.pyc" -delete 2>/dev/null || true

# Create zip file
echo "Creating zip file: $ZIP_FILE"
zip -r "$ZIP_FILE" python/

# Clean up python directory
echo "Cleaning up python directory..."
rm -rf python/

# Check if zip file was created successfully
if [ ! -f "$ZIP_FILE" ]; then
    echo "Error: Failed to create zip file"
    exit 1
fi

ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "Layer zip file created: $ZIP_FILE (Size: $ZIP_SIZE)"

# Upload to AWS Lambda
echo "Uploading layer to AWS Lambda..."
LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
    --compatible-runtimes python3.8 python3.9 python3.10 python3.11 python3.12 \
    --description "Layer created from requirements.txt on $(date)" \
    --query 'LayerVersionArn' \
    --output text)

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Layer uploaded successfully!"
    echo "Layer ARN: $LAYER_VERSION_ARN"
    echo ""
    echo "You can now use this layer in your Lambda functions by adding the ARN:"
    echo "$LAYER_VERSION_ARN"
else
    echo "❌ Failed to upload layer to AWS"
    exit 1
fi

# Optional: Clean up zip file (uncomment if you want to remove it after upload)
# rm "$ZIP_FILE"
# echo "Zip file cleaned up"