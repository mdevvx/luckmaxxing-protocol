from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class DatabaseBase(ABC):
    """Abstract base class for database operations"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection and create tables if needed"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def enroll_user_with_id(
        self, user_id: int, guild_id: int, enrollment_id: str
    ) -> bool:
        """
        Enroll a user in the program with a specific enrollment ID

        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            enrollment_id: The enrollment ID code being used

        Returns:
            True if enrolled successfully, False otherwise
        """
        pass

    @abstractmethod
    async def verify_enrollment_id(self, enrollment_id: str, guild_id: int) -> bool:
        """
        Verify an enrollment ID exists and is unused

        Args:
            enrollment_id: The enrollment ID code
            guild_id: Discord guild ID

        Returns:
            True if ID is valid and unused, False otherwise
        """
        pass

    @abstractmethod
    async def get_user_progress(
        self, user_id: int, guild_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's current progress

        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID

        Returns:
            Dict with user progress or None if not enrolled
        """
        pass

    @abstractmethod
    async def update_user_day(
        self, user_id: int, guild_id: int, current_day: int
    ) -> bool:
        """
        Update user's current day

        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            current_day: New current day number

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """
        Get guild settings

        Args:
            guild_id: Discord guild ID

        Returns:
            Dict with guild settings
        """
        pass

    @abstractmethod
    async def toggle_bot(self, guild_id: int, enabled: bool) -> None:
        """
        Enable or disable bot for a guild

        Args:
            guild_id: Discord guild ID
            enabled: Whether bot should be enabled
        """
        pass

    @abstractmethod
    async def is_bot_enabled(self, guild_id: int) -> bool:
        """
        Check if bot is enabled for a guild

        Args:
            guild_id: Discord guild ID

        Returns:
            True if enabled, False otherwise
        """
        pass

    @abstractmethod
    async def get_all_enrolled_users(self) -> List[Dict[str, Any]]:
        """
        Get all enrolled users across all guilds

        Returns:
            List of user enrollment records
        """
        pass

    @abstractmethod
    async def unenroll_user(self, user_id: int, guild_id: int) -> bool:
        """
        Unenroll a user from the program

        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID

        Returns:
            True if unenrolled successfully
        """
        pass

    @abstractmethod
    async def get_stats(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics about enrollments

        Args:
            guild_id: Optional guild ID to filter stats

        Returns:
            Dict with statistics (total_enrolled, completed, in_progress)
        """
        pass

    @abstractmethod
    async def mark_enrollment_used(self, user_id: int, guild_id: int) -> bool:
        """
        Mark enrollment as used when user starts Day 1

        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID

        Returns:
            True if marked successfully
        """
        pass

    @abstractmethod
    async def generate_enrollment_ids(self, guild_id: int, count: int) -> List[str]:
        """
        Generate unique enrollment IDs for a guild

        Args:
            guild_id: Discord guild ID
            count: Number of IDs to generate

        Returns:
            List of generated ID codes
        """
        pass

    @abstractmethod
    async def get_unused_enrollment_ids(self, guild_id: int) -> List[str]:
        """
        Get all unused enrollment IDs for a guild

        Args:
            guild_id: Discord guild ID

        Returns:
            List of unused ID codes
        """
        pass
