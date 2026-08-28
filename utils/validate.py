import os

from dotenv import load_dotenv

load_dotenv()
DOMAIN = os.getenv('ALLOWED_DOMAIN')

def is_valid_email(email):
    email = email.strip().lower()
    if email.endswith(DOMAIN): return True
    return False