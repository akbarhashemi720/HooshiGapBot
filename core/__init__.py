# HooshiGap Core Backend
# Platform-independent business logic

from core.users import (
    get_user,
    user_exists,
    create_user,
    update_user,
    update_username,
    update_last_seen,
    get_online_status_text,
    ban_user,
    unban_user,
    is_banned,
    get_all_users,
    get_recent_users,
    get_user_stats,
    get_users_by_province,
    get_users_by_age,
    get_new_users,
    get_popular_users,
    get_users_without_chat,
    get_user_link,
    db_get
)

from core.coins import (
    get_coins,
    add_coins,
    deduct_coin,
    has_enough_coins,
    is_vip,
    set_vip,
    buy_vip_with_coins,
    get_vip_broadcast_status,
    use_vip_broadcast_chat,
    use_vip_broadcast_dm,
    referral_reward,
    VIP_PRICE_COINS,
    VIP_PRICE_TOMAN
)

from core.trust import (
    get_trust,
    update_trust,
    shadowban,
    remove_shadowban,
    is_shadowbanned,
    get_shadowban_level,
    report_penalty,
    block_penalty,
    complete_chat_reward,
    warn_user,
    get_warning_count,
    log_moderation
)

from core.moderation import (
    is_toxic,
    is_spam,
    check_rate_limit,
    check_queue_limit,
    analyze_message,
    get_safe_users
)

from core.chat import (
    active_chats,
    start_chat,
    end_chat,
    get_partner,
    is_in_chat,
    save_chat_history,
    get_chat_history,
    send_direct_message,
    get_direct_message,
    block_user,
    report_user,
    like_user,
    check_mutual_like,
    get_blocked_ids
)

from core.matching import (
    calculate_compatibility,
    get_quality_label,
    infer_personality,
    get_smart_matches,
    get_best_match,
    get_recommendations,
    save_skip,
    save_match_history,
    update_behavioral_profile,
    get_skipped_ids,
    get_liked_ids
)

from core.location import (
    distance_km,
    encode_location,
    decode_location,
    get_nearby_geohashes,
    get_distance_bucket,
    update_user_location,
    filter_nearby_users
)

__all__ = [
    # users
    "get_user", "user_exists", "create_user", "update_user",
    "update_username", "update_last_seen", "get_online_status_text",
    "ban_user", "unban_user", "is_banned",
    "get_all_users", "get_recent_users", "get_user_stats",
    "get_users_by_province", "get_users_by_age",
    "get_new_users", "get_popular_users", "get_users_without_chat",
    "get_user_link", "db_get",
    # coins & vip
    "get_coins", "add_coins", "deduct_coin", "has_enough_coins",
    "is_vip", "set_vip", "buy_vip_with_coins",
    "get_vip_broadcast_status", "use_vip_broadcast_chat",
    "use_vip_broadcast_dm", "referral_reward",
    "VIP_PRICE_COINS", "VIP_PRICE_TOMAN",
    # trust
    "get_trust", "update_trust", "shadowban", "remove_shadowban",
    "is_shadowbanned", "get_shadowban_level", "report_penalty",
    "block_penalty", "complete_chat_reward", "warn_user",
    "get_warning_count", "log_moderation",
    # moderation
    "is_toxic", "is_spam", "check_rate_limit", "check_queue_limit",
    "analyze_message", "get_safe_users",
    # chat
    "active_chats", "start_chat", "end_chat", "get_partner",
    "is_in_chat", "save_chat_history", "get_chat_history",
    "send_direct_message", "get_direct_message", "block_user",
    "report_user", "like_user", "check_mutual_like", "get_blocked_ids",
    # matching
    "calculate_compatibility", "get_quality_label", "infer_personality",
    "get_smart_matches", "get_best_match", "get_recommendations",
    "save_skip", "save_match_history", "update_behavioral_profile",
    "get_skipped_ids", "get_liked_ids",
    # location
    "distance_km", "encode_location", "decode_location",
    "get_nearby_geohashes", "get_distance_bucket",
    "update_user_location", "filter_nearby_users"
]
