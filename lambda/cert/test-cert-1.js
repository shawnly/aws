const https = require('https');

exports.handler = async (event) => {
    try {
        // The NODE_EXTRA_CA_CERTS environment variable is automatically used by Node.js
        // No need to manually load certificates in your code
        const response = await makeRequest('your-service.internal', '/api/endpoint');
        
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

function makeRequest(host, path) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: host,
            port: 443,
            path: path,
            method: 'GET'
            // No need to specify cert, key, or ca here!
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