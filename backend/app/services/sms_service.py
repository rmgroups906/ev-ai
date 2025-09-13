from twilio.rest import Client
from ..config import settings

def send_sms(to_number: str, body: str):
    if not settings.TWILIO_SID or not settings.TWILIO_AUTH or not settings.TWILIO_FROM:
        print('Twilio not configured, skipping SMS to', to_number)
        return False
    client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)
    try:
        client.messages.create(body=body, from_=settings.TWILIO_FROM, to=to_number)
        return True
    except Exception as e:
        print('SMS send error', e)
        return False