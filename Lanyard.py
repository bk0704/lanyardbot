import os

from discord.ext import commands
import discord

class Lanyard(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='@', intents=intents)

    async def setup_hook(self):
        # Loading cogs dynamically
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    await self.load_extension(f'commands.{filename[:-3]}')
                    print (f'Loaded command cog: {filename}')
                except Exception as e:
                    print(f'Failed to load cog {filename}: {e}')