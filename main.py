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

# --- WEB SERVER FOR KOYEB HEALTH CHECK ---
async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    server = web.Application()
    server.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    # Koyeb looks for Port 8000 by default
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("Web server started on port 8000 for health checks.")

# --- BOT LOGIC ---
def get_clean_name(text):
    if not text: return "New Video"
    patterns = [
        r"(?i)Join\s*:\s*@\w+", 
        r"(?i)by\s*@\w+", 
        r"@Hanime_universe", 
        r"@hanimeUniverse",
        r"\.mp4|\.mkv|\.mov|\.avi"
    ]
    for p in patterns:
        text = re.sub(p, "", text)
    return text.strip()

def format_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

@app.on_message(filters.chat(Config.DB_CHANNEL_ID) & (filters.video | filters.document))
async def handle_video(client, message):
    raw_name = message.caption or (message.video.file_name if message.video else "Video File")
    clean_name = get_clean_name(raw_name)
    duration = format_duration(message.video.duration) if message.video else "N/A"
    thumb = message.video.thumbs[0].file_id if (message.video and message.video.thumbs) else None
    
    bot = await client.get_me()
    share_link = f"https://t.me/{bot.username}?start={message.id}"
    
    caption = (
        f"🎬 <b>New Video Uploaded!</b>\n\n"
        f"📌 <b>Title:</b> {clean_name}\n"
        f"⏳ <b>Duration:</b> {duration}\n\n"
        f"🚀 <b>Watch Now:</b> <a href='{share_link}'>Click Here</a>"
    )

    try:
        if thumb:
            await client.send_photo(Config.UPDATES_CHANNEL_ID, photo=thumb, caption=caption)
        else:
            await client.send_message(Config.UPDATES_CHANNEL_ID, text=caption)
    except Exception as e:
        print(f"Error: {e}")

# --- STARTUP SEQUENCE ---
async def main():
    # Start web server first to satisfy Koyeb health check
    await start_web_server()
    
    # Start the bot
    await app.start()
    bot_info = await app.get_me()
    print(f"@{bot_info.username} is online.")
    
    # Send Restart/Start Message
    status_text = "🚀 <b>Bot Re-started Successfully!</b>\n\nWeb server is live on Port 8000.\nMonitoring DB Channel..."
    target = Config.OWNER_ID if Config.OWNER_ID != 0 else Config.UPDATES_CHANNEL_ID
    try:
        await app.send_message(target, status_text)
    except:
        pass
        
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
