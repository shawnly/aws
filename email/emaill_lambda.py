import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def lambda_handler(event, context):
    # SMTP Server Configuration
    smtp_server = "smtp.gmail.com"  # Change to your mail server
    smtp_port = 587  # TLS port for Gmail
    smtp_username = os.environ['SMTP_USERNAME']  # Fetch from Lambda environment variables
    smtp_password = os.environ['SMTP_PASSWORD']  # Fetch from Lambda environment variables

    # Email Content
    sender_email = "your-email@gmail.com"  # Change to your sender email
    recipient_email = "recipient@example.com"  # Change to recipient email
    subject = "Test Email from AWS Lambda"
    body_text = "This is a test email sent from AWS Lambda using SMTP."
    
    # Create a MIME Multipart email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Attach the plain text email body
    message.attach(MIMEText(body_text, "plain"))

    # Connect to the SMTP server and send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()

        return {
            'statusCode': 200,
            'body': "Email sent successfully!"
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Failed to send email. Error: {str(e)}"
        }
