# HooshiGap Core - Chat Management System
# This module is platform-independent

import httpx

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

async def db_get(table, params=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)
        return r.json()

async def db_post(table, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SUPABASE_URL}/rest/v1/{table}", json=data, headers=headers)
        return r.json()

async def db_patch(table, params, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}", json=data, headers=headers)

# Active chats in memory
active_chats = {}

def start_chat(user1_id, user2_id):
    active_chats[user1_id] = user2_id
    active_chats[user2_id] = user1_id

def end_chat(user_id):
    partner_id = active_chats.get(user_id)
    if user_id in active_chats:
        del active_chats[user_id]
    if partner_id and partner_id in active_chats:
        del active_chats[partner_id]
    return partner_id

def get_partner(user_id):
    return active_chats.get(user_id)

def is_in_chat(user_id):
    return user_id in active_chats

async def save_chat_history(user1, user2):
    existing = await db_get("chat_history", f"user1=eq.{user1}&user2=eq.{user2}")
    if not existing:
        existing2 = await db_get("chat_history", f"user1=eq.{user2}&user2=eq.{user1}")
        if not existing2:
            await db_post("chat_history", {"user1": user1, "user2": user2})

async def get_chat_history(user_id, gender_filter="همه"):
    history1 = await db_get("chat_history", f"user1=eq.{user_id}")
    history2 = await db_get("chat_history", f"user2=eq.{user_id}")
    partner_ids = [h["user2"] for h in history1] + [h["user1"] for h in history2]
    found = []
    for pid in partner_ids:
        users = await db_get("users", f"telegram_id=eq.{pid}")
        if users:
            u = users[0]
            if gender_filter == "همه" or u.get("gender") == gender_filter:
                found.append(u)
    return found

async def send_direct_message(from_id, to_id, message, is_paid):
    result = await db_post("direct_messages", {
        "from_user": from_id,
        "to_user": to_id,
        "message": message,
        "is_paid": is_paid
    })
    return result[0]["id"] if result and len(result) > 0 else None

async def get_direct_message(msg_id):
    msgs = await db_get("direct_messages", f"id=eq.{msg_id}")
    return msgs[0] if msgs else None

async def block_user(blocker_id, blocked_id):
    await db_post("blocks", {"blocker": blocker_id, "blocked": blocked_id})

async def report_user(reporter_id, reported_id):
    await db_post("reports", {"reporter": reporter_id, "reported": reported_id})

async def like_user(from_id, to_id):
    await db_post("likes", {"from_user": from_id, "to_user": to_id})

async def check_mutual_like(user1_id, user2_id):
    likes = await db_get("likes", f"from_user=eq.{user2_id}&to_user=eq.{user1_id}")
    return bool(likes)

async def get_blocked_ids(user_id):
    blocked = await db_get("blocks", f"blocker=eq.{user_id}&select=blocked")
    return [b["blocked"] for b in blocked] if blocked else []
