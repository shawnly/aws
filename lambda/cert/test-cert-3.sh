
const https = require('https');

exports.handler = async () => {
return new Promise((resolve, reject) => {
    https.get('https://your-secure-api.example.com', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        resolve({
        statusCode: 200,
        body: data,
        });
    });
    }).on('error', err => {
    reject({
        statusCode: 500,
        body: err.message,
    });
    });
});
};
