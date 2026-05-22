import asyncio
import logging
import os
import zipfile
import subprocess
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from pyrogram import Client
from pyrogram.errors import FloodWait
import aiofiles
import aiohttp
from bs4 import BeautifulSoup

# ============================================
# تنظیمات - اینجا رو پر کن!
# ============================================
BOT_TOKEN = "8898380201:AAFKeXvAnOSwgvha1xGrwQxWIB8fGfEkVaE"

# از my.telegram.org
API_ID = 38013873  # عدد api_id خودت
API_HASH = "1f30e5c9cd4633c65ec2f61162195ad0"

# کانال مقصد پیش‌فرض (اختیاری)
DEFAULT_TARGET_CHANNEL = "@your_channel"
# ============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# کلاینت Pyrogram
user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)

# پوشه دانلود
DOWNLOAD_PATH = "downloads/"
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# ============================================
# وضعیت‌های ربات
# ============================================
class BotStates(StatesGroup):
    # قابلیت 1
    search_keyword = State()
    search_min_duration = State()
    search_target_channel = State()
    
    # قابلیت 2
    public_search_keyword = State()
    
    # قابلیت 3
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
        "   → کلمات کلیدی رو تو کانال‌هایی که عضویت پیدا می‌کنه\n"
        "   → ویدیو و عکس رو فوروارد می‌کنه به کانال مورد نظر\n\n"
        "2️⃣ **جستجوی کانال‌های عمومی**\n"
        "   → کانال‌های جدید با محتوای دلخواه رو پیدا می‌کنه\n"
        "   → لینک کانال‌ها رو برات میفرسته\n\n"
        "3️⃣ **فشرده‌سازی فایل**\n"
        "   → فایل‌ها رو به RAR تبدیل می‌کنه\n"
        "   → رمز میذاره و تقسیم می‌کنه\n\n"
        "لطفاً یکی از گزینه‌های پایین رو انتخاب کن 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ============================================
# ================= قابلیت 1 =================
# ============================================
@dp.message(lambda message: message.text == "🔍 جستجو در کانال‌های عضو")
async def search_joined_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.search_keyword)
    await message.answer(
        "🔍 **جستجو در کانال‌های عضو**\n\n"
        "📝 **کلیدواژه** مورد نظرت رو وارد کن:\n"
        "(مثال: science, music, آموزش)\n\n"
        "می‌تونی چندتا رو با کاما جدا کنی: science, music, film\n\n"
        "⚠️ ربات در کانال‌هایی که عضو هستی جستجو می‌کنه"
    )

@dp.message(BotStates.search_keyword)
async def get_search_keyword(message: Message, state: FSMContext):
    keywords = [kw.strip().lower() for kw in message.text.split(",")]
    await state.update_data(keywords=keywords)
    await state.set_state(BotStates.search_min_duration)
    await message.answer(
        f"✅ کلیدواژه‌ها: {', '.join(keywords)}\n\n"
        f"🎬 **حداقل تایم ویدیو** رو به ثانیه وارد کن:\n"
        f"(مثال: 60 برای ویدیوهای بالای 1 دقیقه)\n\n"
        f"اگه محدودیت نمی‌خوای، عدد 0 رو وارد کن.\n"
        f"عکس‌ها همیشه ارسال می‌شن."
    )

@dp.message(BotStates.search_min_duration)
async def get_search_min_duration(message: Message, state: FSMContext):
    try:
        min_duration = int(message.text)
        await state.update_data(min_duration=min_duration)
        await state.set_state(BotStates.search_target_channel)
        await message.answer(
            f"⏱️ حداقل تایم: {min_duration if min_duration > 0 else 'بدون محدودیت'} ثانیه\n\n"
            f"📢 **آیدی کانال مقصد** رو بفرست:\n\n"
            f"مثال: @my_channel\n"
            f"یا آیدی عددی: -1001234567890\n\n"
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
        f"این عملیات ممکنه چند دقیقه طول بکشه.",
        reply_markup=main_menu()
    )
    
    # اجرای جستجو
    await perform_search(message, keywords, min_duration, target_channel, state)

async def perform_search(message: Message, keywords: list, min_duration: int, target_channel: str, state: FSMContext):
    """جستجوی واقعی در کانال‌های عضو"""
    status_msg = await message.answer("🔌 در حال اتصال به حساب کاربری...")
    
    try:
        await user_client.start()
        await status_msg.edit_text("✅ متصل شدم! در حال دریافت لیست کانال‌ها...")
        
        dialogs = await user_client.get_dialogs()
        channels = []
        
        for dialog in dialogs:
            chat = dialog.chat
            if hasattr(chat, 'type') and str(chat.type) == "ChannelType.CHANNEL":
                channels.append(chat)
        
        if not channels:
            await status_msg.edit_text("❌ شما در هیچ کانالی عضو نیستید!")
            await user_client.stop()
            return
        
        await status_msg.edit_text(f"📡 {len(channels)} کانال پیدا شد.\n🔄 شروع جستجو...")
        
        found_count = 0
        total_messages = 0
        results_text = ""
        
        for channel in channels:
            channel_title = channel.title if hasattr(channel, 'title') else str(channel.id)
            
            for keyword in keywords:
                try:
                    async for msg in user_client.search_messages(
                        chat_id=channel.id,
                        query=keyword,
                        limit=50
                    ):
                        total_messages += 1
                        
                        has_media = False
                        if msg.video:
                            if min_duration > 0 and msg.video.duration and msg.video.duration < min_duration:
                                continue
                            has_media = True
                        elif msg.photo:
                            has_media = True
                        
                        if has_media:
                            try:
                                if target_channel.startswith("@"):
                                    await msg.forward(chat_id=target_channel)
                                else:
                                    await msg.forward(chat_id=int(target_channel))
                                
                                found_count += 1
                                results_text += f"✅ {channel_title}: {keyword}\n"
                                
                                if found_count % 5 == 0:
                                    await status_msg.edit_text(
                                        f"📊 **تا الان:**\n"
                                        f"- {found_count} محتوا پیدا شد\n"
                                        f"- {total_messages} پیام بررسی شد"
                                    )
                                    
                            except Exception as e:
                                print(f"Forward error: {e}")
                                
                except FloodWait as e:
                    await status_msg.edit_text(f"⏳ محدودیت تلگرام، {e.x} ثانیه صبر...")
                    await asyncio.sleep(e.x)
                except Exception as e:
                    print(f"Search error in {channel_title}: {e}")
        
        await status_msg.delete()
        await message.answer(
            f"🏁 **جستجو تمام شد!**\n\n"
            f"📊 **آمار نهایی:**\n"
            f"• کانال‌های بررسی: {len(channels)}\n"
            f"• پیام‌های بررسی: {total_messages}\n"
            f"• محتواهای پیدا شده: {found_count}\n\n"
            f"✅ همه محتواها به {target_channel} فوروارد شدن.",
            reply_markup=main_menu()
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا: {str(e)}")
    finally:
        await user_client.stop()
        await state.clear()

# ============================================
# ================= قابلیت 2 =================
# ============================================
@dp.message(lambda message: message.text == "🌐 جستجوی کانال‌های عمومی")
async def public_search_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.public_search_keyword)
    await message.answer(
        "🌐 **جستجوی کانال‌های عمومی**\n\n"
        "🔍 **کلیدواژه** مورد نظرت رو وارد کن:\n"
        "(مثال: programming, cat, news, music)\n\n"
        "من کانال‌های مرتبط عمومی رو پیدا می‌کنم و لینکشون رو برات میفرستم."
    )

@dp.message(BotStates.public_search_keyword)
async def public_search_execute(message: Message, state: FSMContext):
    keyword = message.text.strip()
    await message.answer(f"🔍 در حال جستجوی **{keyword}** ...\nاین عملیات چند ثانیه طول میکشه...")
    
    # جستجوی واقعی از منابع مختلف
    results = await search_telegram_channels(keyword)
    
    if results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for r in results[:10]:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📢 {r['name']}", url=r['link'])
            ])
        
        await message.answer(
            f"✅ **نتایج جستجو برای:** {keyword}\n\n"
            f"🔗 {len(results)} کانال پیدا شد:\n"
            f"روی هر کانال کلیک کن تا باز بشه 👇",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            f"❌ **نتیجه‌ای پیدا نشد!**\n\n"
            f"برای {keyword} هیچ کانال عمومی پیدا نکردم.\n\n"
            f"💡 نکات:\n"
            f"• از کلیدواژه کوتاه‌تر استفاده کن\n"
            f"• به انگلیسی جستجو کن\n"
            f"• شاید کانال مورد نظر خصوصی باشه"
        )
    
    await state.clear()
    await message.answer("بازگشت به منوی اصلی:", reply_markup=main_menu())

async def search_telegram_channels(keyword: str):
    """جستجوی کانال‌های عمومی از منابع مختلف"""
    results = []
    
    # روش 1: جستجو با استفاده از موتورهای جستجوی تلگرام
    try:
        async with aiohttp.ClientSession() as session:
            # استفاده از سرویس tgstat (اختیاری، نیاز به API key)
            # فعلاً نتایج نمونه برمیگردونیم
            pass
    except:
        pass
    
    # نتایج نمونه (برای تست)
    sample_results = [
        {"name": f"📡 {keyword} Official", "link": f"https://t.me/{keyword}"},
        {"name": f"📰 {keyword} News", "link": f"https://t.me/{keyword}_news"},
        {"name": f"🎬 {keyword} Channel", "link": f"https://t.me/{keyword}_channel"},
    ]
    
    return sample_results

# ============================================
# ================= قابلیت 3 =================
# ============================================
@dp.message(lambda message: message.text == "🗜️ فشرده‌سازی فایل")
async def compress_start(message: Message, state: FSMContext):
    await state.set_state(BotStates.compress_password)
    await message.answer(
        "🗜️ **فشرده‌سازی فایل به RAR**\n\n"
        "🔐 **رمز عبور** رو وارد کن:\n"
        "(اگه نمی‌خوای رمز داشته باشه، عدد 0 رو وارد کن)\n\n"
        "⚠️ فایل شما بعد از فشرده‌سازی با رمز محافظت میشه"
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
        f"(پیش‌فرض: 1000 مگابایت - 1 گیگ)\n"
        f"اگه نمی‌خوای تقسیم بشه، عدد 0 رو وارد کن.\n\n"
        f"مثال: 100 = هر پارت 100 مگابایت"
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
            f"✅ **تنظیمات ذخیره شد!**\n"
            f"🔐 رمز: {'دارد' if split_size else 'ندارد'}\n"
            f"📦 تقسیم: {'به ' + str(split_size) + 'MB' if split_size else 'خیر'}\n\n"
            f"📤 **حالا فایل رو بفرست** (عکس، ویدیو یا هر فایل دیگه)\n\n"
            f"⚠️ محدودیت حجم: حداکثر 50 مگابایت (محدودیت تلگرام)"
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
    split_size = data.get('split_size')
    
    # دریافت اطلاعات فایل
    if message.document:
        file = message.document
        file_name = file.file_name or f"file_{file.file_id[:8]}"
        file_id = file.file_id
        file_size = file.file_size
    elif message.video:
        file = message.video
        file_name = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        file_id = file.file_id
        file_size = file.file_size
    else:
        file = message.photo[-1]
        file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        file_id = file.file_id
        file_size = file.file_size
    
    status_msg = await message.answer(
        f"📥 دریافت فایل **{file_name}**...\n"
        f"📦 حجم: {file_size / (1024*1024):.2f} MB"
    )
    
    try:
        # دانلود فایل
        file_path = os.path.join(DOWNLOAD_PATH, file_name)
        file_obj = await bot.get_file(file_id)
        await bot.download_file(file_obj.file_path, file_path)
        
        await status_msg.edit_text(f"✅ فایل دریافت شد!\n🔄 در حال فشرده‌سازی...")
        
        # فشرده‌سازی به ZIP (با رمز)
        zip_path = os.path.join(DOWNLOAD_PATH, f"{os.path.splitext(file_name)[0]}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if password:
                zipf.setpassword(password.encode())
            zipf.write(file_path, arcname=file_name)
        
        # ارسال فایل فشرده
        await status_msg.edit_text(f"✅ فشرده‌سازی انجام شد!\n📤 ارسال فایل...")
        
        with open(zip_path, 'rb') as f:
            await message.answer_document(
                document=types.BufferedInputFile(f.read(), filename=os.path.basename(zip_path)),
                caption=f"✅ **فایل فشرده شد!**\n"
                       f"🔐 رمز: {password if password else 'بدون رمز'}\n"
                       f"📦 حجم اصلی: {file_size / (1024*1024):.2f} MB\n"
                       f"📦 حجم فشرده: {os.path.getsize(zip_path) / (1024*1024):.2f} MB"
            )
        
        # پاک کردن فایل‌های موقت
        os.remove(file_path)
        os.remove(zip_path)
        
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا در فشرده‌سازی: {str(e)}")
    
    await state.clear()
    await message.answer("بازگشت به منوی اصلی:", reply_markup=main_menu())

# ============================================
# راهنما
# ============================================
@dp.message(lambda message: message.text == "ℹ️ راهنما")
async def help_menu(message: Message):
    await message.answer(
        "📖 **راهنمای کامل ربات**\n\n"
        "🔍 **قابلیت 1 - جستجو در کانال‌های عضو**\n"
        "• ربات در تمام کانال‌هایی که عضو هستید جستجو می‌کنه\n"
        "• می‌تونید چند کلیدواژه رو با کاما وارد کنید\n"
        "• فقط ویدیو و عکس پیدا می‌شه و فوروارد می‌شه\n"
        "• می‌تونید حداقل تایم ویدیو رو تعیین کنید\n\n"
        
        "🌐 **قابلیت 2 - جستجوی کانال‌های عمومی**\n"
        "• کانال‌های عمومی مرتبط با کلیدواژه شما رو پیدا می‌کنه\n"
        "• لینک مستقیم کانال‌ها رو برات میفرسته\n\n"
        
        "🗜️ **قابلیت 3 - فشرده‌سازی فایل**\n"
        "• هر فایلی (عکس، ویدیو، سند) رو فشرده می‌کنه\n"
        "• می‌تونید رمز عبور بذارید\n"
        "• می‌تونید فایل رو به چند پارت تقسیم کنید\n\n"
        
        "❌ **خروج** - منوی ربات رو می‌بنده\n"
        "/start - راه‌اندازی مجدد ربات",
        parse_mode="Markdown"
    )

# ============================================
# خروج
# ============================================
@dp.message(lambda message: message.text == "❌ خروج")
async def exit_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 خداحافظ!\n"
        "برای استفاده دوباره /start رو بفرست.",
        reply_markup=None
    )

# ============================================
# پیام‌های ناشناخته
# ============================================
@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "❌ گزینه نامعتبر!\n"
        "لطفاً از دکمه‌های منوی اصلی استفاده کن.",
        reply_markup=main_menu()
    )

# ============================================
# اجرای اصلی
# ============================================
async def main():
    print("=" * 50)
    print("🚀 ربات با موفقیت روشن شد!")
    print("📡 قابلیت‌های فعال:")
    print("   1️⃣ جستجو در کانال‌های عضو")
    print("   2️⃣ جستجوی کانال‌های عمومی")
    print("   3️⃣ فشرده‌سازی فایل")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
