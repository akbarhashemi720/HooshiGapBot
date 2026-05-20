import httpx
import pygeohash as geohash
import time
import math

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

user_message_times = {}
user_queue_times = {}

TOXIC_WORDS = [
    "\u0641\u0627\u062d\u0634\u0647", "\u062c\u0646\u062f\u0647", "\u06a9\u0635", "\u06a9\u06cc\u0631", "\u06a9\u0648\u0646", "\u06af\u0627\u06cc\u06cc\u062f\u0646", "\u0646\u0646\u062a", "\u0645\u0627\u062f\u0631\u062c\u0646\u062f\u0647",
    "\u0628\u06cc\u0627 \u0633\u06a9\u0633", "\u0639\u06a9\u0633 \u0644\u062e\u062a", "\u06a9\u0627\u0646\u0627\u0644 \u0628\u062f\u0647", "\u0622\u06cc \u062f\u06cc \u0628\u062f\u0647", "\u0634\u0645\u0627\u0631\u0647 \u0628\u062f\u0647",
    "porn", "sex", "naked", "nudes"
]

SPAM_PATTERNS = [
    "\u06a9\u0627\u0646\u0627\u0644", "\u0639\u0636\u0648 \u0634\u0648", "\u0644\u06cc\u0646\u06a9", "\u062a\u0628\u0644\u06cc\u063a", "\u0641\u0627\u0644\u0648", "\u0622\u06cc\u062f\u06cc \u0628\u062f\u0647", "\u0634\u0645\u0627\u0631\u0647 \u0628\u062f\u0647"
]

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

async def get_trust(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=trust_score,trust_level,shadowban_level,risk_flags")
    if users:
        return users[0]
    return {"trust_score": 50, "trust_level": "normal", "shadowban_level": 0, "risk_flags": ""}

async def update_trust(telegram_id, delta):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=trust_score")
    if not users:
        return
    current = users[0].get("trust_score", 50)
    new_score = max(0, min(100, current + delta))
    if new_score >= 80:
        level = "high"
    elif new_score >= 50:
        level = "normal"
    elif new_score >= 25:
        level = "low"
    else:
        level = "danger"
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "trust_score": new_score,
        "trust_level": level
    })
    return new_score

async def complete_chat_reward(telegram_id):
    await update_trust(telegram_id, +3)
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=chat_complete_count")
    if users:
        count = users[0].get("chat_complete_count", 0)
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {"chat_complete_count": count + 1})

async def report_penalty(telegram_id):
    await update_trust(telegram_id, -10)
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=report_count")
    if users:
        count = users[0].get("report_count", 0)
        new_count = count + 1
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {"report_count": new_count})
        if new_count >= 3:
            await shadowban(telegram_id, "\u06af\u0632\u0627\u0631\u0634 \u0645\u06a9\u0631\u0631 \u062a\u0648\u0633\u0637 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646", 1)
        elif new_count >= 5:
            await shadowban(telegram_id, "\u06af\u0632\u0627\u0631\u0634 \u0628\u06cc\u0634 \u0627\u0632 \u062d\u062f", 2)

async def block_penalty(telegram_id):
    await update_trust(telegram_id, -5)
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=block_count")
    if users:
        count = users[0].get("block_count", 0)
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {"block_count": count + 1})

async def shadowban(telegram_id, reason, level=1):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "shadowban_level": level,
        "shadowban_reason": reason
    })
    await log_moderation(telegram_id, f"shadowban_level_{level}", reason)

async def remove_shadowban(telegram_id):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "shadowban_level": 0,
        "shadowban_reason": ""
    })

async def is_shadowbanned(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=shadowban_level")
    if users:
        return users[0].get("shadowban_level", 0) > 0
    return False

async def get_shadowban_level(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=shadowban_level")
    if users:
        return users[0].get("shadowban_level", 0)
    return 0

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

async def analyze_message(telegram_id, text):
    toxic, words = is_toxic(text)
    spam = is_spam(text)
    if toxic:
        await update_trust(telegram_id, -15)
        await warn_user(telegram_id, f"\u067e\u06cc\u0627\u0645 \u0646\u0627\u0645\u0646\u0627\u0633\u0628: {', '.join(words)}")
        trust = await get_trust(telegram_id)
        if trust.get("trust_score", 50) < 20:
            await shadowban(telegram_id, "\u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0645\u06a9\u0631\u0631 \u0646\u0627\u0645\u0646\u0627\u0633\u0628", 2)
        return "toxic"
    if spam:
        await update_trust(telegram_id, -5)
        return "spam"
    await update_trust(telegram_id, +1)
    return "clean"

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

async def warn_user(telegram_id, reason):
    await db_post("warnings", {
        "user_id": telegram_id,
        "reason": reason
    })

async def get_warning_count(telegram_id):
    warnings = await db_get("warnings", f"user_id=eq.{telegram_id}")
    return len(warnings) if warnings else 0

async def log_moderation(user_id, action, reason):
    await db_post("moderation_logs", {
        "user_id": user_id,
        "action": action,
        "reason": reason
    })

async def get_safe_users(my_id, blocked_ids, limit=5):
    trust = await get_trust(my_id)
    my_level = trust.get("trust_level", "normal")
    if my_level == "high":
        users = await db_get("users", f"telegram_id=neq.{my_id}&trust_level=eq.high&shadowban_level=eq.0&limit={limit}")
        if not users:
            users = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit={limit}")
    elif my_level == "danger":
        users = await db_get("users", f"telegram_id=neq.{my_id}&limit={limit}")
    else:
        users = await db_get("users", f"telegram_id=neq.{my_id}&shadowban_level=eq.0&limit={limit}")
    if users:
        users = [u for u in users if u["telegram_id"] not in blocked_ids]
    return users or []

def encode_location(lat, lon, precision=4):
    try:
        return geohash.encode(lat, lon, precision)
    except:
        return ""

def decode_location(geohash_str):
    try:
        return geohash.decode(geohash_str)
    except:
        return None, None

def get_nearby_geohashes(lat, lon, precision=4):
    try:
        center = geohash.encode(lat, lon, precision)
        neighbors = geohash.neighbors(center)
        return [center] + neighbors
    except:
        return []

def get_distance_bucket(dist_km):
    if dist_km < 1:
        return "\u06a9\u0645\u062a\u0631 \u0627\u0632 1 \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631"
    elif dist_km < 5:
        return "\u062f\u0631 \u0645\u062d\u062f\u0648\u062f\u0647 5 \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631"
    elif dist_km < 10:
        return "\u062f\u0631 \u0645\u062d\u062f\u0648\u062f\u0647 10 \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631"
    elif dist_km < 30:
        return "\u062f\u0631 \u0645\u062d\u062f\u0648\u062f\u0647 30 \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631"
    else:
        return "\u062f\u0631 \u0645\u062d\u062f\u0648\u062f\u0647 60 \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631"

async def update_user_location(telegram_id, lat, lon):
    gh = encode_location(lat, lon, precision=4)
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "latitude": round(lat, 2),
        "longitude": round(lon, 2),
        "geohash": gh if gh else ""
    })
