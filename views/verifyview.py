import discord

from modals.emailmodal import EmailModal


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Verify', style=discord.ButtonStyle.success, custom_id='lanyard:verify')
    async def verify_button(self, interaction, button):
        await interaction.response.send_modal(EmailModal())