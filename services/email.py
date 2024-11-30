import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import key
from flask import jsonify

def send_email(subject, html, mailto = key.email_id):
    print("html", html)
    try:
        sender_email = mailto
        sender_password = key.gmail_app_password
        recipient_email = mailto
        subject = subject

        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return True
    except Exception as e:
        return False