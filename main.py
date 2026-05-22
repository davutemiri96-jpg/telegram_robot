import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# گرفتن توکن از متغیر محیطی
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# چک کردن اینکه توکن وجود داره یا نه
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not found!")
    print("✅ Make sure you added BOT_TOKEN in Railway Variables")
    exit(1)

print(f"✅ Token found: {BOT_TOKEN[:10]}...")  # فقط ۱۰ کاراکتر اول نشون داده میشه برای امنیت

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)

# ساختن ربات
try:
    bot = Bot(token=BOT_TOKEN)
    print("✅ Bot created successfully!")
except Exception as e:
    print(f"❌ Error creating bot: {e}")
    exit(1)

dp = Dispatcher()

def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو")],
            [KeyboardButton(text="❌ خروج")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "✅ سلام! ربات با موفقیت کار می‌کنه!\n\n"
        "از منوی پایین استفاده کن 👇",
        reply_markup=main_menu()
    )

@dp.message()
async def handle_message(message: Message):
    if message.text == "❌ خروج":
        await message.answer("👋 خداحافظ!", reply_markup=None)
    elif message.text == "🔍 جستجو":
        await message.answer("🔍 قابلیت جستجو به زودی اضافه میشه...")
    else:
        await message.answer("لطفاً از دکمه‌های منو استفاده کن 👆")

async def main():
    print("🚀 Starting bot...")
    print("📡 Connecting to Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
