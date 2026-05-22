import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو در کانال‌های عضو")],
            [KeyboardButton(text="❌ خروج")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "سلام! به ربات خوش اومدی.\nاز منوی پایین یکی رو انتخاب کن:",
        reply_markup=main_menu()
    )

@dp.message()
async def handle_message(message: Message):
    if message.text == "🔍 جستجو در کانال‌های عضو":
        await message.answer("🔍 در حال جستجو... این قابلیت به زودی اضافه میشه.")
    elif message.text == "❌ خروج":
        await message.answer("خداحافظ!", reply_markup=None)
    else:
        await message.answer("لطفاً از منو استفاده کن.")

async def main():
    print("✅ ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())