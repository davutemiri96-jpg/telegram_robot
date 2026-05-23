import asyncio
import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType, ChatMemberStatus

BOT_TOKEN = "8898380201:AAGJk_LWDynC66-BP9eIcuEJcui-KpLk2EA"
API_ID = 38013873
API_HASH = "1f30e5c9cd4633c65ec2f61162195ad0"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_client = None
pagination_cache = {}

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Search in Channel")],
            [KeyboardButton(text="Global Search")],
            [KeyboardButton(text="Convert to RAR")],
            [KeyboardButton(text="Exit")]
        ],
        resize_keyboard=True
    )

class Form(StatesGroup):
    search_keyword = State()
    search_channel_id = State()
    search_duration = State()
    global_search_keyword = State()
    video_to_rar_waiting_file = State()

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Telegram Search Bot\n\n"
        "Features:\n"
        "- Search in specific channels\n"
        "- Global search\n"
        "- Convert video to RAR\n"
        "- Direct post links\n\n"
        "Choose from menu:",
        reply_markup=main_menu()
    )

@dp.message(lambda m: m.text == "Search in Channel")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(Form.search_keyword)
    await message.answer("Enter search keyword:")

@dp.message(Form.search_keyword)
async def search_keyword(message: Message, state: FSMContext):
    await state.update_data(keyword=message.text.strip())
    await state.set_state(Form.search_channel_id)
    await message.answer(
        "Which channels to search?\n\n"
        "- Channel ID: -100123456789 or @username\n"
        "- Multiple: -100123 -100456 -100789\n"
        "- 0 = all my channels"
    )

@dp.message(Form.search_channel_id)
async def search_channel_id(message: Message, state: FSMContext):
    channel_input = message.text.strip()
    await state.update_data(channels=channel_input)
    await state.set_state(Form.search_duration)
    await message.answer("Minimum video duration (seconds):\n(0 = no limit)")

@dp.message(Form.search_duration)
async def search_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        data = await state.get_data()
        await message.answer(f"Searching...\nKeyword: {data['keyword']}\nMin duration: {duration}s")
        asyncio.create_task(search_channels_task(message, data['keyword'], data['channels'], duration))
        await state.clear()
    except ValueError:
        await message.answer("Please enter a number!")

async def search_channels_task(message: Message, keyword: str, channels_input: str, min_duration: int):
    global user_client
    try:
        if user_client is None:
            user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)
            await user_client.start()
        
        channels = []
        
        if channels_input == "0":
            status = await message.answer("Getting all your channels...")
            async for dialog in user_client.get_dialogs():
                if dialog.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                    channels.append(dialog.chat.id)
            await status.delete()
        else:
            channel_items = channels_input.split()
            for item in channel_items:
                try:
                    chat = await user_client.get_chat(item)
                    channels.append(chat.id)
                except Exception as e:
                    logging.error(f"Error getting channel {item}: {e}")
        
        if not channels:
            await message.answer("No channels found.", reply_markup=main_menu())
            return
        
        status_msg = await message.answer(f"Searching in {len(channels)} channels...")
        results = []
        
        for idx, channel_id in enumerate(channels):
            try:
                if idx % 5 == 0:
                    await status_msg.edit_text(f"Searching in {len(channels)} channels...\nProgress: {idx}/{len(channels)}")
                
                async for msg in user_client.search_messages(channel_id, query=keyword, limit=100):
                    if msg.video:
                        duration = msg.video.duration or 0
                        if min_duration == 0 or duration >= min_duration:
                            chat = msg.chat
                            username = chat.username or f"id{chat.id}"
                            post_link = f"https://t.me/{username}/{msg.id}"
                            results.append({
                                'type': 'video',
                                'channel': chat.title or username,
                                'link': post_link,
                                'duration': duration,
                                'caption': msg.caption or msg.text or ''
                            })
                    elif msg.photo:
                        chat = msg.chat
                        username = chat.username or f"id{chat.id}"
                        post_link = f"https://t.me/{username}/{msg.id}"
                        results.append({
                            'type': 'photo',
                            'channel': chat.title or username,
                            'link': post_link,
                            'duration': 0,
                            'caption': msg.caption or msg.text or ''
                        })
            except Exception as e:
                logging.error(f"Error searching channel {channel_id}: {e}")
                continue
        
        await status_msg.delete()
        
        if not results:
            await message.answer(f"No results for '{keyword}'.", reply_markup=main_menu())
            return
        
        cache_key = f"search_{message.from_user.id}_{datetime.now().timestamp()}"
        pagination_cache[cache_key] = results
        await show_results_pagination(message, cache_key, 0)
        
    except Exception as e:
        logging.error(f"Search error: {e}")
        await message.answer(f"Error: {str(e)}", reply_markup=main_menu())

async def show_results_pagination(message: Message, cache_key: str, page: int):
    results = pagination_cache.get(cache_key, [])
    
    if not results:
        await message.answer("No results found.", reply_markup=main_menu())
        return
    
    per_page = 5
    total_pages = (len(results) - 1) // per_page + 1
    
    if page < 0 or page >= total_pages:
        page = 0
    
    start = page * per_page
    end = start + per_page
    results_page = results[start:end]
    
    result_text = f"Search Results (Page {page + 1}/{total_pages})\nTotal: {len(results)} results\n\n"
    
    for i, result in enumerate(results_page, start + 1):
        type_emoji = "Video" if result['type'] == 'video' else "Photo"
        duration_text = f" ({result['duration']}s)" if result['duration'] > 0 else ""
        caption_preview = result['caption'][:30] + "..." if result['caption'] else "No text"
        result_text += f"{i}. {type_emoji} {result['channel']} {duration_text}\n"
        result_text += f"   Link: {result['link']}\n"
        result_text += f"   Text: {caption_preview}\n\n"
    
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton(text="Previous", callback_data=f"page_{cache_key}_{page-1}"))
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton(text="Next", callback_data=f"page_{cache_key}_{page+1}"))
    
    keyboard_layout = [keyboard] if keyboard else []
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_layout) if keyboard_layout else main_menu()
    
    await message.answer(result_text, reply_markup=reply_markup, disable_web_page_preview=True)

@dp.message(lambda m: m.text == "Global Search")
async def global_search_start(message: Message, state: FSMContext):
    await state.set_state(Form.global_search_keyword)
    await message.answer("Global Search\n\nEnter keyword to search in public channels:")

@dp.message(Form.global_search_keyword)
async def global_search_keyword(message: Message, state: FSMContext):
    keyword = message.text.strip()
    status = await message.answer(f"Searching for '{keyword}'...\nThis may take a moment.")
    asyncio.create_task(global_search_task(message, keyword, status))
    await state.clear()

async def global_search_task(message: Message, keyword: str, status_msg: Message):
    global user_client
    try:
        if user_client is None:
            user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)
            await user_client.start()
        
        results = []
        
        try:
            await status_msg.edit_text(f"Searching public channels...\n{len(results)} results so far")
            
            async for msg in user_client.search_global(keyword, limit=150):
                if msg.chat and msg.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                    chat = msg.chat
                    
                    if msg.video:
                        username = chat.username or f"id{chat.id}"
                        post_link = f"https://t.me/{username}/{msg.id}"
                        results.append({
                            'type': 'video',
                            'channel': chat.title or username,
                            'link': post_link,
                            'members': getattr(chat, 'members_count', 0),
                            'caption': msg.caption or msg.text or '',
                            'duration': msg.video.duration or 0
                        })
                    elif msg.photo:
                        username = chat.username or f"id{chat.id}"
                        post_link = f"https://t.me/{username}/{msg.id}"
                        results.append({
                            'type': 'photo',
                            'channel': chat.title or username,
                            'link': post_link,
                            'members': getattr(chat, 'members_count', 0),
                            'caption': msg.caption or msg.text or '',
                            'duration': 0
                        })
        except Exception as e:
            logging.error(f"Global search error: {e}")
        
        await status_msg.delete()
        
        if not results:
            await message.answer(f"No results for '{keyword}'.", reply_markup=main_menu())
            return
        
        unique_results = []
        seen_links = set()
        for result in results:
            if result['link'] not in seen_links:
                unique_results.append(result)
                seen_links.add(result['link'])
        
        results = unique_results
        
        cache_key = f"global_{message.from_user.id}_{datetime.now().timestamp()}"
        pagination_cache[cache_key] = results
        await show_global_results_pagination(message, cache_key, 0)
        
    except Exception as e:
        logging.error(f"Global search error: {e}")
        await message.answer(f"Error: {str(e)}", reply_markup=main_menu())

async def show_global_results_pagination(message: Message, cache_key: str, page: int):
    results = pagination_cache.get(cache_key, [])
    
    if not results:
        await message.answer("No results found.", reply_markup=main_menu())
        return
    
    per_page = 5
    total_pages = (len(results) - 1) // per_page + 1
    
    if page < 0 or page >= total_pages:
        page = 0
    
    start = page * per_page
    end = start + per_page
    results_page = results[start:end]
    
    result_text = f"Global Search Results (Page {page + 1}/{total_pages})\nTotal: {len(results)} results\n\n"
    
    for i, result in enumerate(results_page, start + 1):
        type_emoji = "Video" if result['type'] == 'video' else "Photo"
        caption_preview = result['caption'][:30] + "..." if result['caption'] else "No text"
        result_text += f"{i}. {type_emoji} {result['channel']}\n"
        result_text += f"   Members: {result['members']}\n"
        result_text += f"   Link: {result['link']}\n"
        result_text += f"   Text: {caption_preview}\n\n"
    
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton(text="Previous", callback_data=f"global_page_{cache_key}_{page-1}"))
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton(text="Next", callback_data=f"global_page_{cache_key}_{page+1}"))
    
    keyboard_layout = [keyboard] if keyboard else []
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_layout) if keyboard_layout else main_menu()
    
    await message.answer(result_text, reply_markup=reply_markup, disable_web_page_preview=True)

@dp.callback_query(lambda c: c.data.startswith("page_"))
async def pagination_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    page = int(parts[-1])
    cache_key = "_".join(parts[1:-1])
    
    results = pagination_cache.get(cache_key, [])
    
    if not results:
        await callback.answer("Results expired.", show_alert=True)
        return
    
    per_page = 5
    total_pages = (len(results) - 1) // per_page + 1
    
    if page < 0 or page >= total_pages:
        return
    
    start = page * per_page
    end = start + per_page
    results_page = results[start:end]
    
    result_text = f"Search Results (Page {page + 1}/{total_pages})\nTotal: {len(results)} results\n\n"
    
    for i, result in enumerate(results_page, start + 1):
        type_emoji = "Video" if result['type'] == 'video' else "Photo"
        duration_text = f" ({result['duration']}s)" if result.get('duration', 0) > 0 else ""
        caption_preview = result['caption'][:30] + "..." if result['caption'] else "No text"
        result_text += f"{i}. {type_emoji} {result['channel']} {duration_text}\n"
        result_text += f"   Link: {result['link']}\n"
        result_text += f"   Text: {caption_preview}\n\n"
    
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton(text="Previous", callback_data=f"page_{cache_key}_{page-1}"))
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton(text="Next", callback_data=f"page_{cache_key}_{page+1}"))
    
    keyboard_layout = [keyboard] if keyboard else []
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
    
    await callback.message.edit_text(result_text, reply_markup=reply_markup, disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("global_page_"))
async def global_pagination_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    page = int(parts[-1])
    cache_key = "_".join(parts[2:-1])
    
    results = pagination_cache.get(cache_key, [])
    
    if not results:
        await callback.answer("Results expired.", show_alert=True)
        return
    
    per_page = 5
    total_pages = (len(results) - 1) // per_page + 1
    
    if page < 0 or page >= total_pages:
        return
    
    start = page * per_page
    end = start + per_page
    results_page = results[start:end]
    
    result_text = f"Global Search Results (Page {page + 1}/{total_pages})\nTotal: {len(results)} results\n\n"
    
    for i, result in enumerate(results_page, start + 1):
        type_emoji = "Video" if result['type'] == 'video' else "Photo"
        caption_preview = result['caption'][:30] + "..." if result['caption'] else "No text"
        result_text += f"{i}. {type_emoji} {result['channel']}\n"
        result_text += f"   Members: {result['members']}\n"
        result_text += f"   Link: {result['link']}\n"
        result_text += f"   Text: {caption_preview}\n\n"
    
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton(text="Previous", callback_data=f"global_page_{cache_key}_{page-1}"))
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton(text="Next", callback_data=f"global_page_{cache_key}_{page+1}"))
    
    keyboard_layout = [keyboard] if keyboard else []
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
    
    await callback.message.edit_text(result_text, reply_markup=reply_markup, disable_web_page_preview=True)
    await callback.answer()

@dp.message(lambda m: m.text == "Convert to RAR")
async def video_to_rar_start(message: Message, state: FSMContext):
    await state.set_state(Form.video_to_rar_waiting_file)
    await message.answer("Send a file or video\n\nSupports:\n- Video files\n- Photos\n- Other files\n\nRequires:\n- WinRAR for Windows\n- rar for Linux")

@dp.message(Form.video_to_rar_waiting_file)
async def video_to_rar_convert(message: Message, state: FSMContext):
    if not message.video and not message.document and not message.photo:
        await message.answer("Please send a file!")
        return
    
    if message.video:
        file_id = message.video.file_id
        file_name = f"video_{datetime.now().timestamp()}.mp4"
        file_size = message.video.file_size or 0
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_name = f"photo_{datetime.now().timestamp()}.jpg"
        file_size = 0
    else:
        file_id = message.document.file_id
        file_name = message.document.file_name or f"file_{datetime.now().timestamp()}"
        file_size = message.document.file_size or 0
    
    try:
        status_msg = await message.answer(f"Downloading {file_name}...\nSize: {file_size / (1024*1024):.2f} MB")
        
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)
        
        local_file = os.path.join(downloads_dir, file_name)
        await bot.download_file(file_path, local_file)
        
        await status_msg.edit_text(f"Converting to RAR...\nPlease wait")
        
        rar_name = f"{os.path.splitext(file_name)[0]}.rar"
        rar_path = os.path.join(downloads_dir, rar_name)
        
        rar_success = False
        
        try:
            paths = [r"C:\Program Files\WinRAR\WinRAR.exe", r"C:\Program Files (x86)\WinRAR\WinRAR.exe"]
            for rar_exe in paths:
                if os.path.exists(rar_exe):
                    subprocess.run([rar_exe, "a", "-ep1", "-m5", rar_path, local_file], check=True, capture_output=True, timeout=600)
                    rar_success = True
                    break
        except Exception as e:
            logging.warning(f"WinRAR error: {e}")
        
        if not rar_success:
            try:
                subprocess.run(["rar", "a", "-ep1", "-m5", rar_path, local_file], check=True, capture_output=True, timeout=600)
                rar_success = True
            except Exception as e:
                logging.warning(f"RAR error: {e}")
        
        if not rar_success:
            await status_msg.edit_text("Error: RAR not installed!\n\nFor Windows:\nhttps://www.win-rar.com/download.html\n\nFor Linux:\nsudo apt install rar")
            os.remove(local_file)
            await state.clear()
            return
        
        original_size = os.path.getsize(local_file) / (1024 * 1024)
        rar_size = os.path.getsize(rar_path) / (1024 * 1024)
        ratio = (1 - (rar_size / original_size)) * 100 if original_size > 0 else 0
        
        await status_msg.edit_text("Sending RAR file...")
        
        with open(rar_path, 'rb') as f:
            await bot.send_document(message.chat.id, f, caption=f"Conversion complete!\n\nStats:\n- Original: {original_size:.2f} MB\n- RAR: {rar_size:.2f} MB\n- Compression: {ratio:.1f}%\n- File: {rar_name}")
        
        await status_msg.delete()
        os.remove(local_file)
        os.remove(rar_path)
        
        await message.answer("Done!", reply_markup=main_menu())
        await state.clear()
        
    except subprocess.TimeoutExpired:
        await message.answer("Error: File too large or compression timed out.", reply_markup=main_menu())
        await state.clear()
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(f"Error: {str(e)}", reply_markup=main_menu())
        await state.clear()

@dp.message(lambda m: m.text == "Exit")
async def exit_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Goodbye!", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def unknown(message: Message, state: FSMContext):
    await message.answer("Choose from menu:", reply_markup=main_menu())

async def main():
    print("Bot started!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
