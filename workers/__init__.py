# HooshiGap Workers Layer
# Background tasks and async processing

import asyncio
from core import (
    get_all_users,
    update_trust,
    is_shadowbanned,
    get_shadowban_level,
    remove_shadowban
)

async def cleanup_shadowbans():
    """
    بررسی و پاکسازی shadowban های منقضی شده
    این تابع می‌تونه به صورت دوره‌ای اجرا بشه
    """
    users = await get_all_users()
    for u in users:
        tid = u.get("telegram_id")
        level = await get_shadowban_level(tid)
        if level == 1:
            # shadowban سطح ۱ بعد از مدتی برداشته می‌شه
            await remove_shadowban(tid)

async def daily_trust_decay():
    """
    کاهش تدریجی امتیاز اعتماد کاربران غیرفعال
    """
    users = await get_all_users()
    for u in users:
        tid = u.get("telegram_id")
        await update_trust(tid, -1)

async def run_workers():
    """
    اجرای همه worker ها
    """
    while True:
        try:
            await cleanup_shadowbans()
        except Exception as e:
            print(f"Worker error: {e}")
        await asyncio.sleep(86400)  # هر ۲۴ ساعت

__all__ = ["cleanup_shadowbans", "daily_trust_decay", "run_workers"]
