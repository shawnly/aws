# pip install websocket-client
# pip install email
import websocket
import json
import smtplib
from email.mime.text import MIMEText

# WebSocket URL and mail server details
WEBSOCKET_URL = "wss://your-websocket-api-id.execute-api.region.amazonaws.com/Prod"
MAIL_SERVER = "mail-server.xxx.com"
MAIL_PORT = 25
MAIL_USERNAME = "admin"
MAIL_PASSWORD = "your-password"  # if your mail server requires authentication

def on_message(ws, message):
    try:
        # Parse the received message (assumed to be in JSON format)
        parsed_message = json.loads(message)
        action = parsed_message.get("action")
        email_address = parsed_message.get("email-address")
        email_message = parsed_message.get("message")

        # Check if the action is 'email'
        if action == "email" and email_address and email_message:
            print(f"Action: {action}, Sending email to: {email_address}")
            send_email(email_address, email_message)

    except Exception as e:
        print(f"Error parsing message: {e}")

def send_email(to_email, message_body):
    try:
        # Create the email content
        msg = MIMEText(message_body)
        msg['Subject'] = 'Message from WebSocket'
        msg['From'] = MAIL_USERNAME
        msg['To'] = to_email

        # Connect to the mail server
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)  # If authentication is required
            server.sendmail(MAIL_USERNAME, [to_email], msg.as_string())

        print(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Failed to send email: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection established")

if __name__ == "__main__":
    # Initialize the WebSocket connection
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(WEBSOCKET_URL,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
