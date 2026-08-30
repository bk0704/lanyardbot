from discord import ui, ButtonStyle


class RetryView(ui.View):
    def __init__(self, previous=None):
        super().__init__(timeout=900)
        self.previous = previous

    @ui.Button(label='Try again', style=ButtonStyle.secondary)
    async def retry_button(self, interaction, button):
        from modals.emailmodal import EmailModal
        await interaction.response.send_modal(EmailModal(default=self.previous))