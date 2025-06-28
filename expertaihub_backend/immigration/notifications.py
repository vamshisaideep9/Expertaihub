# from django.core.mail import send_mail
# from twilio.rest import Client as TwilioClient
# from django.conf import settings

# def send_status_alert(user, receipt_number, status):
#     subject = f"USCIS Case {receipt_number} Status Update"
#     message = f"Hello {user.first_name}, your case {receipt_number} status changed to: {status}."
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
#     if user.profile.phone_number and settings.TWILIO_ACCOUNT_SID:
#         client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         client.messages.create(
#             body=message,
#             from_=settings.TWILIO_PHONE_NUMBER,
#             to=user.profile.phone_number
#         )