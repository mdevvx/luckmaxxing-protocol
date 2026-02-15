"""Database package initialization"""

from database.supabase_db import SupabaseDatabase
from database.base import DatabaseBase

# Singleton instance
_database_instance = None


def get_database() -> DatabaseBase:
    """
    Get database instance (singleton pattern)

    Returns:
        DatabaseBase: Database implementation instance
    """
    global _database_instance

    if _database_instance is None:
        _database_instance = SupabaseDatabase()

    return _database_instance


__all__ = ["get_database", "DatabaseBase", "SupabaseDatabase"]
