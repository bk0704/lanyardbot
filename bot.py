import discord
from discord.ext import commands
from discord import app_commands

# Imported before anything else that needs configuration: this validates the
# whole environment and exits with a readable summary before any module
# performs an import-time env read (utils.mailer does exactly that).
from utils.config import DISCORD_TOKEN
from lanyard import Lanyard

bot = Lanyard()
bot.run(DISCORD_TOKEN)
