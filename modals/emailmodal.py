import os

import discord
from discord import ui
from dotenv import load_dotenv
import discord

load_dotenv()
DOMAIN = os.getenv('ALLOWED_DOMAIN')

class EmailModal(ui.Modal, title='Enter e-mail'):
    def __init__(self, default=None):
        super().__init__()
        if default:
            self.email.default = default

        email = ui.TextInput(label='Enter uni email',
                             placeholder=f'you{DOMAIN}',
                             required=True,
                             max_length=100,
                             style=discord.TextStyle.short)
