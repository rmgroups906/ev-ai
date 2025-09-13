import os
from aiosmtplib import SMTP
from email.message import EmailMessage
from ..config import settings

async def send_email_async(to_email: str, subject: str, body: str):
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print('SMTP not configured, skipping email to', to_email)
        return False
    msg = EmailMessage()
    msg['From'] = settings.SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        smtp = SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, start_tls=True)
        await smtp.connect()
        await smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        await smtp.send_message(msg)
        await smtp.quit()
        return True
    except Exception as e:
        print('Email send error', e)
        return False