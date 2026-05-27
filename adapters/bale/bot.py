# HooshiGap - Bale Adapter
# This adapter handles ONLY Bale messenger communication
# Bale API is similar to Telegram Bot API

import httpx
import asyncio
from core import (
    get_user, user_exists, create_user, update_user, update_username,
    ban_user, unban_user, get_user_stats, get_user_link,
    get_coins, add_coins, deduct_coin, has_enough_coins, is_vip,
    get_trust, report_penalty, block_penalty, complete_chat_reward,
    check_rate_limit, check_queue_limit, analyze_message,
    active_chats, start_chat, end_chat, get_partner, is_in_chat,
    save_chat_history, get_chat_history, send_direct_message,
    block_user, report_user, like_user, check_mutual_like,
    get_blocked_ids, get_smart_matches, save_skip,
    update_behavioral_profile, update_user_location,
    filter_nearby_users
)

BALE_TOKEN = ""  # توکن ربات بله رو اینجا بذار
BALE_API = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

BOT_USERNAME = "HooshiGapBot"
ADMIN_IDS = [7049305054]

async def bale_send_message(chat_id, text, reply_markup=None):
    """ارسال پیام در بله"""
    async with httpx.AsyncClient() as client:
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = reply_markup
        r = await client.post(f"{BALE_API}/sendMessage", json=data)
        return r.json()

async def bale_send_photo(chat_id, photo, caption="", reply_markup=None):
    """ارسال عکس در بله"""
    async with httpx.AsyncClient() as client:
        data = {"chat_id": chat_id, "photo": photo, "caption": caption}
        if reply_markup:
            data["reply_markup"] = reply_markup
        r = await client.post(f"{BALE_API}/sendPhoto", json=data)
        return r.json()

async def bale_answer_callback(callback_query_id, text=""):
    """پاسخ به callback query در بله"""
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BALE_API}/answerCallbackQuery", json={
            "callback_query_id": callback_query_id,
            "text": text
        })
        return r.json()

def bale_main_menu():
    """منوی اصلی برای بله"""
    return {
        "keyboard": [
            [{"text": "👥 مرور پروفایل‌ها"}, {"text": "🔍 جستجوی پیشرفته"}],
            [{"text": "🎲 اتصال تصادفی"}, {"text": "👤 پروفایل من"}],
            [{"text": "💰 کیف پول"}, {"text": "🎁 دعوت دوستان"}],
            [{"text": "✏️ ویرایش پروفایل"}, {"text": "🎂 هم‌سن‌های من"}],
            [{"text": "📍 افراد نزدیک"}, {"text": "💬 چت‌های اخیر"}]
        ],
        "resize_keyboard": True
    }

def bale_inline_keyboard(buttons):
    """ساخت inline keyboard برای بله"""
    return {"inline_keyboard": buttons}

async def handle_bale_start(user_id, username, args=None):
    """هندل کردن دستور /start در بله"""
    username = username or ""
    if args and args.startswith("ref_"):
        referrer_id = int(args.split("_")[1])
        if referrer_id != user_id:
            existing = await user_exists(user_id)
            if not existing:
                await add_coins(referrer_id, 5)

    if await user_exists(user_id):
        await update_username(user_id, username)
        await bale_send_message(user_id, "خوش برگشتی به هوشی گپ!", bale_main_menu())
    else:
        await bale_send_message(user_id, "سلام! به هوشی گپ خوش اومدی!\nبرای ثبت‌نام /register بزن")

async def handle_bale_profile(user_id):
    """نمایش پروفایل در بله"""
    user = await get_user(user_id)
    if not user:
        await bale_send_message(user_id, "هنوز ثبت‌نام نکردی! /register بزن")
        return
    coins = await get_coins(user_id)
    trust = await get_trust(user_id)
    trust_score = trust.get("trust_score", 50)
    text = (
        f"پروفایل من:\n"
        f"آیدی: {user_id}\n"
        f"جنسیت: {user['gender']}\n"
        f"سن: {user['age']}\n"
        f"شهر: {user['city']}\n"
        f"علایق: {user['interests']}\n"
        f"سکه: {coins}\n"
        f"امتیاز اعتماد: {trust_score}/100"
    )
    await bale_send_message(user_id, text)

async def handle_bale_browse(user_id):
    """مرور پروفایل‌ها در بله"""
    coins = await get_coins(user_id)
    if coins <= 0:
        await bale_send_message(user_id, "سکه کافی نداری!")
        return
    blocked_ids = await get_blocked_ids(user_id)
    users = await get_smart_matches(user_id, blocked_ids, limit=5)
    if not users:
        await bale_send_message(user_id, "فعلا کاربر دیگری نیست!")
        return
    user = users[0]
    await deduct_coin(user_id)
    user_link = get_user_link(user)
    text = (
        f"جنسیت: {user['gender']}\n"
        f"سن: {user['age']}\n"
        f"شهر: {user['city']}\n"
        f"علایق: {user['interests']}\n"
        f"سکه باقی: {coins-1}"
    )
    keyboard = bale_inline_keyboard([
        [{"text": "❤️ لایک", "callback_data": f"like_{user['telegram_id']}"},
         {"text": "✖ بعدی", "callback_data": "skip"}],
        [{"text": "💬 چت", "callback_data": f"chatreq_{user['telegram_id']}"},
         {"text": "📨 پیام", "callback_data": f"dm_{user['telegram_id']}"}]
    ])
    if user.get("photo_id"):
        await bale_send_photo(user_id, user["photo_id"], text, keyboard)
    else:
        await bale_send_message(user_id, text, keyboard)

async def handle_bale_message(update):
    """هندل کردن پیام‌های ورودی بله"""
    message = update.get("message", {})
    user_id = message.get("from", {}).get("id")
    username = message.get("from", {}).get("username", "")
    text = message.get("text", "")

    if not user_id:
        return

    # چک کردن active chat
    if is_in_chat(user_id):
        partner_id = get_partner(user_id)
        if "پایان دادن چت" in text:
            end_chat(user_id)
            await bale_send_message(user_id, "چت پایان یافت!")
            await bale_send_message(partner_id, "طرف مقابل چت را پایان داد.")
            return
        result = await analyze_message(user_id, text)
        if result == "toxic":
            await bale_send_message(user_id, "پیام نامناسب ارسال نشد!")
            return
        await bale_send_message(partner_id, text)
        return

    # دستورات
    if text == "/start":
        await handle_bale_start(user_id, username)
    elif text == "/profile" or "پروفایل من" in text:
        await handle_bale_profile(user_id)
    elif "مرور پروفایل" in text:
        await handle_bale_browse(user_id)
    elif text == "/coins" or "کیف پول" in text:
        coins = await get_coins(user_id)
        await bale_send_message(user_id, f"💰 سکه شما: {coins} عدد")

async def handle_bale_callback(update):
    """هندل کردن callback query های بله"""
    callback = update.get("callback_query", {})
    callback_id = callback.get("id")
    user_id = callback.get("from", {}).get("id")
    data = callback.get("data", "")

    await bale_answer_callback(callback_id)

    if data.startswith("like_"):
        to_id = int(data.split("_")[1])
        await like_user(user_id, to_id)
        is_match = await check_mutual_like(user_id, to_id)
        if is_match:
            await bale_send_message(user_id, "ماتچ شدید!")
            await bale_send_message(to_id, "ماتچ شدید!")
        else:
            await bale_send_message(user_id, "لایک ثبت شد!")

    elif data.startswith("block_"):
        to_id = int(data.split("_")[1])
        await block_user(user_id, to_id)
        await bale_send_message(user_id, "کاربر بلاک شد.")

    elif data.startswith("report_"):
        to_id = int(data.split("_")[1])
        await report_user(user_id, to_id)
        await report_penalty(to_id)
        await bale_send_message(user_id, "گزارش ثبت شد!")

    elif data == "skip":
        await save_skip(user_id, 0)

async def process_bale_update(update):
    """پردازش آپدیت‌های بله"""
    if "message" in update:
        await handle_bale_message(update)
    elif "callback_query" in update:
        await handle_bale_callback(update)

async def get_bale_updates(offset=0):
    """دریافت آپدیت‌های جدید از بله"""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BALE_API}/getUpdates", params={"offset": offset, "timeout": 30})
        return r.json()

async def run_bale_bot():
    """اجرای ربات بله"""
    print("ربات بله شروع به کار کرد...")
    offset = 0
    while True:
        try:
            updates = await get_bale_updates(offset)
            if updates.get("ok"):
                for update in updates.get("result", []):
                    await process_bale_update(update)
                    offset = update["update_id"] + 1
        except Exception as e:
            print(f"Bale bot error: {e}")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_bale_bot())
