#!/bin/bash
set -e

LAYER_NAME="axios-layer"
NODE_VERSION="nodejs18.x"
LAYER_DIR="layer"
PACKAGE_DIR="${LAYER_DIR}/nodejs"

echo "Cleaning up..."
rm -rf ${LAYER_DIR}
mkdir -p ${PACKAGE_DIR}

echo "Initializing npm and installing axios..."
cd ${PACKAGE_DIR}
npm init -y
npm install axios

cd -

echo "Zipping layer..."
zip -r ${LAYER_NAME}.zip ${LAYER_DIR}

echo "Upload to S3 and deploy with CloudFormation, or use CLI:"
echo "aws lambda publish-layer-version --layer-name ${LAYER_NAME} \\"
echo "  --description 'Axios library' \\"
echo "  --zip-file fileb://${LAYER_NAME}.zip \\"
echo "  --compatible-runtimes ${NODE_VERSION}"
