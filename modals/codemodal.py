import traceback
from datetime import datetime,timezone

import discord
from discord import ui, TextStyle

from utils.role import get_role
from utils.validate import check_code
from views.retryview import RetryView

#: Replies for every non-'ok' outcome of :func:`utils.validate.check_code`.
#: 'expired' and 'none' deliberately share wording, so the reply does not reveal
#: whether a pending entry existed.
STATUS_MESSAGES = {
    'wrong': "Your code ain't right please try again",
    'expired': 'that code has expired or was already used — start over',
    'none': 'that code has expired or was already used — start over',
}

#: Used for any status missing from STATUS_MESSAGES. Reaching this means
#: check_code grew an outcome nobody wired up here; the role is withheld rather
#: than granted, so a new status can never fail open.
UNKNOWN_STATUS_MESSAGE = (
    'Something went wrong with that code. Please start over and request a new one.'
)


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
            await interaction.followup.send(
                f"this server hasn't been set up yet, ask an admin to run `/verify`",
                ephemeral=True,
            )
            return
        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.followup.send(
                f"this server hasn't been set up yet, ask an admin to run `/verify`",
                ephemeral=True,
            )
            return
        # Checked before check_code, which consumes the pending entry on success:
        # an already-verified user should not burn a code to be told they did not
        # need one.
        if role in interaction.user.roles:
            await interaction.followup.send("You're already verified :)", ephemeral=True)
            return
        status = check_code(user_id, raw, now)
        if status != 'ok':
            # Fail closed: only an explicit 'ok' may continue to add_roles.
            kwargs = {'ephemeral': True}
            if status == 'wrong':
                # Imported here, not at module scope: views.codeview imports this
                # module, so a top-level import would be circular.
                from views.codeview import CodeView
                kwargs['view'] = CodeView()
            await interaction.followup.send(
                STATUS_MESSAGES.get(status, UNKNOWN_STATUS_MESSAGE), **kwargs
            )
            return
        try:
            await interaction.user.add_roles(role, reason='LanyardBot Verification')
            await interaction.followup.send('Congrats on being verified', ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I can't assign that role, my own role may have been moved below it, ask an admin", ephemeral=True)
            return
        except discord.HTTPException as e:
            print(f'Assign failed because of {e}')
            # The code was consumed by check_code before we got here, so there is
            # nothing to retry with -- say so rather than leaving them guessing.
            await interaction.followup.send(
                "Discord wouldn't let me assign the role just then. Your code has "
                "already been used, so please start over and request a new one.",
                ephemeral=True,
            )
            return

    async def on_error(self, interaction, error):
        traceback.print_exception(type(error), error, error.__traceback__)
        message = "Something went wrong. Please try again in a moment."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
