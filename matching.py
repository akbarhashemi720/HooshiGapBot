import httpx
import math
from datetime import datetime

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

# ============ COMPATIBILITY SCORE ============

def calculate_interest_overlap(interests1, interests2):
    if not interests1 or not interests2:
        return 0
    set1 = set(interests1.lower().split())
    set2 = set(interests2.lower().split())
    if not set1 or not set2:
        return 0
    overlap = len(set1 & set2)
    total = len(set1 | set2)
    return overlap / total if total > 0 else 0

def calculate_age_compatibility(age1, age2):
    diff = abs(age1 - age2)
    if diff <= 2:
        return 1.0
    elif diff <= 5:
        return 0.8
    elif diff <= 10:
        return 0.6
    elif diff <= 15:
        return 0.4
    else:
        return 0.2

def calculate_trust_compatibility(trust1, trust2):
    diff = abs(trust1 - trust2)
    if diff <= 10:
        return 1.0
    elif diff <= 20:
        return 0.8
    elif diff <= 30:
        return 0.6
    else:
        return 0.4

def calculate_location_score(city1, city2, province1, province2):
    if city1 and city2 and city1.lower() == city2.lower():
        return 1.0
    if province1 and province2 and province1.lower() == province2.lower():
        return 0.6
    return 0.2

def calculate_engagement_compatibility(eng1, eng2):
    diff = abs(eng1 - eng2)
    if diff <= 10:
        return 1.0
    elif diff <= 20:
        return 0.8
    elif diff <= 30:
        return 0.6
    else:
        return 0.4

def calculate_active_hour_compatibility(hour1, hour2):
    diff = abs(hour1 - hour2)
    if diff > 12:
        diff = 24 - diff
    if diff <= 2:
        return 1.0
    elif diff <= 4:
        return 0.8
    elif diff <= 6:
        return 0.6
    else:
        return 0.3

async def calculate_compatibility(user1, user2):
    scores = {}
    scores["interest"] = calculate_interest_overlap(
        user1.get("interests", ""),
        user2.get("interests", "")
    ) * 25

    scores["age"] = calculate_age_compatibility(
        user1.get("age", 25),
        user2.get("age", 25)
    ) * 20

    scores["trust"] = calculate_trust_compatibility(
        user1.get("trust_score", 50),
        user2.get("trust_score", 50)
    ) * 20

    scores["location"] = calculate_location_score(
        user1.get("city", ""),
        user2.get("city", ""),
        user1.get("province", ""),
        user2.get("province", "")
    ) * 15

    scores["engagement"] = calculate_engagement_compatibility(
        user1.get("engagement_score", 50),
        user2.get("engagement_score", 50)
    ) * 10

    scores["active_hour"] = calculate_active_hour_compatibility(
        user1.get("active_hour", 12),
        user2.get("active_hour", 12)
    ) * 10

    total = sum(scores.values())

    if total >= 70:
        quality = "excellent"
    elif total >= 50:
        quality = "good"
    elif total >= 30:
        quality = "average"
    else:
        quality = "low"

    confidence = min(100, total + 10)

    return {
        "compatibility_score": round(total, 2),
        "confidence_score": round(confidence, 2),
        "match_quality_level": quality,
        "breakdown": scores
    }

# ============ BEHAVIORAL PROFILE ============

async def update_behavioral_profile(telegram_id, chat_duration_seconds, completed=True):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=avg_chat_duration,total_chats,successful_chats,engagement_score")
    if not users:
        return
    user = users[0]
    total = user.get("total_chats", 0) + 1
    avg_duration = user.get("avg_chat_duration", 0)
    new_avg = int((avg_duration * (total - 1) + chat_duration_seconds) / total)
    successful = user.get("successful_chats", 0)
    if completed:
        successful += 1
    engagement = min(100, (successful / total) * 100) if total > 0 else 50
    now = datetime.now()
    active_hour = now.hour
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "avg_chat_duration": new_avg,
        "total_chats": total,
        "successful_chats": successful,
        "engagement_score": round(engagement, 2),
        "active_hour": active_hour
    })

async def infer_personality(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=avg_chat_duration,engagement_score,skip_rate,total_chats")
    if not users:
        return "unknown"
    user = users[0]
    avg_dur = user.get("avg_chat_duration", 0)
    eng = user.get("engagement_score", 50)
    skip = user.get("skip_rate", 0)
    if avg_dur > 300 and eng > 70:
        personality = "extrovert"
    elif avg_dur < 60 or skip > 0.7:
        personality = "introvert"
    elif eng > 50:
        personality = "balanced"
    else:
        personality = "shy"
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"personality_type": personality})
    return personality

# ============ SMART MATCHING ============

async def get_smart_matches(my_id, blocked_ids, limit=10):
    my_profile = await db_get("users", f"telegram_id=eq.{my_id}")
    if not my_profile:
        return []
    me = my_profile[0]
    skipped = await db_get("skipped_users", f"from_user=eq.{my_id}&select=to_user")
    skipped_ids = [s["to_user"] for s in skipped] if skipped else []
    exclude_ids = blocked_ids + skipped_ids + [my_id]
    my_trust = me.get("trust_score", 50)
    if my_trust >= 80:
        candidates = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&trust_score=gte.60&limit=20")
    elif my_trust >= 50:
        candidates = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit=20")
    else:
        candidates = await db_get("users", f"telegram_id=neq.{my_id}&limit=20")
    if not candidates:
        return []
    candidates = [c for c in candidates if c["telegram_id"] not in exclude_ids]
    scored = []
    for candidate in candidates:
        result = await calculate_compatibility(me, candidate)
        candidate["_compatibility"] = result["compatibility_score"]
        candidate["_quality"] = result["match_quality_level"]
        scored.append(candidate)
    scored.sort(key=lambda x: x["_compatibility"], reverse=True)
    return scored[:limit]

async def save_match_history(user1_id, user2_id, compatibility_score, quality_score, outcome):
    await db_post("match_history", {
        "user1": user1_id,
        "user2": user2_id,
        "compatibility_score": compatibility_score,
        "quality_score": quality_score,
        "outcome": outcome
    })

async def save_skip(from_user, to_user):
    await db_post("skipped_users", {
        "from_user": from_user,
        "to_user": to_user
    })

# ============ RECOMMENDATIONS ============

async def get_best_match(my_id, blocked_ids):
    matches = await get_smart_matches(my_id, blocked_ids, limit=1)
    if matches:
        return matches[0]
    return None

async def get_recommendations(my_id, blocked_ids, limit=5):
    matches = await get_smart_matches(my_id, blocked_ids, limit=limit)
    return matches

async def get_quality_label(score):
    if score >= 70:
        return "\u0633\u0627\u0632\u06af\u0627\u0631\u06cc \u0639\u0627\u0644\u06cc"
    elif score >= 50:
        return "\u0633\u0627\u0632\u06af\u0627\u0631\u06cc \u062e\u0648\u0628"
    elif score >= 30:
        return "\u0633\u0627\u0632\u06af\u0627\u0631\u06cc \u0645\u062a\u0648\u0633\u0637"
    else:
        return "\u0633\u0627\u0632\u06af\u0627\u0631\u06cc \u067e\u0627\u06cc\u06cc\u0646"