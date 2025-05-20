const fs = require('fs');
const path = require('path');
const { X509Certificate } = require('crypto');

exports.handler = async () => {
  try {
    const certPath = path.join('/opt', 'certs', 'custom-ca.crt');
    const pem = fs.readFileSync(certPath, 'utf-8');
    const x509 = new X509Certificate(pem);

    return {
      statusCode: 200,
      body: JSON.stringify({
        subject: x509.subject,
        issuer: x509.issuer,
        validFrom: x509.validFrom,
        validTo: x509.validTo,
        fingerprint: x509.fingerprint,
      }, null, 2),
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: `Error reading certificate: ${err.message}`,
    };
  }
};
