import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

from core import (
    get_user, user_exists, create_user, update_user, update_username,
    update_last_seen, get_online_status_text,
    ban_user, unban_user, is_banned, get_all_users, get_recent_users,
    get_user_stats, get_user_link,
    get_users_by_province, get_users_by_age, get_new_users,
    get_popular_users, get_users_without_chat, db_get,
    get_coins, add_coins, deduct_coin, has_enough_coins, is_vip,
    set_vip, buy_vip_with_coins, get_vip_broadcast_status,
    use_vip_broadcast_chat, use_vip_broadcast_dm,
    referral_reward, VIP_PRICE_COINS, VIP_PRICE_TOMAN,
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



BOT_USERNAME = "HooshiGapBot"
ADMIN_IDS = [7049305054]

NAME, GENDER, AGE, PROVINCE, CITY, INTERESTS, PHOTO = range(7)
SEARCH_GENDER, SEARCH_AGE, SEARCH_PROVINCE = range(6, 9)
EDIT_CHOICE, EDIT_VALUE = range(9, 11)
NEARBY_DISTANCE, NEARBY_LOCATION = range(11, 13)
RECENT_GENDER = 13
DM_WRITE = 14
VOICE_UPLOAD = 15
SEARCH_TYPE = 17
SEARCH_GENDER_NEW = 18
SEARCH_PAGE = 19

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
        ["🤝 به یه ناشناس وصلم کن!"],
        ["🔍 جستجو کاربران", "📍 افراد نزدیک"],
        ["🧭 راهنما", "👤 پروفایل", "💰 سکه"],
        ["🔗 معرفی به دوستان (سکه رایگان)"],
        ["🎭 لینک ناشناس من"]
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
    username = user.get("username", "")
    display_name = user.get("display_name", "")
    name_line = f"✨ {display_name}\n" if display_name else ""
    username_line = f"👤 @{username}\n" if username else ""
    online_status = get_online_status_text(user)
    like_count = user.get("like_count", 0)
    lines = []
    if vip_badge:
        lines.append(vip_badge)
    if display_name:
        lines.append(f"✨ {display_name}")
    if username:
        lines.append(f"👤 @{username}")
    lines.append("")
    lines.append(f"{gender_emoji} جنسیت: {user.get('gender', '-')}")
    lines.append(f"🎂 سن: {user.get('age', '-')}")
    lines.append(f"🏙 شهر: {user.get('city', '-')}")
    lines.append(f"📡 {online_status}")
    lines.append(f"❤️ لایک: {like_count}")
    if show_link and user_link:
        lines.append(f"🔗 {user_link}")
    if extra:
        lines.append(extra)
    return "\n".join(lines)

def user_action_keyboard(user_id, like_count=0, is_blocked=False):
    block_btn = InlineKeyboardButton("✅ آنبلاک کاربر", callback_data=f"unblock_{user_id}") if is_blocked else InlineKeyboardButton("🚫 بلاک کاربر", callback_data=f"block_{user_id}")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💜 {like_count} لایک", callback_data=f"like_{user_id}")],
        [InlineKeyboardButton("🎁 خرید سکه برای کاربر", callback_data=f"gift_coins_{user_id}")],
        [InlineKeyboardButton("💬 درخواست چت", callback_data=f"chatreq_{user_id}"),
         InlineKeyboardButton("📨 پیام دایرکت", callback_data=f"dm_{user_id}")],
        [block_btn, InlineKeyboardButton("🚨 گزارش کاربر", callback_data=f"report_{user_id}")],
        [InlineKeyboardButton("➕ افزودن به مخاطبین", callback_data=f"add_contact_{user_id}")],
        [InlineKeyboardButton("🔔 اطلاع از آنلاین شدن", callback_data=f"notify_online_{user_id}")]
    ])

async def send_user_card(update, user, extra=""):
    text = format_profile_card(user, extra)
    like_count = user.get("like_count", 0)
    keyboard = user_action_keyboard(user["telegram_id"], like_count)
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
    # اگه banned توی stats نبود، خودمون حساب می‌کنیم
    if "banned" not in stats:
        try:
            banned_users = await db_get("users", "is_banned=eq.true")
            stats["banned"] = len(banned_users)
        except:
            stats["banned"] = 0
    text = (
        f"💜 {BRAND_HEADER}\n"
        f"📊 پنل مدیریت\n"
        f"{BRAND_SEPARATOR}\n"
        f"👥 کل کاربران: {stats['total']}\n"
        f"⭐️ کاربران VIP: {stats['vip']}\n"
        f"🎤 دارای ویس: {stats['voice']}\n"
        f"🚫 بن‌شده‌ها: {stats.get('banned', 0)}\n"
        f"{BRAND_SEPARATOR}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users"),
         InlineKeyboardButton("⚠️ گزارش‌ها", callback_data="admin_reports")],
        [InlineKeyboardButton("🚫 بن کاربر", callback_data="admin_ban"),
         InlineKeyboardButton("✅ آنبن کاربر", callback_data="admin_unban")],
        [InlineKeyboardButton("👻 shadowban کاربر", callback_data="admin_shadowban"),
         InlineKeyboardButton("✨ رفع shadowban", callback_data="admin_unshadowban")],
        [InlineKeyboardButton("💰 اضافه کردن سکه", callback_data="admin_coins"),
         InlineKeyboardButton("👑 دادن VIP", callback_data="admin_vip")],
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
        await update_last_seen(my_id)
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
        # هندل کردن location برای جستجوی نزدیک
        if update.message.location and context.user_data.get("waiting_nearby_location"):
            context.user_data["waiting_nearby_location"] = False
            from core.users import db_get as _db_get
            my_lat = update.message.location.latitude
            my_lon = update.message.location.longitude
            max_km = context.user_data.get("nearby_km", 10)
            await update_user_location(my_id, my_lat, my_lon)
            all_users = await _db_get("users", f"telegram_id=neq.{my_id}&latitude=not.is.null")
            nearby_users = filter_nearby_users(all_users, my_lat, my_lon, max_km)
            if not nearby_users:
                await update.message.reply_text(f"😔 کسی در {max_km} کیلومتر پیدا نشد!", reply_markup=main_menu())
                return
            context.user_data["search_results"] = nearby_users
            context.user_data["search_page"] = 0
            await update.message.reply_text(f"✅ {len(nearby_users)} نفر در {max_km} کیلومتر!", reply_markup=main_menu())
            await show_search_page_inline(update, context, my_id)
            return

        if update.message.photo and context.user_data.get("waiting_edit_value") and context.user_data.get("edit_field") == "عکس":
            photo_id = update.message.photo[-1].file_id
            await update_user(my_id, {"photo_id": photo_id})
            context.user_data["waiting_edit_value"] = False
            context.user_data["waiting_edit"] = False
            await update.message.reply_text("✅ عکس پروفایل به‌روز شد!", reply_markup=main_menu())
            return
        elif update.message.location and context.user_data.get("waiting_edit_value") and context.user_data.get("edit_field") == "gps":
            lat = update.message.location.latitude
            lon = update.message.location.longitude
            await update_user_location(my_id, lat, lon)
            context.user_data["waiting_edit_value"] = False
            context.user_data["waiting_edit"] = False
            await update.message.reply_text("✅ موقعیت به‌روز شد!", reply_markup=main_menu())
            return
        elif update.message.photo:
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
    elif action == "shadowban":
        try:
            user_id = int(text)
            await shadowban(user_id, level=1, reason="توسط ادمین")
            await update.message.reply_text(f"👻 کاربر {user_id} shadowban شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="⚠️ حساب شما محدود شده است.")
            except:
                pass
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "unshadowban":
        try:
            user_id = int(text)
            await remove_shadowban(user_id)
            await update.message.reply_text(f"✅ shadowban کاربر {user_id} برداشته شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="✅ محدودیت حساب شما برطرف شد.")
            except:
                pass
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
        context.user_data["admin_action"] = None
        return True
    elif action == "vip":
        try:
            user_id = int(text)
            await set_vip(user_id, True)
            await update.message.reply_text(f"👑 VIP به کاربر {user_id} داده شد!", reply_markup=main_menu())
            try:
                await context.bot.send_message(chat_id=user_id, text="👑 تبریک! حساب شما VIP شد! ⭐️")
            except:
                pass
        except:
            await update.message.reply_text("❌ آیدی نامعتبر!", reply_markup=main_menu())
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

    # ادمین همیشه اول چک می‌شه — حتی توی چت
    if my_id in ADMIN_IDS and context.user_data.get("admin_action"):
        handled = await handle_admin_text(update, context)
        if handled:
            return

    if is_in_chat(my_id):
        partner_id = get_partner(my_id)
        await update_last_seen(my_id)
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

    # هندل کردن جستجوی نزدیک با GPS
    if context.user_data.get("waiting_nearby_location") and update.message.location:
        context.user_data["waiting_nearby_location"] = False
        from core.users import db_get as _db_get
        my_id = update.effective_user.id
        my_lat = update.message.location.latitude
        my_lon = update.message.location.longitude
        max_km = context.user_data.get("nearby_km", 10)
        await update_user_location(my_id, my_lat, my_lon)
        all_users = await _db_get("users", f"telegram_id=neq.{my_id}&latitude=not.is.null")
        nearby_users = filter_nearby_users(all_users, my_lat, my_lon, max_km)
        if not nearby_users:
            await update.message.reply_text(f"😔 کسی در {max_km} کیلومتر پیدا نشد!", reply_markup=main_menu())
            return
        context.user_data["search_results"] = nearby_users
        context.user_data["search_page"] = 0
        await update.message.reply_text(f"✅ {len(nearby_users)} نفر در {max_km} کیلومتر پیدا شد!", reply_markup=main_menu())
        await show_search_page_inline(update, context, my_id)
        return

    # هندل کردن VIP broadcast
    if context.user_data.get("vip_action"):
        vip_action = context.user_data.get("vip_action")
        context.user_data["vip_action"] = None
        
        if vip_action == "broadcast_chat":
            success, msg = await use_vip_broadcast_chat(my_id)
            if not success:
                await update.message.reply_text(msg, reply_markup=main_menu())
                return
            # ارسال درخواست چت به ۱۰ نفر آنلاین
            candidates = await db_get("users", f"telegram_id=neq.{my_id}&is_banned=eq.false&shadowban_level=eq.0&order=last_seen.desc&limit=10")
            sent = 0
            my_profile = await get_user(my_id)
            for u in candidates:
                try:
                    vip_badge = "⭐️ VIP | "
                    gender_emoji = "👦" if my_profile.get("gender") == "پسر" else "👧"
                    notif = (
                        f"💬 درخواست چت VIP!\n{BRAND_SEPARATOR}\n"
                        f"{vip_badge}{gender_emoji} {my_profile.get('gender')} | "
                        f"🎂 {my_profile.get('age')} | "
                        f"🏙 {my_profile.get('city')}"
                    )
                    kb = InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ قبول", callback_data=f"accept_{my_id}"),
                        InlineKeyboardButton("❌ رد", callback_data=f"reject_{my_id}")
                    ]])
                    await context.bot.send_message(chat_id=u["telegram_id"], text=notif, reply_markup=kb)
                    sent += 1
                except:
                    pass
            await update.message.reply_text(f"✅ درخواست چت به {sent} نفر ارسال شد!", reply_markup=main_menu())
            return

        elif vip_action == "broadcast_dm":
            success, msg_status = await use_vip_broadcast_dm(my_id)
            if not success:
                await update.message.reply_text(msg_status, reply_markup=main_menu())
                return
            # ارسال پیام به ۱۰ نفر آنلاین
            candidates = await db_get("users", f"telegram_id=neq.{my_id}&is_banned=eq.false&shadowban_level=eq.0&order=last_seen.desc&limit=10")
            sent = 0
            my_profile = await get_user(my_id)
            for u in candidates:
                try:
                    vip_badge = "⭐️ VIP | "
                    notif = (
                        f"📨 پیام همگانی VIP\n{BRAND_SEPARATOR}\n"
                        f"{vip_badge}{text}\n"
                        f"از: {my_profile.get('gender')} | {my_profile.get('age')} | {my_profile.get('city')}"
                    )
                    kb = InlineKeyboardMarkup([[
                        InlineKeyboardButton("💬 پاسخ", callback_data=f"chatreq_{my_id}"),
                        InlineKeyboardButton("💜 لایک", callback_data=f"like_{my_id}")
                    ]])
                    await context.bot.send_message(chat_id=u["telegram_id"], text=notif, reply_markup=kb)
                    sent += 1
                except:
                    pass
            await update.message.reply_text(f"✅ پیام به {sent} نفر ارسال شد!", reply_markup=main_menu())
            return

    # هندل کردن ویرایش پروفایل از دکمه پروفایل
    if context.user_data.get("waiting_edit"):
        choice = text
        if "بازگشت" in choice:
            context.user_data["waiting_edit"] = False
            await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
            return
        elif "عکس" in choice:
            context.user_data["edit_field"] = "عکس"
            context.user_data["waiting_edit_value"] = True
            await update.message.reply_text("📸 عکس جدید بفرست:", reply_markup=ReplyKeyboardRemove())
            return
        elif "شهر" in choice:
            context.user_data["edit_field"] = "شهر"
            context.user_data["waiting_edit_value"] = True
            await update.message.reply_text("🏙 شهر جدید بنویس:", reply_markup=ReplyKeyboardRemove())
            return
        elif "علایق" in choice:
            context.user_data["edit_field"] = "علایق"
            context.user_data["waiting_edit_value"] = True
            keyboard = [["موسیقی", "هنر", "کتاب"], ["ورزش", "بازی", "غذا"], ["سفر", "فیلم", "تکنولوژی"]]
            await update.message.reply_text("✨ علایق جدید:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
            return
        elif "اسم" in choice:
            context.user_data["edit_field"] = "اسم"
            context.user_data["waiting_edit_value"] = True
            await update.message.reply_text("👤 اسم مستعار جدید:", reply_markup=ReplyKeyboardRemove())
            return
        elif "جنسیت" in choice:
            context.user_data["edit_field"] = "جنسیت"
            context.user_data["waiting_edit_value"] = True
            keyboard = [["👦 پسر", "👧 دختر"]]
            await update.message.reply_text("⚧ جنسیت جدید:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
            return
        elif "سن" in choice:
            context.user_data["edit_field"] = "سن"
            context.user_data["waiting_edit_value"] = True
            await update.message.reply_text("🎂 سن جدید (حداقل ۱۸):", reply_markup=ReplyKeyboardRemove())
            return
        elif "GPS" in choice or "موقعیت" in choice:
            context.user_data["edit_field"] = "gps"
            context.user_data["waiting_edit_value"] = True
            location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
            keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("📍 موقعیت جدید:", reply_markup=keyboard)
            return

    # هندل کردن مقدار ویرایش
    if context.user_data.get("waiting_edit_value"):
        my_id = update.effective_user.id
        field = context.user_data.get("edit_field")
        context.user_data["waiting_edit_value"] = False
        context.user_data["waiting_edit"] = False
        if field == "شهر":
            await update_user(my_id, {"city": text})
        elif field == "علایق":
            await update_user(my_id, {"interests": text})
        elif field == "اسم":
            await update_user(my_id, {"display_name": text})
        elif field == "جنسیت":
            g = text.replace("👦 ", "").replace("👧 ", "")
            await update_user(my_id, {"gender": g})
        elif field == "سن":
            if text.isdigit() and int(text) >= 18:
                await update_user(my_id, {"age": int(text)})
            else:
                await update.message.reply_text("❌ سن باید حداقل ۱۸ باشه!", reply_markup=main_menu())
                return
        await update.message.reply_text("✅ پروفایل به‌روز شد!", reply_markup=main_menu())
        return

    if "ناشناس وصلم کن" in text:
        await random_user(update, context)
    elif "جستجو کاربران" in text:
        return await new_search(update, context)
    elif "افراد نزدیک" in text:
        return await nearby_start(update, context)
    elif "پروفایل" in text and "ویرایش" not in text:
        await profile(update, context)
    elif "سکه" in text:
        await coins_cmd(update, context)
    elif "معرفی به دوستان" in text:
        await invite(update, context)
    elif "لینک ناشناس" in text:
        my_id = update.effective_user.id
        link = f"https://t.me/{BOT_USERNAME}?start=anon_{my_id}"
        await update.message.reply_text(
            f"🎭 لینک ناشناس شما:\n{link}\n\n"
            f"با این لینک هر کسی می‌تونه بهت پیام بده بدون اینکه بدونه کی هستی!",
            reply_markup=main_menu()
        )
        return
    elif "لینک ناشناس_unused" in text:
        await invite(update, context)
    elif "راهنما" in text:
        await update.message.reply_text(
            f"💜 راهنمای هوشی‌گپ\n{BRAND_SEPARATOR}\n"
            f"🤝 وصلم کن — اتصال تصادفی به یه ناشناس\n"
            f"🔍 جستجو — پیدا کردن کاربران\n"
            f"📍 افراد نزدیک — کاربران اطراف شما\n"
            f"👤 پروفایل — مشاهده و ویرایش پروفایل\n"
            f"💰 سکه — کیف پول و VIP\n"
            f"🔗 معرفی — دعوت دوستان و گرفتن سکه رایگان",
            reply_markup=main_menu()
        )

async def search_type_handler_advanced(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع جستجوی پیشرفته مستقیم"""
    context.user_data["search_type"] = "جستجوی پیشرفته"
    context.user_data["in_advanced_search"] = True
    keyboard = [["پسر", "دختر", "هر دو"], ["🔙 بازگشت"]]
    await update.message.reply_text(
        f"🔍 جستجوی پیشرفته\n{BRAND_SEPARATOR}\nجنسیت مورد نظرت؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SEARCH_GENDER_NEW

async def new_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی جستجوی جدید - Inline"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 به مخاطب خاصم وصلم کن", callback_data="ns_direct")],
        [InlineKeyboardButton("👫 هم سن‌ها", callback_data="ns_age"),
         InlineKeyboardButton("🎯 هم استانی‌ها", callback_data="ns_province")],
        [InlineKeyboardButton("💬 جستجوی پیشرفته", callback_data="ns_advanced")],
        [InlineKeyboardButton("🚶 بدون چت‌ها", callback_data="ns_nochat"),
         InlineKeyboardButton("👰 کاربران جدید", callback_data="ns_new")],
        [InlineKeyboardButton("👀 چت‌های اخیر من", callback_data="ns_recent")],
        [InlineKeyboardButton("📍 جستجو با GPS فعلی من", callback_data="ns_gps")],
        [InlineKeyboardButton("❤️ کاربران محبوب بر اساس لایک", callback_data="ns_popular")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="ns_back")]
    ])
    await update.message.reply_text(
        "🔍 جستجو کاربران\nچه کسایی رو نشونت بدم؟ انتخاب کن",
        reply_markup=keyboard
    )
    return ConversationHandler.END

async def search_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل کردن نوع جستجو"""
    search_type = update.message.text
    context.user_data["search_type"] = search_type

    if "بازگشت" in search_type:
        await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
        return ConversationHandler.END

    if "جستجوی پیشرفته" in search_type:
        keyboard = [["👦 پسر", "👧 دختر", "👥 همه"], ["🔙 بازگشت"]]
        await update.message.reply_text(
            "🔍 جستجوی پیشرفته\nجنسیت مورد نظرت؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        context.user_data["in_advanced_search"] = True
        return SEARCH_GENDER_NEW

    if "چت‌های اخیر" in search_type:
        context.user_data["search_type"] = "recent"
        keyboard = [["پسر", "دختر", "همه"], ["🔙 بازگشت"]]
        await update.message.reply_text(
            "💬 چت‌های اخیر\nبا چه جنسیتی؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SEARCH_GENDER_NEW

    if "GPS" in search_type:
        await update.message.reply_text("لغو شد.", reply_markup=main_menu())
        return await nearby_start(update, context)

    if "مخاطب خاصم" in search_type:
        await update.message.reply_text(
            "❤️ به مخاطب خاصم وصلم کن\nاسم یا آیدی مخاطب رو بنویس:",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data["search_type"] = "مخاطب خاص"
        return SEARCH_GENDER_NEW

    keyboard = [["👦 پسر", "👧 دختر", "👥 همه"]]
    await update.message.reply_text(
        "جنسیت مورد نظر؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SEARCH_GENDER_NEW

async def search_gender_new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل کردن جنسیت در جستجوی جدید"""
    gender_text = update.message.text

    if "بازگشت" in gender_text:
        context.user_data["in_advanced_search"] = False
        await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
        return ConversationHandler.END

    gender = None
    if "پسر" in gender_text:
        gender = "پسر"
    elif "دختر" in gender_text:
        gender = "دختر"

    context.user_data["search_gender_new"] = gender
    my_id = update.effective_user.id
    search_type = context.user_data.get("search_type", "")

    # جستجوی پیشرفته
    if context.user_data.get("in_advanced_search"):
        context.user_data["in_advanced_search"] = False
        g = "همه"
        if gender == "پسر":
            g = "پسر"
        elif gender == "دختر":
            g = "دختر"
        await update.message.reply_text("🔍 شروع جستجوی پیشرفته...", reply_markup=ReplyKeyboardRemove())
        await start_advanced_search(update, context, g)
        return ConversationHandler.END

    if "هم استانی" in search_type:
        my_profile = await get_user(my_id)
        if my_profile:
            users = await get_users_by_province(my_profile["province"], gender, limit=50)
    elif "هم سن" in search_type:
        my_profile = await get_user(my_id)
        if my_profile:
            users = await get_users_by_age(my_profile["age"], gender, limit=50)
    elif "کاربران جدید" in search_type:
        users = await get_new_users(gender, limit=50)
    elif "بدون چت" in search_type:
        users = await get_users_without_chat(my_id, gender, limit=50)
    elif "محبوب" in search_type:
        users = await get_popular_users(gender, limit=50)
    elif "recent" in search_type:
        gender_filter = gender if gender else "همه"
        found = await get_chat_history(my_id, gender_filter)
        if not found:
            await update.message.reply_text("❌ هنوز چتی نداشتی!", reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["search_results"] = found
        context.user_data["search_page"] = 0
        await show_search_page(update, context)
        return ConversationHandler.END
    elif "direct" in search_type:
        # جستجو مستقیم با متن
        search_text = update.message.text.strip().replace("@", "")
        users = await db_get("users", f"username=eq.{search_text}&limit=5")
        if not users:
            await update.message.reply_text("😔 کاربر پیدا نشد!", reply_markup=main_menu())
            return ConversationHandler.END
    elif "مخاطب خاص" in search_type:
        # جستجو بر اساس نام یا آیدی
        search_query = gender_text  # اینجا text همون ورودی کاربره
        all_users = await db_get("users", f"telegram_id=neq.{my_id}&is_banned=eq.false&limit=50")
        users = [u for u in all_users if 
                search_query.lower() in str(u.get("display_name", "")).lower() or
                search_query.lower() in str(u.get("username", "")).lower() or
                search_query == str(u.get("telegram_id", ""))]

    # هندل کردن سن در جستجوی پیشرفته
    if context.user_data.get("in_adv_age"):
        if "بازگشت" in gender_text:
            context.user_data["in_adv_age"] = False
            await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["in_adv_age"] = False
        sa = gender_text
        adv_gender = context.user_data.get("adv_gender")
        keyboard = [["تهران", "اصفهان", "مشهد"], ["شیراز", "تبریز", "سایر"], ["همه استان‌ها"], ["🔙 بازگشت"]]
        await update.message.reply_text(
            "🏙 استان؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        context.user_data["adv_age"] = sa
        context.user_data["in_adv_province"] = True
        return SEARCH_GENDER_NEW

    if context.user_data.get("in_adv_province"):
        if "بازگشت" in gender_text:
            context.user_data["in_adv_province"] = False
            await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["in_adv_province"] = False
        sp = gender_text
        adv_gender = context.user_data.get("adv_gender")
        sa = context.user_data.get("adv_age", "هر سنی")
        params = f"telegram_id=neq.{my_id}"
        if adv_gender and adv_gender != "هر دو":
            params += f"&gender=eq.{adv_gender}"
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
        params += "&limit=50"
        found = await db_get("users", params)
        found = [u for u in found if u.get("telegram_id") != my_id]
        if not found:
            await update.message.reply_text("😔 کسی پیدا نشد!", reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["search_results"] = found
        context.user_data["search_page"] = 0
        await show_search_page(update, context)
        return ConversationHandler.END

    # فیلتر کاربر خودش
    users = [u for u in users if u.get("telegram_id") != my_id]

    if not users:
        await update.message.reply_text("😔 کسی پیدا نشد!", reply_markup=main_menu())
        return ConversationHandler.END

    # ذخیره لیست کاربران
    context.user_data["search_results"] = users
    context.user_data["search_page"] = 0

    await show_search_page(update, context)
    return ConversationHandler.END

async def show_search_page_inline(update, context, chat_id):
    """نمایش صفحه نتایج جستجو"""
    users = context.user_data.get("search_results", [])
    page = context.user_data.get("search_page", 0)
    per_page = 10
    start = page * per_page
    end = start + per_page
    page_users = users[start:end]

    if not page_users:
        await context.bot.send_message(chat_id=chat_id, text="📄 صفحه دیگه‌ای نیست!", reply_markup=main_menu())
        return

    total_pages = (len(users) + per_page - 1) // per_page
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📄 صفحه {page+1} از {total_pages} — {len(users)} نفر پیدا شد",
        reply_markup=main_menu()
    )

    for user in page_users:
        like_count = user.get("like_count", 0)
        online_status = get_online_status_text(user)
        display_name = user.get("display_name", "")
        username = user.get("username", "")
        user_link = get_user_link(user)
        gender_emoji = "👦" if user.get("gender") == "پسر" else "👧"

        text = ""
        if display_name:
            text += f"✨ {display_name}\n"
        if username:
            text += f"👤 @{username}\n"
        text += f"\n{gender_emoji} {user.get('gender')} | 🎂 {user.get('age')} | 🏙 {user.get('city')}\n"
        text += f"📡 {online_status}\n"
        text += f"❤️ {like_count}\n"
        text += f"🔗 {user_link}"

        keyboard = user_action_keyboard(user["telegram_id"], like_count)
        if user.get("photo_id"):
            await context.bot.send_photo(chat_id=chat_id, photo=user["photo_id"], caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="HTML")

    if end < len(users):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ صفحه بعد", callback_data=f"search_next_{page+1}")
        ]])
        await context.bot.send_message(chat_id=chat_id, text="برای دیدن بیشتر:", reply_markup=keyboard)

async def show_search_page(update, context):
    """نمایش صفحه‌بندی نتایج جستجو"""
    users = context.user_data.get("search_results", [])
    page = context.user_data.get("search_page", 0)
    per_page = 10
    start = page * per_page
    end = start + per_page
    page_users = users[start:end]

    if not page_users:
        await update.message.reply_text("📄 صفحه دیگه‌ای وجود نداره!", reply_markup=main_menu())
        return

    total_pages = (len(users) + per_page - 1) // per_page
    await update.message.reply_text(
        f"📄 صفحه {page+1} از {total_pages} — {len(users)} نفر پیدا شد",
        reply_markup=main_menu()
    )

    for user in page_users:
        await send_user_card(update, user)

    if end < len(users):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ صفحه بعد", callback_data=f"search_next_{page+1}")
        ]])
        await update.message.reply_text("برای دیدن بیشتر:", reply_markup=keyboard)

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["پسر", "دختر", "هر دو"], ["🔙 بازگشت"]]
    await update.message.reply_text(
        f"🔍 جستجوی پیشرفته\n{BRAND_SEPARATOR}\nجنسیت مورد نظرت؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SEARCH_GENDER

async def search_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "بازگشت" in update.message.text:
        await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
        return ConversationHandler.END
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
    keyboard = [
        ["🏙 شهر", "✨ علایق"],
        ["📸 عکس", "👤 اسم"],
        ["⚧ جنسیت", "🎂 سن"],
        ["📍 موقعیت GPS", "🔙 بازگشت"]
    ]
    await update.message.reply_text(
        f"✏️ ویرایش پروفایل\n{BRAND_SEPARATOR}\nچی رو میخوای ویرایش کنی؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT_CHOICE

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if "بازگشت" in choice:
        await update.message.reply_text("↩️ لغو شد.", reply_markup=main_menu())
        return ConversationHandler.END
    elif "عکس" in choice:
        context.user_data["edit_field"] = "عکس"
        await update.message.reply_text("📸 عکس جدید بفرست:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif "شهر" in choice:
        context.user_data["edit_field"] = "شهر"
        await update.message.reply_text("🏙 شهر جدید بنویس:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif "علایق" in choice:
        context.user_data["edit_field"] = "علایق"
        keyboard = [["موسیقی", "هنر", "کتاب"], ["ورزش", "بازی", "غذا"], ["سفر", "فیلم", "تکنولوژی"]]
        await update.message.reply_text("✨ علایق جدید رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return EDIT_VALUE
    elif "اسم" in choice:
        context.user_data["edit_field"] = "اسم"
        await update.message.reply_text("👤 اسم مستعار جدید بنویس:", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif "جنسیت" in choice:
        context.user_data["edit_field"] = "جنسیت"
        keyboard = [["👦 پسر", "👧 دختر"]]
        await update.message.reply_text("⚧ جنسیت جدید:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return EDIT_VALUE
    elif "سن" in choice:
        context.user_data["edit_field"] = "سن"
        await update.message.reply_text("🎂 سن جدید بنویس (حداقل ۱۸):", reply_markup=ReplyKeyboardRemove())
        return EDIT_VALUE
    elif "GPS" in choice or "موقعیت" in choice:
        context.user_data["edit_field"] = "gps"
        location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
        keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("📍 موقعیت جدیدت رو بفرست:", reply_markup=keyboard)
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
        text = update.message.text
        for emoji in ["🎵 ", "🎨 ", "📚 ", "⚽ ", "🎮 ", "🍕 ", "✈️ ", "🎬 ", "💻 "]:
            text = text.replace(emoji, "")
        await update_user(my_id, {"interests": text})
    elif field == "اسم":
        await update_user(my_id, {"display_name": update.message.text})
    elif field == "جنسیت":
        text = update.message.text.replace("👦 ", "").replace("👧 ", "")
        await update_user(my_id, {"gender": text})
    elif field == "سن":
        text = update.message.text
        if not text.isdigit() or int(text) < 18:
            await update.message.reply_text("❌ سن باید حداقل ۱۸ باشه:")
            return EDIT_VALUE
        await update_user(my_id, {"age": int(text)})
    elif field == "gps":
        if not update.message.location:
            location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
            keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("📍 لطفا موقعیتت رو بفرست:", reply_markup=keyboard)
            return EDIT_VALUE
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        await update_user_location(my_id, lat, lon)
    await update.message.reply_text(
        f"✅ پروفایل به‌روز شد!\n💜 هوشی‌گپ AI پروفایلت رو بهینه کرد.",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

async def nearby_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("5 km", callback_data="nearby_5"),
         InlineKeyboardButton("10 km", callback_data="nearby_10")],
        [InlineKeyboardButton("30 km", callback_data="nearby_30"),
         InlineKeyboardButton("60 km", callback_data="nearby_60")]
    ])
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            f"📍 افراد نزدیک\nتا چه فاصله‌ای؟",
            reply_markup=keyboard
        )
    return ConversationHandler.END

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



def get_search_gender_keyboard(search_type):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👦 پسر", callback_data=f"sg_پسر_{search_type}"),
         InlineKeyboardButton("👧 دختر", callback_data=f"sg_دختر_{search_type}"),
         InlineKeyboardButton("👥 همه", callback_data=f"sg_همه_{search_type}")]
    ])

# ==================== جستجوی پیشرفته Inline ====================

PROVINCES = [
    "اصفهان", "اردبیل", "آذربایجان غربی", "البرز", "ایلام",
    "بوشهر", "تهران", "چهارمحال و بختیاری", "خراسان جنوبی",
    "خراسان رضوی", "خراسان شمالی", "خوزستان", "زنجان", "سمنان",
    "سیستان و بلوچستان", "فارس", "قزوین", "قم", "کردستان",
    "کرمان", "کرمانشاه", "کهگیلویه وبویراحمد", "گلستان", "گیلان",
    "لرستان", "مازندران", "مرکزی", "هرمزگان", "همدان", "یزد",
    "آذربایجان شرقی"
]

def get_province_keyboard(selected=None):
    """Inline keyboard برای انتخاب استان"""
    buttons = []
    row = []
    for i, p in enumerate(PROVINCES):
        label = f"✅ {p}" if selected == p else p
        row.append(InlineKeyboardButton(label, callback_data=f"adv_prov_{p}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("✅ انتخاب همه", callback_data="adv_prov_all"),
        InlineKeyboardButton("➡️ مرحله بعدی", callback_data="adv_next_age")
    ])
    return InlineKeyboardMarkup(buttons)

def get_age_keyboard(min_age=None, max_age=None):
    """Inline keyboard برای انتخاب سن"""
    buttons = []
    row = []
    for age in range(9, 100):
        if min_age and age == min_age:
            label = f"✅{age}"
        elif max_age and age == max_age:
            label = f"✅{age}"
        else:
            label = str(age)
        row.append(InlineKeyboardButton(label, callback_data=f"adv_age_{age}"))
        if len(row) == 7:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("👥 همه سنی‌ها", callback_data="adv_age_all")])
    return InlineKeyboardMarkup(buttons)

def get_last_seen_keyboard():
    """Inline keyboard برای آخرین حضور"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تا یک ساعت قبل", callback_data="adv_seen_1h"),
         InlineKeyboardButton("تا 6 ساعت قبل", callback_data="adv_seen_6h")],
        [InlineKeyboardButton("تا یک روز قبل", callback_data="adv_seen_1d"),
         InlineKeyboardButton("تا دو روز قبل", callback_data="adv_seen_2d")],
        [InlineKeyboardButton("تا سه روز قبل", callback_data="adv_seen_3d"),
         InlineKeyboardButton("همه", callback_data="adv_seen_all")]
    ])

async def start_advanced_search(update, context, gender):
    """شروع جستجوی پیشرفته inline"""
    context.user_data["adv_gender"] = gender
    context.user_data["adv_province"] = None
    context.user_data["adv_min_age"] = None
    context.user_data["adv_max_age"] = None

    text = (
        f"🔍 جستجوی پیشرفته\n"
        f"━━━━━━━━━━━━\n"
        f"👫 جنسیت: [{gender}]\n"
        f"🎯 استان های انتخاب شده: []\n\n"
        f"استان های مورد نظرتو انتخاب کن و در آخر گزینه ➡️ مرحله بعدی رو بزن 👇"
    )

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=get_province_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=get_province_keyboard())


async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_profile_btn":
        from_id = update.effective_user.id
        keyboard = [
            ["🏙 شهر", "✨ علایق"],
            ["📸 عکس", "👤 اسم"],
            ["⚧ جنسیت", "🎂 سن"],
            ["📍 موقعیت GPS", "🔙 بازگشت"]
        ]
        await context.bot.send_message(
            chat_id=from_id,
            text=f"✏️ ویرایش پروفایل\n{BRAND_SEPARATOR}\nچی رو میخوای ویرایش کنی؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        context.user_data["edit_field"] = None
        context.user_data["waiting_edit"] = True
        return

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

    if query.data == "admin_shadowban":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر برای shadowban (سطح ۱):")
        context.user_data["admin_action"] = "shadowban"
        return

    if query.data == "admin_unshadowban":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر برای رفع shadowban:")
        context.user_data["admin_action"] = "unshadowban"
        return

    if query.data == "admin_vip":
        from_id = update.effective_user.id
        if from_id not in ADMIN_IDS:
            return
        await context.bot.send_message(chat_id=from_id, text="🆔 آیدی عددی کاربر برای دادن VIP:")
        context.user_data["admin_action"] = "vip"
        return

    if query.data.startswith("gift_coins_"):
        to_id = int(query.data.split("_")[2])
        from_id = update.effective_user.id
        if from_id == to_id:
            await query.answer("❌ نمی‌تونی به خودت سکه هدیه بدی!", show_alert=True)
            return
        coins = await get_coins(from_id)
        if coins < 5:
            await query.answer("❌ حداقل ۵ سکه لازمه برای هدیه دادن!", show_alert=True)
            return
        await deduct_coin(from_id)
        await deduct_coin(from_id)
        await deduct_coin(from_id)
        await deduct_coin(from_id)
        await deduct_coin(from_id)
        await add_coins(to_id, 5)
        await query.answer("🎁 ۵ سکه هدیه دادی!", show_alert=True)
        try:
            await context.bot.send_message(
                chat_id=to_id,
                text=f"🎁 یک کاربر ۵ سکه به شما هدیه داد!\n💜 از هوشی‌گپ لذت ببرید!"
            )
        except:
            pass
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

    if query.data == "buy_vip_coins":
        from_id = update.effective_user.id
        success, msg = await buy_vip_with_coins(from_id)
        await context.bot.send_message(chat_id=from_id, text=msg, reply_markup=main_menu())
        return

    if query.data == "buy_vip_toman":
        from_id = update.effective_user.id
        await context.bot.send_message(
            chat_id=from_id,
            text=(
                f"💳 خرید VIP\n{BRAND_SEPARATOR}\n"
                f"قیمت: {VIP_PRICE_TOMAN:,} تومان\n\n"
                f"برای خرید با پشتیبانی تماس بگیرید.\n"
                f"بعد از پرداخت VIP فعال می‌شود."
            )
        )
        return

    if query.data == "vip_broadcast_chat":
        from_id = update.effective_user.id
        vip = await is_vip(from_id)
        if not vip:
            await query.answer("❌ VIP نیستید!", show_alert=True)
            return
        status = await get_vip_broadcast_status(from_id)
        if status["chat_remaining"] <= 0:
            await query.answer("❌ ظرفیت چت همگانی تمام شده!", show_alert=True)
            return
        context.user_data["vip_action"] = "broadcast_chat"
        await context.bot.send_message(
            chat_id=from_id,
            text=f"💬 چت همگانی VIP\n{BRAND_SEPARATOR}\nپیام درخواست چت رو بنویس:\n({status['chat_remaining']} بار باقی)",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if query.data == "vip_broadcast_dm":
        from_id = update.effective_user.id
        vip = await is_vip(from_id)
        if not vip:
            await query.answer("❌ VIP نیستید!", show_alert=True)
            return
        status = await get_vip_broadcast_status(from_id)
        if status["dm_remaining"] <= 0:
            await query.answer("❌ ظرفیت پیام همگانی تمام شده!", show_alert=True)
            return
        context.user_data["vip_action"] = "broadcast_dm"
        await context.bot.send_message(
            chat_id=from_id,
            text=f"📨 پیام همگانی VIP\n{BRAND_SEPARATOR}\nپیام دایرکت رو بنویس:\n({status['dm_remaining']} بار باقی)",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if query.data == "coins_vip":
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                f"👑 امکانات VIP\n{BRAND_SEPARATOR}\n"
                f"⭐️ نشان VIP روی پروفایل\n"
                f"👑 اول لیست جستجوها\n"
                f"💬 چت همگانی به ۱۰ نفر\n"
                f"📨 پیام همگانی به ۱۰ نفر\n"
                f"⏰ دائمی — بدون محدودیت زمانی\n"
                f"{BRAND_SEPARATOR}\n"
                f"💰 {VIP_PRICE_TOMAN:,} تومان یا {VIP_PRICE_COINS:,} سکه"
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

    if query.data == "done":
        await query.answer()
        return

    if query.data.startswith("nearby_"):
        km = int(query.data.replace("nearby_", ""))
        from_id = update.effective_user.id
        context.user_data["nearby_km"] = km
        location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
        keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
        await query.edit_message_text(f"📍 فاصله: {km} کیلومتر\nموقعیتت رو بفرست:")
        await context.bot.send_message(chat_id=from_id, text="📍 موقعیتت رو بفرست:", reply_markup=keyboard)
        context.user_data["waiting_nearby_location"] = True
        return

    if query.data == "ns_back":
        await query.edit_message_text("↩️ لغو شد.")
        await context.bot.send_message(chat_id=update.effective_user.id, text="به منو برگشتی.", reply_markup=main_menu())
        return

    if query.data in ["ns_age", "ns_province", "ns_nochat", "ns_new", "ns_recent", "ns_popular"]:
        await query.edit_message_text(
            "جنسیت مورد نظر؟",
            reply_markup=get_search_gender_keyboard(query.data.replace("ns_", ""))
        )
        return

    if query.data == "ns_advanced":
        await query.edit_message_text(
            "🔍 جستجوی پیشرفته\nجنسیت مورد نظر؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👦 پسر", callback_data="adv_start_پسر"),
                 InlineKeyboardButton("👧 دختر", callback_data="adv_start_دختر"),
                 InlineKeyboardButton("👥 همه", callback_data="adv_start_همه")]
            ])
        )
        return

    if query.data.startswith("adv_start_"):
        gender = query.data.replace("adv_start_", "")
        await query.edit_message_text(f"🔍 جستجوی پیشرفته\nجنسیت: {gender}")
        await start_advanced_search(update, context, gender)
        return

    if query.data == "ns_gps":
        from_id = update.effective_user.id
        location_button = KeyboardButton("📍 ارسال موقعیت", request_location=True)
        keyboard = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
        await context.bot.send_message(chat_id=from_id, text="📍 موقعیتت رو بفرست:", reply_markup=keyboard)
        context.user_data["waiting_location_search"] = True
        return

    if query.data == "ns_direct":
        from_id = update.effective_user.id
        context.user_data["search_type"] = "direct"
        await context.bot.send_message(chat_id=from_id, text="💌 آیدی یا یوزرنیم مخاطب رو بنویس:", reply_markup=ReplyKeyboardRemove())
        context.user_data["waiting_direct_search"] = True
        return

    if query.data.startswith("sg_"):
        parts = query.data.split("_")
        gender = parts[1]
        search_type = parts[2]
        from_id = update.effective_user.id
        my_id = from_id
        users = []

        if search_type == "age":
            my_profile = await get_user(my_id)
            if my_profile:
                users = await get_users_by_age(my_profile["age"], gender if gender != "همه" else None, limit=50)
        elif search_type == "province":
            my_profile = await get_user(my_id)
            if my_profile:
                users = await get_users_by_province(my_profile["province"], gender if gender != "همه" else None, limit=50)
        elif search_type == "nochat":
            users = await get_users_without_chat(my_id, gender if gender != "همه" else None, limit=50)
        elif search_type == "new":
            users = await get_new_users(gender if gender != "همه" else None, limit=50)
        elif search_type == "popular":
            users = await get_popular_users(gender if gender != "همه" else None, limit=50)
        elif search_type == "recent":
            found = await get_chat_history(my_id, gender if gender != "همه" else "همه")
            users = found if found else []

        users = [u for u in users if u.get("telegram_id") != my_id]

        if not users:
            await query.edit_message_text("😔 کسی پیدا نشد!")
            await context.bot.send_message(chat_id=from_id, text="به منو برگشتی.", reply_markup=main_menu())
            return

        context.user_data["search_results"] = users
        context.user_data["search_page"] = 0
        await query.edit_message_text(f"✅ {len(users)} نفر پیدا شد!")
        await show_search_page_inline(update, context, from_id)
        return

    # جستجوی پیشرفته inline
    if query.data.startswith("adv_prov_"):
        prov = query.data.replace("adv_prov_", "")
        from_id = update.effective_user.id
        if prov == "all":
            context.user_data["adv_province"] = "all"
        else:
            context.user_data["adv_province"] = prov
        gender = context.user_data.get("adv_gender", "همه")
        text = (
            f"🔍 جستجوی پیشرفته\n━━━━━━━━━━━━\n"
            f"👫 جنسیت: [{gender}]\n"
            f"🎯 استان های انتخاب شده: [{prov if prov != 'all' else 'همه'}]\n"
            f"👥 بازه سنی: [? - ?]\n\n"
            f"حداقل سن بازه رو انتخاب کن 👇"
        )
        try:
            await query.edit_message_text(text, reply_markup=get_age_keyboard())
        except:
            await context.bot.send_message(chat_id=from_id, text=text, reply_markup=get_age_keyboard())
        return

    if query.data.startswith("adv_age_"):
        age_val = query.data.replace("adv_age_", "")
        from_id = update.effective_user.id
        gender = context.user_data.get("adv_gender", "همه")
        prov = context.user_data.get("adv_province", "همه")

        if age_val == "all":
            context.user_data["adv_min_age"] = None
            context.user_data["adv_max_age"] = None
            text = (
                f"🔍 جستجوی پیشرفته\n━━━━━━━━━━━━\n"
                f"👫 جنسیت: [{gender}]\n"
                f"🎯 استان: [{prov if prov != 'all' else 'همه'}]\n"
                f"👥 بازه سنی: [همه]\n"
                f"👁 آخرین حضور: []\n\n"
                f"آخرین زمان حضور کاربر رو انتخاب کن 👇"
            )
            try:
                await query.edit_message_text(text, reply_markup=get_last_seen_keyboard())
            except:
                await context.bot.send_message(chat_id=from_id, text=text, reply_markup=get_last_seen_keyboard())
            return

        if not context.user_data.get("adv_min_age"):
            context.user_data["adv_min_age"] = int(age_val)
            text = (
                f"🔍 جستجوی پیشرفته\n━━━━━━━━━━━━\n"
                f"👫 جنسیت: [{gender}]\n"
                f"🎯 استان: [{prov if prov != 'all' else 'همه'}]\n"
                f"👥 بازه سنی: [{age_val} - ?]\n\n"
                f"حالا حداکثر سن رو انتخاب کن 👇"
            )
            try:
                await query.edit_message_text(text, reply_markup=get_age_keyboard(min_age=int(age_val)))
            except:
                await context.bot.send_message(chat_id=from_id, text=text, reply_markup=get_age_keyboard(min_age=int(age_val)))
        else:
            context.user_data["adv_max_age"] = int(age_val)
            min_age = context.user_data["adv_min_age"]
            text = (
                f"🔍 جستجوی پیشرفته\n━━━━━━━━━━━━\n"
                f"👫 جنسیت: [{gender}]\n"
                f"🎯 استان: [{prov if prov != 'all' else 'همه'}]\n"
                f"👥 بازه سنی: [{min_age} - {age_val}]\n"
                f"👁 آخرین حضور: []\n\n"
                f"آخرین زمان حضور کاربر رو انتخاب کن 👇"
            )
            try:
                await query.edit_message_text(text, reply_markup=get_last_seen_keyboard())
            except:
                await context.bot.send_message(chat_id=from_id, text=text, reply_markup=get_last_seen_keyboard())
        return

    if query.data.startswith("adv_seen_"):
        from core.users import db_get as _db_get
        seen_val = query.data.replace("adv_seen_", "")
        from_id = update.effective_user.id
        my_id = from_id
        gender = context.user_data.get("adv_gender", "همه")
        prov = context.user_data.get("adv_province")
        min_age = context.user_data.get("adv_min_age")
        max_age = context.user_data.get("adv_max_age")

        # ساخت query
        params = f"telegram_id=neq.{my_id}"
        if gender and gender not in ["همه", "هر دو"]:
            params += f"&gender=eq.{gender}"
        if prov and prov != "all":
            params += f"&province=eq.{prov}"
        if min_age:
            params += f"&age=gte.{min_age}"
        if max_age:
            params += f"&age=lte.{max_age}"
        if seen_val != "all":
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            if seen_val == "1h":
                cutoff = now - timedelta(hours=1)
            elif seen_val == "6h":
                cutoff = now - timedelta(hours=6)
            elif seen_val == "1d":
                cutoff = now - timedelta(days=1)
            elif seen_val == "2d":
                cutoff = now - timedelta(days=2)
            elif seen_val == "3d":
                cutoff = now - timedelta(days=3)
            params += f"&last_seen=gte.{cutoff.isoformat()}"

        params += "&limit=50"
        users = await _db_get("users", params)

        if not users:
            await query.edit_message_text(
                "😔 کسی پیدا نشد! فیلترها رو تغییر بده.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 جستجوی جدید", callback_data="new_adv_search")
                ]])
            )
            await context.bot.send_message(chat_id=from_id, text="به منو برگشتی.", reply_markup=main_menu())
            return

        context.user_data["search_results"] = users
        context.user_data["search_page"] = 0

        await query.edit_message_text(f"✅ {len(users)} نفر پیدا شد!")
        await show_search_page_inline(update, context, from_id)
        return

    if query.data == "new_adv_search":
        from_id = update.effective_user.id
        gender = context.user_data.get("adv_gender", "همه")
        await start_advanced_search(update, context, gender)
        return

    if query.data == "profile_gps":
        from_id = update.effective_user.id
        user = await get_user(from_id)
        if user and user.get("latitude"):
            lat = user.get("latitude")
            lon = user.get("longitude")
            await context.bot.send_location(chat_id=from_id, latitude=lat, longitude=lon)
        else:
            await query.answer("❌ موقعیت GPS ثبت نشده!", show_alert=True)
        return

    if query.data == "profile_likers":
        from_id = update.effective_user.id
        from core.users import db_get as _db_get
        likers = await _db_get("likes", f"to_user=eq.{from_id}&select=from_user&limit=10")
        if not likers:
            await query.answer("❌ هنوز کسی لایک نکرده!", show_alert=True)
            return
        text = f"❤️ لایک کننده‌ها:\n{BRAND_SEPARATOR}\n"
        for l in likers:
            u = await get_user(l["from_user"])
            if u:
                text += f"• {u.get('display_name') or u.get('username') or str(u['telegram_id'])}\n"
        await context.bot.send_message(chat_id=from_id, text=text)
        return

    if query.data == "profile_likes":
        from_id = update.effective_user.id
        coins = await get_coins(from_id)
        user = await get_user(from_id)
        like_count = user.get("like_count", 0) if user else 0
        await query.answer(f"❤️ {like_count} لایک | 🪙 {coins} سکه", show_alert=True)
        return

    if query.data == "profile_contacts":
        from_id = update.effective_user.id
        from core.users import db_get as _db_get
        contacts = await _db_get("contacts", f"user_id=eq.{from_id}&limit=20")
        if not contacts:
            await query.answer("❌ لیست مخاطبین خالیه!", show_alert=True)
            return
        await context.bot.send_message(chat_id=from_id, text=f"👫 لیست مخاطبین:\n{BRAND_SEPARATOR}")
        for c in contacts:
            u = await get_user(c["contact_id"])
            if u:
                like_count = u.get("like_count", 0)
                keyboard = user_action_keyboard(u["telegram_id"], like_count)
                text = format_profile_card(u)
                if u.get("photo_id"):
                    await context.bot.send_photo(chat_id=from_id, photo=u["photo_id"], caption=text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await context.bot.send_message(chat_id=from_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    if query.data == "profile_blocked":
        from_id = update.effective_user.id
        blocked_ids = await get_blocked_ids(from_id)
        if not blocked_ids:
            await query.answer("❌ کسی رو بلاک نکردی!", show_alert=True)
            return
        await context.bot.send_message(chat_id=from_id, text=f"🚫 بلاک شده‌ها:\n{BRAND_SEPARATOR}")
        for bid in blocked_ids[:10]:
            u = await get_user(bid)
            if u:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ آنبلاک", callback_data=f"unblock_{bid}")
                ]])
                text = format_profile_card(u, show_link=False)
                await context.bot.send_message(chat_id=from_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    if query.data == "profile_silent":
        from_id = update.effective_user.id
        user = await get_user(from_id)
        is_silent = user.get("is_silent", False) if user else False
        if is_silent:
            # غیرفعال کردن سایلنت
            await update_user(from_id, {"is_silent": False, "silent_until": None})
            await query.answer("🔔 حالت سایلنت غیرفعال شد!", show_alert=True)
        else:
            # نمایش گزینه‌های سایلنت
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔕 سایلنت تا 30 دقیقه", callback_data="silent_30m"),
                 InlineKeyboardButton("🔕 سایلنت تا یک ساعت", callback_data="silent_1h")],
                [InlineKeyboardButton("🔕 همیشه سایلنت", callback_data="silent_forever")],
                [InlineKeyboardButton("🔔 غیرفعال کردن سایلنت", callback_data="silent_off")]
            ])
            await query.edit_message_reply_markup(reply_markup=keyboard)
        return

    if query.data.startswith("silent_"):
        from_id = update.effective_user.id
        val = query.data.replace("silent_", "")
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)

        if val == "off":
            await update_user(from_id, {"is_silent": False, "silent_until": None})
            await query.answer("🔔 سایلنت غیرفعال شد!", show_alert=True)
        elif val == "30m":
            until = (now + timedelta(minutes=30)).isoformat()
            await update_user(from_id, {"is_silent": True, "silent_until": until})
            await query.answer("🔕 سایلنت تا 30 دقیقه فعال شد!", show_alert=True)
        elif val == "1h":
            until = (now + timedelta(hours=1)).isoformat()
            await update_user(from_id, {"is_silent": True, "silent_until": until})
            await query.answer("🔕 سایلنت تا یک ساعت فعال شد!", show_alert=True)
        elif val == "forever":
            await update_user(from_id, {"is_silent": True, "silent_until": None})
            await query.answer("🔕 همیشه سایلنت فعال شد!", show_alert=True)
        return

    if query.data == "profile_settings":
        from_id = update.effective_user.id
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 ویس پروفایل", callback_data="settings_voice")],
            [InlineKeyboardButton("🔔 اطلاع‌رسانی‌ها", callback_data="settings_notif")],
            [InlineKeyboardButton("🗑 حذف حساب", callback_data="settings_delete")]
        ])
        await context.bot.send_message(
            chat_id=from_id,
            text=f"⚙️ تنظیمات پیشرفته\n{BRAND_SEPARATOR}",
            reply_markup=keyboard
        )
        return

    if query.data == "settings_voice":
        from_id = update.effective_user.id
        voice = await get_voice_profile(from_id)
        if voice:
            mode = voice.get("voice_mode", VOICE_MODE_REAL)
            label = get_voice_label(mode)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ پخش ویس", callback_data="play_my_voice")],
                [InlineKeyboardButton("🔄 جایگزینی", callback_data="replace_voice"),
                 InlineKeyboardButton("🗑 حذف", callback_data="delete_voice")],
                [InlineKeyboardButton("🔒 تغییر حریم خصوصی", callback_data="change_voice_mode")]
            ])
            await context.bot.send_message(chat_id=from_id, text=f"🎤 ویس پروفایل\nحالت: {label}", reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎤 اضافه کردن ویس", callback_data="add_voice")]])
            await context.bot.send_message(chat_id=from_id, text="🎤 ویس پروفایل نداری!", reply_markup=keyboard)
        return

    if query.data == "settings_delete":
        from_id = update.effective_user.id
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ بله، حذف شود", callback_data="confirm_delete"),
             InlineKeyboardButton("❌ انصراف", callback_data="cancel_delete")]
        ])
        await context.bot.send_message(chat_id=from_id, text="⚠️ آیا مطمئنی؟ حساب کاربری حذف میشه!", reply_markup=keyboard)
        return

    if query.data == "confirm_delete":
        from_id = update.effective_user.id
        from core.users import db_delete as _db_delete
        import httpx
        headers = {"apikey": "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R", "Authorization": f"Bearer sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"}
        async with httpx.AsyncClient() as client:
            await client.delete(f"https://ahjdziimhlpynvvwhgiz.supabase.co/rest/v1/users?telegram_id=eq.{from_id}", headers=headers)
        await context.bot.send_message(chat_id=from_id, text="✅ حساب کاربری حذف شد.", reply_markup=ReplyKeyboardRemove())
        return

    if query.data == "cancel_delete":
        await query.answer("❌ انصراف داده شد.")
        return

    if query.data.startswith("search_next_"):
        page = int(query.data.split("_")[2])
        context.user_data["search_page"] = page

        await show_search_page(update, context)
        return

    if query.data == "skip":

        await save_skip(update.effective_user.id, 0)
        return

    if query.data == "random_next":

        return

    if query.data.startswith("gift_coins_"):
        to_id = int(query.data.split("_")[2])
        from_id = update.effective_user.id
        coins = await get_coins(from_id)
        if coins < 5:
            await query.answer("❌ حداقل ۵ سکه نیاز داری!", show_alert=True)
            return
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 هدیه ۵ سکه", callback_data=f"do_gift_5_{to_id}")],
            [InlineKeyboardButton("🎁 هدیه ۱۰ سکه", callback_data=f"do_gift_10_{to_id}")],
            [InlineKeyboardButton("🎁 هدیه ۲۰ سکه", callback_data=f"do_gift_20_{to_id}")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_gift")]
        ])
        await context.bot.send_message(chat_id=from_id, text=f"🎁 چند سکه هدیه بدی?\n🪙 سکه فعلی شما: {coins}", reply_markup=keyboard)
        return

    if query.data.startswith("do_gift_"):
        parts = query.data.split("_")
        amount = int(parts[2])
        to_id = int(parts[3])
        from_id = update.effective_user.id
        coins = await get_coins(from_id)
        if coins < amount:
            await query.answer(f"❌ سکه کافی نداری! داری: {coins}", show_alert=True)
            return
        await add_coins(from_id, -amount)
        await add_coins(to_id, amount)
        await context.bot.send_message(chat_id=from_id, text=f"✅ {amount} سکه هدیه دادی!")
        try:
            await context.bot.send_message(chat_id=to_id, text=f"🎁 {amount} سکه هدیه گرفتی از یه کاربر هوشی‌گپ!")
        except:
            pass
        return

    if query.data == "cancel_gift":

        return

    if query.data.startswith("add_contact_"):
        to_id = int(query.data.split("_")[2])
        from_id = update.effective_user.id
        from core.users import db_post as users_db_post
        import httpx
        headers = {"apikey": "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R", "Authorization": f"Bearer sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            await client.post("https://ahjdziimhlpynvvwhgiz.supabase.co/rest/v1/contacts", json={"user_id": from_id, "contact_id": to_id}, headers=headers)
        await query.answer("✅ به مخاطبین اضافه شد!", show_alert=True)
        try:
            await context.bot.send_message(chat_id=to_id, text="➕ یک نفر شما را به مخاطبین اضافه کرد!")
        except:
            pass
        return

    if query.data.startswith("notify_online_"):
        to_id = int(query.data.split("_")[2])
        from_id = update.effective_user.id
        if from_id == to_id:
            await query.answer("❌ نمی‌تونی خودت رو دنبال کنی!", show_alert=True)
            return
        # ذخیره در فیلد notify_watchers کاربر هدف
        to_user = await get_user(to_id)
        if to_user:
            watchers = to_user.get("notify_watchers") or []
            if isinstance(watchers, str):
                import json
                try:
                    watchers = json.loads(watchers)
                except:
                    watchers = []
            if from_id not in watchers:
                watchers.append(from_id)
                await update_user(to_id, {"notify_watchers": watchers})
        await query.answer("🔔 وقتی آنلاین شد بهت خبر می‌دیم!", show_alert=True)
        return

    if query.data.startswith("unblock_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        import httpx
        headers = {"apikey": "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R", "Authorization": f"Bearer sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"}
        async with httpx.AsyncClient() as client:
            await client.delete(f"https://ahjdziimhlpynvvwhgiz.supabase.co/rest/v1/blocks?blocker=eq.{from_id}&blocked=eq.{to_id}", headers=headers)
        to_user = await get_user(to_id)
        like_count = to_user.get("like_count", 0) if to_user else 0
        try:
            await query.edit_message_reply_markup(reply_markup=user_action_keyboard(to_id, like_count, False))
        except:
            pass
        await query.answer("✅ آنبلاک شد!", show_alert=False)
        return

    if query.data.startswith("block_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        await block_user(from_id, to_id)
        await block_penalty(to_id)
        to_user = await get_user(to_id)
        like_count = to_user.get("like_count", 0) if to_user else 0
        try:
            await query.edit_message_reply_markup(reply_markup=user_action_keyboard(to_id, like_count, True))
        except:
            pass
        await query.answer("🚫 کاربر بلاک شد.", show_alert=False)
        return

    if query.data.startswith("report_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id
        await report_user(from_id, to_id)
        await report_penalty(to_id)
        await query.answer("✅ گزارش ثبت شد!", show_alert=True)
        return

    if query.data.startswith("chatreq_"):
        to_id = int(query.data.split("_")[1])
        from_id = update.effective_user.id

        # چک کردن سایلنت
        to_user = await get_user(to_id)
        if to_user and to_user.get("is_silent"):
            from datetime import datetime, timezone
            silent_until = to_user.get("silent_until")
            if silent_until:
                try:
                    if silent_until.endswith("Z"):
                        silent_until = silent_until[:-1] + "+00:00"
                    until_dt = datetime.fromisoformat(silent_until)
                    if until_dt.tzinfo is None:
                        until_dt = until_dt.replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) > until_dt:
                        # سایلنت منقضی شده
                        await update_user(to_id, {"is_silent": False, "silent_until": None})
                    else:
                        await query.answer("🔕 این کاربر در حالت سایلنت است و درخواست چت دریافت نمی‌کند!", show_alert=True)
                        return
                except:
                    pass
            else:
                await query.answer("🔕 این کاربر در حالت سایلنت است و درخواست چت دریافت نمی‌کند!", show_alert=True)
                return

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
        await context.bot.send_message(
            chat_id=from_id,
            text=f"✅ درخواست چت ارسال شد!\n⏳ منتظر تایید یا رد کاربر باشید."
        )
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
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ قبول شد", callback_data="done")]
            ]))
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
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ رد شد", callback_data="done")]
            ]))
        except:
            pass
        try:
            await context.bot.send_message(chat_id=from_id, text="❌ درخواست چت شما رد شد.")
        except:
            pass
        return

    # فقط like_ رو هندل کن
    if not query.data.startswith("like_"):
        return

    to_id = int(query.data.split("_")[1])
    from_id = update.effective_user.id

    # چک کردن سکه کافی
    from_coins = await get_coins(from_id)
    if from_coins <= 0:
        await query.answer("❌ سکه کافی نداری! برای لایک کردن ۱ سکه نیاز داری.", show_alert=True)
        return

    # کم کردن یه سکه از لایک کننده
    await deduct_coin(from_id)

    await like_user(from_id, to_id)

    # افزایش تعداد لایک و اضافه کردن یه سکه به لایک شونده
    to_user = await get_user(to_id)
    if to_user:
        current_likes = to_user.get("like_count", 0)
        await update_user(to_id, {"like_count": current_likes + 1})
        await add_coins(to_id, 1)

    is_match = await check_mutual_like(from_id, to_id)
    if is_match:
        # شروع خودکار چت بعد از مچ
        start_chat(from_id, to_id)
        await context.bot.send_message(
            chat_id=from_id,
            text=f"💜 ماتچ شدید!\n{BRAND_SEPARATOR}\n✨ هوشی‌گپ AI شما رو به هم وصل کرد!\n🔴 برای پایان چت دکمه زیر رو بزن",
            reply_markup=chat_menu()
        )
        try:
            await context.bot.send_message(
                chat_id=to_id,
                text=f"💜 ماتچ شدید!\n{BRAND_SEPARATOR}\n✨ هوشی‌گپ AI شما رو به هم وصل کرد!\n🔴 برای پایان چت دکمه زیر رو بزن",
                reply_markup=chat_menu()
            )
        except:
            pass
        # ارسال ویس پروفایل اگه داشتن
        from_profile = await get_user(from_id)
        to_profile = await get_user(to_id)
        if from_profile and from_profile.get("has_voice"):
            await send_voice_profile(context.bot, to_id, from_profile, is_matched=True)
        if to_profile and to_profile.get("has_voice"):
            await send_voice_profile(context.bot, from_id, to_profile, is_matched=True)
    else:
        await context.bot.send_message(chat_id=from_id, text=f"💜 لایک ثبت شد!\n🪙 سکه باقی: {from_coins-1}")
        try:
            await context.bot.send_message(chat_id=to_id, text="💜 یک نفر به پروفایلت لایک داد!\n🪙 ۱ سکه هدیه گرفتی!")
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

    # چک ثبت‌نام
    if not await user_exists(my_id):
        await update.message.reply_text("❌ اول ثبت‌نام کن! /register بزن")
        return

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
    await send_user_card(update, user)
    if user.get("has_voice"):
        await send_voice_profile(context.bot, my_id, user, is_matched=False)

async def random_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from core.users import db_get
    import random
    my_id = update.effective_user.id

    # چک ثبت‌نام
    if not await user_exists(my_id):
        await update.message.reply_text("❌ اول ثبت‌نام کن! /register بزن")
        return

    # فقط کاربران عادی — بدون بن‌شده و shadowban
    users = await db_get("users", f"telegram_id=neq.{my_id}&is_banned=eq.false&shadowban_level=eq.0")
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
    users = await db_get("users", f"telegram_id=neq.{my_id}&age=eq.{my_age}&is_banned=eq.false&shadowban_level=eq.0&limit=5")
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
    vip_badge = "⭐️ VIP " if user.get("is_vip") else ""
    voice_info = ""
    if user.get("has_voice"):
        mode = user.get("voice_mode", VOICE_MODE_REAL)
        label = get_voice_label(mode)
        voice_info = f"🎤 {label}\n"
    gender_emoji = "👦" if user.get("gender") == "پسر" else "👧"
    display_name = user.get("display_name", "")
    like_count = user.get("like_count", 0)
    username = user.get("username", "")
    online_status = get_online_status_text(user)

    lines = []
    if vip_badge:
        lines.append(f"• نام: {display_name} {vip_badge}" if display_name else f"• {vip_badge}")
    elif display_name:
        lines.append(f"• نام: {display_name}")
    lines.append(f"• {gender_emoji} جنسیت: {user.get('gender', '-')}")
    lines.append(f"• 🗺 استان: {user.get('province', '-')}")
    lines.append(f"• 🏙 شهر: {user.get('city', '-')}")
    lines.append(f"• 🎂 سن: {user.get('age', '-')}")
    lines.append("")
    lines.append(f"• ❤️ تعداد لایک ها: {like_count}")
    lines.append("")
    lines.append(f"{online_status}")
    lines.append("")
    if username:
        lines.append(f"🆔 آیدی : /{username}")
    lines.append(f"🪙 سکه: {coins}")
    lines.append(f"💜 امتیاز اعتماد: {trust_score}/100")
    if user.get("is_silent"):
        lines.append(f"🔕 حالت سایلنت: فعال")

    text = "\n".join(lines)

    # وضعیت سایلنت
    is_silent = user.get("is_silent", False)
    silent_text = "🔕 حالت سایلنت (فعال)" if is_silent else "🔔 حالت سایلنت (غیرفعال)"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📍 مشاهده موقعیت GPS من", callback_data="profile_gps")],
        [InlineKeyboardButton("❤️ مشاهده لایک کننده‌ها", callback_data="profile_likers"),
         InlineKeyboardButton("✅ لایک (فعال)", callback_data="profile_likes")],
        [InlineKeyboardButton("👫 لیست مخاطبین", callback_data="profile_contacts"),
         InlineKeyboardButton("🚫 بلاک شده‌ها", callback_data="profile_blocked")],
        [InlineKeyboardButton(silent_text, callback_data="profile_silent")],
        [InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="profile_settings")],
        [InlineKeyboardButton("✏️ ویرایش اطلاعات پروفایل", callback_data="edit_profile_btn")]
    ])

    if user.get("photo_id"):
        await update.message.reply_photo(photo=user["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

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
    await update.message.reply_text(
        f"💜 ثبت‌نام در هوشی‌گپ\n"
        f"{BRAND_SEPARATOR}\n"
        f"اسمت چیه؟ (نام مستعار)",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["display_name"] = update.message.text
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👦 پسر", callback_data="reg_gender_پسر"),
         InlineKeyboardButton("👧 دختر", callback_data="reg_gender_دختر")]
    ])
    await update.message.reply_text("جنسیت شما؟", reply_markup=keyboard)
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # این هندلر برای متن نیست - برای callback هست
    await update.message.reply_text("لطفاً روی یکی از دکمه‌ها کلیک کن.")
    return GENDER

async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    g = query.data.replace("reg_gender_", "")
    context.user_data["gender"] = g
    age_rows = []
    row = []
    for a in list(range(18, 56)) + [57, 60, 65]:
        lbl = f"{a}" if a < 57 else f"{a}+"
        row.append(InlineKeyboardButton(lbl, callback_data=f"reg_age_{a}"))
        if len(row) == 5:
            age_rows.append(row)
            row = []
    if row:
        age_rows.append(row)
    await query.edit_message_text(f"✅ جنسیت: {g}\n\n🎂 سن شما؟", reply_markup=InlineKeyboardMarkup(age_rows))
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً روی یکی از دکمه‌های سن کلیک کن.")
    return AGE

async def age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    a = int(query.data.replace("reg_age_", ""))
    context.user_data["age"] = a
    rows = []
    row = []
    for p in PROVINCES:
        row.append(InlineKeyboardButton(p, callback_data=f"reg_prov_{p}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    await query.edit_message_text(f"✅ سن: {a}\n\n🗺 استان شما؟", reply_markup=InlineKeyboardMarkup(rows))
    return PROVINCE

async def province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً روی یکی از دکمه‌ها کلیک کن.")
    return PROVINCE

PROVINCE_CITIES = {
    "تهران": ["تهران", "شهریر", "پاکدشت", "رباط کریم"],
    "اصفهان": ["اصفهان", "کاشان", "نجف‌آباد", "خمینی‌شهر"],
    "فارس": ["شیراز", "مرودشت", "جهرم", "آباده"],
    "خراسان رضوی": ["مشهد", "نیشابور", "سبزوار", "تربت حیدریه"],
    "آذربایجان شرقی": ["تبریز", "مراغه", "عجبشهر", "بناب"],
    "آذربایجان غربی": ["ارومیه", "خوی", "مهاباد", "سلماس"],
    "مازندران": ["ساری", "آمل", "بابل", "قائمشهر"],
    "گیلان": ["رشت", "انزلی", "بندر انزلی", "لاهیجان"],
    "کرمان": ["کرمان", "رفسنجان", "سیرجان", "شهر بابک"],
    "خوزستان": ["اهواز", "آبادان", "سوسنگورد", "دزفول"],
    "البرز": ["کرج", "مشکینشهر", "ساوجبلاغ", "نظرآباد"],
    "هرمزگان": ["بندرعباس", "میناب شهر", "قشم", "جاسک"],
}

async def province_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    p = query.data.replace("reg_prov_", "")
    context.user_data["province"] = p
    cities = PROVINCE_CITIES.get(p, [])
    if cities:
        rows = []
        row = []
        for c in cities:
            row.append(InlineKeyboardButton(c, callback_data=f"reg_city_{c}"))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        rows.append([InlineKeyboardButton("شهر دیگر...", callback_data="reg_city_other")])
        await query.edit_message_text(f"✅ استان: {p}\n\n🏙 شهر خود رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(rows))
    else:
        await query.edit_message_text(f"✅ استان: {p}\n\n🏙 نام شهر خود رو بنویس:")
    return CITY

async def city_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    c = query.data.replace("reg_city_", "")
    if c == "other":
        await query.edit_message_text("🏙 نام شهرت رو بنویس:")
        return CITY
    context.user_data["city"] = c
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 موسیقی", callback_data="reg_int_موسیقی"),
         InlineKeyboardButton("🎨 هنر", callback_data="reg_int_هنر"),
         InlineKeyboardButton("📚 کتاب", callback_data="reg_int_کتاب")],
        [InlineKeyboardButton("⚽ ورزش", callback_data="reg_int_ورزش"),
         InlineKeyboardButton("🎮 بازی", callback_data="reg_int_بازی"),
         InlineKeyboardButton("🍕 غذا", callback_data="reg_int_غذا")],
        [InlineKeyboardButton("✈️ سفر", callback_data="reg_int_سفر"),
         InlineKeyboardButton("🎬 فیلم", callback_data="reg_int_فیلم"),
         InlineKeyboardButton("💻 تکنولوژی", callback_data="reg_int_تکنولوژی")]
    ])
    await query.edit_message_text(f"✅ شهر: {c}\n\n✨ علایقت رو انتخاب کن:", reply_markup=keyboard)
    return INTERESTS

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 موسیقی", callback_data="reg_int_موسیقی"),
         InlineKeyboardButton("🎨 هنر", callback_data="reg_int_هنر"),
         InlineKeyboardButton("📚 کتاب", callback_data="reg_int_کتاب")],
        [InlineKeyboardButton("⚽ ورزش", callback_data="reg_int_ورزش"),
         InlineKeyboardButton("🎮 بازی", callback_data="reg_int_بازی"),
         InlineKeyboardButton("🍕 غذا", callback_data="reg_int_غذا")],
        [InlineKeyboardButton("✈️ سفر", callback_data="reg_int_سفر"),
         InlineKeyboardButton("🎬 فیلم", callback_data="reg_int_فیلم"),
         InlineKeyboardButton("💻 تکنولوژی", callback_data="reg_int_تکنولوژی")]
    ])
    await update.message.reply_text("✨ علایقت رو انتخاب کن:", reply_markup=keyboard)
    return INTERESTS

async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً روی یکی از دکمه‌ها کلیک کن.")
    return INTERESTS

async def interests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    interest = query.data.replace("reg_int_", "")
    context.user_data["interests"] = interest
    skip_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ بدون عکس (عکس پیش‌فرض)", callback_data="reg_skip_photo")]
    ])
    await query.edit_message_text(f"✅ علاقه: {interest}\n\n📸 عکس پروفایلت رو بفرست:\n(اگه عکس نذاری، یه عکس پیش‌فرض برات میذاریم)", reply_markup=skip_keyboard)
    return PHOTO

DEFAULT_PHOTO_BOY = "https://i.imgur.com/4M34hi2.png"
DEFAULT_PHOTO_GIRL = "https://i.imgur.com/OB0y6MR.png"

def get_default_photo(gender):
    if gender == "دختر":
        return DEFAULT_PHOTO_GIRL
    return DEFAULT_PHOTO_BOY

async def skip_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data
    username = update.effective_user.username or ""
    gender = data.get("gender", "پسر")
    default_photo = get_default_photo(gender)
    await create_user(
        update.effective_user.id, username,
        data["gender"], data["age"], data["province"],
        data["city"], data["interests"], default_photo
    )
    display_name = data.get("display_name", "")
    if display_name:
        await update_user(update.effective_user.id, {"display_name": display_name})
    await query.edit_message_text(
        f"💜 ثبت‌نام کامل شد!\n🎁 ۱۰ سکه هدیه گرفتی!"
    )
    return ConversationHandler.END

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
    display_name = data.get("display_name", "")
    if display_name:
        await update_user(update.effective_user.id, {"display_name": display_name})
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
    TOKEN = os.environ.get("BOT_TOKEN", "")
    app = Application.builder().token(TOKEN).build()

    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            GENDER: [
                CallbackQueryHandler(gender_callback, pattern="^reg_gender_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, gender)
            ],
            AGE: [
                CallbackQueryHandler(age_callback, pattern="^reg_age_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, age)
            ],
            PROVINCE: [
                CallbackQueryHandler(province_callback, pattern="^reg_prov_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, province)
            ],
            CITY: [
                CallbackQueryHandler(city_callback, pattern="^reg_city_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, city)
            ],
            INTERESTS: [
                CallbackQueryHandler(interests_callback, pattern="^reg_int_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, interests)
            ],
            PHOTO: [
                CallbackQueryHandler(skip_photo_callback, pattern="^reg_skip_photo$"),
                MessageHandler(filters.PHOTO, photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, photo)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_start),
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
            EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value),
                MessageHandler(filters.PHOTO, edit_value),
                MessageHandler(filters.LOCATION, edit_value)
            ],
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
    new_search_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("جستجو کاربران"), new_search),
            MessageHandler(filters.Regex("جستجوی پیشرفته"), search_type_handler_advanced)
        ],
        states={
            SEARCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_type_handler)],
            SEARCH_GENDER_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_gender_new_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(new_search_conv)
    app.add_handler(search_conv)
    app.add_handler(edit_conv)
    app.add_handler(nearby_conv)
    app.add_handler(recent_conv)
    app.add_handler(register_conv)
    app.add_handler(dm_conv)
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.PHOTO, forward_media))
    app.add_handler(MessageHandler(filters.VIDEO, forward_media))
    app.add_handler(MessageHandler(filters.LOCATION, forward_media))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_in_chat))
    app.add_handler(MessageHandler(filters.AUDIO, forward_media))
    app.add_handler(MessageHandler(filters.Sticker.ALL, forward_media))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, forward_media))
    app.add_handler(MessageHandler(filters.Document.ALL, forward_media))
    app.add_handler(MessageHandler(filters.ANIMATION, forward_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler))
    print("💜 هوشی‌گپ شروع به کار کرد...")
    import httpx
    import requests

    # اول webhook رو پاک کن با requests (sync)
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
        print("✅ Webhook deleted")
    except:
        pass

    # بعد HTTP server رو شروع کن
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, *args):
            pass

    PORT = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
