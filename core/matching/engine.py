# HooshiGap Core - Matching Engine
# Platform-independent matching and recommendation system

import httpx
import math

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

async def db_get(table, params=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)
        return r.json()

async def db_post(table, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.post(f"{SUPABASE_URL}/rest/v1/{table}", json=data, headers=headers)

async def db_patch(table, params, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}", json=data, headers=headers)

def calculate_compatibility(user1, user2):
    score = 0
    # علایق مشترک
    interests1 = set(user1.get("interests", "").split(","))
    interests2 = set(user2.get("interests", "").split(","))
    common = interests1 & interests2
    score += len(common) * 20

    # نزدیکی سنی
    age_diff = abs(user1.get("age", 0) - user2.get("age", 0))
    if age_diff <= 2:
        score += 30
    elif age_diff <= 5:
        score += 20
    elif age_diff <= 10:
        score += 10

    # همشهری
    if user1.get("city") == user2.get("city"):
        score += 25
    elif user1.get("province") == user2.get("province"):
        score += 15

    # trust score
    trust = user2.get("trust_score", 50)
    if trust >= 80:
        score += 20
    elif trust >= 50:
        score += 10

    return min(score, 100)

def get_quality_label(score):
    if score >= 80:
        return "🔥 مچ عالی"
    elif score >= 60:
        return "✨ مچ خوب"
    elif score >= 40:
        return "👍 مچ متوسط"
    else:
        return "🤝 آشنایی جدید"

def infer_personality(user):
    interests = user.get("interests", "").lower()
    if any(w in interests for w in ["موسیقی", "هنر", "فیلم"]):
        return "creative"
    elif any(w in interests for w in ["ورزش", "بازی"]):
        return "active"
    elif any(w in interests for w in ["کتاب", "تکنولوژی"]):
        return "intellectual"
    else:
        return "social"

async def get_smart_matches(my_id, blocked_ids, limit=5):
    my_profile = await db_get("users", f"telegram_id=eq.{my_id}")
    if not my_profile:
        return []
    me = my_profile[0]

    # کاربران shadowban نشده
    candidates = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit=50")
    if not candidates:
        return []

    # فیلتر بلاک شده‌ها
    candidates = [u for u in candidates if u["telegram_id"] not in blocked_ids]

    # محاسبه امتیاز سازگاری
    scored = []
    for u in candidates:
        score = calculate_compatibility(me, u)
        scored.append((score, u))

    # مرتب‌سازی بر اساس امتیاز
    scored.sort(key=lambda x: x[0], reverse=True)
    return [u for _, u in scored[:limit]]

async def get_best_match(my_id, blocked_ids):
    matches = await get_smart_matches(my_id, blocked_ids, limit=1)
    return matches[0] if matches else None

async def get_recommendations(my_id, blocked_ids, limit=3):
    return await get_smart_matches(my_id, blocked_ids, limit=limit)

async def save_skip(user_id, skipped_id):
    await db_post("skipped_users", {"user_id": user_id, "skipped_id": skipped_id})

async def save_match_history(user1, user2):
    await db_post("match_history", {"user1": user1, "user2": user2})

async def update_behavioral_profile(telegram_id, chat_duration, completed=False):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=total_chats,successful_chats,avg_chat_duration")
    if not users:
        return
    u = users[0]
    total = u.get("total_chats", 0) + 1
    successful = u.get("successful_chats", 0) + (1 if completed else 0)
    avg = u.get("avg_chat_duration", 0)
    new_avg = int((avg * (total - 1) + chat_duration) / total)
    skip_rate = round(1 - (successful / total), 2) if total > 0 else 0
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "total_chats": total,
        "successful_chats": successful,
        "avg_chat_duration": new_avg,
        "skip_rate": skip_rate
    })

__all__ = [
    "calculate_compatibility",
    "get_quality_label",
    "infer_personality",
    "get_smart_matches",
    "get_best_match",
    "get_recommendations",
    "save_skip",
    "save_match_history",
    "update_behavioral_profile"
]
