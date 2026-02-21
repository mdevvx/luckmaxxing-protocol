import logging
import os
from logging.handlers import RotatingFileHandler

import config

# Emoji → text fallback map for Windows consoles that choke on UTF-8 emojis
_EMOJI_MAP = {
    "✅": "[OK]",
    "❌": "[ERR]",
    "⚠️": "[WARN]",
    "🔧": "[SETUP]",
    "🚀": "[START]",
    "📥": "[JOIN]",
    "📤": "[LEAVE]",
}


def _strip_emojis(text: str) -> str:
    for emoji, replacement in _EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    return text


class _EmojiSafeFormatter(logging.Formatter):
    """Formatter that replaces known emojis so Windows consoles don't break."""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = _strip_emojis(str(record.msg))
        return super().format(record)


def setup_logger(name: str = "luckmaxxing_bot") -> logging.Logger:
    os.makedirs("logs", exist_ok=True)

    log = logging.getLogger(name)
    log.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    # Avoid duplicate handlers when the module is re-imported
    if log.handlers:
        return log

    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_fmt = _EmojiSafeFormatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Rotating file – keeps up to 5 × 10 MB
    fh = RotatingFileHandler(
        config.LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(console_fmt)

    log.addHandler(fh)
    log.addHandler(ch)
    return log


# Module-level singleton used throughout the project
logger = setup_logger()
