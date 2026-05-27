# HooshiGap API Layer
# FastAPI-based central API for all platforms

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

from core import (
    get_user, user_exists, create_user, update_user,
    update_username, ban_user, unban_user, is_banned,
    get_all_users, get_recent_users, get_user_stats, get_user_link,
    get_coins, add_coins, deduct_coin, has_enough_coins,
    is_vip, set_vip, referral_reward,
    get_trust, update_trust, shadowban, remove_shadowban,
    is_shadowbanned, report_penalty, block_penalty,
    complete_chat_reward, warn_user, log_moderation,
    check_rate_limit, check_queue_limit, analyze_message,
    save_chat_history, get_chat_history,
    send_direct_message, get_direct_message,
    block_user, report_user, like_user, check_mutual_like,
    get_blocked_ids
)

app = FastAPI(title="HooshiGap API", version="1.0.0")

# ==================== Models ====================

class CreateUserModel(BaseModel):
    telegram_id: int
    username: Optional[str] = ""
    gender: str
    age: int
    province: str
    city: str
    interests: str
    photo_id: str

class UpdateUserModel(BaseModel):
    field: str
    value: str

class CoinsModel(BaseModel):
    telegram_id: int
    amount: int

class MessageModel(BaseModel):
    from_id: int
    to_id: int
    message: str
    is_paid: bool

class BanModel(BaseModel):
    telegram_id: int

class ReportModel(BaseModel):
    reporter_id: int
    reported_id: int

class LikeModel(BaseModel):
    from_id: int
    to_id: int

# ==================== Health ====================

@app.get("/")
async def root():
    return {"status": "HooshiGap API is running", "version": "1.0.0"}

# ==================== Users ====================

@app.get("/users/{telegram_id}")
async def get_user_endpoint(telegram_id: int):
    user = await get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    return user

@app.post("/users/create")
async def create_user_endpoint(data: CreateUserModel):
    if await user_exists(data.telegram_id):
        raise HTTPException(status_code=400, detail="کاربر قبلاً ثبت‌نام کرده")
    await create_user(
        data.telegram_id, data.username, data.gender,
        data.age, data.province, data.city, data.interests, data.photo_id
    )
    return {"success": True, "message": "کاربر ساخته شد"}

@app.get("/users/stats/all")
async def get_stats():
    return await get_user_stats()

@app.get("/users/recent/{limit}")
async def get_recent(limit: int = 10):
    return await get_recent_users(limit)

# ==================== Coins ====================

@app.get("/coins/{telegram_id}")
async def get_coins_endpoint(telegram_id: int):
    coins = await get_coins(telegram_id)
    vip = await is_vip(telegram_id)
    return {"coins": coins, "is_vip": vip}

@app.post("/coins/add")
async def add_coins_endpoint(data: CoinsModel):
    new_amount = await add_coins(data.telegram_id, data.amount)
    return {"success": True, "new_amount": new_amount}

@app.post("/coins/deduct/{telegram_id}")
async def deduct_coin_endpoint(telegram_id: int):
    success = await deduct_coin(telegram_id)
    if not success:
        raise HTTPException(status_code=400, detail="سکه کافی نیست")
    return {"success": True}

# ==================== Trust ====================

@app.get("/trust/{telegram_id}")
async def get_trust_endpoint(telegram_id: int):
    return await get_trust(telegram_id)

@app.post("/trust/shadowban/{telegram_id}")
async def shadowban_endpoint(telegram_id: int, reason: str, level: int = 1):
    await shadowban(telegram_id, reason, level)
    return {"success": True}

@app.post("/trust/unshadowban/{telegram_id}")
async def unshadowban_endpoint(telegram_id: int):
    await remove_shadowban(telegram_id)
    return {"success": True}

# ==================== Moderation ====================

@app.post("/moderation/analyze")
async def analyze_endpoint(telegram_id: int, text: str):
    result = await analyze_message(telegram_id, text)
    return {"result": result}

@app.post("/moderation/ban")
async def ban_endpoint(data: BanModel):
    await ban_user(data.telegram_id)
    return {"success": True}

@app.post("/moderation/unban")
async def unban_endpoint(data: BanModel):
    await unban_user(data.telegram_id)
    return {"success": True}

@app.post("/moderation/report")
async def report_endpoint(data: ReportModel):
    await report_user(data.reporter_id, data.reported_id)
    await report_penalty(data.reported_id)
    return {"success": True}

# ==================== Chat ====================

@app.post("/chat/history/save")
async def save_history_endpoint(user1: int, user2: int):
    await save_chat_history(user1, user2)
    return {"success": True}

@app.get("/chat/history/{user_id}")
async def get_history_endpoint(user_id: int, gender: str = "همه"):
    return await get_chat_history(user_id, gender)

@app.post("/chat/dm/send")
async def send_dm_endpoint(data: MessageModel):
    msg_id = await send_direct_message(data.from_id, data.to_id, data.message, data.is_paid)
    return {"success": True, "msg_id": msg_id}

@app.get("/chat/dm/{msg_id}")
async def get_dm_endpoint(msg_id: int):
    msg = await get_direct_message(msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="پیام پیدا نشد")
    return msg

# ==================== Social ====================

@app.post("/social/like")
async def like_endpoint(data: LikeModel):
    await like_user(data.from_id, data.to_id)
    is_match = await check_mutual_like(data.from_id, data.to_id)
    return {"success": True, "is_match": is_match}

@app.post("/social/block")
async def block_endpoint(data: LikeModel):
    await block_user(data.from_id, data.to_id)
    await block_penalty(data.to_id)
    return {"success": True}

@app.get("/social/blocked/{user_id}")
async def get_blocked_endpoint(user_id: int):
    blocked = await get_blocked_ids(user_id)
    return {"blocked_ids": blocked}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
