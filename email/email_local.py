import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# SMTP server configuration
smtp_server = "smtp.gmail.com"  # Replace with your SMTP server
smtp_port = 587  # Port for TLS (for Gmail); you can use 465 for SSL
smtp_username = "your-email@gmail.com"  # Your email address
smtp_password = "your-app-password"  # Your password or app-specific password if using Gmail

# Email content
sender_email = "your-email@gmail.com"  # The email address you're sending from
recipient_email = "recipient@example.com"  # The email address you're sending to
subject = "Test Email from Local Machine"
body_text = "This is a test email sent from a Python script running on a local machine."

# Create a MIME Multipart email message
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = recipient_email
message["Subject"] = subject

# Attach the plain text email body
message.attach(MIMEText(body_text, "plain"))

try:
    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Start TLS (Transport Layer Security) for security
    server.login(smtp_username, smtp_password)  # Log in to the server
    server.sendmail(sender_email, recipient_email, message.as_string())  # Send the email
    server.quit()  # Disconnect from the server
    print("Email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")
