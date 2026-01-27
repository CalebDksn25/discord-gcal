import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# Load the environmental variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Server ID (Right click on server -> Copy ID)
GUILD_ID = 1465479190697611329

class MyClient(discord.Client):

    # Initialize the bot with necessary intents
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    # Setup hook to sync commands to the guild
    async def setup_hook(self):
        # Dev sync the one to server = shows up faster for testing
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Bot is ready and commands are synced.")
    
# Create the client instance
client = MyClient()

# Define a slash ping command
@client.tree.command(name="ping", description="Check if the bot is active")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Bot is active.", ephemeral=True)


# Ensure we have a token before running the bot
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables.")

# Run the bot
client.run(TOKEN)