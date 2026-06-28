import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core import call, music_queue, app
START_IMG_URL = "https://telegra.ph/file/0c9a2f643e2f5b8f2f451.jpg"
# ══════════════════════════════════════════
# /start
# ══════════════════════════════════════════
@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    bot_name = client.me.first_name
    bot_username = client.me.username
    caption_text = (
        f"ʜᴇʏ {message.from_user.mention} , 🥀\n\n"
        f"⊙ ᴛʜɪs ɪs ˹ {bot_name} ˼ !\n\n"
        f"➻ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.\n\n"
        f"⊙ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ
ᴄᴏᴍᴍᴀɴᴅs."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⁺", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_menu")],        [
            InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ↗", url="https://t.me/rushdeveloper"),
            InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ ↗", url="https://t.me/rushbots")
        ]
    ])
    try:
        await message.reply_photo(photo=START_IMG_URL, caption=caption_text,
reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption_text, reply_markup=buttons)
# ══════════════════════════════════════════
# /ping — Bot speed check
# ══════════════════════════════════════════
@Client.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 **Pinging...**")
    end = time.time()
    speed = round((end - start) * 1000, 2)
    await msg.edit_text(
        f"🏓 **PONG!**\n\n"
        f"⚡  **Speed:** `{speed}ms`\n"
        f"✅  **Bot is Online & Running!**"
    )
# ══════════════════════════════════════════
# /reload — Admin only, reload bot in GC
# ══════════════════════════════════════════
@Client.on_message(filters.command("reload") & filters.group)
async def reload_command(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    # Check admin
    is_admin = False
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if "ADMINISTRATOR" in str(member.status).upper() or "OWNER" in str(member.status).upper():
            is_admin = True
    except:
        pass
    if not is_admin:
        return await message.reply_text("⚠️ **Only admins can use this command.**")
    msg = await message.reply_text("🔄 **Reloading bot for this group...**")
    # Clear queue for this group
    music_queue.pop(chat_id, None)
    # Leave VC if active
    try:
        await call.leave_call(int(chat_id))
    except:
        pass
    await asyncio.sleep(1)
    await msg.edit_text(
        "✅  **Bot Reloaded Successfully!**\n\n"
        "▪ Queue cleared\n"
        "▪ Voice Chat left\n"
        "▪ Ready to play again 🎵"
    )
# ══════════════════════════════════════════
# Bot commands list (shown when / is typed)
# ══════════════════════════════════════════
COMMANDS = [
    ("play", "Play a song in Voice Chat"),
    ("ping", "Check bot speed & status"),
    ("reload", "Reload bot in group [Admin]"),
    ("skip", "Skip current track [Admin]"),
    ("pause", "Pause playback [Admin]"),
    ("resume", "Resume playback [Admin]"),
    ("stop", "Stop & leave VC [Admin]"),
    ("end", "End stream & leave VC [Admin]"),
    ("start", "Start the bot"),
]
