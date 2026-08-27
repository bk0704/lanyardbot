import discord
from discord.ext import commands
from discord import app_commands

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='verify', description='Verify')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(role='The role given to members once they verify')
    async def verify(self, interaction: discord.Interaction, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"I can't assign **{role.name}** because it sits above my own role. "
                "Move my role higher in Server Settings > Roles, or pick a lower role.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(title='Verification', description='Click below to verified')
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Verification(bot))
