# HooshiGap Core Backend
# Platform-independent business logic

from core.users import (
    get_user,
    user_exists,
    create_user,
    update_user,
    update_username,
    ban_user,
    unban_user,
    is_banned,
    get_all_users,
    get_recent_users,
    get_user_stats,
    get_user_link
)

from core.coins import (
    get_coins,
    add_coins,
    deduct_coin,
    has_enough_coins,
    is_vip,
    set_vip,
    referral_reward
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

__all__ = [
    # users
    "get_user", "user_exists", "create_user", "update_user",
    "update_username", "ban_user", "unban_user", "is_banned",
    "get_all_users", "get_recent_users", "get_user_stats", "get_user_link",
    # coins
    "get_coins", "add_coins", "deduct_coin", "has_enough_coins",
    "is_vip", "set_vip", "referral_reward",
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
    "report_user", "like_user", "check_mutual_like", "get_blocked_ids"
]
