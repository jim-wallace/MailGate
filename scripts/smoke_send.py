import smtplib
import random
import string
from email.message import EmailMessage
from time import sleep


def random_string(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


recipients = [
    "test1@example.com",
    "test2@example.com",
    "test3@example.com"
]


SMTP_HOST = "127.0.0.1"
SMTP_PORT = 1025
NUM_MESSAGES = 10
DELAY_SEC = 0.5

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
    for i in range(NUM_MESSAGES):
        subject = f"Smoke Test {i + 1}/{NUM_MESSAGES} - {random_string(8)}"
        body = (
            f"This is automated test message #{i + 1}.\n"
            f"Random token: {random_string(20)}\n"
        )
        to_addr = random.choice(recipients)

        msg = EmailMessage()
        msg["From"] = "dev@local"
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)

        s.send_message(msg)
        print(f"Sent email {i + 1} to {to_addr} with subject: '{subject}'")

        if DELAY_SEC > 0:
            sleep(DELAY_SEC)

print(f"Finished sending {NUM_MESSAGES} test emails.")
