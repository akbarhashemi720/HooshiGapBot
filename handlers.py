# HooshiGap - Telegram Adapter
# This layer ONLY handles Telegram events and calls core backend
# NO business logic here

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from core import (
    get_user, user_exists, create_user, update_user,
    update_username, ban_user, unban_user,
    get_all_users, get_recent_users, get_user_stats, get_user_link,
    get_coins, add_coins, deduct_coin, has_enough_coins,
    is_vip, referral_reward,
    get_trust, shadowban, remove_shadowban,
    report_penalty, block_penalty, complete_chat_reward,
    warn_user, log_moderation,
    check_rate_limit, check_queue_limit, analyze_message,
    active_chats, start_chat, end_chat, get_partner, is_in_chat,
    save_chat_history, get_chat_history,
    send_direct_message, get_direct_message,
    block_user, report_user, like_user, check_mutual_like,
    get_blocked_ids
)
from matching import get_smart_matches
from voice import (
    save_voice_profile, delete_voice_profile, get_voice_profile,
    get_voice_badge, send_voice_profile, get_voice_label,
    VOICE_MODE_REAL
)

import math

GENDER, AGE, PROVINCE, CITY, INTERESTS, PHOTO = range(6)
SEARCH_GENDER, SEARCH_AGE, SEARCH_PROVINCE = range(6, 9)
EDIT_CHOICE, EDIT_VALUE = range(9, 11)
NEARBY_DISTANCE, NEARBY_LOCATION = range(11, 13)
RECENT_GENDER = 13
DM_WRITE = 14
VOICE_UPLOAD = 15

BOT_USERNAME = "HooshiGapBot"
ADMIN_IDS = [7049305054]

def main_menu():
    keyboard = [
        ["👥 مرور پروفایل‌ها", "🔍 جستجوی پیشرفته"],
        ["🎲 اتصال تصادفی", "👤 پروفایل من"],
        ["💰 کیف پول", "🎁 دعوت دوستان"],
        ["✏️ ویرایش پروفایل", "🎂 هم‌سن‌های من"],
        ["📍 افراد نزدیک", "💬 چت‌های اخیر"],
        ["🎤 ویس پروفایل"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def chat_menu():
    keyboard = [["⛔ پایان دادن چت"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def show_user_card(user, extra_text="", show_link=True):
    vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
    voice_badge = get_voice_badge(user)
    user_link = get_user_link(user) if show_link else ""
    link_line = f"\n🔗 {user_link}" if show_link else ""
    text = (
        f"{voice_badge}{vip_badge}"
        f"جنسیت: {user.get('gender', '-')}\n"
        f"سن: {user.get('age', '-')}\n"
        f"استان: {user.get('province', '-')}\n"
        f"شهر: {user.get('city', '-')}\n"
        f"علایق: {user.get('interests', '-')}"
        f"{link_line}"
    )
    if extra_text:
        text += f"\n{extra_text}"
    return text

def user_action_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user_id}"), InlineKeyboardButton("✖ بعدی", callback_data="skip")],
        [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user_id}"), InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user_id}")],
        [InlineKeyboardButton("⛔ بلاک", callback_data=f"block_{user_id}"), InlineKeyboardButton("⚠️ گزارش", callback_data=f"report_{user_id}")]
    ])

async def send_user_card(update, user, extra_text="", show_link=True):
    text = show_user_card(user, extra_text, show_link)
    keyboard = user_action_keyboard(user["telegram_id"])
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
