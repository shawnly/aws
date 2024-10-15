const nodemailer = require('nodemailer');

// Configure the email transport using the SMTP server
let transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',  // For Gmail, use 'smtp.gmail.com'
    port: 587,               // Port for TLS (465 for SSL)
    secure: false,           // True for SSL, false for TLS
    auth: {
        user: process.env.SMTP_USERNAME,  // Your email address (can be stored as Lambda environment variable)
        pass: process.env.SMTP_PASSWORD   // Your email password (can be stored as Lambda environment variable)
    }
});

exports.handler = async (event) => {
    let mailOptions = {
        from: '"Your Name" <your-email@gmail.com>',  // Replace with your sender email address
        to: "recipient@example.com",                 // Replace with your recipient email address
        subject: "Test Email from Lambda",
        text: "This is a test email sent from AWS Lambda using Nodemailer and SMTP.",
        html: "<b>This is a test email sent from AWS Lambda using Nodemailer and SMTP.</b>"
    };

    try {
        let info = await transporter.sendMail(mailOptions);
        console.log("Email sent: " + info.response);
        return {
            statusCode: 200,
            body: JSON.stringify('Email sent successfully!')
        };
    } catch (error) {
        console.error("Error sending email:", error);
        return {
            statusCode: 500,
            body: JSON.stringify('Error sending email: ' + error.message)
        };
    }
};
