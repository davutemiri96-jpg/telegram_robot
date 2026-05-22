import asyncio
import logging
import os
import zipfile
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from pyrogram.errors import FloodWait
import aiohttp

# ============================================
# تنظیمات - اینجا رو پر کن!
# ============================================
BOT_TOKEN = "8898380201:AAFKeXvAnOSwgvha1xGrwQxWIB8fGfEkVaE"

# از my.telegram.org
API_ID = 38013873
  # عدد api_id خودت
API_HASH = "1f30e5c9cd4633c65ec2f61162195ad0"
# ============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)

DOWNLOAD_PATH = "downloads/"
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# ============================================
# وضعیت‌های ربات
# ============================================
class BotStates(StatesGroup):
    search_keyword = State()
    search_min_duration = State()
    search_target_channel = State()
    public_search_keyword = State()
    compress_password = State()
    compress_split_size = State()
    compress_waiting_file = State()

# ============================================
# منوی اصلی
# ============================================
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو در کانال‌های عضو")],
            [KeyboardButton(text="🌐 جستجوی کانال‌های عمومی")],
            [KeyboardButton(text="🗜️ فشرده‌سازی فایل")],
            [KeyboardButton(text="ℹ️ راهنما"), KeyboardButton(text="❌ خروج")]
        ],
        resize_keyboard=True
    )
    return keyboard

# ============================================
# دستور start
# ============================================
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 **ربات حرفه‌ای جستجو و فشرده‌سازی**\n\n"
        "**3 قابلیت اصلی:**\n\n"
        "1️⃣ **جستجو در کانال‌های عضو**\n"
        "2️⃣ **جستجوی کانال‌های عمومی**\n"
        "3️⃣ **فشرده‌سازی فایل**\n\n"
        "لطفاً یکی از گزینه‌های پایین رو انتخاب کن 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ============================================
# قابلیت 1: جستجو در کانال‌های عضو
# ============================================
@dp.message(lambda message: message.text == "🔍 جستجو در کانال‌های عضو")
async def search_joined_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.search_keyword)
    await message.answer(
        "🔍 **جستجو در کانال‌های عضو**\n\n"
        "📝 **کلیدواژه** مورد نظرت رو وارد کن:\n"
        "(مثال: science, music, آموزش)\n\n"
        "می‌تونی چندتا رو با کاما جدا کنی"
    )

@dp.message(BotStates.search_keyword)
async def get_search_keyword(message: Message, state: FSMContext):
    keywords = [kw.strip().lower() for kw in message.text.split(",")]
    await state.update_data(keywords=keywords)
    await state.set_state(BotStates.search_min_duration)
    await message.answer(
        f"✅ کلیدواژه‌ها: {', '.join(keywords)}\n\n"
        f"🎬 **حداقل تایم ویدیو** رو به ثانیه وارد کن:\n"
        f"(عدد 0 = بدون محدودیت)"
    )

@dp.message(BotStates.search_min_duration)
async def get_search_min_duration(message: Message, state: FSMContext):
    try:
        min_duration = int(message.text)
        await state.update_data(min_duration=min_duration)
        await state.set_state(BotStates.search_target_channel)
        await message.answer(
            f"📢 **آیدی کانال مقصد** رو بفرست:\n\n"
            f"مثال: @my_channel\n"
            f"⚠️ ربات باید در اون کانال ادمین باشه"
        )
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کن!")

@dp.message(BotStates.search_target_channel)
async def get_search_target_channel(message: Message, state: FSMContext):
    target_channel = message.text.strip()
    data = await state.get_data()
    keywords = data.get('keywords', [])
    min_duration = data.get('min_duration', 0)
    
    await message.answer(
        f"✅ **تنظیمات ذخیره شد!**\n\n"
        f"📝 کلیدواژه‌ها: {', '.join(keywords)}\n"
        f"⏱️ حداقل تایم: {min_duration if min_duration > 0 else 'بدون محدودیت'} ثانیه\n"
        f"📢 کانال مقصد: {target_channel}\n\n"
        f"🔄 **در حال جستجو...**\n"
        f"⚠️ این قابلیت در حال توسعه است.\n"
        f"به زودی اضافه میشه!",
        reply_markup=main_menu()
    )
    await state.clear()

# ============================================
# قابلیت 2: جستجوی کانال‌های عمومی
# ============================================
@dp.message(lambda message: message.text == "🌐 جستجوی کانال‌های عمومی")
async def public_search_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.public_search_keyword)
    await message.answer(
        "🌐 **جستجوی کانال‌های عمومی**\n\n"
        "🔍 **کلیدواژه** مورد نظرت رو وارد کن:\n"
        "(مثال: programming, news, music)"
    )

@dp.message(BotStates.public_search_keyword)
async def public_search_execute(message: Message, state: FSMContext):
    keyword = message.text.strip()
    await message.answer(f"🔍 در حال جستجوی **{keyword}** ...\n\n⚠️ این قابلیت در حال توسعه است.\nبه زودی اضافه میشه!")
    await state.clear()
    await message.answer("بازگشت به منوی اصلی:", reply_markup=main_menu())

# ============================================
# قابلیت 3: فشرده‌سازی فایل
# ============================================
@dp.message(lambda message: message.text == "🗜️ فشرده‌سازی فایل")
async def compress_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.compress_password)
    await message.answer(
        "🗜️ **فشرده‌سازی فایل به ZIP**\n\n"
        "🔐 **رمز عبور** رو وارد کن:\n"
        "(اگه نمی‌خوای رمز داشته باشه، عدد 0 رو وارد کن)"
    )

@dp.message(BotStates.compress_password)
async def compress_get_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if password == "0":
        password = None
    await state.update_data(password=password)
    await state.set_state(BotStates.compress_split_size)
    await message.answer(
        f"🔐 رمز: {'بدون رمز' if not password else '********'}\n\n"
        f"📏 **سایز هر پارت** رو به مگابایت وارد کن:\n"
        f"(اگه نمی‌خوای تقسیم بشه، عدد 0 رو وارد کن)"
    )

@dp.message(BotStates.compress_split_size)
async def compress_get_split_size(message: Message, state: FSMContext):
    try:
        split_size = int(message.text)
        if split_size == 0:
            split_size = None
        await state.update_data(split_size=split_size)
        await state.set_state(BotStates.compress_waiting_file)
        await message.answer(
            f"✅ **تنظیمات ذخیره شد!**\n\n"
            f"📤 **حالا فایل رو بفرست** (عکس، ویدیو یا هر فایل دیگه)"
        )
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کن!")

@dp.message(BotStates.compress_waiting_file)
async def compress_receive_file(message: Message, state: FSMContext):
    if not (message.document or message.video or message.photo):
        await message.answer("❌ لطفاً یک فایل (عکس، ویدیو یا سند) بفرست.")
        return
    
    data = await state.get_data()
    password = data.get('password')
    
    if message.document:
        file = message.document
        file_name = file.file_name or f"file_{file.file_id[:8]}"
    elif message.video:
        file = message.video
        file_name = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    else:
        file = message.photo[-1]
        file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    await message.answer(
        f"✅ فایل **{file_name}** دریافت شد!\n"
        f"🔐 رمز: {'دارد' if password else 'ندارد'}\n\n"
        f"🔄 در حال فشرده‌سازی...\n"
        f"⚠️ این قابلیت در حال توسعه است.\n"
        f"به زودی اضافه میشه!",
        reply_markup=main_menu()
    )
    await state.clear()

# ============================================
# راهنما
# ============================================
@dp.message(lambda message: message.text == "ℹ️ راهنما")
async def help_menu(message: Message):
    await message.answer(
        "📖 **راهنمای ربات**\n\n"
        "🔍 **قابلیت 1** - جستجو در کانال‌های عضو\n"
        "🌐 **قابلیت 2** - جستجوی کانال‌های عمومی\n"
        "🗜️ **قابلیت 3** - فشرده‌سازی فایل\n\n"
        "❌ خروج - بستن منو\n"
        "/start - راه‌اندازی مجدد",
        parse_mode="Markdown"
    )

# ============================================
# خروج
# ============================================
@dp.message(lambda message: message.text == "❌ خروج")
async def exit_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 خداحافظ!", reply_markup=None)

# ============================================
# پیام‌های ناشناخته
# ============================================
@dp.message()
async def unknown_message(message: Message):
    await message.answer("❌ گزینه نامعتبر!", reply_markup=main_menu())

# ============================================
# اجرای اصلی
# ============================================
async def main():
    print("=" * 50)
    print("🚀 ربات با موفقیت روشن شد!")
    print("📡 قابلیت‌های فعال:")
    print("   1️⃣ جستجو در کانال‌های عضو (در حال توسعه)")
    print("   2️⃣ جستجوی کانال‌های عمومی (در حال توسعه)")
    print("   3️⃣ فشرده‌سازی فایل (در حال توسعه)")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
