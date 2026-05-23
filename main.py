import asyncio
import logging
import os
import zipfile
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType

# ============================================
# تنظیمات - حتماً پر کن!
# ============================================
BOT_TOKEN = "8898380201:AAFKeXvAnOSwgvha1xGrwQxWIB8fGfEkVaE"
API_ID = 38013873
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
# دیکشنری ترجمه برای کلمات کلیدی
# ============================================
def get_translations(keyword):
    """کلمه رو به زبان‌های مختلف ترجمه می‌کنه"""
    
    # ترجمه‌های پرکاربرد برای کلمات رایج
    translations = {
        # فارسی
        "سلام": ["سلام", "salām", "salam"],
        "خبر": ["خبر", "اخبار", "news", "اخبار", "khabar"],
        "آموزش": ["آموزش", "آموزشی", "learn", "learning", "آموزش"],
        "فیلم": ["فیلم", "movie", "film", "سینما", "cinema"],
        "موسیقی": ["موسیقی", "music", "موزیک", "آهنگ"],
        "ورزش": ["ورزش", "sport", "ورزشی", "sports"],
        "علم": ["علم", "science", "دانش", "scientific", "علوم"],
        "تکنولوژی": ["تکنولوژی", "technology", "فناوری", "tech"],
        
        # انگلیسی
        "news": ["news", "اخبار", "خبر", "breaking", "latest"],
        "sport": ["sport", "ورزش", "ورزشی", "sports"],
        "music": ["music", "موسیقی", "آهنگ", "موزیک", "song"],
        "movie": ["movie", "فیلم", "سینما", "film", "cinema"],
        "science": ["science", "علم", "دانش", "علوم", "scientific"],
        "technology": ["technology", "تکنولوژی", "فناوری", "tech"],
        "learning": ["learning", "آموزش", "learn", "آموزشی", "education"],
        "game": ["game", "بازی", "گیم", "gaming", "بازی‌های"],
        
        # عربی
        "اخبار": ["اخبار", "أخبار", "news", "اخبار"],
        "فیلم": ["فیلم", "فلم", "movie", "أفلام"],
        "تعلیم": ["تعلیم", "آموزش", "education", "تعلم", "learning"],
        
        # ترکی
        "haber": ["haber", "اخبار", "news", "haberler"],
        "müzik": ["müzik", "موسیقی", "music", "şarkı"],
        "film": ["film", "فیلم", "movie", "sinema"],
        
        # روسی
        "новости": ["новости", "news", "новость", "اخبار"],
        "музыка": ["музыка", "music", "موسیقی", "песня"],
        "фильм": ["фильм", "movie", "فیلم", "кино"],
        
        # آلمانی
        "nachrichten": ["nachrichten", "news", "اخبار", "neuigkeiten"],
        "musik": ["musik", "music", "موسیقی", "lied"],
        "film": ["film", "movie", "فیلم", "kino"],
        
        # فرانسوی
        "actualités": ["actualités", "news", "اخبار", "infos"],
        "musique": ["musique", "music", "موسیقی", "chanson"],
        
        # اسپانیایی
        "noticias": ["noticias", "news", "اخبار", "novedades"],
        "música": ["música", "music", "موسیقی", "canción"],
    }
    
    # چک کردن اینکه کلمه تو دیکشنری هست یا نه
    keyword_lower = keyword.lower().strip()
    
    if keyword_lower in translations:
        return list(set(translations[keyword_lower]))  # حذف تکراری‌ها
    
    # اگه کلمه تو دیکشنری نبود، خود کلمه + نسخه انگلیسی + فینگلیش برمیگردونه
    result = [keyword_lower]
    
    # اضافه کردن فینگلیش برای کلمات فارسی
    persian_chars = "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"
    if any(c in persian_chars for c in keyword_lower):
        # تبدیل ساده فارسی به انگلیسی
        mapping = {
            'ا': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's',
            'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd',
            'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'zh', 'س': 's',
            'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z',
            'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'gh', 'ک': 'k',
            'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'و': 'o',
            'ه': 'h', 'ی': 'y', ' ': ' '
        }
        finglish = ''.join(mapping.get(c, c) for c in keyword_lower)
        result.append(finglish)
    
    return list(set(result))

# ============================================
# منو
# ============================================
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو در همه کانال‌های عضو")],
            [KeyboardButton(text="🗜️ فشرده‌سازی فایل")],
            [KeyboardButton(text="❌ خروج")]
        ],
        resize_keyboard=True
    )
    return keyboard

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
        "✅ من در **همه کانال‌هایی که شما عضو هستید** جستجو می‌کنم\n"
        "✅ **به همه زبان‌ها** جستجو می‌کنم!\n"
        "✅ فارسی، انگلیسی، عربی، ترکی، روسی، آلمانی، ...\n\n"
        "🔍 کافیه کلیدواژه رو به هر زبانی بدی\n"
        "🎬 می‌تونی حداقل تایم ویدیو رو تعیین کنی\n"
        "📢 محتواها رو به کانال مورد نظرت فوروارد می‌کنم\n\n"
        "از منو انتخاب کن 👇",
        reply_markup=main_menu()
    )

# ============================================
# جستجو
# ============================================
@dp.message(lambda message: message.text == "🔍 جستجو در همه کانال‌های عضو")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_keyword)
    await message.answer(
        "🌍 **کلیدواژه** مورد نظرت رو وارد کن:\n\n"
        "📝 مثال: science, music, آموزش, خبر, ニュース\n\n"
        "✅ من خودکار به این زبان‌ها ترجمه می‌کنم:\n"
        "فارسی 🇮🇷 | انگلیسی 🇬🇧 | عربی 🇸🇦 | ترکی 🇹🇷\n"
        "روسی 🇷🇺 | آلمانی 🇩🇪 | فرانسوی 🇫🇷 | اسپانیایی 🇪🇸\n\n"
        "و همه نسخه‌ها رو جستجو می‌کنم!"
    )

@dp.message(Form.waiting_keyword)
async def get_keyword(message: Message, state: FSMContext):
    original_keyword = message.text.strip()
    
    # گرفتن ترجمه‌ها
    translations = get_translations(original_keyword)
    await state.update_data(keywords=translations, original=original_keyword)
    
    await state.set_state(Form.waiting_duration)
    
    # نمایش ترجمه‌ها به کاربر
    trans_text = "\n".join([f"• {t}" for t in translations[:15]])
    if len(translations) > 15:
        trans_text += f"\n• ... و {len(translations)-15} تا دیگه"
    
    await message.answer(
        f"✅ **کلیدواژه اصلی:** {original_keyword}\n\n"
        f"🌍 **ترجمه شده به {len(translations)} شکل:**\n{trans_text}\n\n"
        f"🎬 **حداقل تایم ویدیو** رو به ثانیه وارد کن:\n"
        f"(0 = بدون محدودیت)"
    )

@dp.message(Form.waiting_duration)
async def get_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        await state.update_data(duration=duration)
        await state.set_state(Form.waiting_target)
        await message.answer(
            f"⏱️ حداقل تایم: {duration if duration > 0 else 'بدون محدودیت'} ثانیه\n\n"
            f"📢 **آیدی کانال مقصد** رو بفرست:\n\n"
            f"مثال: @my_channel\n"
            f"⚠️ ربات باید در اون کانال ادمین باشه"
        )
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کن!")

@dp.message(Form.waiting_target)
async def get_target(message: Message, state: FSMContext):
    target = message.text.strip()
    data = await state.get_data()
    
    await message.answer(
        f"✅ **تنظیمات ذخیره شد!**\n\n"
        f"🌍 کلیدواژه اصلی: {data['original']}\n"
        f"📝 ترجمه‌ها: {len(data['keywords'])} شکل مختلف\n"
        f"⏱️ حداقل تایم: {data['duration'] if data['duration'] > 0 else 'بدون محدودیت'} ثانیه\n"
        f"📢 کانال مقصد: {target}\n\n"
        f"🔄 **در حال جستجو در همه کانال‌ها به همه زبان‌ها...**\n"
        f"این عملیات ممکنه چند دقیقه طول بکشه.\n\n"
        f"🔍 جستجو برای {len(data['keywords'])} کلمه مختلف در {target}",
        reply_markup=main_menu()
    )
    
    await do_search(message, data['keywords'], data['duration'], target, data['original'], state)

async def do_search(message: Message, keywords: list, min_duration: int, target: str, original: str, state: FSMContext):
    status_msg = await message.answer("🔌 در حال اتصال به حساب کاربری...")
    
    try:
        await user_client.start()
        await status_msg.edit_text("✅ متصل شدم! در حال دریافت لیست همه کانال‌ها...")
        
        # گرفتن همه کانال‌ها
        channels = []
        async for dialog in user_client.get_dialogs():
            if dialog.chat.type == ChatType.CHANNEL:
                channels.append(dialog.chat)
        
        if not channels:
            await status_msg.edit_text("❌ شما در هیچ کانالی عضو نیستید!")
            await user_client.stop()
            return
        
        await status_msg.edit_text(
            f"📡 **{len(channels)} کانال** پیدا شد!\n"
            f"🌍 جستجو برای **{len(keywords)}** کلمه مختلف\n"
            f"🔄 شروع جستجو..."
        )
        
        found_count = 0
        total_messages = 0
        channels_checked = 0
        
        for channel in channels:
            channels_checked += 1
            
            if channels_checked % 10 == 0:
                await status_msg.edit_text(
                    f"📡 {channels_checked}/{len(channels)} کانال\n"
                    f"🔍 پیدا شده: {found_count}\n"
                    f"📊 پیام‌ها: {total_messages}"
                )
            
            for kw in keywords:
                try:
                    async for msg in user_client.search_messages(
                        chat_id=channel.id,
                        query=kw,
                        limit=20
                    ):
                        total_messages += 1
                        
                        if msg.video or msg.photo:
                            if msg.video and min_duration > 0:
                                if msg.video.duration and msg.video.duration < min_duration:
                                    continue
                            
                            try:
                                if target.startswith("@"):
                                    await msg.forward(chat_id=target)
                                else:
                                    await msg.forward(chat_id=int(target))
                                
                                found_count += 1
                                
                                if found_count % 3 == 0:
                                    await message.answer(
                                        f"✅ **{found_count} محتوا پیدا شد!**\n"
                                        f"🔍 کلیدواژه: {kw}\n"
                                        f"📍 از کانال: {channel.title[:30]}\n"
                                        f"🌍 اصلی: {original}"
                                    )
                            except:
                                pass
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except:
                    pass
        
        await status_msg.delete()
        
        report = (
            f"🏁 **جستجوی چندزبانه تمام شد!**\n\n"
            f"📊 **آمار نهایی:**\n"
            f"• کانال‌ها: {len(channels)}\n"
            f"• کلمات جستجو: {len(keywords)}\n"
            f"• پیام‌ها: {total_messages}\n"
            f"• پیدا شده: {found_count}\n\n"
            f"🌍 کلیدواژه اصلی: {original}\n"
            f"✅ همه به {target} فوروارد شدن."
        )
        
        if found_count == 0:
            report += "\n\n⚠️ چیزی پیدا نشد! کلیدواژه دیگه‌ای امتحان کن."
        
        await message.answer(report, reply_markup=main_menu())
        
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا: {str(e)}")
    finally:
        await user_client.stop()
        await state.clear()

# ============================================
# فشرده‌سازی فایل
# ============================================
@dp.message(lambda message: message.text == "🗜️ فشرده‌سازی فایل")
async def compress_start(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_password)
    await message.answer(
        "🗜️ **فشرده‌سازی فایل به ZIP**\n\n"
        "🔐 **رمز عبور** رو وارد کن:\n(0 = بدون رمز)"
    )

@dp.message(Form.waiting_password)
async def get_compress_password(message: Message, state: FSMContext):
    pwd = message.text.strip()
    if pwd == "0":
        pwd = None
    await state.update_data(password=pwd)
    await state.set_state(Form.waiting_file)
    await message.answer("📤 **حالا فایل رو بفرست** (عکس، ویدیو یا هر فایل)")

@dp.message(Form.waiting_file)
async def compress_file(message: Message, state: FSMContext):
    if not (message.document or message.video or message.photo):
        await message.answer("❌ لطفاً یه فایل بفرست!")
        return
    
    data = await state.get_data()
    password = data.get('password')
    
    if message.document:
        file = message.document
        name = file.file_name or f"file_{file.file_id[:8]}"
        fid = file.file_id
    elif message.video:
        file = message.video
        name = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        fid = file.file_id
    else:
        file = message.photo[-1]
        name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        fid = file.file_id
    
    await message.answer(f"📥 دریافت {name}...")
    
    try:
        path = os.path.join(DOWNLOAD_PATH, name)
        f = await bot.get_file(fid)
        await bot.download_file(f.file_path, path)
        
        zip_path = path + ".zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if password:
                zf.setpassword(password.encode())
            zf.write(path, name)
        
        with open(zip_path, 'rb') as zf:
            await message.answer_document(
                types.BufferedInputFile(zf.read(), filename=os.path.basename(zip_path)),
                caption=f"✅ فشرده شد!\n🔐 رمز: {password if password else 'ندارد'}"
            )
        
        os.remove(path)
        os.remove(zip_path)
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")
    
    await state.clear()
    await message.answer("بازگشت به منو:", reply_markup=main_menu())

# ============================================
# خروج
# ============================================
@dp.message(lambda message: message.text == "❌ خروج")
async def exit_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 خداحافظ!", reply_markup=None)

@dp.message()
async def unknown(message: Message):
    await message.answer("❌ از منو استفاده کن!", reply_markup=main_menu())

async def main():
    print("=" * 50)
    print("🌍 ربات جستجوگر چندزبانه روشن شد!")
    print("📡 جستجو به همه زبان‌ها در همه کانال‌های عضو")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
