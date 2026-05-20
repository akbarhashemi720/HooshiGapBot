# HooshiGap Matching Engine
# This module contains all matching logic independent of Telegram

from matching import (
    calculate_compatibility,
    get_smart_matches,
    get_best_match,
    get_recommendations,
    update_behavioral_profile,
    save_skip,
    save_match_history,
    get_quality_label,
    infer_personality
)

__all__ = [
    "calculate_compatibility",
    "get_smart_matches", 
    "get_best_match",
    "get_recommendations",
    "update_behavioral_profile",
    "save_skip",
    "save_match_history",
    "get_quality_label",
    "infer_personality"
]
