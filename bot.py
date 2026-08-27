import dotenv
import discord
import os
import logging

from discord import app_commands
from discord.ext import commands
import db
from views import VerifyView, verification_embed

dotenv.load_dotenv()
TOKEN = os.environ["DISCORD_TOKEN"]

class LanyardBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned,
                         intents=discord.Intents.default(),
                         help_command=None)
    async def setup_hook(self):
        db.init()
        self.add_view(VerifyView())
        await self.add_cog(Verification(bot))
        await self.tree.sync()

bot = LanyardBot()

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Post the verification message in this channel")
    @app_commands.describe(role="Role granted to students who verify")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def verify(self, interaction: discord.Interaction, role: discord.Role):
        # Caught here so an admin sees it, instead of as a silent 403 for every
        # student who clicks the button.
        if role.is_default() or role.managed:
            await interaction.response.send_message(
                f"I can't assign **{role.name}** -- pick a normal role.", ephemeral=True)
            return
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"**{role.name}** is above me in the role list, so I can't assign it. "
                "Drag my role above it in Server Settings > Roles, then try again.",
                ephemeral=True)
            return

        db.set_guild_role(interaction.guild.id, role.id)
        # The embed landing in the channel is the confirmation, so this is the
        # interaction's one and only response.
        await interaction.response.send_message(
            embed=verification_embed(), view=VerifyView())



@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction,
                               error: app_commands.AppCommandError):
    # A failed check raises before the command body runs, so nothing has
    # responded yet -- without this the user just sees "The application did
    # not respond."
    if isinstance(error, app_commands.MissingPermissions):
        message = "You need the **Manage Server** permission to use this."
    elif isinstance(error, app_commands.NoPrivateMessage):
        message = "This command only works inside a server."
    else:
        message = "Something went wrong. Please try again."
        logging.getLogger(__name__).exception(
            "unhandled error in /%s", getattr(interaction.command, "name", "?"),
            exc_info=error)

    # is_done() covers both cases: a check that failed before anything
    # responded, and a crash after the command already replied.
    send = (interaction.followup.send if interaction.response.is_done()
            else interaction.response.send_message)
    await send(message, ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)