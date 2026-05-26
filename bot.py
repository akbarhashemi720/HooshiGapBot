from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
import httpx
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
        await update.message.reply_text("دسترسی ندارید!")
        return
    total = len(await db_get("users", ""))
    vip_count = len(await db_get("users", "is_vip=eq.true"))
    voice_count = len(await db_get("users", "has_voice=eq.true"))
    reports = len(await db_get("reports", ""))
    blocks = len(await db_get("blocks", ""))
    text = (
        f"📊 پنل ادمین\n"
        f"━━━━━━━━\n"
        f"👥 کل کاربران: {total}\n"
        f"⭐ کاربران VIP: {vip_count}\n"
        f"🎤 دارای ویس: {voice_count}\n"
        f"⚠️ گزارش‌ها: {reports}\n"
        f"⛔ بلاک‌ها: {blocks}\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("⚠️ گزارش‌ها", callback_data="admin_reports")],
        [InlineKeyboardButton("🚫 بن کاربر", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ آنبن کاربر", callback_data="admin_unban")],
        [InlineKeyboardButton("💰 اضافه کردن سکه", callback_data="admin_coins")],
        [InlineKeyboardButton("📢 پیام به همه", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔍 جزئیات کاربر", callback_data="admin_detail")],
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
                    await context.bot.send_message(chat_id=referrer_id, text="یک نفر جدید وارد شد! 5 سکه گرفتید!")
                except:
                    pass
    existing = await db_get("users", f"telegram_id=eq.{my_id}")
    if existing:
        await update.message.reply_text("خوش برگشتی به هوشی گپ!", reply_markup=main_menu())
    else:
        await update.message.reply_text("سلام! به هوشی گپ خوش اومدی!\n/register بزن", reply_markup=ReplyKeyboardRemove())

async def voice_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    voice = await get_voice_profile(my_id)
    if voice:
        mode = voice.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 پخش ویس", callback_data="play_my_voice")],
            [InlineKeyboardButton("♻️ جایگزینی ویس", callback_data="replace_voice")],
            [InlineKeyboardButton("🔒 تغییر حریم خصوصی", callback_data="change_voice_mode")],
            [InlineKeyboardButton("❌ حذف ویس", callback_data="delete_voice")]
        ])
        await update.message.reply_text(
            f"🎤 ویس پروفایل فعاله!\nمدت: {voice.get('voice_duration', 0)} ثانیه\nحالت: {label}",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 اضافه کردن ویس پروفایل", callback_data="add_voice")]
        ])
        await update.message.reply_text(
            "🎤 ویس پروفایل نداری!\n\nبا اضافه کردن ویس:\n✅ امتیاز اعتماد +5\n✅ دیده شدن بیشتر\n✅ مچ بهتر",
            reply_markup=keyboard
        )

async def handle_voice_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if not update.message.voice:
        await update.message.reply_text("لطفا ویس بفرستید!", reply_markup=main_menu())
        return ConversationHandler.END
    voice = update.message.voice
    context.user_data["temp_voice_id"] = voice.file_id
    context.user_data["temp_voice_duration"] = voice.duration
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎤 ویس واقعی", callback_data="vmode_real")],
        [InlineKeyboardButton("🔧 ویس تغییریافته", callback_data="vmode_modified")],
        [InlineKeyboardButton("🔒 پنهان تا مچ", callback_data="vmode_hidden")]
    ])
    await update.message.reply_text("ویست دریافت شد!\nچطور نمایش داده بشه؟", reply_markup=keyboard)
    return ConversationHandler.END

async def send_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_id = context.user_data.get("dm_to")
    if not to_id:
        await update.message.reply_text("خطای فنی!", reply_markup=main_menu())
        return ConversationHandler.END
    from_id = update.effective_user.id
    message_text = update.message.text
    if not check_rate_limit(from_id):
        await update.message.reply_text("پیام ها رو کمتر بفرستید!")
        return ConversationHandler.END
    result_analysis = await analyze_message(from_id, message_text)
    if result_analysis == "toxic":
        await update.message.reply_text("پیام شما نامناسب بود و ارسال نشد!", reply_markup=main_menu())
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
        vip_badge = "⭐ VIP | " if u.get("is_vip") else ""
        voice_badge = get_voice_badge(u)
        if is_paid:
            notif = (
                f"📨 پیام خصوصی جدید!\n"
                f"{voice_badge}{vip_badge}جنسیت: {u['gender']} | سن: {u['age']} | شهر: {u['city']}\n\n"
                f"برای خواندن پیام روی دکمه زیر بزنید:"
            )
        else:
            notif = (
                f"📨 پیام خصوصی جدید!\n"
                f"{voice_badge}{vip_badge}جنسیت: {u['gender']} | سن: {u['age']} | شهر: {u['city']}\n\n"
                f"⚠️ فرستنده سکه کافی نداشت!\n"
                f"برای خواندن پیام، 1 سکه از شما کسر میشود:"
            )
        if msg_id:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("📩 خواندن پیام", callback_data=f"readdm_{msg_id}_{from_id}_{is_paid}")
            ]])
            try:
                if u.get("photo_id"):
                    await context.bot.send_photo(chat_id=to_id, photo=u["photo_id"], caption=notif, reply_markup=kb)
                else:
                    await context.bot.send_message(chat_id=to_id, text=notif, reply_markup=kb)
            except:
                pass
    await update.message.reply_text("✅ پیام ارسال شد!", reply_markup=main_menu())
    return ConversationHandler.END

async def coins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    coins = await get_coins(my_id)
    vip = await is_vip(my_id)
    vip_text = "⭐ VIP فعال" if vip else "VIP ندارید"
    text = (
        f"💰 کیف پول شما\n"
        f"سکه: {coins} عدد\n"
        f"وضعیت: {vip_text}\n\n"
        f"روش‌های دریافت سکه:\n\n"
        f"1 - معرفی دوستان - رایگان\n"
        f"2 - خرید سکه - به زودی\n"
        f"3 - خرید VIP - امکانات ویژه"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 معرفی دوستان (رایگان)", callback_data="coins_invite")],
        [InlineKeyboardButton("💳 خرید سکه (به زودی)", callback_data="coins_buy")],
        [InlineKeyboardButton("⭐ خرید VIP (به زودی)", callback_data="coins_vip")]
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
        await update.message.reply_text("چت پایان یافت!", reply_markup=main_menu())
        try:
            await context.bot.send_message(chat_id=partner_id, text="طرف مقابل چت را پایان داد.", reply_markup=main_menu())
        except:
            pass
    else:
        await update.message.reply_text("چت فعالی نداری!", reply_markup=main_menu())

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
    keyboard = [["پسر", "دختر", "همه"]]
    await update.message.reply_text("چت‌های اخیر با چه جنسیتی؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return RECENT_GENDER

async def recent_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    gender_filter = update.message.text
    history1 = await db_get("chat_history", f"user1=eq.{my_id}")
    history2 = await db_get("chat_history", f"user2=eq.{my_id}")
    partner_ids = [h["user2"] for h in history1] + [h["user1"] for h in history2]
    if not partner_ids:
        await update.message.reply_text("هنوز چتی نداشتی!", reply_markup=main_menu())
        return ConversationHandler.END
    found = []
    for pid in partner_ids:
        users = await db_get("users", f"telegram_id=eq.{pid}")
        if users:
            u = users[0]
            if gender_filter == "همه" or u.get("gender") == gender_filter:
                found.append(u)
    if not found:
        await update.message.reply_text("کسی پیدا نشد!", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(f"{len(found)} نفر پیدا شد:", reply_markup=main_menu())
    for user in found[:10]:
        vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}آیدی: {user['telegram_id']}\nجنسیت: {user['gender']}\nسن: {user['age']}\nشهر: {user['city']}\nعلایق: {user['interests']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if my_id not in ADMIN_IDS:
        return False
    action = context.user_data.get("admin_action")
    if not action:
        return False
    text = update.message.text.strip()
    if action == "ban":
        try:
            user_id = int(text)
            await db_patch("users", f"telegram_id=eq.{user_id}", {"is_banned": True, "shadowban_level": 3})
            await update.message.reply_text(f"✅ کاربر {user_id} بن شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="⛔ حساب شما توسط ادمین مسدود شده است.")
            except:
                pass
        except:
            await update.message.reply_text("آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "unban":
        try:
            user_id = int(text)
            await db_patch("users", f"telegram_id=eq.{user_id}", {"is_banned": False, "shadowban_level": 0})
            await update.message.reply_text(f"✅ کاربر {user_id} آنبن شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="✅ حساب شما رفع مسدودیت شد.")
            except:
                pass
        except:
            await update.message.reply_text("آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "coins":
        try:
            user_id = int(text)
            context.user_data["admin_coins_target"] = user_id
            context.user_data["admin_action"] = "coins_amount"
            await update.message.reply_text("چند سکه اضافه کنم؟")
        except:
            await update.message.reply_text("آیدی نامعتبر!", reply_markup=main_menu())
            context.user_data["admin_action"] = None
        return True
    elif action == "coins_amount":
        try:
            amount = int(text)
            target_id = context.user_data.get("admin_coins_target")
            await add_coins(target_id, amount)
            await update.message.reply_text(f"✅ {amount} سکه به کاربر {target_id} اضافه شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=target_id, text=f"💰 {amount} سکه توسط ادمین به حساب شما اضافه شد!")
            except:
                pass
        except:
            await update.message.reply_text("عدد نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "broadcast":
        users = await db_get("users", "select=telegram_id")
        sent = 0
        failed = 0
        for u in users:
            try:
                await context.bot.send_message(chat_id=u["telegram_id"], text=f"📢 پیام از ادمین:\n\n{text}")
                sent += 1
            except:
                failed += 1
        await update.message.reply_text(f"✅ پیام ارسال شد!\nموفق: {sent}\nناموفق: {failed}", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "detail":
        try:
            user_id = int(text)
            users = await db_get("users", f"telegram_id=eq.{user_id}")
            if not users:
                await update.message.reply_text("کاربر پیدا نشد!", reply_markup=main_menu())
            else:
                u = users[0]
                coins = await get_coins(user_id)
                trust = await get_trust(user_id)
                detail_text = (
                    f"🔍 جزئیات کاربر:\n"
                    f"━━━━━━━━\n"
                    f"آیدی: {u['telegram_id']}\n"
                    f"جنسیت: {u.get('gender', '-')}\n"
                    f"سن: {u.get('age', '-')}\n"
                    f"استان: {u.get('province', '-')}\n"
                    f"شهر: {u.get('city', '-')}\n"
                    f"علایق: {u.get('interests', '-')}\n"
                    f"سکه: {coins}\n"
                    f"VIP: {'✅' if u.get('is_vip') else '❌'}\n"
                    f"بن: {'✅' if u.get('is_banned') else '❌'}\n"
                    f"امتیاز اعتماد: {trust.get('trust_score', 50)}\n"
                    f"shadowban: {u.get('shadowban_level', 0)}\n"
                )
                await update.message.reply_text(detail_text, reply_markup=main_menu())
        except:
            await update.message.reply_text("آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    return False

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    my_id = update.effective_user.id

    if "پایان دادن چت" in text:
        await end_chat_cmd(update, context)
        return

    if my_id in active_chats:
        partner_id = active_chats[my_id]
        if not check_rate_limit(my_id):
            await update.message.reply_text("پیام ها رو کمتر بفرستید!")
            return
        result = await analyze_message(my_id, text)
        if result == "toxic":
            await update.message.reply_text("پیام نامناسب ارسال نشد!")
            return
        try:
            await context.bot.send_message(chat_id=partner_id, text=text)
        except:
            pass
        return

    if "مرور پروفایل" in text:
        await browse(update, context)
    elif "جستجو" in text:
        await search(update, context)
        return SEARCH_GENDER
    elif "اتصال تصادفی" in text:
        await random_user(update, context)
    elif "پروفایل من" in text:
        await profile(update, context)
    elif "کیف پول" in text:
        await coins_cmd(update, context)
    elif "دعوت" in text:
        await invite(update, context)
    elif "ویرایش" in text:
        await edit_profile(update, context)
        return EDIT_CHOICE
    elif "هم‌سن" in text:
        await same_age(update, context)
    elif "نزدیک" in text:
        await nearby(update, context)
        return NEARBY_DISTANCE
    elif "چت‌های اخیر" in text:
        await recent_chats(update, context)
        return RECENT_GENDER
    elif "ویس پروفایل" in text:
        await voice_profile_menu(update, context)

async def smart_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    handled = await handle_admin_text(update, context)
    if not handled:
        await menu_handler(update, context)

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_users":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        users = await db_get("users", "limit=10&order=id.desc")
        text = "👥 آخرین کاربران:\n\n"
        for u in users:
            text += f"آیدی: {u['telegram_id']} | {u.get('gender','')} | {u.get('city','')}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data == "admin_reports":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        reports = await db_get("reports", "limit=10&order=id.desc")
        text = "⚠️ آخرین گزارش‌ها:\n\n"
        for r in reports:
            text += f"گزارش‌دهنده: {r['reporter']} | گزارش‌شده: {r['reported']}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data == "admin_ban":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="آیدی عددی کاربری که میخوای بن کنی رو بفرست:")
        context.user_data["admin_action"] = "ban"
        return

    if query.data == "admin_unban":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="آیدی عددی کاربری که میخوای آنبن کنی رو بفرست:")
        context.user_data["admin_action"] = "unban"
        return

    if query.data == "admin_coins":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="آیدی عددی کاربری که میخوای سکه بدی رو بفرست:")
        context.user_data["admin_action"] = "coins"
        return

    if query.data == "admin_broadcast":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="پیامی که میخوای به همه بفرستی رو بنویس:")
        context.user_data["admin_action"] = "broadcast"
        return

    if query.data == "admin_detail":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="آیدی عددی کاربر مورد نظر رو بفرست:")
        context.user_data["admin_action"] = "detail"
        return

    if query.data.startswith("vmode_"):
        mode = query.data.replace("vmode_", "")
        from_id = update.effective_user.id
        file_id = context.user_data.get("temp_voice_id")
        duration = context.user_data.get("temp_voice_duration", 0)
        if not file_id:
            await context.bot.send_message(chat_id=from_id, text="خطا! دوباره ویس بفرستید.", reply_markup=main_menu())
            return
        await context.bot.send_message(chat_id=from_id, text="در حال پردازش ویس...")
        success, msg = await save_voice_profile(from_id, file_id, duration, mode, bot=context.bot)
        await context.bot.send_message(chat_id=from_id, text=msg, reply_markup=main_menu())
        return

    if query.data == "change_voice_mode":
        from_id = update.effective_user.id
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 ویس واقعی", callback_data="setmode_real")],
            [InlineKeyboardButton("🔧 ویس تغییریافته", callback_data="setmode_modified")],
            [InlineKeyboardButton("🔒 پنهان تا مچ", callback_data="setmode_hidden")]
        ])
        await context.bot.send_message(chat_id=from_id, text="حالت جدید رو انتخاب کن:", reply_markup=keyboard)
        return

    if query.data.startswith("setmode_"):
        mode = query.data.replace("setmode_", "")
        from_id = update.effective_user.id
        await db_patch("users", f"telegram_id=eq.{from_id}", {"voice_mode": mode})
        label = get_voice_label(mode)
        await context.bot.send_message(chat_id=from_id, text=f"✅ حالت ویس تغییر کرد: {label}", reply_markup=main_menu())
        return

    if query.data == "add_voice" or query.data == "replace_voice":
        from_id = update.effective_user.id
        await context.bot.send_message(
            chat_id=from_id,
            text="🎤 یک ویس بین 10 تا 30 ثانیه بفرست:",
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
        await context.bot.send_message(chat_id=my_id, text=f"لینک دعوت:\n{link}\n\nبه ازای هر دوست 5 سکه هدیه میگیرید!")
        return

    if query.data == "coins_buy":
        await context.bot.send_message(chat_id=update.effective_user.id, text="خرید سکه به زودی فعال میشود!")
        return

    if query.data == "coins_vip":
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "⭐ امکانات VIP:\n\n"
                "1 - اول لیست جستجوها\n"
                "2 - نشان VIP روی پروفایل\n"
                "3 - درخواست چت به 10 نفر\n"
                "4 - پیام دایرکت به 10 نفر\n\n"
                "به زودی فعال میشود!"
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
            await query.answer("پیام پیدا نشد!", show_alert=True)
            return
        msg = msgs[0]
        if not is_paid:
            to_coins = await get_coins(to_id)
            if to_coins <= 0:
                await query.answer("سکه کافی ندارید!", show_alert=True)
                return
            await deduct_coin(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        dm_text = msg.get("message", "")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 پاسخ دادن", callback_data=f"chatreq_{from_id}"),
            InlineKeyboardButton("❤️ لایک", callback_data=f"like_{from_id}")
        ]])
        await context.bot.send_message(
            chat_id=to_id,
            text=f"📩 پیام خصوصی:\n\n\"{dm_text}\"",
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
        await context.bot.send_message(chat_id=from_id, text="کاربر بلاک شد.")
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
        await context.bot.send_message(chat_id=from_id, text="گزارش ثبت شد!")
        return

    if query.data.startswith("chatreq_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        my_profile = await db_get("users", f"telegram_id=eq.{from_id}")
        if my_profile:
            u = my_profile[0]
            vip_badge = "⭐ VIP | " if u.get("is_vip") else ""
            voice_badge = get_voice_badge(u)
            text = f"{voice_badge}{vip_badge}درخواست چت!\nجنسیت: {u['gender']}\nسن: {u['age']}\nشهر: {u['city']}\nعلایق: {u['interests']}"
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ قبول", callback_data=f"accept_{from_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{from_id}")
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
        await context.bot.send_message(chat_id=from_id, text="درخواست چت فرستاده شد!")
        return

    if query.data.startswith("dm_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        context.user_data["dm_to"] = to_id
        await context.bot.send_message(
            chat_id=from_id,
            text="📨 پیام خصوصیت رو بنویس:",
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
        await context.bot.send_message(chat_id=to_id, text="چت شروع شد!", reply_markup=chat_menu())
        await context.bot.send_message(chat_id=from_id, text="درخواست قبول شد!", reply_markup=chat_menu())
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
        await context.bot.send_message(chat_id=from_id, text="درخواست چت شما رد شد.")
        return

    to_id = int(query.data.split("_")[1])
    from_id = update.effective_user.id
    await db_post("likes", {"from_user": from_id, "to_user": to_id})
    likes = await db_get("likes", f"from_user=eq.{to_id}&to_user=eq.{from_id}")
    if likes:
        await context.bot.send_message(chat_id=from_id, text="ماتچ شدید!")
        try:
            await context.bot.send_message(chat_id=to_id, text="ماتچ شدید!")
        except:
            pass
    else:
        await context.bot.send_message(chat_id=from_id, text="لایک ثبت شد!")
        try:
            await context.bot.send_message(chat_id=to_id, text="یک نفر به پروفایلت علاقه نشون داد!")
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
                [InlineKeyboardButton("🎤 ویس واقعی", callback_data="vmode_real")],
                [InlineKeyboardButton("🔧 ویس تغییریافته", callback_data="vmode_modified")],
                [InlineKeyboardButton("🔒 پنهان تا مچ", callback_data="vmode_hidden")]
            ])
            await update.message.reply_text("ویست دریافت شد!\nچطور نمایش داده بشه؟", reply_markup=keyboard)
            context.user_data["waiting_voice"] = False
            return
    await forward_media(update, context)

async def browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if not check_queue_limit(my_id):
        await update.message.reply_text("خیلی سریع استفاده میکنید! کمی صبر کنید.")
        return
    coins = await get_coins(my_id)
    if coins <= 0:
        await update.message.reply_text("سکه کافی نداری!")
        return
    blocked = await db_get("blocks", f"blocker=eq.{my_id}&select=blocked")
    blocked_ids = [b["blocked"] for b in blocked] if blocked else []
    users = await get_smart_matches(my_id, blocked_ids, limit=5)
    if not users:
        all_users = await db_get("users", f"telegram_id=neq.{my_id}&limit=1")
        users = [u for u in all_users if u["telegram_id"] not in blocked_ids]
    if not users:
        await update.message.reply_text("فعلا کاربر دیگری نیست!")
        return
    user = users[0]
    await deduct_coin(my_id)
    vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
    voice_badge = get_voice_badge(user)
    text = f"{voice_badge}{vip_badge}آیدی: {user['telegram_id']}\nجنسیت: {user['gender']}\nسن: {user['age']}\nاستان: {user['province']}\nشهر: {user['city']}\nعلایق: {user['interests']}\nسکه باقی: {coins-1}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("✖ بعدی", callback_data="skip")],
        [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user['telegram_id']}")],
        [InlineKeyboardButton("⛔ بلاک", callback_data=f"block_{user['telegram_id']}"), InlineKeyboardButton("⚠️ گزارش", callback_data=f"report_{user['telegram_id']}")]
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
        await update.message.reply_text("فعلا کاربر دیگری نیست!")
        return
    user = random.choice(users)
    vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
    voice_badge = get_voice_badge(user)
    text = f"{voice_badge}{vip_badge}آیدی: {user['telegram_id']}\nیک نفر تصادفی!\nجنسیت: {user['gender']}\nسن: {user['age']}\nشهر: {user['city']}\nعلایق: {user['interests']}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("✖ دیگری", callback_data="random_next")],
        [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user['telegram_id']}")]
    ])
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def same_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    my_profile = await db_get("users", f"telegram_id=eq.{my_id}")
    if not my_profile:
        await update.message.reply_text("اول ثبت‌نام کن! /register بزن")
        return
    my_age = my_profile[0]["age"]
    users = await db_get("users", f"telegram_id=neq.{my_id}&age=eq.{my_age}&limit=5")
    if not users:
        await update.message.reply_text(f"کسی با سن {my_age} پیدا نشد!")
        return
    await update.message.reply_text(f"{len(users)} نفر هم‌سن پیدا شد:")
    for user in users:
        vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}آیدی: {user['telegram_id']}\nجنسیت: {user['gender']}\nسن: {user['age']}\nاستان: {user['province']}\nشهر: {user['city']}\nعلایق: {user['interests']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("✖ بعدی", callback_data="skip")],
            [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)

async def nearby(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["5 km", "10 km"], ["30 km", "60 km"]]
    await update.message.reply_text("تا چه فاصله‌ای؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return NEARBY_DISTANCE

async def nearby_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().replace(" km", "").replace("km", "").strip()
    try:
        context.user_data["nearby_km"] = int(text)
    except:
        context.user_data["nearby_km"] = 10
    location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("موقعیتت رو بفرست:", reply_markup=keyboard)
    return NEARBY_LOCATION

async def nearby_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.location:
        await update.message.reply_text("لطفا موقعیت بفرست:")
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
        await update.message.reply_text(f"کسی در {max_km} کیلومتر پیدا نشد!", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(f"{len(nearby_users)} نفر در {max_km} کیلومتر پیدا شد:", reply_markup=main_menu())
    for user in nearby_users[:5]:
        vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}آیدی: {user['telegram_id']}\nجنسیت: {user['gender']}\nسن: {user['age']}\nشهر: {user['city']}\nعلایق: {user['interests']}\n📍 فاصله: {user['distance_bucket']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("✖ بعدی", callback_data="skip")],
            [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["پسر", "دختر", "هر دو"]]
    await update.message.reply_text("جنسیت مورد نظرت؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_GENDER

async def search_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_gender"] = update.message.text
    keyboard = [["هر سنی", "18-25", "26-35"], ["36-45", "46-60"]]
    await update.message.reply_text("بازه سنی؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_AGE

async def search_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_age"] = update.message.text
    keyboard = [["تهران", "اصفهان", "مشهد"], ["شیراز", "تبریز", "سایر"], ["همه استان‌ها"]]
    await update.message.reply_text("استان؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_PROVINCE

async def search_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    sg = context.user_data.get("search_gender", "")
    sa = context.user_data.get("search_age", "")
    sp = update.message.text
    params = f"telegram_id=neq.{my_id}"
    if sg != "هر دو":
        params += f"&gender=eq.{sg}"
    if sp != "همه استان‌ها":
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
    await update.message.reply_text(f"{len(users)} نفر پیدا شد:", reply_markup=main_menu())
    for user in users:
        vip_badge = "⭐ VIP | " if user.get("is_vip") else ""
        voice_badge = get_voice_badge(user)
        text = f"{voice_badge}{vip_badge}آیدی: {user['telegram_id']}\nجنسیت: {user['gender']}\nسن: {user['age']}\nاستان: {user['province']}\nشهر: {user['city']}\nعلایق: {user['interests']}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ لایک", callback_data=f"like_{user['telegram_id']}"), InlineKeyboardButton("✖ بعدی", callback_data="skip")],
            [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user['telegram_id']}"), InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user['telegram_id']}")]
        ])
        if user.get("photo_id"):
            await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["شهر", "علایق"], ["عکس", "بازگشت"]]
    await update.message.reply_text("چی رو میخوای ویرایش کنی؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return EDIT_CHOICE

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["edit_field"] = choice
    if choice == "عکس":
        await update.message.reply_text("عکس جدید بفرست:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif choice == "بازگشت":
        await update.message.reply_text("لغو شد.", reply_markup=main_menu())
        return ConversationHandler.END
    elif choice == "شهر":
        await update.message.reply_text("شهر جدید بنویس:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif choice == "علایق":
        keyboard = [["موسیقی", "هنر", "کتاب"], ["ورزش", "بازی", "غذا"], ["سفر", "فیلم", "تکنولوژی"]]
        await update.message.reply_text("علایق جدید رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return EDIT_VALUE
    else:
        await update.message.reply_text("گزینه نامعتبر!", reply_markup=main_menu())
        return ConversationHandler.END

async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    field = context.user_data.get("edit_field")
    if field == "عکس":
        if not update.message.photo:
            await update.message.reply_text("لطفا عکس بفرست:")
            return EDIT_VALUE
        photo_id = update.message.photo[-1].file_id
        await db_patch("users", f"telegram_id=eq.{my_id}", {"photo_id": photo_id})
    elif field == "شهر":
        await db_patch("users", f"telegram_id=eq.{my_id}", {"city": update.message.text})
    elif field == "علایق":
        await db_patch("users", f"telegram_id=eq.{my_id}", {"interests": update.message.text})
    await update.message.reply_text("✅ پروفایل به‌روز شد!", reply_markup=main_menu())
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    users = await db_get("users", f"telegram_id=eq.{my_id}")
    if not users:
        await update.message.reply_text("هنوز ثبت‌نام نکردی! /register بزن")
        return
    user = users[0]
    coins = await get_coins(my_id)
    trust = await get_trust(my_id)
    trust_score = trust.get("trust_score", 50)
    vip_badge = "⭐ VIP\n" if user.get("is_vip") else ""
    voice_info = ""
    if user.get("has_voice"):
        mode = user.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        voice_info = f"{label}\n"
    text = (
        f"{vip_badge}{voice_info}پروفایل من:\n"
        f"آیدی: {my_id}\n"
        f"جنسیت: {user['gender']}\n"
        f"سن: {user['age']}\n"
        f"استان: {user['province']}\n"
        f"شهر: {user['city']}\n"
        f"علایق: {user['interests']}\n"
        f"سکه: {coins}\n"
        f"امتیاز اعتماد: {trust_score}/100"
    )
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text)
    else:
        await update.message.reply_text(text)

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{my_id}"
    await update.message.reply_text(f"لینک دعوت شما:\n{link}\n\nبه ازای هر دوست 5 سکه هدیه میگیرید!")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["پسر", "دختر"]]
    await update.message.reply_text("جنسیت شما؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    await update.message.reply_text("سن شما؟ حداقل 18", reply_markup=ReplyKeyboardRemove())
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 18:
        await update.message.reply_text("سن باید حداقل 18 باشه:")
        return AGE
    context.user_data["age"] = int(text)
    keyboard = [["تهران", "اصفهان", "مشهد"], ["شیراز", "تبریز", "اهواز"], ["سایر"]]
    await update.message.reply_text("استان شما؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return PROVINCE

async def province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["province"] = update.message.text
    await update.message.reply_text("شهر شما؟", reply_markup=ReplyKeyboardRemove())
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    keyboard = [["موسیقی", "هنر", "کتاب"], ["ورزش", "بازی", "غذا"], ["سفر", "فیلم", "تکنولوژی"]]
    await update.message.reply_text("علایقت رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return INTERESTS

async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["interests"] = update.message.text
    await update.message.reply_text("عکس پروفایلت رو بفرست:", reply_markup=ReplyKeyboardRemove())
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("لطفا یک عکس بفرست:")
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
        "is_banned": False,
        "trust_score": 50,
        "trust_level": "normal",
        "shadowban_level": 0,
        "has_voice": False
    })
    await update.message.reply_text("ثبت‌نام کامل شد! 10 سکه هدیه گرفتی!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.", reply_markup=main_menu())
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_menu_handler))
    print("ربات شروع به کار کرد...")
    app.run_polling()

if __name__ == "__main__":
    main()
