import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream, Update
from core import call, music_queue, app
async def is_admin(client, chat_id, user_id):
    if user_id in [client.me.id, chat_id]:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if "ADMINISTRATOR" in str(member.status).upper() or "OWNER" in str(member.status).upper():
            return True
        return False
    except:
        return False
async def leave_vc(chat_id):
    try:
        await call.leave_call(int(chat_id))
    except Exception as e:
        print(f"[Leave Error] {e}")
async def play_next_system(chat_id, is_auto=False):
    if chat_id not in music_queue or not music_queue[chat_id]:
        await leave_vc(chat_id)
        return
    old_song = music_queue[chat_id].pop(0)
    try:
        if os.path.exists(old_song.get("file_path", "")):
            os.remove(old_song["file_path"])
    except:
        pass
    if not music_queue[chat_id]:
        await leave_vc(chat_id)
        return
    next_song = music_queue[chat_id][0]
    try:
        if is_auto:
            await asyncio.sleep(0.5)
        try:
            await call.change_stream(int(chat_id), MediaStream(next_song["file_path"]))
        except:
            try:
                await call.play(int(chat_id), MediaStream(next_song["file_path"]))
            except:
                pass
        bot_username = app.me.username
        buttons = InlineKeyboardMarkup([
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
            [InlineKeyboardButton("🎧 Watch on YouTube", url=f"https://youtube.com")],
            [InlineKeyboardButton(
                "➕  Add Me To Your Group",
                url=f"https://t.me/{bot_username}?startgroup=true"
            )],
        ])
        caption = (
            f"**⬡ PLAYBACK ACTIVATED. | ENJOY THE MUSIC |**\n\n"
            f"▪ **MELODY :** {next_song['title']}\n"
            f"▪ **LENGTH :** {next_song['duration']}\n"
            f"▪ **REQUESTER :** {next_song['requester']}"
        )
        await app.send_photo(
            chat_id,
            photo=next_song["thumbnail"],
            caption=caption,
            reply_markup=buttons,
        )
    except:
        await play_next_system(chat_id, is_auto=True)
@call.on_update()
async def global_update_handler(client, update: Update):
    try:
        chat_id = getattr(update, "chat_id", None)
        if not chat_id:
            return
        update_type = type(update).__name__
        if "ChatUpdate" in update_type or hasattr(update, "status"):
            status = str(getattr(update, "status", "")).lower()
            if any(x in status for x in ["kicked", "left", "closed", "dropped"]):
                music_queue.pop(chat_id, None)
                return
        if "Ended" in update_type or "Stop" in update_type:
            await play_next_system(chat_id, is_auto=True)
    except:
        pass
async def process_action(client, chat_id, action, user_id, query=None, message=None):
    if not await is_admin(client, chat_id, user_id):
        err_msg = "⚠️ Only admins can use this command."
        if query:
            return await query.answer(err_msg, show_alert=True)
        if message:
            return await message.reply_text(err_msg)
    if action in ["stop", "end"]:
        music_queue.pop(chat_id, None)
        await leave_vc(chat_id)
        if query:
            try:
                await query.message.delete()
            except:
                pass
            return await query.answer("Stream Stopped!")
        if message:
            return await message.reply_text("⏹ **STREAM ENDED & LEFT VC.**")
    if chat_id not in music_queue or len(music_queue[chat_id]) == 0:
        if query:
            return await query.answer("Nothing is playing right now!", show_alert=True)
        if message:
            return await message.reply_text("⚠️ Nothing is playing right now.")
        return
    try:
        if action == "pause":
            await call.pause(int(chat_id))
            if query:
                await query.answer("Stream Paused!")
        elif action == "resume":
            await call.resume(int(chat_id))
            if query:
                await query.answer("Stream Resumed!")
        elif action == "skip":
            if len(music_queue[chat_id]) > 1:
                if query:
                    await query.answer("Skipping to next track...")
                    try:
                        await query.message.delete()
                    except:
                        pass
                await play_next_system(chat_id, is_auto=False)
            else:
                music_queue.pop(chat_id, None)
                await leave_vc(chat_id)
                if query:
                    try:
                        await query.message.delete()
                    except:
                        pass
                    await query.answer("Queue is empty! Stream stopped.")
    except Exception as e:
        if query:
            await query.answer(f"Error: {str(e)[:40]}", show_alert=True)
@Client.on_callback_query(filters.regex("^(pause|resume|skip|stop|end|seek_back|seek_fwd|loop)$"))
async def button_route(client: Client, query: CallbackQuery):
    if query.data in ["seek_back", "seek_fwd", "loop"]:
        await query.answer("Coming soon!", show_alert=False)
        return
    await process_action(client, query.message.chat.id, query.data, query.from_user.id, query=query)
@Client.on_message(filters.command(["skip", "stop", "end", "pause", "resume"]) & filters.group)
async def text_route(client: Client, message: Message):
    action = message.command[0].lower().split("@")[0]
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    await process_action(client, message.chat.id, action, user_id, message=message)
