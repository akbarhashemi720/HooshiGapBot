import httpx
import time
import os
import subprocess
from datetime import datetime

SUPABASE_URL = "https://ahjdziimhlpynvvwhgiz.supabase.co"
SUPABASE_KEY = "sb_publishable_DBlfUH3YcVEsCJ2m-3tOWg_nJNMBh5R"

VOICE_MIN_DURATION = 10
VOICE_MAX_DURATION = 30
VOICE_MODE_REAL = "real"
VOICE_MODE_MODIFIED = "modified"
VOICE_MODE_HIDDEN = "hidden"

async def db_get(table, params=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=headers)
        return r.json()

async def db_patch(table, params, data):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}", json=data, headers=headers)

def validate_voice(duration):
    if duration < VOICE_MIN_DURATION:
        return False, f"\u0648\u06cc\u0633 \u062e\u06cc\u0644\u06cc \u06a9\u0648\u062a\u0627\u0647\u0647! \u062d\u062f\u0627\u0642\u0644 {VOICE_MIN_DURATION} \u062b\u0627\u0646\u06cc\u0647 \u0628\u0627\u0634\u0647"
    if duration > VOICE_MAX_DURATION:
        return False, f"\u0648\u06cc\u0633 \u062e\u06cc\u0644\u06cc \u0628\u0644\u0646\u062f\u0647! \u062d\u062f\u0627\u06a9\u062b\u0631 {VOICE_MAX_DURATION} \u062b\u0627\u0646\u06cc\u0647 \u0628\u0627\u0634\u0647"
    return True, ""

async def download_voice(bot, file_id, output_path):
    try:
        file = await bot.get_file(file_id)
        await file.download_to_drive(output_path)
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def apply_voice_modification_ffmpeg(input_path, output_path):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", "asetrate=44100*0.9,aresample=44100",
            "-c:a", "libopus",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False

async def save_voice_profile(telegram_id, file_id, duration, mode=VOICE_MODE_REAL, bot=None):
    valid, msg = validate_voice(duration)
    if not valid:
        return False, msg
    trust_boost = 5 if mode == VOICE_MODE_REAL else 3 if mode == VOICE_MODE_MODIFIED else 1
    modified_file_id = file_id
    if mode == VOICE_MODE_MODIFIED and bot is not None:
        try:
            input_path = f"temp_voice_{telegram_id}_in.ogg"
            output_path = f"temp_voice_{telegram_id}_out.ogg"
            downloaded = await download_voice(bot, file_id, input_path)
            if downloaded:
                success = apply_voice_modification_ffmpeg(input_path, output_path)
                if success:
                    with open(output_path, "rb") as f:
                        sent = await bot.send_voice(chat_id=telegram_id, voice=f)
                    modified_file_id = sent.voice.file_id
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
        except Exception as e:
            print(f"Voice modification failed: {e}")
            modified_file_id = file_id
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "voice_id": modified_file_id,
        "voice_duration": duration,
        "has_voice": True,
        "voice_mode": mode,
        "voice_uploaded_at": datetime.now().isoformat()
    })
    from safety import update_trust
    await update_trust(telegram_id, trust_boost)
    mode_text = {
        VOICE_MODE_REAL: "\u0648\u06cc\u0633 \u0648\u0627\u0642\u0639\u06cc",
        VOICE_MODE_MODIFIED: "\u0648\u06cc\u0633 \u062a\u063a\u06cc\u06cc\u0631\u06cc\u0627\u0641\u062a\u0647",
        VOICE_MODE_HIDDEN: "\u0648\u06cc\u0633 \u067e\u0646\u0647\u0627\u0646"
    }.get(mode, "")
    return True, f"\u2705 \u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f! ({mode_text})"

async def delete_voice_profile(telegram_id):
    await db_patch("users", f"telegram_id=eq.{telegram_id}", {
        "voice_id": "",
        "voice_duration": 0,
        "has_voice": False,
        "voice_mode": "",
        "voice_uploaded_at": None
    })
    from safety import update_trust
    await update_trust(telegram_id, -2)
    return True, "\u0648\u06cc\u0633 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u062d\u0630\u0641 \u0634\u062f"

async def get_voice_profile(telegram_id):
    users = await db_get("users", f"telegram_id=eq.{telegram_id}&select=voice_id,voice_duration,has_voice,voice_mode")
    if users and users[0].get("has_voice"):
        return users[0]
    return None

def get_voice_badge(user):
    if not user.get("has_voice"):
        return ""
    mode = user.get("voice_mode", VOICE_MODE_REAL)
    if mode == VOICE_MODE_HIDDEN:
        return "\U0001f512 "
    return "\U0001f3a4 "

def get_voice_label(mode):
    labels = {
        VOICE_MODE_REAL: "\U0001f3a4 \u0648\u06cc\u0633 \u0648\u0627\u0642\u0639\u06cc",
        VOICE_MODE_MODIFIED: "\U0001f527 \u0648\u06cc\u0633 \u062a\u063a\u06cc\u06cc\u0631\u06cc\u0627\u0641\u062a\u0647",
        VOICE_MODE_HIDDEN: "\U0001f512 \u0648\u06cc\u0633 \u067e\u0646\u0647\u0627\u0646"
    }
    return labels.get(mode, "\U0001f3a4 \u0648\u06cc\u0633")

async def send_voice_profile(bot, chat_id, target_user, is_matched=False):
    voice_id = target_user.get("voice_id")
    duration = target_user.get("voice_duration", 0)
    mode = target_user.get("voice_mode", VOICE_MODE_REAL)
    if not voice_id:
        return False
    if mode == VOICE_MODE_HIDDEN and not is_matched:
        await bot.send_message(
            chat_id=chat_id,
            text="\U0001f512 \u0648\u06cc\u0633 \u067e\u0646\u0647\u0627\u0646 \u0647\u0633\u062a - \u0628\u0639\u062f \u0627\u0632 \u0642\u0628\u0648\u0644 \u0686\u062a \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0645\u06cc\u0634\u0647"
        )
        return True
    label = get_voice_label(mode)
    try:
        await bot.send_voice(
            chat_id=chat_id,
            voice=voice_id,
            caption=f"{label} ({duration} \u062b\u0627\u0646\u06cc\u0647)"
        )
        return True
    except:
        return False