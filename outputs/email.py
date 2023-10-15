import smtplib
from email.message import EmailMessage

def send_email(subject, body, to_email, from_email, smtp_server, smtp_port, smtp_login, smtp_password):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_login, smtp_password)
        server.send_message(msg)
