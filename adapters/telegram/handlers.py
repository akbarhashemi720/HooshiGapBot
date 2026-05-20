# HooshiGap Telegram Adapter
# This module is ONLY a transport layer
# All business logic must be in core/

# Telegram adapter receives events and calls core services
# It must NOT contain any matching, AI, or moderation logic

from core.matching.engine import get_smart_matches, update_behavioral_profile
from core.trust.engine import get_trust, complete_chat_reward
from core.moderation.engine import analyze_message, check_rate_limit
from core.profiles.engine import get_voice_badge, send_voice_profile
