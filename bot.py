from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
import httpx
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_server():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()
import random
import math
from safety import (
    analyze_message, check_rate_limit, check_queue_limit,
    get_trust, update_trust, shadowban, is_shadowbanned,
    get_shadowban_level, report_penalty, block_penalty,
    complete_chat_reward, get_safe_users, warn_user,
    get_warning_count, log_moderation, update_user_location,
    get_distance_bucket
)
from matching import (
    get_smart_matches, get_best_match, get_recommendations,
    update_behavioral_profile, save_skip, save_match_history,
    calculate_compatibility, get_quality_label, infer_personality
)
from voice import (
    save_voice_profile, delete_voice_profile, get_voice_profile,
    get_voice_badge, send_voice_profile, get_voice_label,
    VOICE_MODE_REAL, VOICE_MODE_MODIFIED, VOICE_MODE_HIDDEN
)

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"
BOT_USERNAME = "HooshiGapBot"
ADMIN_IDS = [7049305054]

GENDER, AGE, PROVINCE, CITY, INTERESTS, PHOTO = range(6)
SEARCH_GENDER, SEARCH_AGE, SEARCH_PROVINCE = range(6, 9)
EDIT_CHOICE, EDIT_VALUE = range(9, 11)
NEARBY_DISTANCE, NEARBY_LOCATION = range(11, 13)
RECENT_GENDER = 13
DM_WRITE = 14
VOICE_UPLOAD = 15
VOICE_MODE_SELECT = 16

active_chats = {}

def main_menu():
    keyboard = [
        ["\U0001f465 \u0645\u0631\u0648\u0631 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644\u200c\u0647\u0627", "\U0001f50d \u062c\u0633\u062a\u062c\u0648\u06cc \u067e\u06cc\u0634\u0631\u0641\u062a\u0647"],
        ["\U0001f3b2 \u0627\u062a\u0635\u0627\u0644 \u062a\u0635\u0627\u062f\u0641\u06cc", "\U0001f464 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0645\u0646"],
        ["\U0001f4b0 \u06a9\u06cc\u0641 \u067e\u0648\u0644", "\U0001f381 \u062f\u0639\u0648\u062a \u062f\u0648\u0633\u062a\u0627\u0646"],
        ["\u270f\ufe0f \u0648\u06cc\u0631\u0627\u06cc\u0634 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644", "\U0001f382 \u0647\u0645\u200c\u0633\u0646\u200c\u0647\u0627\u06cc \u0645\u0646"],
        ["\U0001f4cd \u0627\u0641\u0631\u0627\u062f \u0646\u0632\u062f\u06cc\u06a9", "\U0001f4ac \u0686\u062a\u200c\u0647\u0627\u06cc \u0627\u062e\u06cc\u0631"],
        ["\U0001f3a4 \u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def chat_menu():
    keyboard = [["\u26d4 \u067e\u0627\u06cc\u0627\u0646 \u062f\u0627\u062f\u0646 \u0686\u062a"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

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

async def db_delete(table, params):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        await client.delete(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)

async def get_coins(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=coins")
    if users:
        return users[0].get("coins", 0)
    return 0

async def add_coins(telegram_id, amount):
    coins = await get_coins(telegram_id)
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"coins": coins + amount})

async def deduct_coin(telegram_id):
    coins = await get_coins(telegram_id)
    if coins <= 0:
        return False
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {"coins": coins - 1})
    return True

async def is_vip(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=is_vip")
    if users:
        return users[0].get("is_vip", False)
    return False

async def save_chat_history(user1, user2):
    existing = await db_get("chat_history", f"user1=eq.{user1}&user2=eq.{user2}")
    if not existing:
        existing2 = await db_get("chat_history", f"user1=eq.{user2}&user2=eq.{user1}")
        if not existing2:
            await db_post("chat_history", {"user1": user1, "user2": user2})

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if my_id not in ADMIN_IDS:
        await update.message.reply_text("\u062f\u0633\u062a\u0631\u0633\u06cc \u0646\u062f\u0627\u0631\u06cc\u062f!")
        return
    total = len(await db_get("users", ""))
    vip_count = len(await db_get("users", "is_vip=eq.true"))
    voice_count = len(await db_get("users", "has_voice=eq.true"))
    reports = len(await db_get("reports", ""))
    blocks = len(await db_get("blocks", ""))
    text = (
        f"\U0001f4ca \u067e\u0646\u0644 \u0627\u062f\u0645\u06cc\u0646\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f465 \u06a9\u0644 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646: {total}\n"
        f"\u2b50 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646 VIP: {vip_count}\n"
        f"\U0001f3a4 \u062f\u0627\u0631\u0627\u06cc \u0648\u06cc\u0633: {voice_count}\n"
        f"\u26a0\ufe0f \u06af\u0632\u0627\u0631\u0634\u200c\u0647\u0627: {reports}\n"
        f"\u26d4 \u0628\u0644\u0627\u06a9\u200c\u0647\u0627: {blocks}\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f465 \u0644\u06cc\u0633\u062a \u06a9\u0627\u0631\u0628\u0631\u0627\u0646", callback_data="admin_users")],
        [InlineKeyboardButton("\u26a0\ufe0f \u06af\u0632\u0627\u0631\u0634\u200c\u0647\u0627", callback_data="admin_reports")],
    ])
    await update.message.reply_text(text, reply_markup=keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    args = context.args
    if args and args[0].startswith("ref_"):
        referrer_id = int(args[0].split("_")[1])
        if referrer_id != my_id:
            existing = await db_get("users", f"telegram_id=eq.{my_id}")
            if not existing:
                await add_coins(referrer_id, 5)
                try:
                    await context.bot.send_message(chat_id=referrer_id, text="\u06cc\u06a9 \u0646\u0641\u0631 \u062c\u062f\u06cc\u062f \u0648\u0627\u0631\u062f \u0634\u062f! 5 \u0633\u06a9\u0647 \u06af\u0631\u0641\u062a\u06cc\u062f!")
                except:
                    pass
    existing = await db_get("users", f"telegram_id=eq.{my_id}")
    if existing:
        await update.message.reply_text("\u062e\u0648\u0634 \u0628\u0631\u06af\u0634\u062a\u06cc \u0628\u0647 \u0647\u0648\u0634\u06cc \u06af\u067e!", reply_markup=main_menu())
    else:
        await update.message.reply_text("\u0633\u0644\u0627\u0645! \u0628\u0647 \u0647\u0648\u0634\u06cc \u06af\u067e \u062e\u0648\u0634 \u0627\u0648\u0645\u062f\u06cc!\n/register \u0628\u0632\u0646", reply_markup=ReplyKeyboardRemove())

async def voice_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    voice = await get_voice_profile(my_id)
    if voice:
        mode = voice.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\U0001f3a4 \u067e\u062e\u0634 \u0648\u06cc\u0633", callback_data="play_my_voice")],
            [InlineKeyboardButton("\u267b\ufe0f \u062c\u0627\u06cc\u06af\u0632\u06cc\u0646\u06cc \u0648\u06cc\u0633", callback_data="replace_voice")],
            [InlineKeyboardButton("\U0001f512 \u062a\u063a\u06cc\u06cc\u0631 \u062d\u0631\u06cc\u0645 \u062e\u0635\u0648\u0635\u06cc", callback_data="change_voice_mode")],
            [InlineKeyboardButton("\u274c \u062d\u0630\u0641 \u0648\u06cc\u0633", callback_data="delete_voice")]
        ])
        await update.message.reply_text(
            f"\U0001f3a4 \u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0641\u0639\u0627\u0644\u0647!\n\u0645\u062f\u062a: {voice.get('voice_duration', 0)} \u062b\u0627\u0646\u06cc\u0647\n\u062d\u0627\u0644\u062a: {label}",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\U0001f3a4 \u0627\u0636\u0627\u0641\u0647 \u06a9\u0631\u062f\u0646 \u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644", callback_data="add_voice")]
        ])
        await update.message.reply_text(
            "\U0001f3a4 \u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0646\u062f\u0627\u0631\u06cc!\n\n\u0628\u0627 \u0627\u0636\u0627\u0641\u0647 \u06a9\u0631\u062f\u0646 \u0648\u06cc\u0633:\n\u2705 \u0627\u0645\u062a\u06cc\u0627\u0632 \u0627\u0639\u062a\u0645\u0627\u062f +5\n\u2705 \u062f\u06cc\u062f\u0647 \u0634\u062f\u0646 \u0628\u06cc\u0634\u062a\u0631\n\u2705 \u0645\u0686 \u0628\u0647\u062a\u0631",
            reply_markup=keyboard
        )

async def handle_voice_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if not update.message.voice:
        await update.message.reply_text("\u0644\u0637\u0641\u0627 \u0648\u06cc\u0633 \u0628\u0641\u0631\u0633\u062a\u06cc\u062f!", reply_markup=main_menu())
        return ConversationHandler.END
    voice = update.message.voice
    context.user_data["temp_voice_id"] = voice.file_id
    context.user_data["temp_voice_duration"] = voice.duration
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f3a4 \u0648\u06cc\u0633 \u0648\u0627\u0642\u0639\u06cc", callback_data="vmode_real")],
        [InlineKeyboardButton("\U0001f527 \u0648\u06cc\u0633 \u062a\u063a\u06cc\u06cc\u0631\u06cc\u0627\u0641\u062a\u0647", callback_data="vmode_modified")],
        [InlineKeyboardButton("\U0001f512 \u067e\u0646\u0647\u0627\u0646 \u062a\u0627 \u0645\u0686", callback_data="vmode_hidden")]
    ])
    await update.message.reply_text(
        "\u0648\u06cc\u0633\u062a \u062f\u0631\u06cc\u0627\u0641\u062a \u0634\u062f!\n\u0686\u0637\u0648\u0631 \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0628\u0634\u0647\u061f",
        reply_markup=keyboard
    )
    return ConversationHandler.END

async def send_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_id = context.user_data.get("dm_to")
    if not to_id:
        await update.message.reply_text("\u062e\u0637\u0627\u06cc \u0641\u0646\u06cc!", reply_markup=main_menu())
        return ConversationHandler.END
    from_id = update.effective_user.id
    message_text = update.message.text
    if not check_rate_limit(from_id):
        await update.message.reply_text("\u067e\u06cc\u0627\u0645 \u0647\u0627 \u0631\u0648 \u06a9\u0645\u062a\u0631 \u0628\u0641\u0631\u0633\u062a\u06cc\u062f!")
        return ConversationHandler.END
    result_analysis = await analyze_message(from_id, message_text)
    if result_analysis == "toxic":
        await update.message.reply_text("\u067e\u06cc\u0627\u0645 \u0634\u0645\u0627 \u0646\u0627\u0645\u0646\u0627\u0633\u0628 \u0628\u0648\u062f \u0648 \u0627\u0631\u0633\u0627\u0644 \u0646\u0634\u062f!", reply_markup=main_menu())
        return ConversationHandler.END
    from_coins = await get_coins(from_id)
    if from_coins >= 1:
        await deduct_coin(from_id)
        is_paid = True
    else:
        is_paid = False
    result = await db_post("direct_messages", {
        "from_user": from_id,
        "to_user": to_id,
        "message": message_text,
        "is_paid": is_paid
    })
    msg_id = result[0]["id"] if result and len(result) > 0 else None
    from_profile = await db_get("users", f"telegram_id=eq.{from_id}")
    if from_profile:
        u = from_profile[0]
        vip_badge = "\u2b50 VIP | " if u.get("is_vip") else ""
        voice_badge = get_voice_badge(u)
        if is_paid:
            notif = (
                f"\U0001f4e8 \u067e\u06cc\u0627\u0645 \u062e\u0635\u0648\u0635\u06cc \u062c\u062f\u06cc\u062f!\n"
                f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {u['gender']} | \u0633\u0646: {u['age']} | \u0634\u0647\u0631: {u['city']}\n\n"
                f"\u0628\u0631\u0627\u06cc \u062e\u0648\u0627\u0646\u062f\u0646 \u067e\u06cc\u0627\u0645 \u0631\u0648\u06cc \u062f\u06a9\u0645\u0647 \u0632\u06cc\u0631 \u0628\u0632\u0646\u06cc\u062f:"
            )
        else:
            notif = (
                f"\U0001f4e8 \u067e\u06cc\u0627\u0645 \u062e\u0635\u0648\u0635\u06cc \u062c\u062f\u06cc\u062f!\n"
                f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {u['gender']} | \u0633\u0646: {u['age']} | \u0634\u0647\u0631: {u['city']}\n\n"
                f"\u26a0\ufe0f \u0641\u0631\u0633\u062a\u0646\u062f\u0647 \u0633\u06a9\u0647 \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0634\u062a!\n"
                f"\u0628\u0631\u0627\u06cc \u062e\u0648\u0627\u0646\u062f\u0646 \u067e\u06cc\u0627\u0645\u060c 1 \u0633\u06a9\u0647 \u0627\u0632 \u0634\u0645\u0627 \u06a9\u0633\u0631 \u0645\u06cc\u0634\u0648\u062f:"
            )
        if msg_id:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("\U0001f4e9 \u062e\u0648\u0627\u0646\u062f\u0646 \u067e\u06cc\u0627\u0645", callback_data=f"readdm_{msg_id}_{from_id}_{is_paid}")
            ]])
            try:
                if u.get("photo_id"):
                    await context.bot.send_photo(chat_id=to_id, photo=u["photo_id"], caption=notif, reply_markup=kb)
                else:
                    await context.bot.send_message(chat_id=to_id, text=notif, reply_markup=kb)
            except:
                pass
    await update.message.reply_text("\u2705 \u067e\u06cc\u0627\u0645 \u0627\u0631\u0633\u0627\u0644 \u0634\u062f!", reply_markup=main_menu())
    return ConversationHandler.END

async def coins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    coins = await get_coins(my_id)
    vip = await is_vip(my_id)
    vip_text = "\u2b50 VIP \u0641\u0639\u0627\u0644" if vip else "VIP \u0646\u062f\u0627\u0631\u06cc\u062f"
    text = (
        f"\U0001f4b0 \u06a9\u06cc\u0641 \u067e\u0648\u0644 \u0634\u0645\u0627\n"
        f"\u0633\u06a9\u0647: {coins} \u0639\u062f\u062f\n"
        f"\u0648\u0636\u0639\u06cc\u062a: {vip_text}\n\n"
        f"\u0631\u0648\u0634\u200c\u0647\u0627\u06cc \u062f\u0631\u06cc\u0627\u0641\u062a \u0633\u06a9\u0647:\n\n"
        f"1 - \u0645\u0639\u0631\u0641\u06cc \u062f\u0648\u0633\u062a\u0627\u0646 - \u0631\u0627\u06cc\u06af\u0627\u0646\n"
        f"2 - \u062e\u0631\u06cc\u062f \u0633\u06a9\u0647 - \u0628\u0647 \u0632\u0648\u062f\u06cc\n"
        f"3 - \u062e\u0631\u06cc\u062f VIP - \u0627\u0645\u06a9\u0627\u0646\u0627\u062a \u0648\u06cc\u0698\u0647"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f381 \u0645\u0639\u0631\u0641\u06cc \u062f\u0648\u0633\u062a\u0627\u0646 (\u0631\u0627\u06cc\u06af\u0627\u0646)", callback_data="coins_invite")],
        [InlineKeyboardButton("\U0001f4b3 \u062e\u0631\u06cc\u062f \u0633\u06a9\u0647 (\u0628\u0647 \u0632\u0648\u062f\u06cc)", callback_data="coins_buy")],
        [InlineKeyboardButton("\u2b50 \u062e\u0631\u06cc\u062f VIP (\u0628\u0647 \u0632\u0648\u062f\u06cc)", callback_data="coins_vip")]
    ])
    await update.message.reply_text(text, reply_markup=keyboard)

async def end_chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if my_id in active_chats:
        partner_id = active_chats[my_id]
        await save_chat_history(my_id, partner_id)
        await complete_chat_reward(my_id)
        await complete_chat_reward(partner_id)
        await update_behavioral_profile(my_id, 300, completed=True)
        await update_behavioral_profile(partner_id, 300, completed=True)
        del active_chats[my_id]
        if partner_id in active_chats:
            del active_chats[partner_id]
        await update.message.reply_text("\u0686\u062a \u067e\u0627\u06cc\u0627\u0646 \u06cc\u0627\u0641\u062a!", reply_markup=main_menu())
        try:
            await context.bot.send_message(chat_id=partner_id, text="\u0637\u0631\u0641 \u0645\u0642\u0627\u0628\u0644 \u0686\u062a \u0631\u0627 \u067e\u0627\u06cc\u0627\u0646 \u062f\u0627\u062f.", reply_markup=main_menu())
        except:
            pass
    else:
        await update.message.reply_text("\u0686\u062a \u0641\u0639\u0627\u0644\u06cc \u0646\u062f\u0627\u0631\u06cc!", reply_markup=main_menu())

async def forward_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if my_id not in active_chats:
        if update.message.photo:
            await photo(update, context)
        return
    partner_id = active_chats[my_id]
    try:
        msg = update.message
        if msg.photo:
            await context.bot.send_photo(chat_id=partner_id, photo=msg.photo[-1].file_id, caption=msg.caption or "")
        elif msg.video:
            await context.bot.send_video(chat_id=partner_id, video=msg.video.file_id, caption=msg.caption or "")
        elif msg.voice:
            await context.bot.send_voice(chat_id=partner_id, voice=msg.voice.file_id)
        elif msg.audio:
            await context.bot.send_audio(chat_id=partner_id, audio=msg.audio.file_id)
        elif msg.sticker:
            await context.bot.send_sticker(chat_id=partner_id, sticker=msg.sticker.file_id)
        elif msg.video_note:
            await context.bot.send_video_note(chat_id=partner_id, video_note=msg.video_note.file_id)
        elif msg.document:
            await context.bot.send_document(chat_id=partner_id, document=msg.document.file_id, caption=msg.caption or "")
        elif msg.animation:
            await context.bot.send_animation(chat_id=partner_id, animation=msg.animation.file_id)
    except:
        pass

async def recent_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["\u067e\u0633\u0631", "\u062f\u062e\u062a\u0631", "\u0647\u0645\u0647"]]
    await update.message.reply_text("\u0686\u062a\u200c\u0647\u0627\u06cc \u0627\u062e\u06cc\u0631 \u0628\u0627 \u0686\u0647 \u062c\u0646\u0633\u06cc\u062a\u06cc\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return RECENT_GENDER

async def recent_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    gender_filter = update.message.text
    history1 = await db_get("chat_history", f"user1=eq.{my_id}")
    history2 = await db_get("chat_history", f"user2=eq.{my_id}")
    partner_ids = [h["user2"] for h in history1] + [h["user1"] for h in history2]
    if not partner_ids:
        await update.message.reply_text("\u0647\u0646\u0648\u0632 \u0686\u062a\u06cc \u0646\u062f\u0627\u0634\u062a\u06cc!", reply_markup=main_menu())
        return ConversationHandler.END
    found = []
    for pid in partner_ids:
        users = await db_get("users", f"telegram_id=eq.{pid}")
        if users:
            u = users[0]
            if gender_filter == "\u0647\u0645\u0647" or u.get("gender") == gender_filter:
                found.append(u)
    if not found:
        await update.message.reply_text("\u06a9\u0633\u06cc \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f!", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(f"{len(found)} \u0646\u0641\u0631 \u067e\u06cc\u062f\u0627 \u0634\u062f:", reply_markup=main_menu())
    for user in found[:10]:
        vip_badge = "\u2b50 VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n\u0633\u0646: {user['age']}\n\u0634\u0647\u0631: {user['city']}\n\u0639\u0644\u0627\u06cc\u0642: {user['interests']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\U0001f4ac \u0686\u062a", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    my_id = update.effective_user.id

    if "\u067e\u0627\u06cc\u0627\u0646 \u062f\u0627\u062f\u0646 \u0686\u062a" in text:
        await end_chat_cmd(update, context)
        return

    if my_id in active_chats:
        partner_id = active_chats[my_id]
        if not check_rate_limit(my_id):
            await update.message.reply_text("\u067e\u06cc\u0627\u0645 \u0647\u0627 \u0631\u0648 \u06a9\u0645\u062a\u0631 \u0628\u0641\u0631\u0633\u062a\u06cc\u062f!")
            return
        result = await analyze_message(my_id, text)
        if result == "toxic":
            await update.message.reply_text("\u067e\u06cc\u0627\u0645 \u0646\u0627\u0645\u0646\u0627\u0633\u0628 \u0627\u0631\u0633\u0627\u0644 \u0646\u0634\u062f!")
            return
        try:
            await context.bot.send_message(chat_id=partner_id, text=text)
        except:
            pass
        return

    if "\u0645\u0631\u0648\u0631 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644" in text:
        await browse(update, context)
    elif "\u062c\u0633\u062a\u062c\u0648" in text:
        await search(update, context)
        return SEARCH_GENDER
    elif "\u0627\u062a\u0635\u0627\u0644 \u062a\u0635\u0627\u062f\u0641\u06cc" in text:
        await random_user(update, context)
    elif "\u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0645\u0646" in text:
        await profile(update, context)
    elif "\u06a9\u06cc\u0641 \u067e\u0648\u0644" in text:
        await coins_cmd(update, context)
    elif "\u062f\u0639\u0648\u062a" in text:
        await invite(update, context)
    elif "\u0648\u06cc\u0631\u0627\u06cc\u0634" in text:
        await edit_profile(update, context)
        return EDIT_CHOICE
    elif "\u0647\u0645\u200c\u0633\u0646" in text:
        await same_age(update, context)
    elif "\u0646\u0632\u062f\u06cc\u06a9" in text:
        await nearby(update, context)
        return NEARBY_DISTANCE
    elif "\u0686\u062a\u200c\u0647\u0627\u06cc \u0627\u062e\u06cc\u0631" in text:
        await recent_chats(update, context)
        return RECENT_GENDER
    elif "\u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644" in text:
        await voice_profile_menu(update, context)

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_users":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        users = await db_get("users", "limit=10&order=id.desc")
        text = "\U0001f465 \u0622\u062e\u0631\u06cc\u0646 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646:\n\n"
        for u in users:
            text += f"ID: {u['telegram_id']} | {u.get('gender','')} | {u.get('city','')}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data == "admin_reports":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        reports = await db_get("reports", "limit=10&order=id.desc")
        text = "\u26a0\ufe0f \u0622\u062e\u0631\u06cc\u0646 \u06af\u0632\u0627\u0631\u0634\u200c\u0647\u0627:\n\n"
        for r in reports:
            text += f"\u06af\u0632\u0627\u0631\u0634\u062f\u0647\u0646\u062f\u0647: {r['reporter']} | \u06af\u0632\u0627\u0631\u0634\u0634\u062f\u0647: {r['reported']}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data.startswith("vmode_"):
        mode = query.data.replace("vmode_", "")
        from_id = update.effective_user.id
        file_id = context.user_data.get("temp_voice_id")
        duration = context.user_data.get("temp_voice_duration", 0)
        if not file_id:
            await context.bot.send_message(chat_id=from_id, text="\u062e\u0637\u0627! \u062f\u0648\u0628\u0627\u0631\u0647 \u0648\u06cc\u0633 \u0628\u0641\u0631\u0633\u062a\u06cc\u062f.", reply_markup=main_menu())
            return
        await context.bot.send_message(chat_id=from_id, text="\u062f\u0631 \u062d\u0627\u0644 \u067e\u0631\u062f\u0627\u0632\u0634 \u0648\u06cc\u0633...")
        success, msg = await save_voice_profile(from_id, file_id, duration, mode, bot=context.bot)
        await context.bot.send_message(chat_id=from_id, text=msg, reply_markup=main_menu())
        return

    if query.data == "change_voice_mode":
        from_id = update.effective_user.id
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\U0001f3a4 \u0648\u06cc\u0633 \u0648\u0627\u0642\u0639\u06cc", callback_data="setmode_real")],
            [InlineKeyboardButton("\U0001f527 \u0648\u06cc\u0633 \u062a\u063a\u06cc\u06cc\u0631\u06cc\u0627\u0641\u062a\u0647", callback_data="setmode_modified")],
            [InlineKeyboardButton("\U0001f512 \u067e\u0646\u0647\u0627\u0646 \u062a\u0627 \u0645\u0686", callback_data="setmode_hidden")]
        ])
        await context.bot.send_message(chat_id=from_id, text="\u062d\u0627\u0644\u062a \u062c\u062f\u06cc\u062f \u0631\u0648 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646:", reply_markup=keyboard)
        return

    if query.data.startswith("setmode_"):
        mode = query.data.replace("setmode_", "")
        from_id = update.effective_user.id
        await db_patch("users", f"telegram_id=eq.{from_id}", {"voice_mode": mode})
        label = get_voice_label(mode)
        await context.bot.send_message(chat_id=from_id, text=f"\u2705 \u062d\u0627\u0644\u062a \u0648\u06cc\u0633 \u062a\u063a\u06cc\u06cc\u0631 \u06a9\u0631\u062f: {label}", reply_markup=main_menu())
        return

    if query.data == "add_voice" or query.data == "replace_voice":
        from_id = update.effective_user.id
        await context.bot.send_message(
            chat_id=from_id,
            text="\U0001f3a4 \u06cc\u06a9 \u0648\u06cc\u0633 \u0628\u06cc\u0646 10 \u062a\u0627 30 \u062b\u0627\u0646\u06cc\u0647 \u0628\u0641\u0631\u0633\u062a:",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data["waiting_voice"] = True
        return

    if query.data == "delete_voice":
        from_id = update.effective_user.id
        success, msg = await delete_voice_profile(from_id)
        await context.bot.send_message(chat_id=from_id, text=msg, reply_markup=main_menu())
        return

    if query.data == "play_my_voice":
        from_id = update.effective_user.id
        voice = await get_voice_profile(from_id)
        if voice:
            await send_voice_profile(context.bot, from_id, voice, is_matched=True)
        return

    if query.data == "coins_invite":
        my_id = update.effective_user.id
        link = f"https://t.me/{BOT_USERNAME}?start=ref_{my_id}"
        await context.bot.send_message(chat_id=my_id, text=f"\u0644\u06cc\u0646\u06a9 \u062f\u0639\u0648\u062a:\n{link}\n\n\u0628\u0647 \u0627\u0632\u0627\u06cc \u0647\u0631 \u062f\u0648\u0633\u062a 5 \u0633\u06a9\u0647 \u0647\u062f\u06cc\u0647 \u0645\u06cc\u06af\u06cc\u0631\u06cc\u062f!")
        return

    if query.data == "coins_buy":
        await context.bot.send_message(chat_id=update.effective_user.id, text="\u062e\u0631\u06cc\u062f \u0633\u06a9\u0647 \u0628\u0647 \u0632\u0648\u062f\u06cc \u0641\u0639\u0627\u0644 \u0645\u06cc\u0634\u0648\u062f!")
        return

    if query.data == "coins_vip":
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "\u2b50 \u0627\u0645\u06a9\u0627\u0646\u0627\u062a VIP:\n\n"
                "1 - \u0627\u0648\u0644 \u0644\u06cc\u0633\u062a \u062c\u0633\u062a\u062c\u0648\u200c\u0647\u0627\n"
                "2 - \u0646\u0634\u0627\u0646 VIP \u0631\u0648\u06cc \u067e\u0631\u0648\u0641\u0627\u06cc\u0644\n"
                "3 - \u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0686\u062a \u0628\u0647 10 \u0646\u0641\u0631\n"
                "4 - \u067e\u06cc\u0627\u0645 \u062f\u0627\u06cc\u0631\u06a9\u062a \u0628\u0647 10 \u0646\u0641\u0631\n\n"
                "\u0628\u0647 \u0632\u0648\u062f\u06cc \u0641\u0639\u0627\u0644 \u0645\u06cc\u0634\u0648\u062f!"
            )
        )
        return

    if query.data.startswith("readdm_"):
        parts = query.data.split("_")
        msg_id = parts[1]
        from_id = int(parts[2])
        is_paid = parts[3] == "True"
        to_id = update.effective_user.id
        msgs = await db_get("direct_messages", f"id=eq.{msg_id}")
        if not msgs:
            await query.answer("\u067e\u06cc\u0627\u0645 \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f!", show_alert=True)
            return
        msg = msgs[0]
        if not is_paid:
            to_coins = await get_coins(to_id)
            if to_coins <= 0:
                await query.answer("\u0633\u06a9\u0647 \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0631\u06cc\u062f!", show_alert=True)
                return
            await deduct_coin(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        dm_text = msg.get("message", "")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("\U0001f4ac \u067e\u0627\u0633\u062e \u062f\u0627\u062f\u0646", callback_data=f"chatreq_{from_id}"),
            InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{from_id}")
        ]])
        await context.bot.send_message(
            chat_id=to_id,
            text=f"\U0001f4e9 \u067e\u06cc\u0627\u0645 \u062e\u0635\u0648\u0635\u06cc:\n\n\"{dm_text}\"",
            reply_markup=kb
        )
        return

    if query.data == "skip":
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await save_skip(update.effective_user.id, 0)
        return

    if query.data == "random_next":
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        return

    if query.data.startswith("block_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        await db_post("blocks", {"blocker": from_id, "blocked": to_id})
        await block_penalty(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=from_id, text="\u06a9\u0627\u0631\u0628\u0631 \u0628\u0644\u0627\u06a9 \u0634\u062f.")
        return

    if query.data.startswith("report_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        await db_post("reports", {"reporter": from_id, "reported": to_id})
        await report_penalty(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=from_id, text="\u06af\u0632\u0627\u0631\u0634 \u062b\u0628\u062a \u0634\u062f!")
        return

    if query.data.startswith("chatreq_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        my_profile = await db_get("users", f"telegram_id=eq.{from_id}")
        if my_profile:
            u = my_profile[0]
            vip_badge = "\u2b50 VIP | " if u.get("is_vip") else ""
            voice_badge = get_voice_badge(u)
            text = f"{voice_badge}{vip_badge}\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0686\u062a!\n\u062c\u0646\u0633\u06cc\u062a: {u['gender']}\n\u0633\u0646: {u['age']}\n\u0634\u0647\u0631: {u['city']}\n\u0639\u0644\u0627\u06cc\u0642: {u['interests']}"
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("\u2705 \u0642\u0628\u0648\u0644", callback_data=f"accept_{from_id}"),
                InlineKeyboardButton("\u274c \u0631\u062f", callback_data=f"reject_{from_id}")
            ]])
            try:
                if u.get("photo_id"):
                    await context.bot.send_photo(chat_id=to_id, photo=u["photo_id"], caption=text, reply_markup=kb)
                else:
                    await context.bot.send_message(chat_id=to_id, text=text, reply_markup=kb)
                if u.get("has_voice"):
                    await send_voice_profile(context.bot, to_id, u, is_matched=False)
            except:
                pass
        await context.bot.send_message(chat_id=from_id, text="\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0686\u062a \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f!")
        return

    if query.data.startswith("dm_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        context.user_data["dm_to"] = to_id
        await context.bot.send_message(
            chat_id=from_id,
            text="\U0001f4e8 \u067e\u06cc\u0627\u0645 \u062e\u0635\u0648\u0635\u06cc\u062a \u0631\u0648 \u0628\u0646\u0648\u06cc\u0633:",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if query.data.startswith("accept_"):
        from_id = int(query.data.split("_")[1])
        to_id = update.effective_user.id
        active_chats[from_id] = to_id
        active_chats[to_id] = from_id
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=to_id, text="\u0686\u062a \u0634\u0631\u0648\u0639 \u0634\u062f!", reply_markup=chat_menu())
        await context.bot.send_message(chat_id=from_id, text="\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0642\u0628\u0648\u0644 \u0634\u062f!", reply_markup=chat_menu())
        from_profile = await db_get("users", f"telegram_id=eq.{from_id}")
        to_profile = await db_get("users", f"telegram_id=eq.{to_id}")
        if from_profile and from_profile[0].get("has_voice"):
            await send_voice_profile(context.bot, to_id, from_profile[0], is_matched=True)
        if to_profile and to_profile[0].get("has_voice"):
            await send_voice_profile(context.bot, from_id, to_profile[0], is_matched=True)
        return

    if query.data.startswith("reject_"):
        from_id = int(query.data.split("_")[1])
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=from_id, text="\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0686\u062a \u0634\u0645\u0627 \u0631\u062f \u0634\u062f.")
        return

    to_id = int(query.data.split("_")[1])
    from_id = update.effective_user.id
    await db_post("likes", {"from_user": from_id, "to_user": to_id})
    likes = await db_get("likes", f"from_user=eq.{to_id}&to_user=eq.{from_id}")
    if likes:
        await context.bot.send_message(chat_id=from_id, text="\u0645\u0627\u062a\u0686 \u0634\u062f\u06cc\u062f!")
        try:
            await context.bot.send_message(chat_id=to_id, text="\u0645\u0627\u062a\u0686 \u0634\u062f\u06cc\u062f!")
        except:
            pass
    else:
        await context.bot.send_message(chat_id=from_id, text="\u0644\u0627\u06cc\u06a9 \u062b\u0628\u062a \u0634\u062f!")
        try:
            await context.bot.send_message(chat_id=to_id, text="\u06cc\u06a9 \u0646\u0641\u0631 \u0628\u0647 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644\u062a \u0639\u0644\u0627\u0642\u0647 \u0646\u0634\u0648\u0646 \u062f\u0627\u062f!")
        except:
            pass

async def handle_voice_in_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if context.user_data.get("waiting_voice"):
        voice = update.message.voice
        if voice:
            context.user_data["temp_voice_id"] = voice.file_id
            context.user_data["temp_voice_duration"] = voice.duration
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001f3a4 \u0648\u06cc\u0633 \u0648\u0627\u0642\u0639\u06cc", callback_data="vmode_real")],
                [InlineKeyboardButton("\U0001f527 \u0648\u06cc\u0633 \u062a\u063a\u06cc\u06cc\u0631\u06cc\u0627\u0641\u062a\u0647", callback_data="vmode_modified")],
                [InlineKeyboardButton("\U0001f512 \u067e\u0646\u0647\u0627\u0646 \u062a\u0627 \u0645\u0686", callback_data="vmode_hidden")]
            ])
            await update.message.reply_text(
                "\u0648\u06cc\u0633\u062a \u062f\u0631\u06cc\u0627\u0641\u062a \u0634\u062f!\n\u0686\u0637\u0648\u0631 \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0628\u0634\u0647\u061f",
                reply_markup=keyboard
            )
            context.user_data["waiting_voice"] = False
            return
    await forward_media(update, context)

async def browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if not check_queue_limit(my_id):
        await update.message.reply_text("\u062e\u06cc\u0644\u06cc \u0633\u0631\u06cc\u0639 \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u0645\u06cc\u06a9\u0646\u06cc\u062f! \u06a9\u0645\u06cc \u0635\u0628\u0631 \u06a9\u0646\u06cc\u062f.")
        return
    coins = await get_coins(my_id)
    if coins <= 0:
        await update.message.reply_text("\u0633\u06a9\u0647 \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0631\u06cc!")
        return
    blocked = await db_get("blocks", f"blocker=eq.{my_id}&select=blocked")
    blocked_ids = [b["blocked"] for b in blocked] if blocked else []
    users = await get_smart_matches(my_id, blocked_ids, limit=5)
    if not users:
        all_users = await db_get("users", f"telegram_id=neq.{my_id}&limit=1")
        users = [u for u in all_users if u["telegram_id"] not in blocked_ids]
    if not users:
        await update.message.reply_text("\u0641\u0639\u0644\u0627 \u06a9\u0627\u0631\u0628\u0631 \u062f\u06cc\u06af\u0631\u06cc \u0646\u06cc\u0633\u062a!")
        return
    user = users[0]
    await deduct_coin(my_id)
    vip_badge = "\u2b50 VIP | " if user.get("is_vip") else ""
    voice_badge = get_voice_badge(user)
    text = f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n\u0633\u0646: {user['age']}\n\u0627\u0633\u062a\u0627\u0646: {user['province']}\n\u0634\u0647\u0631: {user['city']}\n\u0639\u0644\u0627\u06cc\u0642: {user['interests']}\n\u0633\u06a9\u0647 \u0628\u0627\u0642\u06cc: {coins-1}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("\u274e \u0628\u0639\u062f\u06cc", callback_data="skip")],
        [InlineKeyboardButton("\U0001f4ac \u0686\u062a", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("\U0001f4e8 \u067e\u06cc\u0627\u0645", callback_data=f"dm_{user['telegram_id']}")],
        [InlineKeyboardButton("\u26d4 \u0628\u0644\u0627\u06a9", callback_data=f"block_{user['telegram_id']}"), InlineKeyboardButton("\u26a0\ufe0f \u06af\u0632\u0627\u0631\u0634", callback_data=f"report_{user['telegram_id']}")]
    ])
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)
    if user.get("has_voice"):
        await send_voice_profile(context.bot, my_id, user, is_matched=False)

async def random_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    users = await db_get("users", f"telegram_id=neq.{my_id}")
    if not users:
        await update.message.reply_text("\u0641\u0639\u0644\u0627 \u06a9\u0627\u0631\u0628\u0631 \u062f\u06cc\u06af\u0631\u06cc \u0646\u06cc\u0633\u062a!")
        return
    user = random.choice(users)
    vip_badge = "\u2b50 VIP | " if user.get("is_vip") else ""
    voice_badge = get_voice_badge(user)
    text = f"{voice_badge}{vip_badge}\u06cc\u06a9 \u0646\u0641\u0631 \u062a\u0635\u0627\u062f\u0641\u06cc!\n\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n\u0633\u0646: {user['age']}\n\u0634\u0647\u0631: {user['city']}\n\u0639\u0644\u0627\u06cc\u0642: {user['interests']}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("\u274e \u062f\u06cc\u06af\u0631\u06cc", callback_data="random_next")],
        [InlineKeyboardButton("\U0001f4ac \u0686\u062a", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("\U0001f4e8 \u067e\u06cc\u0627\u0645", callback_data=f"dm_{user['telegram_id']}")]
    ])
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def same_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    my_profile = await db_get("users", f"telegram_id=eq.{my_id}")
    if not my_profile:
        await update.message.reply_text("\u0627\u0648\u0644 \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0646! /register \u0628\u0632\u0646")
        return
    my_age = my_profile[0]["age"]
    users = await db_get("users", f"telegram_id=neq.{my_id}&age=eq.{my_age}&limit=5")
    if not users:
        await update.message.reply_text(f"\u06a9\u0633\u06cc \u0628\u0627 \u0633\u0646 {my_age} \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f!")
        return
    await update.message.reply_text(f"{len(users)} \u0646\u0641\u0631 \u0647\u0645\u200c\u0633\u0646 \u067e\u06cc\u062f\u0627 \u0634\u062f:")
    for user in users:
        vip_badge = "\u2b50 VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n\u0633\u0646: {user['age']}\n\u0627\u0633\u062a\u0627\u0646: {user['province']}\n\u0634\u0647\u0631: {user['city']}\n\u0639\u0644\u0627\u06cc\u0642: {user['interests']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("\u274e \u0628\u0639\u062f\u06cc", callback_data="skip")],
            [InlineKeyboardButton("\U0001f4ac \u0686\u062a", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("\U0001f4e8 \u067e\u06cc\u0627\u0645", callback_data=f"dm_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)

async def nearby(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["5 km", "10 km"], ["30 km", "60 km"]]
    await update.message.reply_text("\u062a\u0627 \u0686\u0647 \u0641\u0627\u0635\u0644\u0647\u200c\u0627\u06cc\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return NEARBY_DISTANCE

async def nearby_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().replace(" km", "").replace("km", "")
    try:
        context.user_data["nearby_km"] = int(text)
    except:
        context.user_data["nearby_km"] = 10
    location_button = KeyboardButton("\U0001f4cd \u0627\u0631\u0633\u0627\u0644 \u0645\u0648\u0642\u0639\u06cc\u062a", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("\u0645\u0648\u0642\u0639\u06cc\u062a\u062a \u0631\u0648 \u0628\u0641\u0631\u0633\u062a:", reply_markup=keyboard)
    return NEARBY_LOCATION

async def nearby_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.location:
        await update.message.reply_text("\u0644\u0637\u0641\u0627 \u0645\u0648\u0642\u0639\u06cc\u062a \u0628\u0641\u0631\u0633\u062a:")
        return NEARBY_LOCATION
    my_id = update.effective_user.id
    my_lat = update.message.location.latitude
    my_lon = update.message.location.longitude
    max_km = context.user_data.get("nearby_km", 10)
    await update_user_location(my_id, my_lat, my_lon)
    all_users = await db_get("users", f"telegram_id=neq.{my_id}&latitude=not.is.null")
    nearby_users = []
    for user in all_users:
        if user.get("latitude") and user.get("longitude"):
            dist = distance_km(my_lat, my_lon, user["latitude"], user["longitude"])
            if dist <= max_km:
                user["distance"] = round(dist, 1)
                user["distance_bucket"] = get_distance_bucket(dist)
                nearby_users.append(user)
    nearby_users.sort(key=lambda x: x["distance"])
    if not nearby_users:
        await update.message.reply_text(f"\u06a9\u0633\u06cc \u062f\u0631 {max_km} \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631 \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f!", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(f"{len(nearby_users)} \u0646\u0641\u0631 \u062f\u0631 {max_km} \u06a9\u06cc\u0644\u0648\u0645\u062a\u0631 \u067e\u06cc\u062f\u0627 \u0634\u062f:", reply_markup=main_menu())
    for user in nearby_users[:5]:
        vip_badge = "\u2b50 VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n\u0633\u0646: {user['age']}\n\u0634\u0647\u0631: {user['city']}\n\u0639\u0644\u0627\u06cc\u0642: {user['interests']}\n\U0001f4cd \u0641\u0627\u0635\u0644\u0647: {user['distance_bucket']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("\u274e \u0628\u0639\u062f\u06cc", callback_data="skip")],
            [InlineKeyboardButton("\U0001f4ac \u0686\u062a", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("\U0001f4e8 \u067e\u06cc\u0627\u0645", callback_data=f"dm_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["\u067e\u0633\u0631", "\u062f\u062e\u062a\u0631", "\u0647\u0631 \u062f\u0648"]]
    await update.message.reply_text("\u062c\u0646\u0633\u06cc\u062a \u0645\u0648\u0631\u062f \u0646\u0638\u0631\u062a\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_GENDER

async def search_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_gender"] = update.message.text
    keyboard = [["\u0647\u0631 \u0633\u0646\u06cc", "18-25", "26-35"], ["36-45", "46-60"]]
    await update.message.reply_text("\u0628\u0627\u0632\u0647 \u0633\u0646\u06cc\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_AGE

async def search_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_age"] = update.message.text
    keyboard = [["\u062a\u0647\u0631\u0627\u0646", "\u0627\u0635\u0641\u0647\u0627\u0646", "\u0645\u0634\u0647\u062f"], ["\u0634\u06cc\u0631\u0627\u0632", "\u062a\u0628\u0631\u06cc\u0632", "\u0633\u0627\u06cc\u0631"], ["\u0647\u0645\u0647 \u0627\u0633\u062a\u0627\u0646\u200c\u0647\u0627"]]
    await update.message.reply_text("\u0627\u0633\u062a\u0627\u0646\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_PROVINCE

async def search_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    sg = context.user_data.get("search_gender", "")
    sa = context.user_data.get("search_age", "")
    sp = update.message.text
    params = f"telegram_id=neq.{my_id}"
    if sg != "\u0647\u0631 \u062f\u0648":
        params += f"&gender=eq.{sg}"
    if sp != "\u0647\u0645\u0647 \u0627\u0633\u062a\u0627\u0646\u200c\u0647\u0627":
        params += f"&province=eq.{sp}"
    if sa == "18-25":
        params += "&age=gte.18&age=lte.25"
    elif sa == "26-35":
        params += "&age=gte.26&age=lte.35"
    elif sa == "36-45":
        params += "&age=gte.36&age=lte.45"
    elif sa == "46-60":
        params += "&age=gte.46&age=lte.60"
    params += "&limit=5"
    users = await db_get("users", params)
    await update.message.reply_text(f"{len(users)} \u0646\u0641\u0631 \u067e\u06cc\u062f\u0627 \u0634\u062f:", reply_markup=main_menu())
    for user in users:
        vip_badge = "\u2b50 VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n\u0633\u0646: {user['age']}\n\u0627\u0633\u062a\u0627\u0646: {user['province']}\n\u0634\u0647\u0631: {user['city']}\n\u0639\u0644\u0627\u06cc\u0642: {user['interests']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2764\ufe0f \u0644\u0627\u06cc\u06a9", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("\u274e \u0628\u0639\u062f\u06cc", callback_data="skip")],
            [InlineKeyboardButton("\U0001f4ac \u0686\u062a", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("\U0001f4e8 \u067e\u06cc\u0627\u0645", callback_data=f"dm_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["\u0634\u0647\u0631", "\u0639\u0644\u0627\u06cc\u0642"], ["\u0639\u06a9\u0633", "\u0628\u0627\u0632\u06af\u0634\u062a"]]
    await update.message.reply_text("\u0686\u06cc \u0631\u0648 \u0645\u06cc\u062e\u0648\u0627\u06cc \u0648\u06cc\u0631\u0627\u06cc\u0634 \u06a9\u0646\u06cc\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return EDIT_CHOICE

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["edit_field"] = choice
    if choice == "\u0639\u06a9\u0633":
        await update.message.reply_text("\u0639\u06a9\u0633 \u062c\u062f\u06cc\u062f \u0628\u0641\u0631\u0633\u062a:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif choice == "\u0628\u0627\u0632\u06af\u0634\u062a":
        await update.message.reply_text("\u0644\u063a\u0648 \u0634\u062f.", reply_markup=main_menu())
        return ConversationHandler.END
    elif choice == "\u0634\u0647\u0631":
        await update.message.reply_text("\u0634\u0647\u0631 \u062c\u062f\u06cc\u062f \u0628\u0646\u0648\u06cc\u0633:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif choice == "\u0639\u0644\u0627\u06cc\u0642":
        keyboard = [["\u0645\u0648\u0633\u06cc\u0642\u06cc", "\u0647\u0646\u0631", "\u06a9\u062a\u0627\u0628"], ["\u0648\u0631\u0632\u0634", "\u0628\u0627\u0632\u06cc", "\u063a\u0630\u0627"], ["\u0633\u0641\u0631", "\u0641\u06cc\u0644\u0645", "\u062a\u06a9\u0646\u0648\u0644\u0648\u0698\u06cc"]]
        await update.message.reply_text("\u0639\u0644\u0627\u06cc\u0642 \u062c\u062f\u06cc\u062f:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return EDIT_VALUE

async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    field = context.user_data.get("edit_field")
    if field == "\u0639\u06a9\u0633":
        if not update.message.photo:
            await update.message.reply_text("\u0644\u0637\u0641\u0627 \u0639\u06a9\u0633 \u0628\u0641\u0631\u0633\u062a:")
            return EDIT_VALUE
        photo_id = update.message.photo[-1].file_id
        await db_patch("users", f"telegram_id=eq.{my_id}", {"photo_id": photo_id})
    elif field == "\u0634\u0647\u0631":
        await db_patch("users", f"telegram_id=eq.{my_id}", {"city": update.message.text})
    elif field == "\u0639\u0644\u0627\u06cc\u0642":
        await db_patch("users", f"telegram_id=eq.{my_id}", {"interests": update.message.text})
    await update.message.reply_text("\u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0628\u0647\u200c\u0631\u0648\u0632 \u0634\u062f!", reply_markup=main_menu())
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    users = await db_get("users", f"telegram_id=eq.{my_id}")
    if not users:
        await update.message.reply_text("\u0647\u0646\u0648\u0632 \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0646\u06a9\u0631\u062f\u06cc! /register \u0628\u0632\u0646")
        return
    user = users[0]
    coins = await get_coins(my_id)
    trust = await get_trust(my_id)
    trust_score = trust.get("trust_score", 50)
    vip_badge = "\u2b50 VIP\n" if user.get("is_vip") else ""
    voice_info = ""
    if user.get("has_voice"):
        mode = user.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        voice_info = f"{label}\n"
    text = (
        f"{vip_badge}{voice_info}\u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0645\u0646:\n"
        f"\u062c\u0646\u0633\u06cc\u062a: {user['gender']}\n"
        f"\u0633\u0646: {user['age']}\n"
        f"\u0627\u0633\u062a\u0627\u0646: {user['province']}\n"
        f"\u0634\u0647\u0631: {user['city']}\n"
        f"\u0639\u0644\u0627\u06cc\u0642: {user['interests']}\n"
        f"\u0633\u06a9\u0647: {coins}\n"
        f"\u0627\u0645\u062a\u06cc\u0627\u0632 \u0627\u0639\u062a\u0645\u0627\u062f: {trust_score}/100"
    )
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text)
    else:
        await update.message.reply_text(text)

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{my_id}"
    await update.message.reply_text(f"\u0644\u06cc\u0646\u06a9 \u062f\u0639\u0648\u062a \u0634\u0645\u0627:\n{link}\n\n\u0628\u0647 \u0627\u0632\u0627\u06cc \u0647\u0631 \u062f\u0648\u0633\u062a 5 \u0633\u06a9\u0647 \u0647\u062f\u06cc\u0647 \u0645\u06cc\u06af\u06cc\u0631\u06cc\u062f!")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["\u067e\u0633\u0631", "\u062f\u062e\u062a\u0631"]]
    await update.message.reply_text("\u062c\u0646\u0633\u06cc\u062a \u0634\u0645\u0627\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    await update.message.reply_text("\u0633\u0646 \u0634\u0645\u0627\u061f \u062d\u062f\u0627\u0642\u0644 18", reply_markup=ReplyKeyboardRemove())
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 18:
        await update.message.reply_text("\u0633\u0646 \u0628\u0627\u06cc\u062f \u062d\u062f\u0627\u0642\u0644 18 \u0628\u0627\u0634\u0647:")
        return AGE
    context.user_data["age"] = int(text)
    keyboard = [["\u062a\u0647\u0631\u0627\u0646", "\u0627\u0635\u0641\u0647\u0627\u0646", "\u0645\u0634\u0647\u062f"], ["\u0634\u06cc\u0631\u0627\u0632", "\u062a\u0628\u0631\u06cc\u0632", "\u0627\u0647\u0648\u0627\u0632"], ["\u0633\u0627\u06cc\u0631"]]
    await update.message.reply_text("\u0627\u0633\u062a\u0627\u0646 \u0634\u0645\u0627\u061f", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return PROVINCE

async def province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["province"] = update.message.text
    await update.message.reply_text("\u0634\u0647\u0631 \u0634\u0645\u0627\u061f", reply_markup=ReplyKeyboardRemove())
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    keyboard = [["\u0645\u0648\u0633\u06cc\u0642\u06cc", "\u0647\u0646\u0631", "\u06a9\u062a\u0627\u0628"], ["\u0648\u0631\u0632\u0634", "\u0628\u0627\u0632\u06cc", "\u063a\u0630\u0627"], ["\u0633\u0641\u0631", "\u0641\u06cc\u0644\u0645", "\u062a\u06a9\u0646\u0648\u0644\u0648\u0698\u06cc"]]
    await update.message.reply_text("\u0639\u0644\u0627\u06cc\u0642\u062a \u0631\u0648 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return INTERESTS

async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["interests"] = update.message.text
    await update.message.reply_text("\u0639\u06a9\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644\u062a \u0631\u0648 \u0628\u0641\u0631\u0633\u062a:", reply_markup=ReplyKeyboardRemove())
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("\u0644\u0637\u0641\u0627 \u06cc\u06a9 \u0639\u06a9\u0633 \u0628\u0641\u0631\u0633\u062a:")
        return PHOTO
    photo_id = update.message.photo[-1].file_id
    data = context.user_data
    await db_post("users", {
        "telegram_id": update.effective_user.id,
        "gender": data["gender"],
        "age": data["age"],
        "province": data["province"],
        "city": data["city"],
        "interests": data["interests"],
        "photo_id": photo_id,
        "coins": 10,
        "is_vip": False,
        "trust_score": 50,
        "trust_level": "normal",
        "shadowban_level": 0,
        "has_voice": False
    })
    await update.message.reply_text("\u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0627\u0645\u0644 \u0634\u062f! 10 \u0633\u06a9\u0647 \u0647\u062f\u06cc\u0647 \u06af\u0631\u0641\u062a\u06cc!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\u0644\u063a\u0648 \u0634\u062f.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    TOKEN = "8992632783:AAEyc2COdSjBC3cWlSVvY-oG6AZMAcW3nq4"
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, province)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, interests)],
            PHOTO: [MessageHandler(filters.PHOTO, photo), MessageHandler(filters.TEXT & ~filters.COMMAND, photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    search_conv = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            SEARCH_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_gender)],
            SEARCH_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_age)],
            SEARCH_PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_province)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_profile)],
        states={
            EDIT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_choice)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value), MessageHandler(filters.PHOTO, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    nearby_conv = ConversationHandler(
        entry_points=[CommandHandler("nearby", nearby)],
        states={
            NEARBY_DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nearby_distance)],
            NEARBY_LOCATION: [MessageHandler(filters.LOCATION, nearby_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    recent_conv = ConversationHandler(
        entry_points=[CommandHandler("recent", recent_chats)],
        states={
            RECENT_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, recent_gender)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dm_conv = ConversationHandler(
        entry_points=[],
        states={
            DM_WRITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_dm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    voice_conv = ConversationHandler(
        entry_points=[],
        states={
            VOICE_UPLOAD: [MessageHandler(filters.VOICE, handle_voice_upload)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("browse", browse))
    app.add_handler(CommandHandler("random", random_user))
    app.add_handler(CommandHandler("coins", coins_cmd))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(CommandHandler("sameage", same_age))
    app.add_handler(CommandHandler("endchat", end_chat_cmd))
    app.add_handler(conv)
    app.add_handler(search_conv)
    app.add_handler(edit_conv)
    app.add_handler(nearby_conv)
    app.add_handler(recent_conv)
    app.add_handler(dm_conv)
    app.add_handler(voice_conv)
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.PHOTO, forward_media))
    app.add_handler(MessageHandler(filters.VIDEO, forward_media))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_in_chat))
    app.add_handler(MessageHandler(filters.AUDIO, forward_media))
    app.add_handler(MessageHandler(filters.Sticker.ALL, forward_media))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, forward_media))
    app.add_handler(MessageHandler(filters.Document.ALL, forward_media))
    app.add_handler(MessageHandler(filters.ANIMATION, forward_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    print("\u0631\u0628\u0627\u062a \u0634\u0631\u0648\u0639 \u0628\u0647 \u06a9\u0627\u0631 \u06a9\u0631\u062f...")
    app.run_polling()

if __name__ == "__main__":
    main()
