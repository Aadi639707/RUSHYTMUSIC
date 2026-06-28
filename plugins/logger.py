from pyrogram import Client, filters
from pyrogram.types import Message
import os
@Client.on_message(filters.all, group=-1)
async def chat_logger(client: Client, message: Message):
    if not message.chat:
        return
    chat_id = str(message.chat.id)
    if not os.path.exists("chats.txt"):
        open("chats.txt", "w").close()
    with open("chats.txt", "r+") as f:
        chats = f.read().splitlines()
        if chat_id not in chats:
            f.write(chat_id + "\n")
