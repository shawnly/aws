#!/bin/bash

set -e

LAYER_NAME="custom-cert-layer"
CERT_DIR="layer/certs"
ZIP_FILE="custom-cert-layer.zip"

echo "Zipping certificate layer..."
cd layer
zip -r9 "../$ZIP_FILE" .
cd ..

echo "Publishing layer to Lambda..."
aws lambda publish-layer-version \
  --layer-name "$LAYER_NAME" \
  --description "Layer containing custom CA certificate" \
  --zip-file "fileb://$ZIP_FILE" \
  --compatible-runtimes nodejs18.x \
  --license-info "MIT"

echo "Done. Layer created and published."
