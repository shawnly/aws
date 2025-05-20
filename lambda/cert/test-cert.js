const fs = require('fs');
const https = require('https');
const path = require('path');

exports.handler = async (event) => {
    try {
        // Path to certificates in the Lambda Layer
        // The /opt directory is where Lambda mounts layers
        const certPath = '/opt/nodejs/certs/';
        
        // Read certificates from layer
        const cert = fs.readFileSync(path.join(certPath, 'certificate.pem'));
        const key = fs.readFileSync(path.join(certPath, 'private-key.pem'));
        const ca = fs.readFileSync(path.join(certPath, 'ca-certificate.pem'));
        
        // Make secure request using certificates
        const response = await makeSecureRequest('api.example.com', '/endpoint', cert, key, ca);
        
        return {
            statusCode: 200,
            body: JSON.stringify(response)
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: 'Error processing request', error: error.toString() })
        };
    }
};

function makeSecureRequest(host, path, cert, key, ca) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: host,
            port: 443,
            path: path,
            method: 'GET',
            cert: cert,
            key: key,
            ca: ca
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve(data);
                }
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        req.end();
    });
}