from typing import Callable, List, Optional, Tuple

import discord

import config
from utils.logger import logger


class DialogueView(discord.ui.View):
    """
    Interactive view that drives the step-by-step training dialogue.

    Each "Gamblors" line becomes a clickable button (the user's response).
    "Intern" lines are displayed in the embed automatically.

    The view is posted in the user's private training channel.
    Only the enrolled user can interact with it.
    """

    def __init__(
        self,
        content: List[Tuple[str, str]],
        on_complete: Optional[Callable] = None,
        user_id: Optional[int] = None,
        timeout: float = 600,
        on_button_click: Optional[Callable] = None,
    ):
        super().__init__(timeout=timeout)
        self.content = content
        self.on_complete_callback = on_complete
        self.on_button_click = on_button_click
        self.user_id = user_id
        self.current_index: int = 0
        self.message: Optional[discord.Message] = None
        self._completed = False

        self._render_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Reject button presses from users other than the enrolled trainee."""
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This is not your training channel.", ephemeral=True
            )
            return False
        return True

    def _render_buttons(self):
        """Rebuild the button row for the current position."""
        self.clear_items()

        at_end = self.current_index >= len(self.content) - 1

        if at_end:
            btn = discord.ui.Button(
                label="Complete",
                style=discord.ButtonStyle.success,
                custom_id="dialogue_complete",
            )
            btn.callback = self._on_complete
        else:
            next_speaker, next_msg = self.content[self.current_index + 1]
            if next_speaker == "Gamblors":
                label = next_msg[:77] + "..." if len(next_msg) > 80 else next_msg
            else:
                label = "Next"

            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id="dialogue_next",
            )
            btn.callback = self._on_next

        self.add_item(btn)

    async def _on_next(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if self.on_button_click:
            try:
                self.on_button_click()
            except Exception as exc:
                logger.warning(f"on_button_click hook error: {exc}")

        self.current_index += 1
        self._render_buttons()
        try:
            await interaction.message.edit(
                content=None,
                embed=self._build_embed(),
                view=self,
            )
        except Exception as exc:
            logger.error(f"DialogueView._on_next edit failed: {exc}")

    async def _on_complete(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if self.on_button_click:
            try:
                self.on_button_click()
            except Exception as exc:
                logger.warning(f"on_button_click hook error: {exc}")

        self._completed = True

        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        try:
            await interaction.message.edit(content=None, view=self)
        except Exception as exc:
            logger.error(f"DialogueView._on_complete edit failed: {exc}")

        if self.on_complete_callback:
            try:
                await self.on_complete_callback(interaction.user)
            except Exception as exc:
                logger.error(f"on_complete_callback raised: {exc}")

        logger.info(f"User {interaction.user.id} completed a dialogue")

    def _build_embed(self) -> discord.Embed:
        speaker, message = self.content[self.current_index]
        embed = discord.Embed(description=message, color=config.EMBED_COLOR)
        embed.set_footer(
            text=f"{speaker}  •  {self.current_index + 1}/{len(self.content)}"
        )
        return embed

    def get_initial_embed(self) -> discord.Embed:
        return self._build_embed()

    def _spawn_resumed_view(self) -> "DialogueView":
        timeout = self.timeout if self.timeout is not None else 600
        resumed_view = DialogueView(
            self.content,
            on_complete=self.on_complete_callback,
            user_id=self.user_id,
            timeout=timeout,
            on_button_click=self.on_button_click,
        )
        resumed_view.current_index = self.current_index
        resumed_view.message = self.message
        resumed_view._render_buttons()
        return resumed_view

    async def on_timeout(self):
        if self._completed or not self.message:
            return

        try:
            resumed_view = self._spawn_resumed_view()
            await self.message.edit(
                content="> Session timed out. Continue when ready.",
                embed=resumed_view.get_initial_embed(),
                view=resumed_view,
            )
        except Exception:
            pass
