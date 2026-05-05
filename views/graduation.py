from typing import Optional, Union

import discord

import config
from database.base import DatabaseBase
from utils.logger import logger

_CLOSE_BUTTON_ID = "graduation_close_channel"
_KEEP_OPEN_BUTTON_ID = "graduation_keep_open"


def create_graduation_embed(
    user: Union[discord.Member, discord.User],
    *,
    questions_enabled: bool = False,
) -> discord.Embed:
    """Return the completion embed posted after Day 8."""
    embed = discord.Embed(
        title="Luckmaxxing Protocol Complete",
        description=(
            f"{user.mention}, you finished the 8-Day Luckmaxxing Protocol.\n\n"
            f"You are now a **{config.GRADUATE_ROLE_NAME}** and a **statistical anomaly**.\n\n"
            "Use the buttons below to close this channel or keep it open for questions or feedback."
        ),
        color=config.EMBED_COLOR,
    )

    if questions_enabled:
        embed.add_field(
            name="Questions unlocked",
            value="You can type in this channel now. Close it any time with the red button.",
            inline=False,
        )
        embed.set_footer(text="Badge unlocked. Questions and feedback are enabled.")
    else:
        embed.set_footer(text="Badge unlocked. Choose what happens to this channel next.")

    return embed


class GraduationActionsView(discord.ui.View):
    """Persistent controls for the final post-training channel decision."""

    def __init__(self, db: DatabaseBase, *, questions_enabled: bool = False):
        super().__init__(timeout=None)
        self.db = db

        if questions_enabled:
            self.keep_open.disabled = True

    async def _resolve_context(
        self, interaction: discord.Interaction
    ) -> tuple[Optional[dict], Optional[discord.TextChannel]]:
        channel = interaction.channel
        guild = interaction.guild

        if guild is None or not isinstance(channel, discord.TextChannel):
            return None, None

        progress = await self.db.get_enrollment_by_channel(guild.id, channel.id)
        if not progress:
            return None, channel

        return progress, channel

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        progress, _channel = await self._resolve_context(interaction)
        if not progress:
            await interaction.response.send_message(
                "This completion action is no longer available.",
                ephemeral=True,
            )
            return False

        if not progress.get("completed"):
            await interaction.response.send_message(
                "This action unlocks after training is complete.",
                ephemeral=True,
            )
            return False

        if interaction.user.id != progress["user_id"]:
            await interaction.response.send_message(
                "This is not your completion badge.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Chief, me ready use powers.",
        style=discord.ButtonStyle.danger,
        custom_id=_CLOSE_BUTTON_ID,
    )
    async def close_channel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        progress, channel = await self._resolve_context(interaction)
        if not progress or channel is None:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "This channel is already gone.",
                    ephemeral=True,
                )
            return

        await interaction.response.send_message(
            "Closing this channel.",
            ephemeral=True,
        )

        try:
            await self.db.save_channel_id(
                progress["user_id"], progress["guild_id"], None
            )
            await channel.delete(reason="Graduate chose to close their channel")
        except discord.Forbidden:
            logger.warning(f"Missing permission to delete completed channel {channel.id}")
            await interaction.followup.send(
                "I could not close this channel. Ask an admin to check my permissions.",
                ephemeral=True,
            )
        except Exception as exc:
            logger.error(f"GraduationActionsView.close_channel: {exc}")
            await interaction.followup.send(
                "Something went wrong while closing this channel.",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Chief, me has question / feedback.",
        style=discord.ButtonStyle.success,
        custom_id=_KEEP_OPEN_BUTTON_ID,
    )
    async def keep_open(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        progress, channel = await self._resolve_context(interaction)
        if not progress or channel is None:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "This completion action is no longer available.",
                    ephemeral=True,
                )
            return

        overwrite = channel.overwrites_for(interaction.user)
        if overwrite.send_messages is True:
            await interaction.response.send_message(
                "Questions are already enabled in this channel.",
                ephemeral=True,
            )
            return

        overwrite.read_messages = True
        overwrite.read_message_history = True
        overwrite.send_messages = True

        try:
            await channel.set_permissions(
                interaction.user,
                overwrite=overwrite,
                reason="Graduate kept channel open for questions or feedback",
            )

            await interaction.response.edit_message(
                embed=create_graduation_embed(
                    interaction.user,
                    questions_enabled=True,
                ),
                view=GraduationActionsView(self.db, questions_enabled=True),
            )
            await interaction.followup.send(
                "Questions and feedback are now enabled. Send your message here when ready.",
                ephemeral=True,
            )
        except discord.Forbidden:
            logger.warning(
                f"Missing permission to reopen completed channel {channel.id} for messaging"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "I could not open this channel for messages. Ask an admin to check my permissions.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "I could not open this channel for messages. Ask an admin to check my permissions.",
                    ephemeral=True,
                )
        except Exception as exc:
            logger.error(f"GraduationActionsView.keep_open: {exc}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Something went wrong while opening this channel for questions.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Something went wrong while opening this channel for questions.",
                    ephemeral=True,
                )
