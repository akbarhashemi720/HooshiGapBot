# HooshiGap Core - AI Matching Engine v2
# Smart behavioral and compatibility matching

import httpx

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

async def db_get(table, params=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)
        result = r.json()
        if isinstance(result, list):
            return result
        return []

async def db_post(table, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.post(f"{SUPABASE_URL}/rest/v1/{table}", json=data, headers=headers)

async def db_patch(table, params, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}", json=data, headers=headers)

def infer_personality(user):
    interests = user.get("interests", "").lower()
    if any(w in interests for w in ["موسیقی", "هنر", "فیلم", "نقاشی"]):
        return "creative"
    elif any(w in interests for w in ["ورزش", "بازی", "کوهنوردی"]):
        return "active"
    elif any(w in interests for w in ["کتاب", "تکنولوژی", "علم"]):
        return "intellectual"
    elif any(w in interests for w in ["سفر", "غذا", "عکاسی"]):
        return "explorer"
    else:
        return "social"

def personality_compatibility(type1, type2):
    compatibility_matrix = {
        ("creative", "creative"): 90,
        ("creative", "intellectual"): 80,
        ("creative", "explorer"): 75,
        ("creative", "social"): 70,
        ("creative", "active"): 60,
        ("active", "active"): 85,
        ("active", "explorer"): 80,
        ("active", "social"): 75,
        ("active", "intellectual"): 60,
        ("intellectual", "intellectual"): 90,
        ("intellectual", "creative"): 80,
        ("intellectual", "social"): 65,
        ("explorer", "explorer"): 90,
        ("explorer", "social"): 80,
        ("explorer", "active"): 80,
        ("social", "social"): 85,
    }
    key = (type1, type2)
    reverse_key = (type2, type1)
    return compatibility_matrix.get(key, compatibility_matrix.get(reverse_key, 65))

def calculate_interest_score(user1, user2):
    interests1 = set(i.strip() for i in user1.get("interests", "").split(","))
    interests2 = set(i.strip() for i in user2.get("interests", "").split(","))
    if not interests1 or not interests2:
        return 0
    common = interests1 & interests2
    total = interests1 | interests2
    if not total:
        return 0
    return int(len(common) / len(total) * 100)

def calculate_age_score(user1, user2):
    age_diff = abs(user1.get("age", 25) - user2.get("age", 25))
    if age_diff == 0:
        return 100
    elif age_diff <= 2:
        return 90
    elif age_diff <= 5:
        return 75
    elif age_diff <= 10:
        return 50
    elif age_diff <= 15:
        return 30
    else:
        return 10

def calculate_location_score(user1, user2):
    if user1.get("city") == user2.get("city"):
        return 100
    elif user1.get("province") == user2.get("province"):
        return 70
    else:
        return 30

def calculate_trust_score(user2):
    trust = user2.get("trust_score", 50)
    if trust >= 80:
        return 100
    elif trust >= 60:
        return 80
    elif trust >= 40:
        return 60
    elif trust >= 20:
        return 40
    else:
        return 20

def calculate_activity_score(user2):
    score = 50
    if user2.get("has_voice"):
        score += 20
    if user2.get("photo_id"):
        score += 10
    if user2.get("total_chats", 0) > 5:
        score += 10
    if user2.get("successful_chats", 0) > 3:
        score += 10
    return min(score, 100)

def calculate_compatibility(user1, user2):
    interest_score = calculate_interest_score(user1, user2)
    age_score = calculate_age_score(user1, user2)
    location_score = calculate_location_score(user1, user2)
    trust_score = calculate_trust_score(user2)
    activity_score = calculate_activity_score(user2)
    type1 = infer_personality(user1)
    type2 = infer_personality(user2)
    personality_score = personality_compatibility(type1, type2)
    final_score = (
        interest_score * 0.30 +
        age_score * 0.20 +
        location_score * 0.15 +
        trust_score * 0.15 +
        activity_score * 0.10 +
        personality_score * 0.10
    )
    return round(final_score)

def get_quality_label(score):
    if score >= 85:
        return "🔥 مچ فوق‌العاده"
    elif score >= 70:
        return "✨ مچ عالی"
    elif score >= 55:
        return "👍 مچ خوب"
    elif score >= 40:
        return "🤝 مچ متوسط"
    else:
        return "👋 آشنایی جدید"

async def get_skipped_ids(user_id):
    try:
        skipped = await db_get("skipped_users", f"user_id=eq.{user_id}&select=skipped_id")
        if not skipped or not isinstance(skipped, list):
            return []
        return [s["skipped_id"] for s in skipped if isinstance(s, dict) and "skipped_id" in s]
    except:
        return []

async def get_liked_ids(user_id):
    try:
        liked = await db_get("likes", f"from_user=eq.{user_id}&select=to_user")
        if not liked or not isinstance(liked, list):
            return []
        return [l["to_user"] for l in liked if isinstance(l, dict) and "to_user" in l]
    except:
        return []

async def get_smart_matches(my_id, blocked_ids, limit=5):
    try:
        my_profile = await db_get("users", f"telegram_id=eq.{my_id}")
        if not my_profile or not isinstance(my_profile, list):
            return []
        me = my_profile[0]
        skipped_ids = await get_skipped_ids(my_id)
        liked_ids = await get_liked_ids(my_id)
        excluded_ids = set(blocked_ids + skipped_ids + liked_ids + [my_id])
        candidates = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&is_banned=eq.false&limit=100")
        if not candidates:
            return []
        candidates = [u for u in candidates if isinstance(u, dict) and u.get("telegram_id") not in excluded_ids]
        if not candidates:
            candidates = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit=50")
            candidates = [u for u in candidates if isinstance(u, dict) and u.get("telegram_id") not in set(blocked_ids + [my_id])]
        scored = []
        for u in candidates:
            score = calculate_compatibility(me, u)
            scored.append((score, u))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [u for _, u in scored[:limit]]
    except:
        return []

async def get_best_match(my_id, blocked_ids):
    matches = await get_smart_matches(my_id, blocked_ids, limit=1)
    return matches[0] if matches else None

async def get_recommendations(my_id, blocked_ids, limit=3):
    return await get_smart_matches(my_id, blocked_ids, limit=limit)

async def save_skip(user_id, skipped_id):
    try:
        if skipped_id and skipped_id != 0:
            await db_post("skipped_users", {"user_id": user_id, "skipped_id": skipped_id})
    except:
        pass

async def save_match_history(user1, user2):
    try:
        await db_post("match_history", {"user1": user1, "user2": user2})
    except:
        pass

async def update_behavioral_profile(telegram_id, chat_duration, completed=False):
    try:
        users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=total_chats,successful_chats,avg_chat_duration")
        if not users or not isinstance(users, list):
            return
        u = users[0]
        total = u.get("total_chats", 0) + 1
        successful = u.get("successful_chats", 0) + (1 if completed else 0)
        avg = u.get("avg_chat_duration", 0)
        new_avg = int((avg * (total - 1) + chat_duration) / total)
        skip_rate = round(1 - (successful / total), 2) if total > 0 else 0
        personality = infer_personality(u)
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {
            "total_chats": total,
            "successful_chats": successful,
            "avg_chat_duration": new_avg,
            "skip_rate": skip_rate,
            "personality_type": personality
        })
    except:
        pass

__all__ = [
    "calculate_compatibility",
    "get_quality_label",
    "infer_personality",
    "personality_compatibility",
    "get_smart_matches",
    "get_best_match",
    "get_recommendations",
    "save_skip",
    "save_match_history",
    "update_behavioral_profile",
    "get_skipped_ids",
    "get_liked_ids"
]
