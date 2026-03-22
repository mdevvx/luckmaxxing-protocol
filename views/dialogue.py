# import discord
# import config
# from typing import Callable, List, Optional, Tuple

# from utils.logger import logger


# class DialogueView(discord.ui.View):
#     """
#     Interactive view that drives the step-by-step training dialogue.

#     Each "Gamblors" line becomes a clickable button (the user's response).
#     "Intern" lines are displayed in the embed automatically.

#     The view is posted in the user's private training channel.
#     Only the enrolled user can interact with it.
#     """

#     # ──────────────────────────────────────────
#     #  Construction
#     # ──────────────────────────────────────────

#     def __init__(
#         self,
#         content: List[Tuple[str, str]],
#         on_complete: Optional[Callable] = None,
#         user_id: Optional[int] = None,
#         timeout: float = 600,
#     ):
#         """
#         Args:
#             content:     List of (speaker, message) tuples.
#             on_complete: Async callback(user) invoked when the last button is pressed.
#             user_id:     If set, only this Discord user can interact with the view.
#             timeout:     Seconds before the view auto-disables (default 10 min).
#         """
#         super().__init__(timeout=timeout)
#         self.content = content
#         self.on_complete_callback = on_complete
#         self.user_id = user_id
#         self.current_index: int = 0
#         self.message: Optional[discord.Message] = None
#         self._completed = False

#         self._render_buttons()

#     # ──────────────────────────────────────────
#     #  Interaction guard
#     # ──────────────────────────────────────────

#     async def interaction_check(self, interaction: discord.Interaction) -> bool:
#         """Reject button presses from users other than the enrolled trainee."""
#         if self.user_id and interaction.user.id != self.user_id:
#             await interaction.response.send_message(
#                 "This is not your training channel.", ephemeral=True
#             )
#             return False
#         return True

#     # ──────────────────────────────────────────
#     #  Button management
#     # ──────────────────────────────────────────

#     def _render_buttons(self):
#         """Rebuild the button row for the current position."""
#         self.clear_items()

#         at_end = self.current_index >= len(self.content) - 1

#         if at_end:
#             btn = discord.ui.Button(
#                 label="Complete",
#                 style=discord.ButtonStyle.success,
#                 custom_id="dialogue_complete",
#             )
#             btn.callback = self._on_complete
#         else:
#             # Show the next Gamblors line as the button label so it feels like
#             # the user is *speaking* the response.
#             next_speaker, next_msg = self.content[self.current_index + 1]
#             if next_speaker == "Gamblors":
#                 label = next_msg[:77] + "..." if len(next_msg) > 80 else next_msg
#             else:
#                 label = "Next"

#             btn = discord.ui.Button(
#                 label=label,
#                 style=discord.ButtonStyle.primary,
#                 custom_id="dialogue_next",
#             )
#             btn.callback = self._on_next

#         self.add_item(btn)

#     # ──────────────────────────────────────────
#     #  Callbacks
#     # ──────────────────────────────────────────

#     async def _on_next(self, interaction: discord.Interaction):
#         await interaction.response.defer()
#         self.current_index += 1
#         self._render_buttons()
#         try:
#             await interaction.message.edit(embed=self._build_embed(), view=self)
#         except Exception as exc:
#             logger.error(f"DialogueView._on_next edit failed: {exc}")

#     async def _on_complete(self, interaction: discord.Interaction):
#         await interaction.response.defer()

#         self._completed = True

#         # Disable all buttons to signal finality
#         for item in self.children:
#             item.disabled = True  # type: ignore[attr-defined]

#         try:
#             await interaction.message.edit(view=self)
#         except Exception as exc:
#             logger.error(f"DialogueView._on_complete edit failed: {exc}")

#         if self.on_complete_callback:
#             try:
#                 await self.on_complete_callback(interaction.user)
#             except Exception as exc:
#                 logger.error(f"on_complete_callback raised: {exc}")

#         logger.info(f"User {interaction.user.id} completed a dialogue")

#     # ──────────────────────────────────────────
#     #  Embed builder
#     # ──────────────────────────────────────────

#     def _build_embed(self) -> discord.Embed:
#         speaker, message = self.content[self.current_index]
#         color = config.EMBED_COLOR if speaker == "Intern" else config.EMBED_COLOR
#         embed = discord.Embed(description=message, color=color)
#         embed.set_footer(
#             text=f"{speaker}  •  {self.current_index + 1}/{len(self.content)}"
#         )
#         return embed

#     def get_initial_embed(self) -> discord.Embed:
#         return self._build_embed()

#     # ──────────────────────────────────────────
#     #  Timeout
#     # ──────────────────────────────────────────

#     async def on_timeout(self):
#         if self._completed:  # ← add this guard
#             return
#         for item in self.children:
#             item.disabled = True
#         if self.message:
#             try:
#                 await self.message.edit(
#                     content="> Session timed out. Click the button below to resume when ready.",
#                     view=self,
#                 )
#             except Exception:
#                 pass

import discord
import config
from typing import Callable, List, Optional, Tuple

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
        """
        Args:
            content:         List of (speaker, message) tuples.
            on_complete:     Async callback(user) invoked when the last button is pressed.
            user_id:         If set, only this Discord user can interact with the view.
            timeout:         Seconds before the view auto-disables (default 10 min).
            on_button_click: Optional zero-arg callable fired on every button press
                             (used to reset the 24-hour inactivity timer).
        """
        super().__init__(timeout=timeout)
        self.content = content
        self.on_complete_callback = on_complete
        self.on_button_click = on_button_click
        self.user_id = user_id
        self.current_index: int = 0
        self.message: Optional[discord.Message] = None
        self._completed = False

        self._render_buttons()

    # ──────────────────────────────────────────
    #  Interaction guard
    # ──────────────────────────────────────────

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Reject button presses from users other than the enrolled trainee."""
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This is not your training channel.", ephemeral=True
            )
            return False
        return True

    # ──────────────────────────────────────────
    #  Button management
    # ──────────────────────────────────────────

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

    # ──────────────────────────────────────────
    #  Callbacks
    # ──────────────────────────────────────────

    async def _on_next(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Fire inactivity-reset hook (non-blocking)
        if self.on_button_click:
            try:
                self.on_button_click()
            except Exception as exc:
                logger.warning(f"on_button_click hook error: {exc}")

        self.current_index += 1
        self._render_buttons()
        try:
            await interaction.message.edit(embed=self._build_embed(), view=self)
        except Exception as exc:
            logger.error(f"DialogueView._on_next edit failed: {exc}")

    async def _on_complete(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Fire inactivity-reset hook before marking complete
        if self.on_button_click:
            try:
                self.on_button_click()
            except Exception as exc:
                logger.warning(f"on_button_click hook error: {exc}")

        self._completed = True

        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

        try:
            await interaction.message.edit(view=self)
        except Exception as exc:
            logger.error(f"DialogueView._on_complete edit failed: {exc}")

        if self.on_complete_callback:
            try:
                await self.on_complete_callback(interaction.user)
            except Exception as exc:
                logger.error(f"on_complete_callback raised: {exc}")

        logger.info(f"User {interaction.user.id} completed a dialogue")

    # ──────────────────────────────────────────
    #  Embed builder
    # ──────────────────────────────────────────

    def _build_embed(self) -> discord.Embed:
        speaker, message = self.content[self.current_index]
        embed = discord.Embed(description=message, color=config.EMBED_COLOR)
        embed.set_footer(
            text=f"{speaker}  •  {self.current_index + 1}/{len(self.content)}"
        )
        return embed

    def get_initial_embed(self) -> discord.Embed:
        return self._build_embed()

    # ──────────────────────────────────────────
    #  Timeout
    # ──────────────────────────────────────────

    async def on_timeout(self):
        if self._completed:
            return
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(
                    content="> Session timed out. Click the button below to resume when ready.",
                    view=self,
                )
            except Exception:
                pass
