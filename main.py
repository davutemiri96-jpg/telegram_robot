import asyncio
import logging
import os
import zipfile
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType

# ============================================
# تنظیمات
# ============================================
BOT_TOKEN = "8898380201:AAFKeXvAnOSwgvha1xGrwQxWIB8fGfEkVaE"
API_ID = 38013873
API_HASH = "1f30e5c9cd4633c65ec2f61162195ad0"

# ============================================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_PATH = "downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Client سراسری (بهتر از ساختن هر بار)
user_client = None

# ============================================
# ترجمه کلیدواژه‌ها
# ============================================
def get_translations(keyword: str):
    translations = {
        "سلام": ["سلام", "salam", "hello", "hi"],
        "خبر": ["خبر", "اخبار", "news", "khabar"],
        "آموزش": ["آموزش", "learn", "education"],
        "فیلم": ["فیلم", "movie", "film", "سینما"],
        "موسیقی": ["موسیقی", "music", "موزیک", "آهنگ"],
        "ورزش": ["ورزش", "sport"],
        "علم": ["علم", "science", "دانش"],
        "تکنولوژی": ["تکنولوژی", "technology", "tech"],
    }
    
    keyword_lower = keyword.lower().strip()
    if keyword_lower in translations:
        result = translations[keyword_lower]
    else:
        result = [keyword_lower]
    
    return list(set(result))  # حذف تکراری

# ============================================
# منو
# ============================================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو در همه کانال‌های عضو")],
            [KeyboardButton(text="🗜️ فشرده‌سازی فایل")],
            [KeyboardButton(text="❌ خروج")]
        ],
        resize_keyboard=True
    )

# ============================================
# وضعیت‌ها
# ============================================
class Form(StatesGroup):
    waiting_keyword = State()
    waiting_duration = State()
    waiting_target = State()
    waiting_password = State()
    waiting_file = State()

# ============================================
# استارت
# ============================================
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🌍 **ربات جستجوگر چندزبانه**\n\n"
        "جستجو در همه کانال‌هایی که عضو هستید\n"
        "پشتیبانی از چند زبان\n"
        "فوروارد خودکار به کانال مقصد",
        reply_markup=main_menu()
    )

# ============================================
# جستجو
# ============================================
@dp.message(lambda m: m.text == "🔍 جستجو در همه کانال‌های عضو")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_keyword)
    await message.answer("🌍 **کلیدواژه** را وارد کنید:")

@dp.message(Form.waiting_keyword)
async def get_keyword(message: Message, state: FSMContext):
    original = message.text.strip()
    translations = get_translations(original)
    
    await state.update_data(keywords=translations, original=original)
    await state.set_state(Form.waiting_duration)
    
    await message.answer(
        f"✅ کلیدواژه: `{original}`\n"
        f"🌐 {len(translations)} شکل مختلف جستجو خواهد شد.\n\n"
        f"🎬 حداقل مدت ویدیو (ثانیه) را وارد کنید:\n(0 = بدون محدودیت)"
    )

@dp.message(Form.waiting_duration)
async def get_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        await state.update_data(duration=duration)
        await state.set_state(Form.waiting_target)
        await message.answer("📢 آیدی کانال مقصد را بفرستید:\nمثال: `@my_channel` یا `-1001234567890`")
    except ValueError:
        await message.answer("❌ لطفاً عدد وارد کنید!")

@dp.message(Form.waiting_target)
async def get_target(message: Message, state: FSMContext):
    target = message.text.strip()
    data = await state.get_data()
    
    await message.answer("🔄 در حال شروع جستجو...", reply_markup=main_menu())
    asyncio.create_task(do_search(message, data['keywords'], data['duration'], target, data['original']))

# ============================================
async def do_search(message: Message, keywords: list, min_duration: int, target: str, original: str):
    global user_client
    status_msg = await message.answer("🔌 در حال اتصال به اکانت...")

    if user_client is None:
        user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)
        await user_client.start()
        await status_msg.edit_text("✅ متصل شد!")

    try:
        channels = [dialog.chat async for dialog in user_client.get_dialogs() 
                   if dialog.chat.type == ChatType.CHANNEL]
        
        await status_msg.edit_text(f"📡 {len(channels)} کانال پیدا شد. در حال جستجو...")

        found_count = 0
        for channel in channels:
            for kw in keywords:
                try:
                    async for msg in user_client.search_messages(
                        chat_id=channel.id,
                        query=kw,
                        limit=30
                    ):
                        if msg.video or msg.photo:
                            if msg.video and min_duration > 0:
                                if getattr(msg.video, 'duration', 0) < min_duration:
                                    continue
                            
                            try:
                                await msg.forward(chat_id=target)
                                found_count += 1
                                
                                if found_count % 10 == 0:
                                    await message.answer(f"✅ {found_count} محتوا فوروارد شد...")
                            except Exception:
                                pass
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    continue

        await status_msg.delete()
        await message.answer(
            f"🏁 **جستجو تمام شد!**\n\n"
            f"📊 کانال‌ها: {len(channels)}\n"
            f"🔤 کلمات جستجو: {len(keywords)}\n"
            f"✅ پیدا و فوروارد شد: **{found_count}**",
            reply_markup=main_menu()
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ خطا: {str(e)}")
    finally:
        await state.clear()  # اگر از FSMContext استفاده می‌کنی

# ============================================
# فشرده‌سازی فایل
# ============================================
@dp.message(lambda m: m.text == "🗜️ فشرده‌سازی فایل")
async def compress_start(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_password)
    await message.answer("🔐 رمز عبور را وارد کنید:\n(0 = بدون رمز)")

@dp.message(Form.waiting_password)
async def get_compress_password(message: Message, state: FSMContext):
    pwd = message.text.strip()
    await state.update_data(password=None if pwd == "0" else pwd)
    await state.set_state(Form.waiting_file)
    await message.answer("📤 فایل را ارسال کنید (عکس، ویدیو یا سند)")

@dp.message(Form.waiting_file)
async def compress_file(message: Message, state: FSMContext):
    if not (message.document or message.video or message.photo):
        return await message.answer("❌ لطفاً فایل بفرستید!")

    data = await state.get_data()
    password = data.get('password')

    # دریافت فایل
    if message.document:
        file = message.document
        name = file.file_name or f"file_{file.file_id[:8]}"
    elif message.video:
        file = message.video
        name = f"video_{datetime.now():%Y%m%d_%H%M%S}.mp4"
    else:
        file = message.photo[-1]
        name = f"photo_{datetime.now():%Y%m%d_%H%M%S}.jpg"

    path = os.path.join(DOWNLOAD_PATH, name)
    zip_path = path + ".zip"

    try:
        await message.answer(f"📥 در حال دانلود {name}...")
        await bot.download(file, destination=path)

        await message.answer("🗜️ در حال فشرده‌سازی...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if password:
                zf.setpassword(password.encode('utf-8'))
            zf.write(path, arcname=name)

        with open(zip_path, 'rb') as zf:
            await message.answer_document(
                BufferedInputFile(zf.read(), filename=os.path.basename(zip_path)),
                caption=f"✅ فشرده‌سازی کامل شد!\n🔐 رمز: {'دارد' if password else 'ندارد'}"
            )

    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")
    finally:
        # پاک کردن فایل‌های موقتی
        for p in (path, zip_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
        await state.clear()
        await message.answer("بازگشت به منو:", reply_markup=main_menu())

# ============================================
@dp.message(lambda m: m.text == "❌ خروج")
async def exit_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 خداحافظ!", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def unknown(message: Message):
    await message.answer("از منوی زیر استفاده کنید:", reply_markup=main_menu())

# ============================================
async def main():
    print("🌍 ربات جستجوگر با موفقیت راه‌اندازی شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
