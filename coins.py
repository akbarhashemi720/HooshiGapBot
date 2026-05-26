# HooshiGap Core - Coins & VIP Management
# This module is platform-independent

import httpx

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

async def db_get(table, params=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)
        return r.json()

async def db_patch(table, params, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}", json=data, headers=headers)

async def get_coins(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=coins")
    if users:
        return users[0].get("coins", 0)
    return 0

async def add_coins(telegram_id, amount):
    coins = await get_coins(telegram_id)
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"coins": coins + amount})
    return coins + amount

async def deduct_coin(telegram_id):
    coins = await get_coins(telegram_id)
    if coins <= 0:
        return False
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"coins": coins - 1})
    return True

async def has_enough_coins(telegram_id, amount=1):
    coins = await get_coins(telegram_id)
    return coins >= amount

async def is_vip(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=is_vip")
    if users:
        return users[0].get("is_vip", False)
    return False

async def set_vip(telegram_id, status=True):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"is_vip": status})

async def referral_reward(referrer_id, amount=5):
    await add_coins(referrer_id, amount)
