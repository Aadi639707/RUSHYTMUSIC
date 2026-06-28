import os
import asyncio
import subprocess
import aiohttp
import random
import string
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
from core import call, music_queue, app, assistant
os.makedirs("downloads", exist_ok=True)
SHRUTI_API_URL = "https://api01.shrutibots.site"
SHRUTI_APIS = [
    "API",
    "API",
    "API",
    "API",
    "API",
]
API_INDEX = 0
CACHE_CHANNEL = -1004404949582
KNOWN_CACHE = set()
def clean_title(title: str, max_len: int = 35) -> str:
    import re
    title = re.sub(r'\(.*?(Official|Lyric|Video|Audio|HD|HQ|4K|Full).*?\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\[.*?(Official|Lyric|Video|Audio|HD|HQ|4K|Full).*?\]', '', title, flags=re.IGNORECASE)
    title = title.strip(" |-:")
    if len(title) > max_len:
        title = title[:max_len].rsplit(" ", 1)[0] + "..."
    return title
def yt_search(query: str) -> dict | None:
    try:
        # Yahan max_results=10 kiya hai aur duration filter lagaya hai
        result = subprocess.run(
            [
                "/usr/bin/python3", "-c",
                f"""
from youtube_search import YoutubeSearch
results = YoutubeSearch({repr(query)}, max_results=10).to_dict()
for v in results:
    duration = v.get('duration', '0:00')
    parts = duration.split(':')
    # Agar video me hours hain (jaise 1:02:05) ya 10 minute se bada hai, toh
skip karo
    if len(parts) >= 3:
        continue
    if len(parts) == 2 and int(parts[0]) > 10:
        continue
    print(v['id'])
    print(v['title'])
    print(v.get('duration', 'N/A'))
    thumbs = v.get('thumbnails', [])
    print(thumbs[0] if thumbs else '')
    break
"""
            ],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 3 and lines[0]:
            return {
                "id":       lines[0].strip(),
                "title":    lines[1].strip(),
                "duration": lines[2].strip() if len(lines) > 2 else "N/A",
                "thumb":    lines[3].strip() if len(lines) > 3 else "",
                "link":     f"https://youtube.com/watch?v={lines[0].strip()}",
            }
    except Exception as e:
        print(f"[YT Search Error] {e}")
    return None
async def search_cache(video_id: str) -> str | None:
    file_path = os.path.join("downloads", f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        KNOWN_CACHE.add(video_id)
        return file_path
    try:
        async for msg in app.search_messages(CACHE_CHANNEL, video_id):
            if msg.audio or msg.document:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    KNOWN_CACHE.add(video_id)
                    return file_path
                print(f"[Cache] Downloading: {video_id}")
                await app.download_media(msg, file_name=file_path)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    KNOWN_CACHE.add(video_id)
                    return file_path
    except Exception as e:
        print(f"[Cache Search Error] {e}")
    return None
async def upload_to_cache(file_path: str, video_id: str, title: str) -> None:    if video_id in KNOWN_CACHE:
        return
    try:
        await app.send_audio(
            CACHE_CHANNEL,
            audio=file_path,
            caption=f"#{video_id}\n{title}",
            title=title,
        )
        KNOWN_CACHE.add(video_id)
        print(f"[Cache] Uploaded: {title}")
    except Exception as e:
        print(f"[Cache Upload Error] {e}")
async def shruti_download(video_id: str) -> str | None:
    global API_INDEX
    try:
        file_path = os.path.join("downloads", f"{video_id}.mp3")
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        for attempt in range(len(SHRUTI_APIS)):
            api_key = SHRUTI_APIS[API_INDEX % len(SHRUTI_APIS)]
            print(f"[Shruti] Using API #{(API_INDEX % len(SHRUTI_APIS)) + 1}")
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{SHRUTI_API_URL}/download",
                    params={"url": video_id, "type": "audio", "api_key": api_key},
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as r:
                    if r.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in r.content.iter_chunked(131072):
                                f.write(chunk)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            return file_path
                    else:
                        print(f"[Shruti] API #{(API_INDEX % len(SHRUTI_APIS)) + 1} failed, rotating...")
                        API_INDEX += 1
        return None
    except Exception as e:
        print(f"[Shruti Download Error] {e}")
        API_INDEX += 1
        return None
def make_buttons(bot_username: str, link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▷",  callback_data="resume"),
            InlineKeyboardButton("II", callback_data="pause"),
            InlineKeyboardButton("⏭", callback_data="skip"),
            InlineKeyboardButton("⏹", callback_data="stop"),
        ],
        [
            InlineKeyboardButton("⏪  -15",  callback_data="seek_back"),
            InlineKeyboardButton("🔁 Loop", callback_data="loop"),
            InlineKeyboardButton("⏩  +15",  callback_data="seek_fwd"),
        ],
        [InlineKeyboardButton("🎧 Watch on YouTube", url=link)],
        [InlineKeyboardButton(
            "➕  Add Me To Your Group",
            url=f"https://t.me/{bot_username}?startgroup=true"
        )],
    ])
async def play_song(client: Client, chat_id: int, track: dict, requester: str, msg=None):
    short_title = clean_title(track["title"])
    video_id    = track["id"]
    from_cache  = False
    if msg:
        await msg.edit_text(
            f"🎵 **{short_title}**\n"
            f"⏱ `{track['duration']}`\n"
            "⚡  **Loading...**"
        )
    file_path = await search_cache(video_id)
    if file_path:
        from_cache = True
    else:
        file_path = await shruti_download(video_id)
        if not file_path:
            if msg:
                await msg.edit_text("⚠️ **Download failed.** Trying next song...")
            return False
        asyncio.create_task(upload_to_cache(file_path, video_id, short_title))
    song = {
        "title":     short_title,
        "duration":  track["duration"],
        "thumbnail": track["thumb"],
        "link":      track["link"],
        "file_path": file_path,
        "requester": requester,
    }
    if chat_id not in music_queue:
        music_queue[chat_id] = []
    music_queue[chat_id].append(song)
    bot_username = client.me.username
    buttons      = make_buttons(bot_username, song["link"])
    if len(music_queue[chat_id]) == 1:
        try:
            await call.play(chat_id, MediaStream(song["file_path"]))
        except Exception as e:
            music_queue.pop(chat_id, None)
            if msg:
                await msg.edit_text("⚠️ **Voice Chat Error!** Start Voice Chat first.")
            return False
        caption = (
            f"**⬡ PLAYBACK ACTIVATED. | ENJOY THE MUSIC |**\n\n"
            f"▪ **MELODY :** {song['title']}\n"
            f"▪ **LENGTH :** {song['duration']}\n"
            f"▪ **REQUESTER :** {song['requester']}\n"
        )
        await client.send_photo(
            chat_id,
            photo=song["thumbnail"],
            caption=caption,
            reply_markup=buttons,
        )
        if msg:
            await msg.delete()
    return True
@Client.on_message(filters.command("play") & filters.group)
async def play_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ **Format:** `/play [song name]`\n"
            "**Example:** `/play Kesariya Arijit Singh`"
        )
    chat_id = message.chat.id
    query   = message.text.split(None, 1)[1].strip()
    msg     = await message.reply_text("🔍 **Searching...**")
    try:
        await assistant.get_chat(chat_id)
    except Exception:
        try:
            chat_info   = await app.get_chat(chat_id)
            invite_link = chat_info.invite_link or await app.export_chat_invite_link(chat_id)
            await asyncio.sleep(1)
            await assistant.join_chat(invite_link)
        except Exception:
            return await msg.edit_text(
                "⚠️ **Cannot add Assistant.**\n"
                "Please grant **Invite Users** permission."
            )
    track = await asyncio.to_thread(yt_search, query)
    if not track:
        return await msg.edit_text("⚠️ **Track not found.**")
    await play_song(client, chat_id, track, message.from_user.mention, msg)
@Client.on_message(filters.command("random") & filters.group)
async def random_command(client: Client, message: Message):
    chat_id = message.chat.id
    is_admin = False
    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if "ADMINISTRATOR" in str(member.status).upper() or "OWNER" in str(member.status).upper():
            is_admin = True
    except:
        pass
    if not is_admin:
        return await message.reply_text("⚠️ **Only admins can use this command.**")
    msg = await message.reply_text("🎲 **Starting random 24/7 mode...**")
    try:
        await assistant.get_chat(chat_id)
    except Exception:
        try:
            chat_info   = await app.get_chat(chat_id)
            invite_link = chat_info.invite_link or await app.export_chat_invite_link(chat_id)
            await asyncio.sleep(1)
            await assistant.join_chat(invite_link)
        except Exception:
            return await msg.edit_text("⚠️ **Cannot add Assistant.**")
    await msg.edit_text("✅  **Random 24/7 mode activated!**\n\nUse `/end` to
stop.")
    genres = ["hindi song", "bollywood hit", "english song", "punjabi track", "lofi mashup", "trending song"]
    while chat_id in music_queue or True:
        try:
            if chat_id not in music_queue or len(music_queue[chat_id]) == 0:
                char1 = random.choice(string.ascii_lowercase)
                char2 = random.choice(string.ascii_lowercase)
                random_genre = random.choice(genres)
                query = f"{char1}{char2} {random_genre}"
                track = await asyncio.to_thread(yt_search, query)
                if track:
                    await play_song(client, chat_id, track, "🎲 Random Mode")
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(10)
        except Exception as e:
            print(f"[Random Error] {e}")
            await asyncio.sleep(10)
