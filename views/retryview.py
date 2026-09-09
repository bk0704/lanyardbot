from discord import ui, ButtonStyle


class RetryView(ui.View):
    def __init__(self, previous=None):
        # Persistent, for the same reason as CodeView.
        #
        # `previous` only pre-fills the email box as a convenience. Within a
        # single process the instance attached to the message is dispatched to
        # and the pre-fill works; after a restart discord.py falls back to the
        # instance registered in setup_hook, where previous is None, so the
        # button still works and the user just retypes the address. Losing a
        # pre-fill is a much better failure than a dead button.
        super().__init__(timeout=None)
        self.previous = previous

    @ui.button(label='Try again', style=ButtonStyle.secondary, custom_id='lanyard:retry')
    async def retry_button(self, interaction, button):
        from modals.emailmodal import EmailModal
        await interaction.response.send_modal(EmailModal(default=self.previous))
