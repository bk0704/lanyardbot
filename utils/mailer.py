import os
import resend
from dotenv import load_dotenv
from resend.exceptions import ResendError

load_dotenv()
resend.api_key = os.environ['RESEND_API_KEY']
EMAIL_FROM = os.getenv('EMAIL_FROM')

def build_html(code):
    return f"""
<div style="font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #222222; line-height: 1.5;">
  <p>Your LanyardBot verification code:</p>
  <p style="font-size: 30px; font-weight: bold; letter-spacing: 4px; margin: 20px 0;">{code}</p>
  <p>This code expires in 15 minutes.</p>
  <p style="font-size: 13px; color: #666666;">If you didn't request this, you can ignore this email.</p>
</div>
"""

def send_code(email, code):
    params: resend.Emails.SendParams = {
        'from': EMAIL_FROM,
        'to': [email],
        'subject': f'Your LanyardBot OTP is {code}',
        'html': build_html(code),
        'text': f"Your LanyardBot verification code: {code}\n\nThis code expires in 15 minutes.\n\nIf you didn't request this, you can ignore this email."
    }

    try:
        mail_sent = resend.Emails.send(params)
        return f'Email ID: {mail_sent['id']}'
    except ResendError as error:
        print(error)
        return None