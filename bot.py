import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from lanyard import Lanyard

# Loading the bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = Lanyard()
bot.run(TOKEN)