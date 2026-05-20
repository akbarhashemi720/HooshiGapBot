# HooshiGap Voice Profile
# This module contains all voice logic independent of Telegram

from voice import (
    save_voice_profile,
    delete_voice_profile,
    get_voice_profile,
    get_voice_badge,
    send_voice_profile,
    get_voice_label,
    VOICE_MODE_REAL,
    VOICE_MODE_MODIFIED,
    VOICE_MODE_HIDDEN
)

__all__ = [
    "save_voice_profile",
    "delete_voice_profile",
    "get_voice_profile",
    "get_voice_badge",
    "send_voice_profile",
    "get_voice_label",
    "VOICE_MODE_REAL",
    "VOICE_MODE_MODIFIED",
    "VOICE_MODE_HIDDEN"
]
