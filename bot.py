import dotenv
import discord
import os
from discord.ext import commands
import db
from views import VerifyView

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
        await self.tree.sync()

# TODO: Instantiate

# TODO: Create Verify Command

# TODO: Create the embed

# TODO: Create the @bot.tree.error handler

