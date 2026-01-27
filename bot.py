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

# Define the slash help command
@client.tree.command(name="help", description="Get help and list of the commands")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**Available Commands:**\n"
        "/ping - Check if the bot is active.\n"
        "/help - Get help and list of the commands.\n"
        "/add <text> - Add a new event or task to google calendar.\n"
        # Add more commands here as needed
    )
    await interaction.response.send_message(help_text, ephemeral=True)

# Define the /add command 
@client.tree.command(name="add", description="Add a new event or task using NLP")
@app_commands.describe(text="What do you want to add?")
async def add(interaction: discord.Interaction, text: str):
    # Placeholder for NLP processing logic
    await interaction.response.send_message(f"Recieved your request to add: {text}", ephemeral=True)


# Ensure we have a token before running the bot
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables.")

# Run the bot
client.run(TOKEN)