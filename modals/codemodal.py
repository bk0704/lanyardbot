import traceback
from datetime import datetime,timezone

import discord
from discord import ui, TextStyle

from utils.role import get_role
from utils.validate import check_code
from views.retryview import RetryView


class CodeModal(ui.Modal, title='Enter OTP'):
    code = ui.TextInput(label='Enter 6-digit OTP',
                        placeholder=f'000000',
                        required=True,
                        max_length=6,
                        min_length=6,
                        style=TextStyle.short
                        )

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        raw = self.code.value
        now = datetime.now(timezone.utc)
        user_id = interaction.user.id
        role_id = await get_role(interaction.guild.id)
        if role_id is None:
            await interaction.followup.send(f"this server hasn't been set up yet, ask an admin to run `/verify`")
            return
        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.followup.send(f"this server hasn't been set up yet, ask an admin to run `/verify`")
            return
        status = check_code(user_id, raw, now)
        if status == 'wrong':
            from views.codeview import CodeView
            await interaction.followup.send('Your code ain\'t right please try again', view=CodeView(), ephemeral=True)
            return
        if status == 'expired' or status == 'none':
            await interaction.followup.send('that code has expired or was already used — start over', ephemeral=True)
            return
        if role in interaction.user.roles: await interaction.followup.send('Your are already verified :)', ephemeral=True)
        try:
            await interaction.user.add_roles(role, reason='LanyardBot Verification')
            await interaction.followup.send('Congrats on being verified', ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I can't assign that role, my own role may have been moved below it, ask an admin", ephemeral=True)
            return
        except discord.HTTPException as e:
            print(f'Assign failed because of {e}')
            return

    async def on_error(self, interaction, error):
        traceback.print_exception(type(error), error, error.__traceback__)
        message = "Something went wrong. Please try again in a moment."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        await interaction.response.send_message(message, ephemeral=True)
