from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from core import (
    get_user, user_exists, create_user, update_user, update_username,
    ban_user, unban_user, is_banned, get_all_users, get_recent_users,
    get_user_stats, get_user_link,
    get_coins, add_coins, deduct_coin, has_enough_coins, is_vip, referral_reward,
    get_trust, update_trust, shadowban, remove_shadowban, is_shadowbanned,
    report_penalty, block_penalty, complete_chat_reward, warn_user, log_moderation,
    check_rate_limit, check_queue_limit, analyze_message,
    active_chats, start_chat, end_chat, get_partner, is_in_chat,
    save_chat_history, get_chat_history, send_direct_message, get_direct_message,
    block_user, report_user, like_user, check_mutual_like, get_blocked_ids,
    get_smart_matches, save_skip, save_match_history, update_behavioral_profile,
    update_user_location, filter_nearby_users, get_distance_bucket
)
from voice import (
    save_voice_profile, delete_voice_profile, get_voice_profile,
    get_voice_badge, send_voice_profile, get_voice_label,
    VOICE_MODE_REAL
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

BOT_USERNAME = "HooshiGapBot"
ADMIN_IDS = [7049305054]

GENDER, AGE, PROVINCE, CITY, INTERESTS, PHOTO = range(6)
SEARCH_GENDER, SEARCH_AGE, SEARCH_PROVINCE = range(6, 9)
EDIT_CHOICE, EDIT_VALUE = range(9, 11)
NEARBY_DISTANCE, NEARBY_LOCATION = range(11, 13)
RECENT_GENDER = 13
DM_WRITE = 14
VOICE_UPLOAD = 15

# ═══════════════════════════════════════
# 🎨 برند هوشی‌گپ — هویت بصری
# رنگ اصلی: بنفش 💜
# شخصیت: هوشمند، جسور، صمیمی
# ═══════════════════════════════════════

BRAND_HEADER = "💜 هوشی‌گپ"
BRAND_SEPARATOR = "┄┄┄┄┄┄┄┄┄┄┄┄"
BRAND_FOOTER = "⚡️ powered by HooshiGap AI"

def main_menu():
    keyboard = [
        ["💜 مرور پروفایل‌ها", "🔍 جستجوی پیشرفته"],
        ["🎲 اتصال تصادفی", "👤 پروفایل من"],
        ["💰 کیف پول", "🎁 دعوت دوستان"],
        ["✏️ ویرایش پروفایل", "🎂 هم‌سن‌های من"],
        ["📍 افراد نزدیک", "💬 چت‌های اخیر"],
        ["🎤 ویس پروفایل"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def chat_menu():
    keyboard = [["🔴 پایان دادن چت"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def format_profile_card(user, extra="", show_link=True):
    """کارت پروفایل با هویت بصری هوشی‌گپ"""
    vip_badge = "⭐️ VIP  " if user.get("is_vip") else ""
    voice_badge = get_voice_badge(user)
    user_link = get_user_link(user) if show_link else ""

    gender_emoji = "👦" if user.get("gender") == "پسر" else "👧"
    
    text = (
        f"{vip_badge}{voice_badge}\n"
        f"{BRAND_SEPARATOR}\n"
        f"{gender_emoji} جنسیت: {user.get('gender', '-')}\n"
        f"🎂 سن: {user.get('age', '-')}\n"
        f"🏙 شهر: {user.get('city', '-')}\n"
        f"✨ علایق: {user.get('interests', '-')}\n"
        f"{BRAND_SEPARATOR}"
    )
    if show_link and user_link:
        text += f"\n🔗 {user_link}"
    if extra:
        text += f"\n{extra}"
    return text

def user_action_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💜 لایک", callback_data=f"like_{user_id}"),
         InlineKeyboardButton("⏭ بعدی", callback_data="skip")],
        [InlineKeyboardButton("💬 چت", callback_data=f"chatreq_{user_id}"),
         InlineKeyboardButton("📨 پیام", callback_data=f"dm_{user_id}")],
        [InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{user_id}"),
         InlineKeyboardButton("⚠️ گزارش", callback_data=f"report_{user_id}")]
    ])

async def send_user_card(update, user, extra=""):
    text = format_profile_card(user, extra)
    keyboard = user_action_keyboard(user["telegram_id"])
    if user.get("photo_id"):
        await update.message.reply_photo(
            photo=user["photo_id"], caption=text,
            reply_markup=keyboard, parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if my_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ندارید!")
        return
    stats = await get_user_stats()
    text = (
        f"💜 {BRAND_HEADER}\n"
        f"📊 پنل مدیریت\n"
        f"{BRAND_SEPARATOR}\n"
        f"👥 کل کاربران: {stats['total']}\n"
        f"⭐️ کاربران VIP: {stats['vip']}\n"
        f"🎤 دارای ویس: {stats['voice']}\n"
        f"{BRAND_SEPARATOR}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users"),
         InlineKeyboardButton("⚠️ گزارش‌ها", callback_data="admin_reports")],
        [InlineKeyboardButton("🚫 بن کاربر", callback_data="admin_ban"),
         InlineKeyboardButton("✅ آنبن کاربر", callback_data="admin_unban")],
        [InlineKeyboardButton("💰 اضافه کردن سکه", callback_data="admin_coins")],
        [InlineKeyboardButton("📢 پیام به همه", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔍 جزئیات کاربر", callback_data="admin_detail")],
    ])
    await update.message.reply_text(text, reply_markup=keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    username = update.effective_user.username or ""
    args = context.args
    if args and args[0].startswith("ref_"):
        referrer_id = int(args[0].split("_")[1])
        if referrer_id != my_id:
            if not await user_exists(my_id):
                await referral_reward(referrer_id, 5)
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text="💜 یک دوست جدید با لینک شما وارد هوشی‌گپ شد!\n🎁 ۵ سکه هدیه گرفتید!"
                    )
                except:
                    pass
    if await user_exists(my_id):
        await update_username(my_id, username)
        await update.message.reply_text(
            f"💜 خوش برگشتی به هوشی‌گپ!\n"
            f"{BRAND_SEPARATOR}\n"
            f"⚡️ پلتفرم هوشمند آشنایی ایرانی",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            f"💜 به هوشی‌گپ خوش اومدی!\n"
            f"{BRAND_SEPARATOR}\n"
            f"🤖 پلتفرم هوشمند آشنایی با AI\n"
            f"🔒 کاملاً ناشناس و امن\n"
            f"✨ مچینگ بر اساس شخصیت\n"
            f"{BRAND_SEPARATOR}\n"
            f"برای شروع /register بزن 👇",
            reply_markup=ReplyKeyboardRemove()
        )

async def voice_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    voice = await get_voice_profile(my_id)
    if voice:
        mode = voice.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ پخش ویس", callback_data="play_my_voice")],
            [InlineKeyboardButton("🔄 جایگزینی ویس", callback_data="replace_voice")],
            [InlineKeyboardButton("🔒 تغییر حریم خصوصی", callback_data="change_voice_mode")],
            [InlineKeyboardButton("🗑 حذف ویس", callback_data="delete_voice")]
        ])
        await update.message.reply_text(
            f"🎤 ویس پروفایل\n"
            f"{BRAND_SEPARATOR}\n"
            f"⏱ مدت: {voice.get('voice_duration', 0)} ثانیه\n"
            f"🔐 حالت: {label}\n"
            f"{BRAND_SEPARATOR}",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 اضافه کردن ویس پروفایل", callback_data="add_voice")]
        ])
        await update.message.reply_text(
            f"🎤 ویس پروفایل\n"
            f"{BRAND_SEPARATOR}\n"
            f"هنوز ویس نداری!\n\n"
            f"با اضافه کردن ویس:\n"
            f"💜 امتیاز اعتماد +۵\n"
            f"👁 دیده شدن بیشتر\n"
            f"🎯 مچ دقیق‌تر\n"
            f"{BRAND_SEPARATOR}",
            reply_markup=keyboard
        )

async def coins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    coins = await get_coins(my_id)
    vip = await is_vip(my_id)
    vip_text = "⭐️ VIP فعال" if vip else "❌ VIP ندارید"
    text = (
        f"💰 کیف پول\n"
        f"{BRAND_SEPARATOR}\n"
        f"🪙 سکه: {coins} عدد\n"
        f"👑 وضعیت: {vip_text}\n"
        f"{BRAND_SEPARATOR}\n"
        f"روش‌های دریافت سکه:\n"
        f"🎁 معرفی دوستان — رایگان\n"
        f"💳 خرید سکه — به زودی\n"
        f"👑 خرید VIP — امکانات ویژه"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 معرفی دوستان (رایگان)", callback_data="coins_invite")],
        [InlineKeyboardButton("💳 خرید سکه (به زودی)", callback_data="coins_buy")],
        [InlineKeyboardButton("👑 خرید VIP (به زودی)", callback_data="coins_vip")]
    ])
    await update.message.reply_text(text, reply_markup=keyboard)

async def end_chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if is_in_chat(my_id):
        partner_id = get_partner(my_id)
        await save_chat_history(my_id, partner_id)
        await complete_chat_reward(my_id)
        await complete_chat_reward(partner_id)
        await update_behavioral_profile(my_id, 300, completed=True)
        await update_behavioral_profile(partner_id, 300, completed=True)
        end_chat(my_id)
        await update.message.reply_text(
            f"🔴 چت پایان یافت\n"
            f"{BRAND_SEPARATOR}\n"
            f"💜 ممنون که از هوشی‌گپ استفاده کردی!",
            reply_markup=main_menu()
        )
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text=f"🔴 چت توسط طرف مقابل پایان یافت.",
                reply_markup=main_menu()
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ چت فعالی نداری!", reply_markup=main_menu())

async def forward_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if not is_in_chat(my_id):
        if update.message.photo:
            await photo(update, context)
        return
    partner_id = get_partner(my_id)
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
            await ban_user(user_id)
            await update.message.reply_text(f"✅ کاربر {user_id} بن شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="🚫 حساب شما توسط ادمین مسدود شده است.")
            except:
                pass
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "unban":
        try:
            user_id = int(text)
            await unban_user(user_id)
            await update.message.reply_text(f"✅ کاربر {user_id} آنبن شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="✅ حساب شما رفع مسدودیت شد.")
            except:
                pass
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "coins":
        try:
            user_id = int(text)
            context.user_data["admin_coins_target"] = user_id
            context.user_data["admin_action"] = "coins_amount"
            await update.message.reply_text("💰 چند سکه اضافه کنم؟")
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
            context.user_data["admin_action"] = None
        return True
    elif action == "coins_amount":
        try:
            amount = int(text)
            target_id = context.user_data.get("admin_coins_target")
            await add_coins(target_id, amount)
            await update.message.reply_text(f"✅ {amount} سکه به کاربر {target_id} اضافه شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=target_id, text=f"💜 {amount} سکه توسط ادمین به حساب شما اضافه شد! 🎁")
            except:
                pass
        except:
            await update.message.reply_text("❌ عدد نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "broadcast":
        users = await get_all_users()
        sent = 0
        failed = 0
        for u in users:
            try:
                await context.bot.send_message(
                    chat_id=u["telegram_id"],
                    text=f"💜 پیام از هوشی‌گپ:\n{BRAND_SEPARATOR}\n{text}"
                )
                sent += 1
            except:
                failed += 1
        await update.message.reply_text(
            f"✅ پیام ارسال شد!\n✔️ موفق: {sent}\n❌ ناموفق: {failed}",
            reply_markup=main_menu()
        )
        context.user_data["admin_action"] = None
        return True
    elif action == "detail":
        try:
            user_id = int(text)
            u = await get_user(user_id)
            if not u:
                await update.message.reply_text("❌ کاربر پیدا نشد!", reply_markup=main_menu())
            else:
                coins = await get_coins(user_id)
                trust = await get_trust(user_id)
                user_link = get_user_link(u)
                detail_text = (
                    f"🔍 جزئیات کاربر\n"
                    f"{BRAND_SEPARATOR}\n"
                    f"🆔 آیدی: {u['telegram_id']}\n"
                    f"🔗 {user_link}\n"
                    f"{'👦' if u.get('gender') == 'پسر' else '👧'} جنسیت: {u.get('gender', '-')}\n"
                    f"🎂 سن: {u.get('age', '-')}\n"
                    f"🏙 شهر: {u.get('city', '-')}\n"
                    f"🪙 سکه: {coins}\n"
                    f"👑 VIP: {'✅' if u.get('is_vip') else '❌'}\n"
                    f"🚫 بن: {'✅' if u.get('is_banned') else '❌'}\n"
                    f"💜 امتیاز اعتماد: {trust.get('trust_score', 50)}/100\n"
                    f"{BRAND_SEPARATOR}"
                )
                await update.message.reply_text(detail_text, reply_markup=main_menu(), parse_mode="HTML")
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    return False

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    my_id = update.effective_user.id

    if "پایان دادن چت" in text:
        await end_chat_cmd(update, context)
        return

    if is_in_chat(my_id):
        partner_id = get_partner(my_id)
        if not check_rate_limit(my_id):
            await update.message.reply_text("⚠️ پیام‌ها رو کمتر بفرستید!")
            return
        result = await analyze_message(my_id, text)
        if result == "toxic":
            await update.message.reply_text("🚫 پیام نامناسب ارسال نشد!")
            return
        try:
            await context.bot.send_message(chat_id=partner_id, text=text)
        except:
            pass
        return

    handled = await handle_admin_text(update, context)
    if handled:
        return

    if "مرور پروفایل" in text:
        await browse(update, context)
    elif "اتصال تصادفی" in text:
        await random_user(update, context)
    elif "پروفایل من" in text:
        await profile(update, context)
    elif "کیف پول" in text:
        await coins_cmd(update, context)
    elif "دعوت" in text:
        await invite(update, context)
    elif "هم‌سن" in text:
        await same_age(update, context)
    elif "ویس پروفایل" in text:
        await voice_profile_menu(update, context)

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["پسر", "دختر", "هر دو"]]
    await update.message.reply_text(
        f"🔍 جستجوی پیشرفته\n{BRAND_SEPARATOR}\nجنسیت مورد نظرت؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SEARCH_GENDER

async def search_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_gender"] = update.message.text
    keyboard = [["هر سنی", "18-25", "26-35"], ["36-45", "46-60"]]
    await update.message.reply_text("🎂 بازه سنی؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_AGE

async def search_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["search_age"] = update.message.text
    keyboard = [["تهران", "اصفهان", "مشهد"], ["شیراز", "تبریز", "سایر"], ["همه استان‌ها"]]
    await update.message.reply_text("🏙 استان؟", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SEARCH_PROVINCE

async def search_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.users import db_get
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
    await update.message.reply_text(
        f"🔍 {len(users)} نفر پیدا شد",
        reply_markup=main_menu()
    )
    for user in users:
        await send_user_card(update, user)
    return ConversationHandler.END

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🏙 شهر", "✨ علایق"], ["📸 عکس", "🔙 بازگشت"]]
    await update.message.reply_text(
        f"✏️ ویرایش پروفایل\n{BRAND_SEPARATOR}\nچی رو میخوای ویرایش کنی؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT_CHOICE

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["edit_field"] = choice
    if "عکس" in choice:
        context.user_data["edit_field"] = "عکس"
        await update.message.reply_text("📸 عکس جدید بفرست:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif "بازگشت" in choice:
        await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
        return ConversationHandler.END
    elif "شهر" in choice:
        context.user_data["edit_field"] = "شهر"
        await update.message.reply_text("🏙 شهر جدید بنویس:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif "علایق" in choice:
        context.user_data["edit_field"] = "علایق"
        keyboard = [["موسیقی", "هنر", "کتاب"], ["ورزش", "بازی", "غذا"], ["سفر", "فیلم", "تکنولوژی"]]
        await update.message.reply_text("✨ علایق جدید رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return EDIT_VALUE
    else:
        await update.message.reply_text("❌ گزینه نامعتبر!", reply_markup=main_menu())
        return ConversationHandler.END

async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    field = context.user_data.get("edit_field")
    if field == "عکس":
        if not update.message.photo:
            await update.message.reply_text("📸 لطفا عکس بفرست:")
            return EDIT_VALUE
        photo_id = update.message.photo[-1].file_id
        await update_user(my_id, {"photo_id": photo_id})
    elif field == "شهر":
        await update_user(my_id, {"city": update.message.text})
    elif field == "علایق":
        await update_user(my_id, {"interests": update.message.text})
    await update.message.reply_text(
        f"✅ پروفایل به‌روز شد!\n💜 هوشی‌گپ AI پروفایلت رو بهینه کرد.",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

async def nearby_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["5 km", "10 km"], ["30 km", "60 km"]]
    await update.message.reply_text(
        f"📍 افراد نزدیک\n{BRAND_SEPARATOR}\nتا چه فاصله‌ای؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return NEARBY_DISTANCE

async def nearby_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().replace(" km", "").replace("km", "").strip()
    try:
        context.user_data["nearby_km"] = int(text)
    except:
        context.user_data["nearby_km"] = 10
    location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("📍 موقعیتت رو بفرست:", reply_markup=keyboard)
    return NEARBY_LOCATION

async def nearby_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.location:
        await update.message.reply_text("📍 لطفا موقعیت بفرست:")
        return NEARBY_LOCATION
    from core.users import db_get
    my_id = update.effective_user.id
    my_lat = update.message.location.latitude
    my_lon = update.message.location.longitude
    max_km = context.user_data.get("nearby_km", 10)
    await update_user_location(my_id, my_lat, my_lon)
    all_users = await db_get("users", f"telegram_id=neq.{my_id}&latitude=not.is.null")
    nearby_users = filter_nearby_users(all_users, my_lat, my_lon, max_km)
    if not nearby_users:
        await update.message.reply_text(
            f"📍 کسی در {max_km} کیلومتر پیدا نشد!",
            reply_markup=main_menu()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        f"📍 {len(nearby_users)} نفر در {max_km} کیلومتر",
        reply_markup=main_menu()
    )
    for user in nearby_users[:5]:
        extra = f"📍 فاصله: {user['distance_bucket']}"
        await send_user_card(update, user, extra)
    return ConversationHandler.END

async def recent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["پسر", "دختر", "همه"]]
    await update.message.reply_text(
        f"💬 چت‌های اخیر\n{BRAND_SEPARATOR}\nبا چه جنسیتی؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return RECENT_GENDER

async def recent_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    gender_filter = update.message.text
    found = await get_chat_history(my_id, gender_filter)
    if not found:
        await update.message.reply_text("❌ کسی پیدا نشد!", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(f"💬 {len(found)} نفر پیدا شد:", reply_markup=main_menu())
    for user in found[:10]:
        await send_user_card(update, user)
    return ConversationHandler.END

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_users":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        users = await get_recent_users(10)
        text = f"👥 آخرین کاربران\n{BRAND_SEPARATOR}\n"
        for u in users:
            text += f"🆔 {u['telegram_id']} | {'👦' if u.get('gender')=='پسر' else '👧'} | 🏙 {u.get('city','')}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data == "admin_reports":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        from core.users import db_get
        reports = await db_get("reports", "limit=10&order=id.desc")
        text = f"⚠️ آخرین گزارش‌ها\n{BRAND_SEPARATOR}\n"
        for r in reports:
            text += f"از: {r['reporter']} | به: {r['reported']}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data == "admin_ban":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر مورد نظر:")
        context.user_data["admin_action"] = "ban"
        return

    if query.data == "admin_unban":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر مورد نظر:")
        context.user_data["admin_action"] = "unban"
        return

    if query.data == "admin_coins":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر مورد نظر:")
        context.user_data["admin_action"] = "coins"
        return

    if query.data == "admin_broadcast":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="📢 پیام خود را بنویسید:")
        context.user_data["admin_action"] = "broadcast"
        return

    if query.data == "admin_detail":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر مورد نظر:")
        context.user_data["admin_action"] = "detail"
        return

    if query.data.startswith("vmode_"):
        mode = query.data.replace("vmode_", "")
        from_id = update.effective_user.id
        file_id = context.user_data.get("temp_voice_id")
        duration = context.user_data.get("temp_voice_duration", 0)
        if not file_id:
            await context.bot.send_message(chat_id=from_id, text="❌ خطا! دوباره ویس بفرستید.", reply_markup=main_menu())
            return
        await context.bot.send_message(chat_id=from_id, text="⏳ در حال پردازش ویس...")
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
        await context.bot.send_message(chat_id=from_id, text="🔐 حالت جدید را انتخاب کن:", reply_markup=keyboard)
        return

    if query.data.startswith("setmode_"):
        mode = query.data.replace("setmode_", "")
        from_id = update.effective_user.id
        await update_user(from_id, {"voice_mode": mode})
        label = get_voice_label(mode)
        await context.bot.send_message(chat_id=from_id, text=f"✅ حالت ویس تغییر کرد: {label}", reply_markup=main_menu())
        return

    if query.data in ["add_voice", "replace_voice"]:
        from_id = update.effective_user.id
        await context.bot.send_message(chat_id=from_id, text="🎤 یک ویس بین ۱۰ تا ۳۰ ثانیه بفرست:", reply_markup=ReplyKeyboardRemove())
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
        await context.bot.send_message(
            chat_id=my_id,
            text=f"🎁 لینک دعوت شما:\n{link}\n\n💜 به ازای هر دوست ۵ سکه هدیه می‌گیرید!"
        )
        return

    if query.data == "coins_buy":
        await context.bot.send_message(chat_id=update.effective_user.id, text="💳 خرید سکه به زودی فعال می‌شود!")
        return

    if query.data == "coins_vip":
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                f"👑 امکانات VIP\n{BRAND_SEPARATOR}\n"
                f"⭐️ اول لیست جستجوها\n"
                f"💜 نشان VIP روی پروفایل\n"
                f"💬 درخواست چت به ۱۰ نفر\n"
                f"📨 پیام دایرکت به ۱۰ نفر\n"
                f"{BRAND_SEPARATOR}\n"
                f"به زودی فعال می‌شود!"
            )
        )
        return

    if query.data.startswith("readdm_"):
        parts = query.data.split("_")
        msg_id = parts[1]
        from_id = int(parts[2])
        is_paid = parts[3] == "True"
        to_id = update.effective_user.id
        msg = await get_direct_message(msg_id)
        if not msg:
            await query.answer("❌ پیام پیدا نشد!", show_alert=True)
            return
        if not is_paid:
            if not await has_enough_coins(to_id):
                await query.answer("❌ سکه کافی ندارید!", show_alert=True)
                return
            await deduct_coin(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        dm_text = msg.get("message", "")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 پاسخ", callback_data=f"chatreq_{from_id}"),
            InlineKeyboardButton("💜 لایک", callback_data=f"like_{from_id}")
        ]])
        await context.bot.send_message(
            chat_id=to_id,
            text=f"📨 پیام خصوصی:\n{BRAND_SEPARATOR}\n{dm_text}",
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
        await block_user(from_id, to_id)
        await block_penalty(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=from_id, text="🚫 کاربر بلاک شد.")
        return

    if query.data.startswith("report_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        await report_user(from_id, to_id)
        await report_penalty(to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=from_id, text="✅ گزارش ثبت شد!")
        return

    if query.data.startswith("chatreq_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        my_profile = await get_user(from_id)
        if my_profile:
            vip_badge = "⭐️ VIP  " if my_profile.get("is_vip") else ""
            voice_badge = get_voice_badge(my_profile)
            gender_emoji = "👦" if my_profile.get("gender") == "پسر" else "👧"
            text = (
                f"💬 درخواست چت!\n{BRAND_SEPARATOR}\n"
                f"{vip_badge}{voice_badge}\n"
                f"{gender_emoji} جنسیت: {my_profile['gender']}\n"
                f"🎂 سن: {my_profile['age']}\n"
                f"🏙 شهر: {my_profile['city']}\n"
                f"✨ علایق: {my_profile['interests']}\n"
                f"{BRAND_SEPARATOR}"
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ قبول", callback_data=f"accept_{from_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{from_id}")
            ]])
            try:
                if my_profile.get("photo_id"):
                    await context.bot.send_photo(chat_id=to_id, photo=my_profile["photo_id"], caption=text, reply_markup=kb)
                else:
                    await context.bot.send_message(chat_id=to_id, text=text, reply_markup=kb)
                if my_profile.get("has_voice"):
                    await send_voice_profile(context.bot, to_id, my_profile, is_matched=False)
            except:
                pass
        await context.bot.send_message(chat_id=from_id, text="✅ درخواست چت فرستاده شد!")
        return

    if query.data.startswith("dm_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        context.user_data["dm_to"] = to_id
        await context.bot.send_message(
            chat_id=from_id,
            text=f"📨 پیام خصوصی\n{BRAND_SEPARATOR}\nپیامت رو بنویس:",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if query.data.startswith("accept_"):
        from_id = int(query.data.split("_")[1])
        to_id = update.effective_user.id
        start_chat(from_id, to_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(
            chat_id=to_id,
            text=f"💜 چت شروع شد!\n{BRAND_SEPARATOR}\n🔴 برای پایان دادن دکمه زیر رو بزن",
            reply_markup=chat_menu()
        )
        await context.bot.send_message(
            chat_id=from_id,
            text=f"💜 درخواست قبول شد!\n{BRAND_SEPARATOR}\n🔴 برای پایان دادن دکمه زیر رو بزن",
            reply_markup=chat_menu()
        )
        from_profile = await get_user(from_id)
        to_profile = await get_user(to_id)
        if from_profile and from_profile.get("has_voice"):
            await send_voice_profile(context.bot, to_id, from_profile, is_matched=True)
        if to_profile and to_profile.get("has_voice"):
            await send_voice_profile(context.bot, from_id, to_profile, is_matched=True)
        return

    if query.data.startswith("reject_"):
        from_id = int(query.data.split("_")[1])
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await context.bot.send_message(chat_id=from_id, text="❌ درخواست چت شما رد شد.")
        return

    to_id = int(query.data.split("_")[1])
    from_id = update.effective_user.id
    await like_user(from_id, to_id)
    is_match = await check_mutual_like(from_id, to_id)
    if is_match:
        await context.bot.send_message(
            chat_id=from_id,
            text=f"💜 ماتچ شدید!\n{BRAND_SEPARATOR}\n✨ هوشی‌گپ AI شما رو به هم وصل کرد!"
        )
        try:
            await context.bot.send_message(
                chat_id=to_id,
                text=f"💜 ماتچ شدید!\n{BRAND_SEPARATOR}\n✨ هوشی‌گپ AI شما رو به هم وصل کرد!"
            )
        except:
            pass
    else:
        await context.bot.send_message(chat_id=from_id, text="💜 لایک ثبت شد!")
        try:
            await context.bot.send_message(chat_id=to_id, text="💜 یک نفر به پروفایلت علاقه نشون داد!")
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
            await update.message.reply_text("✅ ویست دریافت شد!\nچطور نمایش داده بشه؟", reply_markup=keyboard)
            context.user_data["waiting_voice"] = False
            return
    await forward_media(update, context)

async def send_dm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_id = context.user_data.get("dm_to")
    if not to_id:
        await update.message.reply_text("❌ خطای فنی!", reply_markup=main_menu())
        return ConversationHandler.END
    from_id = update.effective_user.id
    message_text = update.message.text
    if not check_rate_limit(from_id):
        await update.message.reply_text("⚠️ پیام‌ها رو کمتر بفرستید!")
        return ConversationHandler.END
    result = await analyze_message(from_id, message_text)
    if result == "toxic":
        await update.message.reply_text("🚫 پیام نامناسب ارسال نشد!", reply_markup=main_menu())
        return ConversationHandler.END
    coins = await get_coins(from_id)
    is_paid = coins >= 1
    if is_paid:
        await deduct_coin(from_id)
    msg_id = await send_direct_message(from_id, to_id, message_text, is_paid)
    my_profile = await get_user(from_id)
    if my_profile and msg_id:
        vip_badge = "⭐️ VIP  " if my_profile.get("is_vip") else ""
        voice_badge = get_voice_badge(my_profile)
        notif = (
            f"📨 پیام خصوصی جدید!\n{BRAND_SEPARATOR}\n"
            f"{vip_badge}{voice_badge}\n"
            f"{'👦' if my_profile.get('gender')=='پسر' else '👧'} | 🎂 {my_profile['age']} | 🏙 {my_profile['city']}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📨 خواندن پیام", callback_data=f"readdm_{msg_id}_{from_id}_{is_paid}")
        ]])
        try:
            if my_profile.get("photo_id"):
                await context.bot.send_photo(chat_id=to_id, photo=my_profile["photo_id"], caption=notif, reply_markup=kb)
            else:
                await context.bot.send_message(chat_id=to_id, text=notif, reply_markup=kb)
        except:
            pass
    await update.message.reply_text("✅ پیام ارسال شد!", reply_markup=main_menu())
    return ConversationHandler.END

async def browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    if not check_queue_limit(my_id):
        await update.message.reply_text("⚠️ خیلی سریع! کمی صبر کنید.")
        return
    coins = await get_coins(my_id)
    if coins <= 0:
        await update.message.reply_text(
            f"❌ سکه کافی نداری!\n{BRAND_SEPARATOR}\n💰 از کیف پول سکه بگیر"
        )
        return
    blocked_ids = await get_blocked_ids(my_id)
    users = await get_smart_matches(my_id, blocked_ids, limit=5)
    if not users:
        await update.message.reply_text("😔 فعلا کاربر جدیدی نیست!")
        return
    user = users[0]
    await deduct_coin(my_id)
    await send_user_card(update, user, f"🪙 سکه باقی: {coins-1}")
    if user.get("has_voice"):
        await send_voice_profile(context.bot, my_id, user, is_matched=False)

async def random_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.users import db_get
    import random
    my_id = update.effective_user.id
    users = await db_get("users", f"telegram_id=neq.{my_id}")
    if not users:
        await update.message.reply_text("😔 فعلا کاربر دیگری نیست!")
        return
    user = random.choice(users)
    await send_user_card(update, user)

async def same_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.users import db_get
    my_id = update.effective_user.id
    my_profile = await get_user(my_id)
    if not my_profile:
        await update.message.reply_text("❌ اول ثبت‌نام کن! /register بزن")
        return
    my_age = my_profile["age"]
    users = await db_get("users", f"telegram_id=neq.{my_id}&age=eq.{my_age}&limit=5")
    if not users:
        await update.message.reply_text(f"😔 کسی با سن {my_age} پیدا نشد!")
        return
    await update.message.reply_text(f"🎂 {len(users)} نفر هم‌سن پیدا شد:")
    for user in users:
        await send_user_card(update, user)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    user = await get_user(my_id)
    if not user:
        await update.message.reply_text("❌ هنوز ثبت‌نام نکردی! /register بزن")
        return
    coins = await get_coins(my_id)
    trust = await get_trust(my_id)
    trust_score = trust.get("trust_score", 50)
    vip_badge = "⭐️ VIP\n" if user.get("is_vip") else ""
    voice_info = ""
    if user.get("has_voice"):
        mode = user.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        voice_info = f"🎤 {label}\n"
    gender_emoji = "👦" if user.get("gender") == "پسر" else "👧"
    text = (
        f"💜 پروفایل من\n"
        f"{BRAND_SEPARATOR}\n"
        f"{vip_badge}{voice_info}"
        f"🆔 آیدی: {my_id}\n"
        f"{gender_emoji} جنسیت: {user['gender']}\n"
        f"🎂 سن: {user['age']}\n"
        f"🗺 استان: {user['province']}\n"
        f"🏙 شهر: {user['city']}\n"
        f"✨ علایق: {user['interests']}\n"
        f"🪙 سکه: {coins}\n"
        f"💜 امتیاز اعتماد: {trust_score}/100\n"
        f"{BRAND_SEPARATOR}"
    )
    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text)
    else:
        await update.message.reply_text(text)

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{my_id}"
    await update.message.reply_text(
        f"🎁 دعوت دوستان\n"
        f"{BRAND_SEPARATOR}\n"
        f"لینک اختصاصی شما:\n{link}\n\n"
        f"💜 به ازای هر دوست ۵ سکه هدیه!\n"
        f"{BRAND_SEPARATOR}\n"
        f"{BRAND_FOOTER}"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["👦 پسر", "👧 دختر"]]
    await update.message.reply_text(
        f"💜 ثبت‌نام در هوشی‌گپ\n"
        f"{BRAND_SEPARATOR}\n"
        f"جنسیت شما؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("👦 ", "").replace("👧 ", "")
    context.user_data["gender"] = text
    await update.message.reply_text("🎂 سن شما؟ (حداقل ۱۸)", reply_markup=ReplyKeyboardRemove())
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 18:
        await update.message.reply_text("❌ سن باید حداقل ۱۸ باشه:")
        return AGE
    context.user_data["age"] = int(text)
    keyboard = [["تهران", "اصفهان", "مشهد"], ["شیراز", "تبریز", "اهواز"], ["سایر"]]
    await update.message.reply_text(
        "🗺 استان شما؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PROVINCE

async def province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["province"] = update.message.text
    await update.message.reply_text("🏙 شهر شما؟", reply_markup=ReplyKeyboardRemove())
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    keyboard = [["🎵 موسیقی", "🎨 هنر", "📚 کتاب"], ["⚽ ورزش", "🎮 بازی", "🍕 غذا"], ["✈️ سفر", "🎬 فیلم", "💻 تکنولوژی"]]
    await update.message.reply_text(
        "✨ علایقت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return INTERESTS

async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    for emoji in ["🎵 ", "🎨 ", "📚 ", "⚽ ", "🎮 ", "🍕 ", "✈️ ", "🎬 ", "💻 "]:
        text = text.replace(emoji, "")
    context.user_data["interests"] = text
    await update.message.reply_text("📸 عکس پروفایلت رو بفرست:", reply_markup=ReplyKeyboardRemove())
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📸 لطفا یک عکس بفرست:")
        return PHOTO
    photo_id = update.message.photo[-1].file_id
    data = context.user_data
    username = update.effective_user.username or ""
    await create_user(
        update.effective_user.id, username,
        data["gender"], data["age"], data["province"],
        data["city"], data["interests"], photo_id
    )
    await update.message.reply_text(
        f"💜 ثبت‌نام کامل شد!\n"
        f"{BRAND_SEPARATOR}\n"
        f"🎁 ۱۰ سکه هدیه گرفتی!\n"
        f"🤖 هوشی‌گپ AI منتظر مچ کردنته!\n"
        f"{BRAND_SEPARATOR}\n"
        f"{BRAND_FOOTER}",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    TOKEN = "8992632783:AAEyc2COdSjBC3cWlSVvY-oG6AZMAcW3nq4"
    app = Application.builder().token(TOKEN).build()

    register_conv = ConversationHandler(
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
        entry_points=[
            CommandHandler("search", search_start),
            MessageHandler(filters.Regex("جستجو"), search_start)
        ],
        states={
            SEARCH_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_gender)],
            SEARCH_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_age)],
            SEARCH_PROVINCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_province)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    edit_conv = ConversationHandler(
        entry_points=[
            CommandHandler("edit", edit_start),
            MessageHandler(filters.Regex("ویرایش"), edit_start)
        ],
        states={
            EDIT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_choice)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value), MessageHandler(filters.PHOTO, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    nearby_conv = ConversationHandler(
        entry_points=[
            CommandHandler("nearby", nearby_start),
            MessageHandler(filters.Regex("نزدیک"), nearby_start)
        ],
        states={
            NEARBY_DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nearby_distance)],
            NEARBY_LOCATION: [MessageHandler(filters.LOCATION, nearby_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    recent_conv = ConversationHandler(
        entry_points=[
            CommandHandler("recent", recent_start),
            MessageHandler(filters.Regex("چت‌های اخیر"), recent_start)
        ],
        states={
            RECENT_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, recent_gender)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    dm_conv = ConversationHandler(
        entry_points=[],
        states={
            DM_WRITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_dm_handler)],
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
    app.add_handler(search_conv)
    app.add_handler(edit_conv)
    app.add_handler(nearby_conv)
    app.add_handler(recent_conv)
    app.add_handler(register_conv)
    app.add_handler(dm_conv)
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.PHOTO, forward_media))
    app.add_handler(MessageHandler(filters.VIDEO, forward_media))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_in_chat))
    app.add_handler(MessageHandler(filters.AUDIO, forward_media))
    app.add_handler(MessageHandler(filters.Sticker.ALL, forward_media))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, forward_media))
    app.add_handler(MessageHandler(filters.Document.ALL, forward_media))
    app.add_handler(MessageHandler(filters.ANIMATION, forward_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler))
    print("💜 هوشی‌گپ شروع به کار کرد...")
    app.run_polling()

if __name__ == "__main__":
    main()
