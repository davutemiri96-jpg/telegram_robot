import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# توکن ربات (توکن خودت اینجاست)
# ============================================
BOT_TOKEN = "8898380201:AAFKeXvAnOSwgvha1xGrwQxWIB8fGfEkVaE"
# ============================================

# تنظیمات اولیه
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# وضعیت‌های مختلف ربات
class BotStates(StatesGroup):
    waiting_keyword = State()
    waiting_channel = State()
    waiting_min_duration = State()
    waiting_password = State()
    waiting_split_size = State()
    waiting_search_public = State()

# ============================================
# منوی اصلی (4 گزینه)
# ============================================
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو در کانال‌های عضو")],
            [KeyboardButton(text="🌐 جستجوی کانال‌های عمومی")],
            [KeyboardButton(text="🗜️ فشرده‌سازی فایل")],
            [KeyboardButton(text="☁️ آپلود در ابر")],
            [KeyboardButton(text="❌ خروج")]
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
        "🤖 **ربات جستجوگر حرفه‌ای**\n\n"
        "این ربات ۴ قابلیت داره:\n\n"
        "1️⃣ جستجو در کانال‌های عضو - کلمات کلیدی رو پیدا می‌کنه و فوروارد می‌کنه\n"
        "2️⃣ جستجوی کانال‌های عمومی - کانال‌های جدید با محتوای دلخواه پیدا می‌کنه\n"
        "3️⃣ فشرده‌سازی فایل - تبدیل به RAR با رمز و تقسیم بندی\n"
        "4️⃣ آپلود در ابر - آپلود و لینک دانلود مستقیم\n\n"
        "لطفاً یکی از گزینه‌های پایین رو انتخاب کن 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ============================================
# قابلیت 1: جستجو در کانال‌های عضو
# ============================================
@dp.message(lambda message: message.text == "🔍 جستجو در کانال‌های عضو")
async def search_joined_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_keyword)
    await message.answer(
        "🔍 **جستجو در کانال‌های عضو**\n\n"
        "لطفاً **کلیدواژه** مورد نظرت رو وارد کن:\n"
        "(مثال: science, music, آموزش)\n\n"
        "می‌تونی چندتا رو با کاما جدا کنی: science, music"
    )

@dp.message(BotStates.waiting_keyword)
async def get_keyword(message: Message, state: FSMContext):
    keywords = [kw.strip().lower() for kw in message.text.split(",")]
    await state.update_data(keywords=keywords)
    await state.set_state(BotStates.waiting_min_duration)
    await message.answer(
        "🎬 **حداقل تایم ویدیو** رو به ثانیه وارد کن\n"
        "(مثال: 60 برای ویدیوهای بالای ۱ دقیقه)\n\n"
        "اگه محدودیت نمی‌خوای، عدد 0 رو وارد کن."
    )

@dp.message(BotStates.waiting_min_duration)
async def get_duration(message: Message, state: FSMContext):
    try:
        min_duration = int(message.text)
        await state.update_data(min_duration=min_duration)
        await state.set_state(BotStates.waiting_channel)
        await message.answer(
            "📢 **آیدی کانال مقصد** رو بفرست\n\n"
            "مثال: @my_channel یا آیدی عددی مثل -1001234567890\n\n"
            "⚠️ ربات باید در اون کانال ادمین باشه"
        )
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کن!")

@dp.message(BotStates.waiting_channel)
async def get_channel(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    data = await state.get_data()
    keywords = data.get('keywords', [])
    min_duration = data.get('min_duration', 0)
    
    await message.answer(
        f"✅ تنظیمات ذخیره شد!\n"
        f"📝 کلیدواژه‌ها: {', '.join(keywords)}\n"
        f"⏱️ حداقل تایم: {min_duration if min_duration > 0 else 'بدون محدودیت'} ثانیه\n"
        f"📢 کانال مقصد: {channel_id}\n\n"
        f"🔄 در حال جستجو...\n"
        f"⚠️ این قابلیت در نسخه فعلی در حال توسعه است.\n"
        f"به زودی اضافه میشه!",
        reply_markup=main_menu()
    )
    await state.clear()

# ============================================
# قابلیت 2: جستجوی کانال‌های عمومی
# ============================================
@dp.message(lambda message: message.text == "🌐 جستجوی کانال‌های عمومی")
async def search_public_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_search_public)
    await message.answer(
        "🌐 **جستجوی کانال‌های عمومی**\n\n"
        "لطفاً **کلیدواژه** مورد نظرت رو وارد کن:\n"
        "(مثال: programming, cat, news)\n\n"
        "من کانال‌های مرتبط رو پیدا می‌کنم و لینکشون رو برات میفرستم."
    )

@dp.message(BotStates.waiting_search_public)
async def search_public_execute(message: Message, state: FSMContext):
    keyword = message.text.strip()
    await message.answer(f"🔍 در حال جستجوی کانال‌های مرتبط با **{keyword}** ...\nاین عملیات چند ثانیه طول میکشه.")
    
    # اینجا کد جستجوی واقعی میاد (الان نمونه)
    await asyncio.sleep(2)
    
    # نتایج نمونه
    results = [
        {"name": f"کانال {keyword} 1", "link": f"https://t.me/example1"},
        {"name": f"کانال {keyword} 2", "link": f"https://t.me/example2"},
    ]
    
    if results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for r in results[:5]:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"📢 {r['name']}", url=r['link'])])
        
        await message.answer(
            f"✅ **نتایج جستجو برای:** {keyword}\n\n"
            f"روی لینک کانال‌ها کلیک کن 👇",
            reply_markup=keyboard
        )
    else:
        await message.answer(f"❌ هیچ کانالی با کلیدواژه **{keyword}** پیدا نشد.")
    
    await state.clear()
    await message.answer("بازگشت به منوی اصلی:", reply_markup=main_menu())

# ============================================
# قابلیت 3: فشرده‌سازی فایل
# ============================================
@dp.message(lambda message: message.text == "🗜️ فشرده‌سازی فایل")
async def compress_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.waiting_password)
    await message.answer(
        "🗜️ **فشرده‌سازی فایل**\n\n"
        "لطفاً **رمز عبور** رو وارد کن:\n"
        "(اگه نمی‌خوای رمز داشته باشه، عدد 0 رو وارد کن)\n\n"
        "بعد از وارد کردن رمز، فایل رو برام بفرست."
    )

@dp.message(BotStates.waiting_password)
async def get_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if password == "0":
        password = None
    await state.update_data(password=password)
    await state.set_state(BotStates.waiting_split_size)
    await message.answer(
        f"🔐 رمز: {'بدون رمز' if not password else '********'}\n\n"
        f"📏 **سایز هر پارت** رو به مگابایت وارد کن:\n"
        f"(پیش‌فرض: 1000 مگابایت - اگه نمی‌خوای تقسیم بشه، 0 رو وارد کن)"
    )

@dp.message(BotStates.waiting_split_size)
async def get_split_size(message: Message, state: FSMContext):
    try:
        split_size = int(message.text)
        if split_size == 0:
            split_size = None
        await state.update_data(split_size=split_size)
        await state.set_state(BotStates.waiting_for_file)
        await message.answer(
            f"✅ تنظیمات ذخیره شد!\n\n"
            f"📤 حالا **فایل** (ویدیو یا عکس) رو برام بفرست.\n"
            f"بعد از دریافت، فشرده میکنم و برات میفرستم."
        )
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کن!")

@dp.message(BotStates.waiting_for_file)
async def receive_file_for_compress(message: Message, state: FSMContext):
    if message.document or message.video or message.photo:
        data = await state.get_data()
        password = data.get('password')
        split_size = data.get('split_size')
        
        await message.answer(
            f"✅ فایل دریافت شد!\n"
            f"🔐 رمز: {'دارد' if password else 'ندارد'}\n"
            f"📦 تقسیم: {'به ' + str(split_size) + 'MB' if split_size else 'خیر'}\n\n"
            f"🔄 در حال فشرده‌سازی...\n"
            f"⚠️ این قابلیت در نسخه فعلی در حال توسعه است."
        )
        await state.clear()
        await message.answer("بازگشت به منوی اصلی:", reply_markup=main_menu())
    else:
        await message.answer("❌ لطفاً یک فایل (عکس، ویدیو یا سند) بفرست.")

# ============================================
# قابلیت 4: آپلود در ابر
# ============================================
@dp.message(lambda message: message.text == "☁️ آپلود در ابر")
async def upload_start(message: Message, state: FSMContext):
    await message.answer(
        "☁️ **آپلود در سرور ابری**\n\n"
        "لطفاً فایل مورد نظرت رو برام بفرست.\n"
        "بعد از آپلود، لینک دانلود مستقیم در اختیارت قرار میگیره.\n\n"
        "⚠️ این قابلیت در نسخه فعلی در حال توسعه است."
    )

# ============================================
# خروج از ربات
# ============================================
@dp.message(lambda message: message.text == "❌ خروج")
async def exit_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 خداحافظ! برای استفاده دوباره /start رو بفرست.", reply_markup=None)

# ============================================
# پیام‌های ناشناخته
# ============================================
@dp.message()
async def unknown_message(message: Message):
    await message.answer("❌ گزینه نامعتبر! لطفاً از منوی اصلی استفاده کن.", reply_markup=main_menu())

# ============================================
# اجرای اصلی
# ============================================
async def main():
    print("🚀 ربات با موفقیت روشن شد!")
    print("📡 در حال انتظار برای پیام‌ها...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
