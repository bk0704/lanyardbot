from discord import ui

class EmailModal(ui.Modal, title='Enter e-mail'):
    def __init__(self, default=None):
        super().__init__()
        if default: self.email.default = default

