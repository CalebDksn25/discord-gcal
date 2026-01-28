import discord
from typing import Callable, Optional, Awaitable, List, Tuple
from dateutil.parser import isoparse

OnAction = Callable[[discord.Interaction], Awaitable[None]]

class SelectTaskView(discord.ui.View):
    """View with numbered emoji buttons for selecting which task to mark complete"""
    def __init__(self, user_id: int, matches: List[Tuple[int, float]], items: list, on_select: Callable[[discord.Interaction, int], Awaitable[None]], on_cancel: Optional[OnAction] = None):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.matches = matches
        self.items = items
        self.on_select = on_select
        self.on_cancel = on_cancel
        
        # Emoji numbers for buttons
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        
        # Add numbered buttons for each match
        for idx, (item_idx, score) in enumerate(matches[:5]):  # Max 5 buttons
            task = items[item_idx]
            button = discord.ui.Button(
                emoji=emojis[idx],
                style=discord.ButtonStyle.primary,
                custom_id=f"select_{idx}"
            )
            
            async def button_callback(interaction: discord.Interaction, selected_idx=idx):
                await self.on_select(interaction, selected_idx)
                self.stop()
            
            button.callback = button_callback
            self.add_item(button)
        
        # Add cancel button
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
        async def cancel_callback(interaction: discord.Interaction):
            if self.on_cancel:
                await self.on_cancel(interaction)
            else:
                await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
            self.stop()
        cancel_button.callback = cancel_callback
        self.add_item(cancel_button)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This selection isn't for you.",
                ephemeral=True
            )
            return False
        return True

class ConfirmView(discord.ui.View):
    def __init__(self, user_id: int, on_confirm: OnAction, on_cancel: Optional[OnAction] = None):
        super().__init__(timeout=60)  # 1 minute timeout
        self.user_id = user_id
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the user who invoked the command to click buttons
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This confirmation isn't for you.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.on_confirm(interaction)
        self.stop()  # stop listening after action

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.on_cancel:
            await self.on_cancel(interaction)
        else:
            await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.stop()


def build_preview_embed(item: dict) -> discord.Embed:
    embed = discord.Embed(title="Preview")

    item_type = item.get("type", "task")
    title = (item.get("title") or "Untitled").strip().title()
    location = item.get("location")
    assumptions = item.get("assumptions") or []

    embed.add_field(name="Type", value=item_type.capitalize(), inline=True)
    embed.add_field(name="Title", value=title, inline=True)

    if item_type == "event":
        start_s = item.get("start_time")
        end_s = item.get("end_time")
        if start_s and end_s:
            start = isoparse(start_s)
            end = isoparse(end_s)
            when_text = f"{start:%a %b %d, %I:%M %p} – {end:%I:%M %p}"
        elif start_s:
            start = isoparse(start_s)
            when_text = f"{start:%a %b %d, %I:%M %p} (end time missing)"
        else:
            when_text = "⚠️ Could not determine time"
        embed.add_field(name="When", value=when_text, inline=False)

    if item_type == "task":
        due = item.get("due_date")
        embed.add_field(name="Due", value=due or "—", inline=False)

    if location:
        embed.add_field(name="Location", value=location, inline=False)

    if assumptions:
        # Keep it short for Discord
        short = assumptions[:4]
        embed.add_field(name="Assumptions", value="• " + "\n• ".join(short), inline=False)

    notes = item.get("notes")
    if notes:
        embed.add_field(name="Notes", value=notes[:300], inline=False)

    embed.set_footer(text="Confirm adding this item?")
    return embed
