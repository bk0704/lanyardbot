import os

import discord
from discord import ui, Interaction
from discord._types import ClientT
from dotenv import load_dotenv
import discord

from utils.validate import is_valid_email

load_dotenv()
DOMAIN = os.getenv('ALLOWED_DOMAIN')

class EmailModal(ui.Modal, title='Enter e-mail'):
    email = ui.TextInput(label='Enter uni email',
                         placeholder=f'you{DOMAIN}',
                         required=True,
                         max_length=100,
                         style=discord.TextStyle.short)

    def __init__(self, default=None):
        super().__init__()
        if default:
            self.email.default = default

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        raw = self.email.value
        if not is_valid_email(raw):
            await interaction.followup.send('Your email is a lil bit too shitty imo')
            return
