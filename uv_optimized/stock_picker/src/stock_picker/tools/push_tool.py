import os
import smtplib
from email.message import EmailMessage

from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()


@tool("Send Mail Notification")
def send_push_email(message: str, subject: str = "Stock Picker Notification") -> str:
    """Send a notification email to the configured recipient using Gmail SMTP.

    Args:
        message: The plain-text body of the notification.
        subject: The subject line of the email.
    """
    sender = os.environ["GMAIL_SENDER_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("NOTIFY_EMAIL_ADDRESS", sender)

    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = subject
    email.set_content(message)

    # Gmail rejects account passwords for SMTP; GMAIL_APP_PASSWORD must be a
    # 16-character App Password generated with 2-Step Verification enabled.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.send_message(email)

    return f"Email notification sent to {recipient}"
