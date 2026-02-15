import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# Discord Configuration
# ============================================
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ============================================
# Supabase Database Configuration
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ============================================
# Bot Settings
# ============================================
TOTAL_DAYS = 8  # Number of training days
PROTOCOL_CHANNEL_NAME = "luckmaxxing-protocol"  # Default channel name

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "logs/bot.log"


# ============================================
# Validation
# ============================================
def validate_config():
    """Validate that all required configuration is present"""
    errors = []

    if not DISCORD_TOKEN:
        errors.append("DISCORD_BOT_TOKEN is missing in .env file")

    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is missing in .env file")

    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY is missing in .env file")

    if errors:
        error_msg = "\n❌ Configuration Errors:\n" + "\n".join(
            f"  - {err}" for err in errors
        )
        error_msg += (
            "\n\n📝 Please check your .env file and ensure all required values are set."
        )
        raise ValueError(error_msg)

    return True
