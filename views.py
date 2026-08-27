"""Discord UI components for LanyardBot: the persistent Verify button."""

import discord


class VerifyView(discord.ui.View):
    """The view attached to the verification embed posted by /verify.

    timeout=None plus a static custom_id is what makes the button survive a
    restart: bot.add_view(VerifyView()) in setup_hook re-registers this handler
    for every message that already carries the button, including ones posted
    weeks ago. A timed-out view, or one whose custom_id varies per message,
    goes dead the moment the process stops.
    """

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.primary,
        custom_id="lanyard:verify",
    )
    async def verify(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Verification isn't wired up yet -- check back soon.",
            ephemeral=True,
        )
