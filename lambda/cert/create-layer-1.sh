mkdir -p ca-cert-layer/nodejs/certs
# Add your CA certificate
cp your-ca-certificate.pem ca-cert-layer/nodejs/certs/
# Zip the layer
cd ca-cert-layer
zip -r ../ca-cert-layer.zip .
cd ..

aws lambda publish-layer-version \
  --layer-name ca-cert-layer \
  --description "Layer containing CA certificates" \
  --zip-file fileb://ca-cert-layer.zip \
  --compatible-runtimes nodejs16.x nodejs18.x nodejs20.x


# attach layer to lambda function

aws lambda update-function-configuration \
  --function-name your-function-name \
  --layers arn:aws:lambda:your-region:your-account-id:layer:ca-cert-layer:1 \
  --environment "Variables={NODE_EXTRA_CA_CERTS=/opt/nodejs/certs/your-ca-certificate.pem}"