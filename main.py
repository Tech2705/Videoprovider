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

# --- WEB SERVER (Required for Koyeb Health Check) ---
async def health_check(request):
    return web.Response(text="Bot is online!")

async def start_web_server():
    server = web.Application()
    server.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("Health check server live on port 8000")

# --- UTILITIES ---
def get_clean_name(text):
    if not text: return "New Video"
    patterns = [r"(?i)Join\s*:\s*@\w+", r"(?i)by\s*@\w+", r"@Hanime_universe", r"@hanimeUniverse", r"\.mp4|\.mkv"]
    for p in patterns:
        text = re.sub(p, "", text)
    return text.strip()

def get_readable_size(size_bytes):
    if size_bytes == 0: return "0B"
    import math
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

# --- HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    print(f"User {message.from_user.id} sent /start")
    if len(message.command) > 1:
        data = message.command[1]
        try:
            await client.copy_message(
                chat_id=message.from_user.id,
                from_chat_id=Config.DB_CHANNEL_ID,
                message_id=int(data)
            )
        except Exception as e:
            await message.reply_text(f"❌ Error: File not found.\n{e}")
    else:
        await message.reply_text("👋 Bot is active! Send a link to get your video.")

@app.on_message(filters.chat(Config.DB_CHANNEL_ID) & (filters.video | filters.document))
async def handle_db_upload(client, message):
    print(f"New file in DB! ID: {message.id}")
    file = message.video or message.document
    raw_name = message.caption or file.file_name or "Video File"
    clean_name = get_clean_name(raw_name)
    
    # Duration Logic
    duration = "N/A"
    if message.video and message.video.duration:
        m, s = divmod(message.video.duration, 60)
        h, m = divmod(m, 60)
        duration = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
    
    caption = (
        f"🎬 <b>New Video Alert!</b>\n\n"
        f"📌 <b>Name:</b> {clean_name}\n"
        f"⏳ <b>Duration:</b> {duration}\n"
        f"📁 <b>Size:</b> {get_readable_size(file.file_size)}\n\n"
        f"🚀 <b>Link:</b> <a href='https://t.me/{(await client.get_me()).username}?start={message.id}'>Click Here</a>"
    )

    thumb = message.video.thumbs[0].file_id if (message.video and message.video.thumbs) else None
    await client.send_photo(Config.UPDATES_CHANNEL_ID, photo=thumb or "https://telegra.ph/file/default.jpg", caption=caption)

# --- MAIN STARTUP ---
async def main():
    # 1. Start Web Server first so Koyeb is happy
    await start_web_server()
    
    # 2. Start Bot
    await app.start()
    bot_info = await app.get_me()
    print(f"Successfully started as @{bot_info.username}")
    
    # 3. Robust Startup Notification
    startup_text = "🚀 <b>Bot Started/Restarted Successfully!</b>\n\nWatching DB Channel and ready for /start commands."
    
    # Try sending to Owner, then try Updates Channel
    try:
        if Config.OWNER_ID != 0:
            await app.send_message(Config.OWNER_ID, startup_text)
        else:
            await app.send_message(Config.UPDATES_CHANNEL_ID, startup_text)
    except Exception as e:
        print(f"Could not send startup message: {e}")
        
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
