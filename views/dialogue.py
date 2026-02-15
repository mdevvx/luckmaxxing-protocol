import discord
from typing import List, Tuple, Optional, Callable
from utils.logger import logger


class DialogueView(discord.ui.View):
    """Interactive view for dialogue progression"""

    def __init__(
        self,
        content: List[Tuple[str, str]],
        on_complete: Optional[Callable] = None,
        timeout: float = 300,
    ):
        """
        Initialize dialogue view

        Args:
            content: List of (speaker, message) tuples
            on_complete: Callback function when dialogue is complete
            timeout: Timeout in seconds (default 5 minutes)
        """
        super().__init__(timeout=timeout)
        self.content = content
        self.current_index = 0
        self.on_complete_callback = on_complete
        self.message: Optional[discord.Message] = None

        # Update button state
        self._update_buttons()

    def _update_buttons(self):
        """Update button states based on current position"""
        # Clear existing buttons
        self.clear_items()

        # Add Next button if not at the end
        if self.current_index < len(self.content) - 1:
            next_button = discord.ui.Button(
                label=self._get_button_label(),
                style=discord.ButtonStyle.primary,
                custom_id="next",
            )
            next_button.callback = self._next_callback
            self.add_item(next_button)
        else:
            # Add Complete button at the end
            complete_button = discord.ui.Button(
                label="✅ Complete",
                style=discord.ButtonStyle.success,
                custom_id="complete",
            )
            complete_button.callback = self._complete_callback
            self.add_item(complete_button)

    def _get_button_label(self) -> str:
        """Get label for the next button based on current speaker"""
        if self.current_index + 1 < len(self.content):
            next_speaker, next_message = self.content[self.current_index + 1]
            if next_speaker == "Gamblors":
                # Show the Gamblor's response as the button text
                # Truncate if too long (Discord button limit is 80 chars)
                label = (
                    next_message[:77] + "..."
                    if len(next_message) > 80
                    else next_message
                )
                return label
        return "Next ➡️"

    async def _next_callback(self, interaction: discord.Interaction):
        """Handle next button click"""
        await interaction.response.defer()

        # Move to next dialogue
        self.current_index += 1

        # Update the message
        embed = self._create_embed()
        self._update_buttons()

        try:
            await interaction.message.edit(embed=embed, view=self)
            logger.debug(f"Moved to dialogue index {self.current_index}")
        except Exception as e:
            logger.error(f"Error updating dialogue: {e}")

    async def _complete_callback(self, interaction: discord.Interaction):
        """Handle complete button click"""
        await interaction.response.defer()

        # Disable all buttons
        for item in self.children:
            item.disabled = True

        try:
            await interaction.message.edit(view=self)

            # Call completion callback if provided
            if self.on_complete_callback:
                await self.on_complete_callback(interaction.user)

            logger.info(f"User {interaction.user.id} completed dialogue")
        except Exception as e:
            logger.error(f"Error completing dialogue: {e}")

    def _create_embed(self) -> discord.Embed:
        """Create embed for current dialogue"""
        speaker, message = self.content[self.current_index]

        # Choose color based on speaker
        color = discord.Color.blue() if speaker == "Intern" else discord.Color.green()

        embed = discord.Embed(description=message, color=color)

        # Add speaker as footer
        embed.set_footer(
            text=f"{speaker} • {self.current_index + 1}/{len(self.content)}"
        )

        return embed

    def get_initial_embed(self) -> discord.Embed:
        """Get the initial embed to display"""
        return self._create_embed()

    async def on_timeout(self):
        """Handle view timeout"""
        # Disable all buttons
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
                logger.debug("Dialogue view timed out")
            except:
                pass
