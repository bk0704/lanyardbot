import asyncio
import traceback
from datetime import datetime, timezone

import discord
from discord import ui, Interaction
from discord._types import ClientT

from utils.config import ALLOWED_DOMAIN
from utils.generator import generate_code
from utils.mailer import send_code
from utils.pending import save_pending, get_pending, clear_pending
from utils.ratelimit import describe_wait, record_send, retry_after_for_send
from utils.validate import is_valid_email
from views.codeview import CodeView

DOMAIN = ALLOWED_DOMAIN

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
        # Normalised once, and used for the rate-limit key as well as the send:
        # keying on the raw value would let capitalisation open a second bucket.
        email = raw.strip().lower()
        now = datetime.now(timezone.utc)
        wait = retry_after_for_send(interaction.user.id, email, now)
        if wait is not None:
            # No RetryView here. Every other failure path offers one, but a
            # "Try again" button on a cooldown invites the loop this limit
            # exists to stop. The wording is identical whichever limit tripped,
            # so it cannot be used to learn that a given address is mid-flow.
            await interaction.followup.send(
                f'Too many code requests — try again in {describe_wait(wait)}.',
                ephemeral=True,
            )
            return
        record_send(interaction.user.id, email, now)
        code = generate_code()
        save_pending(interaction.user.id, code, now=now)
        result = await asyncio.to_thread(send_code, email, code)
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
