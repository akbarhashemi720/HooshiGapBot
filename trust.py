# HooshiGap Core - Trust & Moderation System
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

async def report_penalty(telegram_id):
    await update_trust(telegram_id, -10)
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=report_count")
    if users:
        count = users[0].get("report_count", 0)
        new_count = count + 1
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {"report_count": new_count})
        if new_count >= 5:
            await shadowban(telegram_id, "گزارش بیش از حد", 2)
        elif new_count >= 3:
            await shadowban(telegram_id, "گزارش مکرر توسط کاربران", 1)

async def block_penalty(telegram_id):
    await update_trust(telegram_id, -5)
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=block_count")
    if users:
        count = users[0].get("block_count", 0)
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {"block_count": count + 1})

async def complete_chat_reward(telegram_id):
    await update_trust(telegram_id, +3)
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=chat_complete_count")
    if users:
        count = users[0].get("chat_complete_count", 0)
        await db_patch("users", f"telegram_id=eq.{telegram_id}", {"chat_complete_count": count + 1})

async def warn_user(telegram_id, reason):
    await db_post("warnings", {"user_id": telegram_id, "reason": reason})

async def get_warning_count(telegram_id):
    warnings = await db_get("warnings", f"user_id=eq.{telegram_id}")
    return len(warnings) if warnings else 0

async def log_moderation(user_id, action, reason):
    await db_post("moderation_logs", {"user_id": user_id, "action": action, "reason": reason})
