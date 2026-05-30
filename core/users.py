# HooshiGap Core - User Management
# This module is platform-independent

import httpx
from datetime import datetime, timezone

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
        "has_voice": False,
        "like_count": 0,
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "is_online": True
    })

async def update_user(telegram_id, data):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", data)

async def update_username(telegram_id, username):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"username": username or ""})

async def update_last_seen(telegram_id):
    """آپدیت آخرین بازدید کاربر"""
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "is_online": True
    })

def get_online_status_text(user):
    """محاسبه وضعیت آنلاین از last_seen"""
    last_seen_str = user.get("last_seen")
    if not last_seen_str:
        return "⚫️ ناشناس"
    try:
        if last_seen_str.endswith("Z"):
            last_seen_str = last_seen_str[:-1] + "+00:00"
        last_seen = datetime.fromisoformat(last_seen_str)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - last_seen
        seconds = diff.total_seconds()
        if seconds < 300:
            return "🟢 آنلاین"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"🟡 {minutes} دقیقه پیش"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"🟠 {hours} ساعت پیش"
        else:
            days = int(seconds / 86400)
            return f"⚫️ {days} روز پیش"
    except:
        return "⚫️ نامشخص"

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

async def get_users_by_province(province, gender=None, limit=20):
    """دریافت کاربران هم استانی"""
    params = f"province=eq.{province}"
    if gender:
        params += f"&gender=eq.{gender}"
    params += f"&limit={limit}"
    return await db_get("users", params)

async def get_users_by_age(age, gender=None, limit=20):
    """دریافت کاربران هم سن"""
    params = f"age=eq.{age}"
    if gender:
        params += f"&gender=eq.{gender}"
    params += f"&order=last_seen.desc&limit={limit}"
    return await db_get("users", params)

async def get_new_users(gender=None, limit=20):
    """دریافت کاربران جدید"""
    params = "order=id.desc"
    if gender:
        params += f"&gender=eq.{gender}"
    params += f"&limit={limit}"
    return await db_get("users", params)

async def get_popular_users(gender=None, limit=20):
    """دریافت کاربران محبوب بر اساس لایک"""
    params = "order=like_count.desc"
    if gender:
        params += f"&gender=eq.{gender}"
    params += f"&limit={limit}"
    return await db_get("users", params)

async def get_users_without_chat(my_id, gender=None, limit=20):
    """دریافت کاربرانی که هنوز باهاشون چت نکردی"""
    params = f"telegram_id=neq.{my_id}"
    if gender:
        params += f"&gender=eq.{gender}"
    params += f"&order=last_seen.desc&limit={limit}"
    return await db_get("users", params)

def get_user_link(user):
    username = user.get("username")
    tid = user.get("telegram_id")
    if username:
        return f'<a href="https://t.me/{username}">پروفایل تلگرام</a>'
    else:
        return f'<a href="tg://user?id={tid}">پروفایل تلگرام</a>'

__all__ = [
    "get_user", "user_exists", "create_user", "update_user",
    "update_username", "update_last_seen", "get_online_status_text",
    "ban_user", "unban_user", "is_banned",
    "get_all_users", "get_recent_users", "get_user_stats",
    "get_users_by_province", "get_users_by_age",
    "get_new_users", "get_popular_users", "get_users_without_chat",
    "get_user_link", "db_get"
]
