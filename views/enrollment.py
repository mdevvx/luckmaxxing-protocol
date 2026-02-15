import discord
from typing import Callable
from utils.logger import logger


class EnrollmentIDModal(discord.ui.Modal, title="Enter Enrollment ID"):
    """Modal for entering enrollment ID"""

    enrollment_id = discord.ui.TextInput(
        label="Enrollment ID",
        placeholder="Enter your 5-character enrollment ID (e.g., XKP87)",
        min_length=5,
        max_length=5,
        required=True,
    )

    def __init__(self, on_submit_callback: Callable):
        super().__init__()
        self.on_submit_callback = on_submit_callback

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            # Pass the enrollment ID to the callback
            await self.on_submit_callback(interaction, self.enrollment_id.value)
        except Exception as e:
            logger.error(f"Error in enrollment ID modal callback: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again later.",
                ephemeral=True,
            )


class EnrollmentView(discord.ui.View):
    """Persistent view for enrollment button"""

    def __init__(self, on_enroll: Callable):
        """
        Initialize enrollment view

        Args:
            on_enroll: Async callback function when user submits enrollment ID
                       Signature: async def callback(interaction, enrollment_id)
        """
        super().__init__(timeout=None)  # Persistent view (no timeout)
        self.on_enroll_callback = on_enroll

    @discord.ui.button(
        label="🎯 Enroll in Luckmaxxing Protocol",
        style=discord.ButtonStyle.success,
        custom_id="enroll_button",  # Persistent ID
    )
    async def enroll_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Handle enrollment button click - show ID input modal"""
        try:
            # Show the ID input modal
            modal = EnrollmentIDModal(on_submit_callback=self.on_enroll_callback)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Error showing enrollment modal: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again later.",
                ephemeral=True,
            )


def create_enrollment_embed() -> discord.Embed:
    """Create the enrollment embed for the protocol channel"""
    embed = discord.Embed(
        title="🎯 Luckmaxxing Protocol",
        description=(
            "Welcome to the **8-Day Luckmaxxing Training Program**!\n\n"
            "Transform from an average gamblor into a statistical anomaly. "
            "This intensive training will equip you with the tools to cultivate luck as a skill.\n\n"
            "**What to Expect:**\n"
            "• Daily training delivered via DM\n"
            "• Interactive dialogue format\n"
            "• 8 days of transformative exercises\n"
            "• Scientifically-backed luck cultivation techniques\n\n"
            "**Requirements:**\n"
            "✅ Valid enrollment ID (get from admins)\n"
            "✅ Commitment to daily practice\n"
            "✅ Open DMs to receive training\n"
            "✅ Dedication to your transformation\n\n"
            "Click the button below and enter your enrollment ID to begin your journey."
        ),
        color=discord.Color.gold(),
    )

    embed.set_footer(text="Gorillions await you. 🚀")

    return embed
