import asyncio
from datetime import datetime, timezone
import os

import discord
from discord import ui, Interaction
from discord._types import ClientT
from dotenv import load_dotenv
import discord

from tests.utils.compose import user_id
from utils.generator import generate_code
from utils.mailer import send_code
from utils.pending import save_pending, get_pending, clear_pending
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
        code = generate_code()
        save_pending(interaction.user.id, code, now=datetime.now(timezone.utc))
        result = await asyncio.to_thread(send_code, raw.strip().lower(), code)
