import re
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from config import Config

app = Client(
    "video_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- WEB SERVER ---
async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    server = web.Application()
    server.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

# --- UTILITIES ---
def get_clean_name(text):
    if not text: return "New Video"
    patterns = [r"(?i)Join\s*:\s*@\w+", r"(?i)by\s*@\w+", r"@Hanime_universe", r"@hanimeUniverse", r"\.mp4|\.mkv"]
    for p in patterns:
        text = re.sub(p, "", text)
    return text.strip()

def get_readable_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

# --- HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    # This prints in Koyeb so you can see if the bot receives your /start
    print(f"DEBUG: Start command received from {message.from_user.id}")
    
    if len(message.command) > 1:
        data = message.command[1]
        try:
            await client.copy_message(
                chat_id=message.from_user.id,
                from_chat_id=Config.DB_CHANNEL_ID,
                message_id=int(data)
            )
        except Exception as e:
            print(f"DEBUG START ERROR: {e}")
            await message.reply_text("❌ The file could not be found. It may have been deleted from the database.")
    else:
        await message.reply_text(f"👋 Hello {message.from_user.first_name}!\n\nI am your Video Provider Bot. Send me a link to get your file.")

@app.on_message(filters.chat(Config.DB_CHANNEL_ID) & (filters.video | filters.document))
async def handle_db_upload(client, message):
    print(f"DEBUG: New upload detected! ID: {message.id}")
    
    file = message.video or message.document
    raw_name = message.caption or file.file_name or "Video File"
    
    clean_name = get_clean_name(raw_name)
    duration = "N/A"
    if message.video and message.video.duration:
        m, s = divmod(message.video.duration, 60)
        h, m = divmod(m, 60)
        duration = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
    
    file_size = get_readable_size(file.file_size)
    thumb = message.video.thumbs[0].file_id if (message.video and message.video.thumbs) else None
    
    bot = await client.get_me()
    share_link = f"https://t.me/{bot.username}?start={message.id}"
    
    caption = (
        f"🎬 <b>New Video Alert!</b>\n\n"
        f"📌 <b>Name:</b> {clean_name}\n"
        f"⏳ <b>Duration:</b> {duration}\n"
        f"📁 <b>Size:</b> {file_size}\n\n"
        f"🚀 <b>Watch/Download:</b> <a href='{share_link}'>Click Here</a>"
    )

    try:
        await client.send_photo(
            chat_id=Config.UPDATES_CHANNEL_ID,
            photo=thumb if thumb else "https://telegra.ph/file/default_thumbnail.jpg",
            caption=caption
        )
        print("DEBUG: Notification sent!")
    except Exception as e:
        print(f"DEBUG NOTIFY ERROR: {e}")

# --- MAIN ---
async def main():
    await start_web_server()
    await app.start()
    bot_info = await app.get_me()
    print(f"Bot @{bot_info.username} is running!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
