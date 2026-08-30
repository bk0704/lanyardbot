from discord import ui, TextStyle

class CodeModal(ui.Modal, title='Enter OTP'):
    code = ui.TextInput(label='Enter 6-digit OTP',
                        placeholder=f'000000',
                        required=True,
                        max_length=6,
                        min_length=6,
                        style=TextStyle.short
                        )


