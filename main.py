import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ========================================
# توکن خودت را اینجا بگذار
# ========================================
BOT_TOKEN = "8898380201:AAFKeXvAnOSwgvha1xGrwQxWIB8fGfEkVaE"
# ========================================

# چک کردن
if not BOT_TOKEN or BOT_TOKEN == "توکن_واقعی_خودت_را_اینجا_بگذار":
    print("❌ ERROR: Please put your real token in the code!")
    exit(1)

print(f"✅ Token loaded. Length: {len(BOT_TOKEN)}")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 جستجو")], [KeyboardButton(text="❌ خروج")]],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ ربات کار می‌کند!", reply_markup=main_menu())

@dp.message()
async def handle_message(message: Message):
    if message.text == "❌ خروج":
        await message.answer("خداحافظ!")

async def main():
    print("🚀 Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
