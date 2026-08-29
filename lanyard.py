import os

from discord.ext import commands
import discord

from utils.db import init_pool, close_pool


class Lanyard(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='@', intents=intents)

    async def setup_hook(self):
        await init_pool()

        # Loading cogs dynamically
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    await self.load_extension(f'commands.{filename[:-3]}')
                    print (f'Loaded command cog: {filename}')
                except Exception as e:
                    print(f'Failed to load cog {filename}: {e}')


        # # Load event handlers
        # for filename in os.listdir('./events'):
        #     if filename.endswith('.py') and filename != '__init__.py':
        #         try:
        #             await self.load_extension(f'events.{filename[:-3]}')
        #             print(f"Loaded event handler: {filename}")
        #         except Exception as e:
        #             print(f"Failed to load event handler {filename}: {e}")

        # Sync slash commands
        try:
            await self.tree.sync()
            print('Commands synced globally')
            # Debug: Print all registered commands
            print("Registered commands:")
            for cmd in self.tree.get_commands():
                print(f"- {cmd.name}: {cmd.description}")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def close(self) -> None:
        await super().close()
        await close_pool()