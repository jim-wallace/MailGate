import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "dev@local"
msg["To"] = "test@example.com"
msg["Subject"] = "Hello from smoke test"
msg.set_content("Lets See")

with smtplib.SMTP("127.0.0.1", 1025) as s:
    s.send_message(msg)

print("Sent test email to 127.0.0.1:1025")