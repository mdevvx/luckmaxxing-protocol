from database.supabase_db import SupabaseDatabase

_db_instance = None


def get_database() -> SupabaseDatabase:
    """
    Return a singleton database instance.
    Creating one shared instance avoids duplicate connections.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDatabase()
    return _db_instance
