# from abc import ABC, abstractmethod
# from typing import Optional, List, Dict, Any


# class DatabaseBase(ABC):
#     """Abstract base class defining all database operations for the bot."""

#     # ─────────────────────────────────────────────
#     #  Lifecycle
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def initialize(self) -> None:
#         """Initialize / verify the database connection."""
#         pass

#     @abstractmethod
#     async def close(self) -> None:
#         """Clean up the database connection."""
#         pass

#     # ─────────────────────────────────────────────
#     #  Enrollment IDs
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def generate_enrollment_ids(self, guild_id: int, count: int) -> List[str]:
#         """Generate `count` unique enrollment codes for `guild_id`."""
#         pass

#     @abstractmethod
#     async def get_unused_enrollment_ids(self, guild_id: int) -> List[str]:
#         """Return all unused enrollment codes for `guild_id`."""
#         pass

#     @abstractmethod
#     async def verify_enrollment_id(self, enrollment_id: str, guild_id: int) -> bool:
#         """Return True if the code exists, belongs to this guild, and is unused."""
#         pass

#     # ─────────────────────────────────────────────
#     #  User Enrollment
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def enroll_user_with_id(
#         self, user_id: int, guild_id: int, enrollment_id: str
#     ) -> bool:
#         """Create an enrollment record and mark the code as used."""
#         pass

#     @abstractmethod
#     async def unenroll_user(self, user_id: int, guild_id: int) -> bool:
#         """Delete the user's enrollment record and free their code."""
#         pass

#     @abstractmethod
#     async def mark_enrollment_used(self, user_id: int, guild_id: int) -> bool:
#         """Flip enrollment_used=True once the user starts Day 1."""
#         pass

#     # ─────────────────────────────────────────────
#     #  Progress Tracking
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def get_user_progress(
#         self, user_id: int, guild_id: int
#     ) -> Optional[Dict[str, Any]]:
#         """Return the enrollment row for the user, or None if not enrolled."""
#         pass

#     @abstractmethod
#     async def update_user_day(
#         self, user_id: int, guild_id: int, current_day: int
#     ) -> bool:
#         """Advance the user to `current_day` and timestamp last_message_sent."""
#         pass

#     @abstractmethod
#     async def get_all_enrolled_users(self) -> List[Dict[str, Any]]:
#         """
#         Return every enrollment whose next daily message is due
#         (last_message_sent >= 24 h ago, or never sent, and not completed).
#         """
#         pass

#     # ─────────────────────────────────────────────
#     #  Channel management  (NEW - channel-based flow)
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def save_channel_id(
#         self, user_id: int, guild_id: int, channel_id: int
#     ) -> bool:
#         """Persist the private training channel ID on the enrollment row."""
#         pass

#     # ─────────────────────────────────────────────
#     #  Guild Settings
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
#         """Return all settings for the guild (creates defaults if missing)."""
#         pass

#     @abstractmethod
#     async def toggle_bot(self, guild_id: int, enabled: bool) -> None:
#         """Enable or disable the bot for a guild."""
#         pass

#     @abstractmethod
#     async def is_bot_enabled(self, guild_id: int) -> bool:
#         """Return True if the bot is enabled in this guild."""
#         pass

#     @abstractmethod
#     async def set_guild_config(
#         self,
#         guild_id: int,
#         category_id: Optional[int] = None,
#         role_id: Optional[int] = None,
#         log_channel_id: Optional[int] = None,
#     ) -> bool:
#         """
#         Persist training category, onboarding role, and/or log channel for a guild.
#         Only updates fields that are not None.
#         """
#         pass

#     # ─────────────────────────────────────────────
#     #  Statistics
#     # ─────────────────────────────────────────────

#     @abstractmethod
#     async def get_stats(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
#         """
#         Return enrollment statistics.
#         Pass guild_id to scope to a single server, or None for global.
#         """
#         pass

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class DatabaseBase(ABC):
    """Abstract base class defining all database operations for the bot."""

    # ─────────────────────────────────────────────
    #  Lifecycle
    # ─────────────────────────────────────────────

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    # ─────────────────────────────────────────────
    #  Enrollment IDs
    # ─────────────────────────────────────────────

    @abstractmethod
    async def generate_enrollment_ids(self, guild_id: int, count: int) -> List[str]:
        pass

    @abstractmethod
    async def get_unused_enrollment_ids(self, guild_id: int) -> List[str]:
        pass

    @abstractmethod
    async def verify_enrollment_id(self, enrollment_id: str, guild_id: int) -> bool:
        pass

    # ─────────────────────────────────────────────
    #  User Enrollment
    # ─────────────────────────────────────────────

    @abstractmethod
    async def enroll_user_with_id(
        self, user_id: int, guild_id: int, enrollment_id: str
    ) -> bool:
        pass

    @abstractmethod
    async def unenroll_user(self, user_id: int, guild_id: int) -> bool:
        pass

    @abstractmethod
    async def mark_enrollment_used(self, user_id: int, guild_id: int) -> bool:
        pass

    # ─────────────────────────────────────────────
    #  Progress Tracking
    # ─────────────────────────────────────────────

    @abstractmethod
    async def get_user_progress(
        self, user_id: int, guild_id: int
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_user_day(
        self, user_id: int, guild_id: int, current_day: int
    ) -> bool:
        pass

    @abstractmethod
    async def get_all_enrolled_users(self) -> List[Dict[str, Any]]:
        pass

    # ─────────────────────────────────────────────
    #  Inactivity tracking
    # ─────────────────────────────────────────────

    @abstractmethod
    async def update_last_button_click(self, user_id: int, guild_id: int) -> bool:
        """Stamp the current UTC time as last_button_click on the enrollment row."""
        pass

    @abstractmethod
    async def get_inactive_users(self, seconds: int = 86400) -> List[Dict[str, Any]]:
        """
        Return enrollments (non-completed) where last_button_click is older
        than `seconds` ago, or where the user has never clicked anything and
        enrolled more than `seconds` ago.
        """
        pass

    # ─────────────────────────────────────────────
    #  Channel management
    # ─────────────────────────────────────────────

    @abstractmethod
    async def save_channel_id(
        self, user_id: int, guild_id: int, channel_id: int
    ) -> bool:
        pass

    # ─────────────────────────────────────────────
    #  Guild Settings
    # ─────────────────────────────────────────────

    @abstractmethod
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def toggle_bot(self, guild_id: int, enabled: bool) -> None:
        pass

    @abstractmethod
    async def is_bot_enabled(self, guild_id: int) -> bool:
        pass

    @abstractmethod
    async def set_guild_config(
        self,
        guild_id: int,
        category_id: Optional[int] = None,
        role_id: Optional[int] = None,
        log_channel_id: Optional[int] = None,
    ) -> bool:
        pass

    # ─────────────────────────────────────────────
    #  Statistics
    # ─────────────────────────────────────────────

    @abstractmethod
    async def get_stats(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
        pass
