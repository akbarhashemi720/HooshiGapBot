# HooshiGap Core - Content Moderation System
# This module is platform-independent

import time

user_message_times = {}
user_queue_times = {}

TOXIC_WORDS = [
    "فاحشه", "جنده", "کص", "کیر", "کون", "گاییدن", "ننت", "مادرجنده",
    "بیا سکس", "عکس لخت", "کانال بده", "آی دی بده", "شماره بده",
    "porn", "sex", "naked", "nudes"
]

SPAM_PATTERNS = [
    "کانال", "عضو شو", "لینک", "تبلیغ", "فالو", "آیدی بده", "شماره بده"
]

def is_toxic(text):
    if not text:
        return False, []
    text_lower = text.lower()
    found = []
    for word in TOXIC_WORDS:
        if word in text_lower:
            found.append(word)
    return len(found) > 0, found

def is_spam(text):
    if not text:
        return False
    text_lower = text.lower()
    for pattern in SPAM_PATTERNS:
        if pattern in text_lower:
            return True
    if len(text) > 10:
        if text.count(text[:5]) > 3:
            return True
    return False

def check_rate_limit(telegram_id, limit=5, window=10):
    now = time.time()
    if telegram_id not in user_message_times:
        user_message_times[telegram_id] = []
    times = user_message_times[telegram_id]
    times = [t for t in times if now - t < window]
    user_message_times[telegram_id] = times
    if len(times) >= limit:
        return False
    times.append(now)
    return True

def check_queue_limit(telegram_id, limit=10, window=60):
    now = time.time()
    if telegram_id not in user_queue_times:
        user_queue_times[telegram_id] = []
    times = user_queue_times[telegram_id]
    times = [t for t in times if now - t < window]
    user_queue_times[telegram_id] = times
    if len(times) >= limit:
        return False
    times.append(now)
    return True

async def analyze_message(telegram_id, text, trust_module=None):
    toxic, words = is_toxic(text)
    spam = is_spam(text)

    if toxic:
        if trust_module:
            await trust_module.update_trust(telegram_id, -15)
            await trust_module.warn_user(telegram_id, f"پیام نامناسب: {', '.join(words)}")
            trust = await trust_module.get_trust(telegram_id)
            if trust.get("trust_score", 50) < 20:
                await trust_module.shadowban(telegram_id, "پیام‌های مکرر نامناسب", 2)
        return "toxic"

    if spam:
        if trust_module:
            await trust_module.update_trust(telegram_id, -5)
        return "spam"

    if trust_module:
        await trust_module.update_trust(telegram_id, +1)
    return "clean"

async def get_safe_users(my_id, blocked_ids, trust_level="normal", limit=5):
    from core.users import db_get
    if trust_level == "high":
        users = await db_get("users", f"telegram_id=neq.{my_id}&trust_level=eq.high&shadowban_level=eq.0&limit={limit}")
        if not users:
            users = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit={limit}")
    elif trust_level == "danger":
        users = await db_get("users", f"telegram_id=neq.{my_id}&limit={limit}")
    else:
        users = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit={limit}")
    if users:
        users = [u for u in users if u["telegram_id"] not in blocked_ids]
    return users or []
