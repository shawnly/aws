mkdir lambda-email
cd lambda-email
npm init -y
npm install nodemailer
After you’ve written the function, zip the entire lambda-email folder (including node_modules)

zip -r lambda-email.zip .
Upload the ZIP: Go to the Lambda console and upload the zip file under the Code section.

Set Environment Variables (if using external SMTP):

    SMTP_USERNAME: Your email address (for Gmail, for example, your-email@gmail.com).
    SMTP_PASSWORD: Your password (if you’re using Gmail with 2FA, you will need an app-specific password).

    test

    Go to the Test tab in the AWS Lambda console.
    Create a test event (this can be empty).
    Click Test, and if everything is configured correctly, you should receive the email.