import discord

class ConfirmView(discord.ui.View):
    def __init__(self, user_id: int, on_confirm, on_cancel=None):
        super().__init__(timeout=60) # 1 Minute Timeout
        self.user_id = user_id
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        async def interaction_check(interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.user_id

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.on_confirm(interaction)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.on_cancel:
                await self.on_cancel(interaction)
            else:
                await interaction.response.send_message("Action cancelled.", ephemeral=True)