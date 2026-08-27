from discord.ext import commands
from discord import app_commands

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='verify', description='Verify')
    async def verify(self, interaction):
        await interaction.response.send_message(f'Verify verify verify')

async def setup(bot):
    await bot.add_cog(Verification(bot))