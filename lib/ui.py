import discord
from typing import Callable, Optional, Awaitable

OnAction = Callable[[discord.Interaction], Awaitable[None]]

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