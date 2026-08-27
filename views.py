"""Discord UI for LanyardBot: the verification embed and its persistent button."""

import os

import discord
from dotenv import load_dotenv

load_dotenv()

# Read here rather than in bot.py: the embed copy and the domain check that
# enforces it are both this module's concern, and bot.py stays pure wiring.
ALLOWED_DOMAIN = os.environ["ALLOWED_DOMAIN"]


def verification_embed() -> discord.Embed:
    """The public embed posted by /verify.

    Describes the process only -- deliberately says nothing about which role is
    granted. Re-running /verify can repoint that role, and this message (weeks
    old by then) can't be edited by the new invocation. The process is stable;
    the role is not.
    """
    embed = discord.Embed(
        title="Student Verification",
        description=(
            "Verify that you're a student to unlock the rest of the server.\n"
            "\n"
            "**How it works**\n"
            "1. Click **Verify** below\n"
            f"2. Enter your `@{ALLOWED_DOMAIN}` email address\n"
            "3. Check your inbox for a 6-digit code\n"
            "4. Click **Enter OTP** and type it in\n"
            "\n"
            "**Privacy**\n"
            "Your email is used once to send your code, and is never stored "
            "or shared."
        ),
        color=discord.Color.blurple(),
    )
    # Footer renders small and gray -- the right weight for these two facts.
    embed.set_footer(
        text="Codes expire after 15 minutes | Only you can see your replies"
    )
    return embed


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
        # Phase 2 replaces this body with:
        #     await interaction.response.send_modal(EmailModal())
        # Note that a modal must be the *first* response to an interaction, so
        # nothing slow can happen before it.
        await interaction.response.send_message(
            "Verification isn't wired up yet -- check back soon.",
            ephemeral=True,
        )
