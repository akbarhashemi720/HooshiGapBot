# HooshiGap Core - Coins & VIP Management
# This module is platform-independent

import httpx

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

VIP_PRICE_COINS = 6800
VIP_PRICE_TOMAN = 1500000

async def db_get(table, params=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)
        result = r.json()
        if isinstance(result, list):
            return result
        return []

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
    new_amount = coins + amount
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"coins": new_amount})
    return new_amount

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
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "is_vip": status,
        "vip_broadcast_chat_used": 0,
        "vip_broadcast_dm_used": 0
    })

async def buy_vip_with_coins(telegram_id):
    """خرید VIP با سکه"""
    coins = await get_coins(telegram_id)
    if coins < VIP_PRICE_COINS:
        return False, f"❌ سکه کافی نداری!\nنیاز: {VIP_PRICE_COINS} سکه\nداری: {coins} سکه"
    
    new_coins = coins - VIP_PRICE_COINS
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "coins": new_coins,
        "is_vip": True,
        "vip_broadcast_chat_used": 0,
        "vip_broadcast_dm_used": 0
    })
    return True, f"✅ VIP فعال شد!\n🪙 سکه باقی: {new_coins}"

async def get_vip_broadcast_status(telegram_id):
    """وضعیت broadcast VIP"""
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=vip_broadcast_chat_used,vip_broadcast_dm_used")
    if users:
        return {
            "chat_used": users[0].get("vip_broadcast_chat_used", 0),
            "dm_used": users[0].get("vip_broadcast_dm_used", 0),
            "chat_remaining": max(0, 10 - users[0].get("vip_broadcast_chat_used", 0)),
            "dm_remaining": max(0, 10 - users[0].get("vip_broadcast_dm_used", 0))
        }
    return {"chat_used": 0, "dm_used": 0, "chat_remaining": 10, "dm_remaining": 10}

async def use_vip_broadcast_chat(telegram_id):
    """استفاده از یه درخواست چت VIP"""
    status = await get_vip_broadcast_status(telegram_id)
    if status["chat_remaining"] <= 0:
        return False, "❌ ظرفیت درخواست چت VIP تمام شده!"
    used = status["chat_used"] + 1
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"vip_broadcast_chat_used": used})
    return True, f"✅ درخواست چت ارسال شد! ({used}/10)"

async def use_vip_broadcast_dm(telegram_id):
    """استفاده از یه پیام دایرکت VIP"""
    status = await get_vip_broadcast_status(telegram_id)
    if status["dm_remaining"] <= 0:
        return False, "❌ ظرفیت پیام دایرکت VIP تمام شده!"
    used = status["dm_used"] + 1
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"vip_broadcast_dm_used": used})
    return True, f"✅ پیام دایرکت ارسال شد! ({used}/10)"

async def referral_reward(referrer_id, amount=5):
    await add_coins(referrer_id, amount)

__all__ = [
    "get_coins", "add_coins", "deduct_coin", "has_enough_coins",
    "is_vip", "set_vip", "buy_vip_with_coins",
    "get_vip_broadcast_status", "use_vip_broadcast_chat",
    "use_vip_broadcast_dm", "referral_reward",
    "VIP_PRICE_COINS", "VIP_PRICE_TOMAN"
]
