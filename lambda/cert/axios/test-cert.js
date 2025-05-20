const axios = require('axios');

exports.handler = async () => {
try {
    const response = await axios.get('https://your-custom-domain.example.com');
    return {
    statusCode: 200,
    body: JSON.stringify(response.data),
    };
} catch (err) {
    return {
    statusCode: 500,
    body: `Request failed: ${err.message}`,
    };
}
};