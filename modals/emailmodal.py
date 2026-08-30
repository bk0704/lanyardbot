import asyncio
import traceback
from datetime import datetime, timezone
import os

import discord
from discord import ui, Interaction
from discord._types import ClientT
from dotenv import load_dotenv
import discord

from utils.generator import generate_code
from utils.mailer import send_code
from utils.pending import save_pending, get_pending, clear_pending
from utils.validate import is_valid_email
from views.codeview import CodeView

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
            from views.retryview import RetryView
            await interaction.followup.send(f'Please enter a valid {DOMAIN} email', view=RetryView(raw), ephemeral=True)
            return
        code = generate_code()
        save_pending(interaction.user.id, code, now=datetime.now(timezone.utc))
        result = await asyncio.to_thread(send_code, raw.strip().lower(), code)
        if result is None:
            from views.retryview import RetryView
            clear_pending(interaction.user.id)
            await interaction.followup.send(f'Error sending le email, please try again', view=RetryView(raw), ephemeral=True)
            return
        embed = discord.Embed(
            title='Code sent',
            description=f"A code has been sent to {raw}. Check your inbox — if it's not "
                        "there, look in junk. The code expires in 15 minutes.",
        )
        await interaction.followup.send(embed=embed, view=CodeView(), ephemeral=True)

    async def on_error(self, interaction, error):
        traceback.print_exception(type(error), error, error.__traceback__)
        message = "Something went wrong. Please try again in a moment."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
