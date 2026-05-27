# HooshiGap Core - User Management
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

async def get_user(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}")
    return users[0] if users else None

async def user_exists(telegram_id):
    user = await get_user(telegram_id)
    return user is not None

async def create_user(telegram_id, username, gender, age, province, city, interests, photo_id):
    await db_post("users", {
        "telegram_id": telegram_id,
        "username": username or "",
        "gender": gender,
        "age": age,
        "province": province,
        "city": city,
        "interests": interests,
        "photo_id": photo_id,
        "coins": 10,
        "is_vip": False,
        "is_banned": False,
        "trust_score": 50,
        "trust_level": "normal",
        "shadowban_level": 0,
        "has_voice": False
    })

async def update_user(telegram_id, data):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", data)

async def update_username(telegram_id, username):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"username": username or ""})

async def ban_user(telegram_id):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "is_banned": True,
        "shadowban_level": 3
    })

async def unban_user(telegram_id):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "is_banned": False,
        "shadowban_level": 0
    })

async def is_banned(telegram_id):
    user = await get_user(telegram_id)
    if user:
        return user.get("is_banned", False)
    return False

async def get_all_users():
    return await db_get("users", "select=telegram_id")

async def get_recent_users(limit=10):
    return await db_get("users", f"limit={limit}&order=id.desc")

async def get_user_stats():
    total = len(await db_get("users", ""))
    vip_count = len(await db_get("users", "is_vip=eq.true"))
    voice_count = len(await db_get("users", "has_voice=eq.true"))
    return {
        "total": total,
        "vip": vip_count,
        "voice": voice_count
    }

def get_user_link(user):
    username = user.get("username")
    tid = user.get("telegram_id")
    if username:
        return f'<a href="https://t.me/{username}">پروفایل تلگرام</a>'
    else:
        return f'<a href="tg://user?id={tid}">پروفایل تلگرام</a>'
