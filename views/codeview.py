from discord import ui, ButtonStyle

from modals.codemodal import CodeModal


class CodeView(ui.View):
    def __init__(self):
        super().__init__(timeout=900)

    @ui.button(label='Enter OTP', style=ButtonStyle.primary)
    async def code_button(self, interaction, button):
        await interaction.response.send_modal(CodeModal())
