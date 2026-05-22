import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# --- اصلاح اصلی: خواندن درست توکن از متغیر محیطی ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# بررسی: اگر توکن وجود نداشت یا None بود، خطا بده و بایست
if not BOT_TOKEN:
    # این خطا در لاگ Railway نشان داده می‌شود و از ادامه کار جلوگیری می‌کند.
    raise ValueError("ERROR: BOT_TOKEN environment variable is not set!")

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)

# --- ایجاد ربات ---
try:
    bot = Bot(token=BOT_TOKEN)
    print("✅ Bot created successfully!") # این پیام در لاگ Railway نشان داده می‌شود
except Exception as e:
    print(f"❌ Error creating bot: {e}")
    exit(1)

dp = Dispatcher()

# --- منوی ساده برای تست ---
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
    await message.answer("✅ ربات با موفقیت کار می‌کند!", reply_markup=main_menu())

@dp.message()
async def handle_message(message: Message):
    if message.text == "❌ خروج":
        await message.answer("خداحافظ!", reply_markup=None)

async def main():
    print("🚀 Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
