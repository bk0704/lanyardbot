from discord import ui, ButtonStyle

from modals.codemodal import CodeModal


class CodeView(ui.View):
    def __init__(self):
        # Persistent: no timeout, and the button below carries a custom_id, so
        # the button still resolves after a restart. Registered in
        # Lanyard.setup_hook. Previously timeout=900 with no custom_id, which
        # meant every "Enter OTP" button in the channel died on redeploy and
        # answered clicks with "This interaction failed".
        super().__init__(timeout=None)

    @ui.button(label='Enter OTP', style=ButtonStyle.primary, custom_id='lanyard:code')
    async def code_button(self, interaction, button):
        await interaction.response.send_modal(CodeModal())
