import os
import json
import asyncio
import functools
import discord
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime
from lib.parser import parse_text, ParsedItem
from lib.ui import ConfirmView, build_preview_embed, SelectTaskView

# Choose between OpenAI and Ollama
# View line 381 to switch from OpenAI to Ollama
from lib.openai_client import get_openai_response
from lib.ollama import get_ollama_response


from lib.google_calendar import create_calendar_event, create_task, list_today_items, list_open_tasks, done_task, delete_task
from lib.google_auth import get_creds
from lib.fuzz_match import get_best_match
from lib.canvas_client import CanvasClient
from lib.canvas_sync import sync_canvas_assignments_to_google_tasks

# Load the environmental variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Server ID (Right click on server -> Copy ID)
GUILD_ID = 000000000000000  # Replace with your server ID

# Add small pending items storage
PENDING = {}

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
        "/list - List today's events and tasks.\n"
        "/done <item> - Mark an item as completed.\n"
        "/delete <item> - Delete an item.\n"
        "/canvas_sync - Sync Canvas assignments to Google Tasks.\n"
        # Add more commands here as needed
    )
    await interaction.response.send_message(help_text, ephemeral=True)

# Define the /list command that will list upcoming events and tasks
@client.tree.command(name="list", description="List today's events and tasks")
async def list_items(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    # Get the google API credentials
    creds = get_creds()

    # List today's items
    items = list_today_items(creds)

    if not items["events"] and not items["tasks"] and not items["completed"]:
        await interaction.followup.send("No events or tasks found for today.", ephemeral=True)
        return
    response_lines = ["**Today's Events and Tasks:**"]
    if items["events"]:
        response_lines.append("\n**Events:**")
        for event in items["events"]:
            start = event.get("start").get("dateTime", event.get("start").get("date"))
            # Parse and format the datetime
            try:
                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%I:%M %p")  # e.g., "07:00 PM"
                response_lines.append(f"- {event.get('summary')} at {formatted_time}")
            except:
                response_lines.append(f"- {event.get('summary')} at {start}")
    else:
        response_lines.append("\nNo events found for today.")

    if items["tasks"]:
        response_lines.append("\n**Tasks:**")
        for task in items["tasks"]:
            due = task.get("due")
            if due:
                # Parse and format the due date
                try:
                    dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%b %d, %Y")  # e.g., "Jan 27, 2026"
                    response_lines.append(f"- {task.get('title')} (Due: {formatted_date})")
                except:
                    response_lines.append(f"- {task.get('title')} (Due: {due})")
            else:
                response_lines.append(f"- {task.get('title')} (No due date)")
    else:
        response_lines.append("\nNo tasks found for today.")
    
    if items["completed"]:
        response_lines.append("\n**Completed Items:**")
        for completed in items["completed"]:
            response_lines.append(f"~~{completed.get('title')}~~")
    else:
        response_lines.append("\nNo completed items for today.")

    await interaction.followup.send("\n".join(response_lines), ephemeral=True)

# Define the /delete command that will delete a task or event as completed
@client.tree.command(name="delete", description="Delete an item")
@app_commands.describe(item="What is the name of the item to delete?")
async def delete(interaction: discord.Interaction, item: str):
    # Acknowledge quickly to avoid interaction timeout
    await interaction.response.defer(thinking=True, ephemeral=True)

    # Run all blocking operations in a thread pool
    loop = asyncio.get_event_loop()
    creds = await loop.run_in_executor(None, get_creds)
    items = await loop.run_in_executor(None, list_open_tasks, creds)
    matches = await loop.run_in_executor(None, get_best_match, item, items)
    # RETURNS: [(index, score), ...] EX-> [(2, 68.42), (4, 55.55)]

    # If no matches found, inform the user
    if not matches:
        await interaction.followup.send(
            f"No matching item found for '{item}'.",
            ephemeral=True
        )
        return
    
    # Store in pending for confirmation
    PENDING[interaction.user.id] = {
        "original_query": item,
        "matches": matches,
        "items": items
    }

    async def on_select(interaction2: discord.Interaction, selected_idx: int):
        # Get the pending item
        item_dict = PENDING.pop(interaction2.user.id, None)

        # If there is no pending item, inform the user
        if not item_dict:
            await interaction2.response.send_message("No pending item found.", ephemeral=True)
            return

        # Get the selected task
        match_idx = item_dict["matches"][selected_idx][0]
        matched_task = item_dict["items"][match_idx]
        
        # Verify task has an ID
        task_id = matched_task.get("id")
        if not task_id:
            await interaction2.response.send_message(
                f" Error: Task '{matched_task.get('title')}' has no ID. Cannot delete.",
                ephemeral=True
            )
            return
        
        # Run delete_task in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            # Use functools.partial to bind the creds argument
            delete_func = functools.partial(delete_task, creds, task_id)
            success = await loop.run_in_executor(None, delete_func)
        except Exception as e:
            await interaction2.response.send_message(
                f"Error deleting task: {str(e)}",
                ephemeral=True
            )
            return

        if not success:
            await interaction2.response.send_message(
                f"Failed to delete '{matched_task.get('title')}'.",
                ephemeral=True
            )
            return
        
        await interaction2.response.send_message(
            f"Deleted: **{matched_task.get('title')}**",
            ephemeral=True
        )
    
    async def on_cancel(interaction2: discord.Interaction):
        PENDING.pop(interaction2.user.id, None)
        await interaction2.response.send_message(f"Cancelled.", ephemeral=True)

    # Build preview text showing all matches (limit to top 5)
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    top_matches = matches[:5]  # Only show top 5 matches
    preview_lines = [f"**Found {len(matches)} match(es) for '{item}':**\n"]
    
    for idx, (item_idx, score) in enumerate(top_matches):
        task = items[item_idx]
        preview_lines.append(f"{emojis[idx]} **{task.get('title')}** (Match: {score:.0f}%)")
    
    preview_lines.append("\n**Select the item to delete:**")
    preview_text = "\n".join(preview_lines)

    await interaction.followup.send(
        preview_text,
        view=SelectTaskView(interaction.user.id, matches, items, on_select, on_cancel),
        ephemeral=True
    )

# Define the /done command that will mark tasks or events as completed
@client.tree.command(name="done", description="Mark an item as completed")
@app_commands.describe(item="What is the name of the item to mark as done?")
async def done(interaction: discord.Interaction, item: str):
    # Acknowledge quickly to avoid interaction timeout - MUST be first thing
    await interaction.response.defer(thinking=True, ephemeral=True)

    # Run all blocking operations in a thread pool
    loop = asyncio.get_event_loop()
    creds = await loop.run_in_executor(None, get_creds)
    items = await loop.run_in_executor(None, list_open_tasks, creds)
    matches = await loop.run_in_executor(None, get_best_match, item, items)
    # RETURNS: [(index, score), ...] EX-> [(2, 68.42), (4, 55.55)]

    # If no matches found, inform the user
    if not matches:
        await interaction.followup.send(
            f"No matching item found for '{item}'.",
            ephemeral=True
        )
        return
    
    # Store in pending for confirmation
    PENDING[interaction.user.id] = {
        "original_query": item,
        "matches": matches,
        "items": items
    }

    async def on_select(interaction2: discord.Interaction, selected_idx: int):
        # Get the pending item
        item_dict = PENDING.pop(interaction2.user.id, None)

        # If there is no pending item, inform the user
        if not item_dict:
            await interaction2.response.send_message("No pending item found.", ephemeral=True)
            return

        # Get the selected task
        match_idx = item_dict["matches"][selected_idx][0]
        matched_task = item_dict["items"][match_idx]
        
        # Verify task has an ID
        task_id = matched_task.get("id")
        if not task_id:
            await interaction2.response.send_message(
                f" Error: Task '{matched_task.get('title')}' has no ID. Cannot mark as complete.",
                ephemeral=True
            )
            return
        
        # Run done_task in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            # Use functools.partial to bind the creds argument
            delete_func = functools.partial(done_task, creds, task_id)
            success = await loop.run_in_executor(None, delete_func)
        except Exception as e:
            await interaction2.response.send_message(
                f"Error marking task as complete: {str(e)}",
                ephemeral=True
            )
            return

        if not success:
            await interaction2.response.send_message(
                f"Failed to mark '{matched_task.get('title')}' as complete.",
                ephemeral=True
            )
            return
        
        await interaction2.response.send_message(
            f"Marked as complete: **{matched_task.get('title')}**",
            ephemeral=True
        )
    
    async def on_cancel(interaction2: discord.Interaction):
        PENDING.pop(interaction2.user.id, None)
        await interaction2.response.send_message(f"Cancelled.", ephemeral=True)

    # Build preview text showing all matches (limit to top 5)
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    top_matches = matches[:5]  # Only show top 5 matches
    preview_lines = [f"**Found {len(matches)} match(es) for '{item}':**\n"]
    
    for idx, (item_idx, score) in enumerate(top_matches):
        task = items[item_idx]
        preview_lines.append(f"{emojis[idx]} **{task.get('title')}** (Match: {score:.0f}%)")
    
    preview_lines.append("\n**Select the item to mark as complete:**")
    preview_text = "\n".join(preview_lines)

    await interaction.followup.send(
        preview_text,
        view=SelectTaskView(interaction.user.id, matches, items, on_select, on_cancel),
        ephemeral=True
    )

# Define the /add command 
@client.tree.command(name="add", description="Add a new event or task using NLP")
@app_commands.describe(text="What do you want to add?")
async def add(interaction: discord.Interaction, text: str):
    # Acknowledge quickly to avoid interaction timeout
    await interaction.response.defer(thinking=True, ephemeral=True)

    async def on_confirm(interaction2: discord.Interaction):
        item_dict = PENDING.pop(interaction2.user.id, None)

        # If no pending item, inform the user
        if not item_dict:
            await interaction2.response.send_message("No pending item found.", ephemeral=True)
            return

        # Get Google API credentials
        creds = get_creds()      

        # Depending on the type, create calendar event or task
        if item_dict["type"] == "event":
            if not item_dict.get("start_time") or not item_dict.get("end_time"):
                await interaction2.response.send_message(
                    "Missing start/end time for event. Try rephrasing.",
                    ephemeral=True
                )
                return

            # Create the appropriate item
            link = create_calendar_event(creds, item_dict)
            await interaction2.response.send_message(
                f"Added Event: **{item_dict['title'].title()}**\n{link}",
                ephemeral=True
            )

        elif item_dict["type"] == "task":
            # Create a task
            task_id = create_task(creds, item_dict)
            link = f"https://tasks.google.com/embed/list/@default/task/{task_id}"
            await interaction2.response.send_message(
                f"Added task: **{item_dict['title'].title()}**\n{link}",
                ephemeral=True
            )
        
        else:
            # Unknown type
            await interaction2.response.send_message(
                f"Unknown item type: {item_dict.get('type')}",
                ephemeral=True
            )
    
    async def on_cancel(interaction2: discord.Interaction):
        PENDING.pop(interaction2.user.id, None)
        await interaction2.response.send_message(f"Cancelled adding item.", ephemeral=True)

    # Call OpenAI asynchronously to parse the text
    # THIS IS WHERE YOU WOULD PUT `get_ollama_response` IF YOU WANT TO USE OLLAMA INSTEAD
    openai_response = await get_openai_response(text)

    try:
        ai_payload = json.loads(openai_response)
    except json.JSONDecodeError:
        await interaction.followup.send(
            "Sorry, I couldn't parse the AI response. Please try again.",
            ephemeral=True,
        )
        return

    # Store the AI payload for confirmation
    PENDING[interaction.user.id] = ai_payload

    # Build the embed structure
    embed = build_preview_embed(ai_payload)

    await interaction.followup.send(
        embed=embed,
        view=ConfirmView(interaction.user.id, on_confirm, on_cancel),
        ephemeral=True
    )

# Define the /canvas_sync command
@client.tree.command(name="canvas_sync", description="Sync Canvas assignments to Google Tasks")
async def canvas_sync(interaction: discord.Interaction):
    # Acknowledge quickly to avoid interaction timeout
    await interaction.response.defer(thinking=True, ephemeral=True)

    async def run_sync():
        try:
            # Get Canvas token from environment
            canvas_token = os.getenv("CANVAS_TOKEN")
            canvas_api_url = os.getenv("CANVAS_BASE_URL")
            
            if not canvas_token or not canvas_api_url:
                return "Canvas API credentials not configured. Set CANVAS_TOKEN and CANVAS_BASE_URL in .env"
            
            # Initialize Canvas client
            canvas_client = CanvasClient(canvas_api_url, canvas_token)
            
            # Get Google credentials
            creds = get_creds()
            
            # Run the sync in executor to avoid blocking
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                sync_canvas_assignments_to_google_tasks,
                canvas_client,
                creds
            )
            
            # Format response
            response = (
                f"**Canvas Sync Complete**\n\n"
                f"Created: {summary['created']}\n"
                f"Updated: {summary['updated']}\n"
                f"⏭Skipped: {summary['skipped']}\n"
                f"Errors: {summary['errors']}"
            )
            return response
        
        except Exception as e:
            return f"Sync failed: {str(e)}"

    # Run sync and send result
    result = await run_sync()
    await interaction.followup.send(result, ephemeral=True)

# Ensure we have a token before running the bot
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables.")

# Run the bot
client.run(TOKEN)