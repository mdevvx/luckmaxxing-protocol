from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from database.base import DatabaseBase
from utils.logger import logger
import config


class SupabaseDatabase(DatabaseBase):
    """Supabase database implementation with synchronous initialization"""

    def __init__(self):
        """Initialize with immediate client creation"""
        self.client: Optional[Client] = None
        self._initialized = False

        # Try to initialize immediately
        try:
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            self._initialized = True
            logger.info("Supabase client created in __init__")
        except Exception as e:
            logger.error(f"Failed to create Supabase client in __init__: {e}")
            self.client = None
            self._initialized = False

    async def initialize(self) -> None:
        """Initialize or re-initialize Supabase client"""
        try:
            if self.client is None:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

            self._initialized = True
            logger.info("✅ Supabase client initialized/verified")

            # Test the connection immediately
            try:
                test_response = (
                    self.client.table("enrollments").select("*").limit(1).execute()
                )
                logger.info(
                    f"✅ Database connection verified (found {len(test_response.data) if test_response.data else 0} rows)"
                )
            except Exception as test_error:
                logger.error(f"❌ Database connection test failed: {test_error}")
                raise

        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            self.client = None
            self._initialized = False
            raise

    def _get_client(self) -> Client:
        """Get client, creating it if necessary"""
        if self.client is None:
            logger.warning("Client was None, attempting to recreate...")
            try:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                logger.info("✅ Client recreated successfully")
            except Exception as e:
                logger.error(f"❌ Failed to recreate client: {e}")
                raise RuntimeError(f"Cannot connect to Supabase: {e}")
        return self.client

    async def close(self) -> None:
        """Close Supabase connection"""
        self._initialized = False
        self.client = None
        logger.info("Supabase connection closed")

    async def verify_enrollment_id(self, enrollment_id: str, guild_id: int) -> bool:
        """Verify an enrollment ID exists and is unused"""
        try:
            client = self._get_client()

            # Check if ID exists and is unused
            response = (
                client.table("enrollment_ids")
                .select("*")
                .eq("id_code", enrollment_id)
                .eq("guild_id", guild_id)
                .eq("used", False)
                .execute()
            )

            if response.data and len(response.data) > 0:
                logger.info(
                    f"Enrollment ID {enrollment_id} verified for guild {guild_id}"
                )
                return True
            else:
                logger.warning(
                    f"Invalid or used enrollment ID: {enrollment_id} for guild {guild_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error verifying enrollment ID: {e}")
            return False

    async def enroll_user_with_id(
        self, user_id: int, guild_id: int, enrollment_id: str
    ) -> bool:
        """Enroll a user in the program with a specific enrollment ID"""
        try:
            client = self._get_client()

            # Create enrollment record
            data = {
                "user_id": user_id,
                "guild_id": guild_id,
                "enrollment_id": enrollment_id,
                "enrollment_used": False,  # Will be set to True when they start Day 1
                "current_day": 0,  # Start at intro
                "enrolled_at": datetime.utcnow().isoformat(),
            }

            client.table("enrollments").insert(data).execute()

            # Mark the enrollment ID as used in enrollment_ids table
            client.table("enrollment_ids").update(
                {
                    "used": True,
                    "used_by": user_id,
                    "used_at": datetime.utcnow().isoformat(),
                }
            ).eq("id_code", enrollment_id).eq("guild_id", guild_id).execute()

            logger.info(
                f"✅ User {user_id} enrolled in guild {guild_id} with ID {enrollment_id}"
            )
            return True

        except Exception as e:
            error_msg = str(e)
            if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                logger.warning(f"User {user_id} already enrolled in guild {guild_id}")
                return False
            logger.error(f"Error enrolling user: {e}")
            return False

    async def get_user_progress(
        self, user_id: int, guild_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get user's current progress"""
        try:
            client = self._get_client()
            response = (
                client.table("enrollments")
                .select("*")
                .eq("user_id", user_id)
                .eq("guild_id", guild_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return None

    async def update_user_day(
        self, user_id: int, guild_id: int, current_day: int
    ) -> bool:
        """Update user's current day"""
        try:
            client = self._get_client()

            # Update enrollment
            client.table("enrollments").update(
                {
                    "current_day": current_day,
                    "last_message_sent": datetime.utcnow().isoformat(),
                    "completed": current_day > config.TOTAL_DAYS,
                }
            ).eq("user_id", user_id).eq("guild_id", guild_id).execute()

            # Log progress
            try:
                client.table("daily_progress").insert(
                    {
                        "user_id": user_id,
                        "guild_id": guild_id,
                        "day_number": current_day,
                        "completed_at": datetime.utcnow().isoformat(),
                    }
                ).execute()
            except Exception as progress_error:
                logger.warning(f"Failed to log daily progress: {progress_error}")
                # Don't fail the whole operation if progress logging fails

            logger.info(
                f"✅ Updated user {user_id} to day {current_day} in guild {guild_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user day: {e}")
            return False

    async def mark_enrollment_used(self, user_id: int, guild_id: int) -> bool:
        """Mark enrollment as used when user starts Day 1"""
        try:
            client = self._get_client()
            client.table("enrollments").update(
                {
                    "enrollment_used": True,
                }
            ).eq(
                "user_id", user_id
            ).eq("guild_id", guild_id).execute()

            logger.info(
                f"✅ Marked enrollment as used for user {user_id} in guild {guild_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error marking enrollment as used: {e}")
            return False

    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get guild settings"""
        try:
            client = self._get_client()
            response = (
                client.table("guild_settings")
                .select("*")
                .eq("guild_id", guild_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]

            # Create default settings if not exists
            try:
                data = {
                    "guild_id": guild_id,
                    "bot_enabled": True,
                    "created_at": datetime.utcnow().isoformat(),
                }
                client.table("guild_settings").insert(data).execute()
                logger.info(f"Created default settings for guild {guild_id}")
                return data
            except Exception as insert_error:
                logger.warning(f"Failed to create default settings: {insert_error}")
                # Return default even if insert fails
                return {"guild_id": guild_id, "bot_enabled": True}

        except Exception as e:
            logger.error(f"Error getting guild settings: {e}")
            return {"guild_id": guild_id, "bot_enabled": True}

    async def toggle_bot(self, guild_id: int, enabled: bool) -> None:
        """Enable or disable bot for a guild"""
        try:
            client = self._get_client()
            client.table("guild_settings").upsert(
                {
                    "guild_id": guild_id,
                    "bot_enabled": enabled,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).execute()
            logger.info(
                f"Bot {'enabled' if enabled else 'disabled'} for guild {guild_id}"
            )
        except Exception as e:
            logger.error(f"Error toggling bot: {e}")

    async def is_bot_enabled(self, guild_id: int) -> bool:
        """Check if bot is enabled for a guild"""
        settings = await self.get_guild_settings(guild_id)
        return settings.get("bot_enabled", True)

    async def get_all_enrolled_users(self) -> List[Dict[str, Any]]:
        """Get all enrolled users who are ready for their next message (24hr+ since last message)"""
        try:
            client = self._get_client()

            # Get users who:
            # 1. Haven't completed (completed = false)
            # 2. Are on Day 1-8 (not intro, current_day > 0)
            response = (
                client.table("enrollments")
                .select("*")
                .eq("completed", False)
                .gt("current_day", 0)  # Only users past intro
                .execute()
            )

            # Filter for users who haven't received a message in 24+ hours
            if response.data:
                result = []
                for enrollment in response.data:
                    last_sent = enrollment.get("last_message_sent")

                    # If never sent a message, or sent 24+ hours ago
                    if not last_sent:
                        result.append(enrollment)
                    else:
                        try:
                            last_sent_dt = datetime.fromisoformat(
                                last_sent.replace("Z", "+00:00")
                            )
                            hours_since = (
                                datetime.utcnow() - last_sent_dt.replace(tzinfo=None)
                            ).total_seconds() / 3600

                            if hours_since >= 24:
                                result.append(enrollment)
                        except Exception as e:
                            logger.warning(
                                f"Error parsing date for user {enrollment.get('user_id')}: {e}"
                            )
                            # Include user if we can't parse the date (safer)
                            result.append(enrollment)

                return result

            return []
        except Exception as e:
            logger.error(f"Error getting enrolled users: {e}")
            return []

    async def unenroll_user(self, user_id: int, guild_id: int) -> bool:
        """Unenroll a user from the program and remove all related data"""
        try:
            client = self._get_client()

            # Get the enrollment ID first so we can free it up
            enrollment = await self.get_user_progress(user_id, guild_id)
            enrollment_id = enrollment.get("enrollment_id") if enrollment else None

            # Delete from daily_progress first (foreign key consideration)
            try:
                client.table("daily_progress").delete().eq("user_id", user_id).eq(
                    "guild_id", guild_id
                ).execute()
                logger.info(
                    f"Deleted daily progress for user {user_id} in guild {guild_id}"
                )
            except Exception as e:
                logger.warning(f"Error deleting daily progress: {e}")

            # Delete from enrollments
            client.table("enrollments").delete().eq("user_id", user_id).eq(
                "guild_id", guild_id
            ).execute()

            # Free up the enrollment ID if it exists
            if enrollment_id:
                try:
                    client.table("enrollment_ids").update(
                        {
                            "used": False,
                            "used_by": None,
                            "used_at": None,
                        }
                    ).eq("id_code", enrollment_id).eq("guild_id", guild_id).execute()
                    logger.info(f"Freed enrollment ID {enrollment_id}")
                except Exception as e:
                    logger.warning(f"Error freeing enrollment ID: {e}")

            logger.info(f"✅ User {user_id} fully unenrolled from guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error unenrolling user: {e}")
            return False

    async def get_stats(self, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics about enrollments"""
        try:
            client = self._get_client()

            # Build base query
            query = client.table("enrollments").select("*", count="exact")
            if guild_id:
                query = query.eq("guild_id", guild_id)

            total_response = query.execute()
            total = (
                total_response.count
                if hasattr(total_response, "count")
                else len(total_response.data) if total_response.data else 0
            )

            # Get completed count
            completed_query = (
                client.table("enrollments")
                .select("*", count="exact")
                .eq("completed", True)
            )
            if guild_id:
                completed_query = completed_query.eq("guild_id", guild_id)

            completed_response = completed_query.execute()
            completed = (
                completed_response.count
                if hasattr(completed_response, "count")
                else len(completed_response.data) if completed_response.data else 0
            )

            return {
                "total_enrolled": total,
                "completed": completed,
                "in_progress": total - completed,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_enrolled": 0, "completed": 0, "in_progress": 0}

    async def generate_enrollment_ids(self, guild_id: int, count: int) -> List[str]:
        """Generate unique enrollment IDs for a guild"""
        try:
            client = self._get_client()
            generated_ids = []

            import secrets
            import string

            for _ in range(count):
                # Generate a random 5-character ID
                id_code = "".join(
                    secrets.choice(string.ascii_uppercase + string.digits)
                    for _ in range(5)
                )

                try:
                    # Insert into enrollment_ids table
                    client.table("enrollment_ids").insert(
                        {
                            "id_code": id_code,
                            "guild_id": guild_id,
                            "created_at": datetime.utcnow().isoformat(),
                            "used": False,
                        }
                    ).execute()

                    generated_ids.append(id_code)
                    logger.info(
                        f"Generated enrollment ID: {id_code} for guild {guild_id}"
                    )

                except Exception as e:
                    error_msg = str(e)
                    if (
                        "duplicate" in error_msg.lower()
                        or "unique" in error_msg.lower()
                    ):
                        # If duplicate, try again with a new ID
                        logger.warning(f"Duplicate ID {id_code}, regenerating...")
                        continue
                    else:
                        logger.error(f"Error generating ID {id_code}: {e}")
                        continue

            return generated_ids

        except Exception as e:
            logger.error(f"Error in generate_enrollment_ids: {e}")
            return []

    async def get_unused_enrollment_ids(self, guild_id: int) -> List[str]:
        """Get all unused enrollment IDs for a guild"""
        try:
            client = self._get_client()

            response = (
                client.table("enrollment_ids")
                .select("id_code")
                .eq("guild_id", guild_id)
                .eq("used", False)
                .order("created_at", desc=True)
                .execute()
            )

            if response.data:
                return [row["id_code"] for row in response.data]

            return []

        except Exception as e:
            logger.error(f"Error getting unused enrollment IDs: {e}")
            return []
