// Import axios from the layer
const axios = require('axios');

exports.handler = async (event) => {
    try {
        // With NODE_EXTRA_CA_CERTS environment variable set,
        // Axios will automatically use the additional CA certificates
        // for all HTTPS requests
        
        const response = await makeApiRequest('https://your-service.internal/api/endpoint');
        
        return {
            statusCode: 200,
            body: JSON.stringify(response.data)
        };
    } catch (error) {
        console.error('Error:', error);
        
        // Enhanced error handling for Axios errors
        let errorMessage = error.message;
        if (error.response) {
            // Server responded with a status code outside 2xx range
            errorMessage = `Request failed with status ${error.response.status}: ${JSON.stringify(error.response.data)}`;
        } else if (error.request) {
            // Request was made but no response received
            errorMessage = `No response received: ${error.request}`;
        }
        
        return {
            statusCode: 500,
            body: JSON.stringify({ 
                message: 'Error processing request', 
                error: errorMessage 
            })
        };
    }
};

async function makeApiRequest(url, options = {}) {
    // Basic Axios request
    return await axios({
        url,
        method: options.method || 'GET',
        headers: options.headers || {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        data: options.data || {},
        timeout: options.timeout || 5000,
        // No need to specify CA certificates here as they're handled by NODE_EXTRA_CA_CERTS
    });
}