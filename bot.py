import dotenv
import discord
import os

from discord import app_commands
from discord.ext import commands
import db
from views import VerifyView, verification_embed

dotenv.load_dotenv()
TOKEN = os.environ["DISCORD_TOKEN"]

# TODO: Create LanyardBot Class
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

# TODO: Create Verify Command
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



# TODO: Create the @bot.tree.error handler

