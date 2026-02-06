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
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("Web server started on port 8000")

# --- BOT LOGIC ---
def get_clean_name(text):
    if not text: return "New Video"
    patterns = [r"(?i)Join\s*:\s*@\w+", r"(?i)by\s*@\w+", r"@Hanime_universe", r"@hanimeUniverse", r"\.mp4|\.mkv"]
    for p in patterns:
        text = re.sub(p, "", text)
    return text.strip()

@app.on_message(filters.chat(Config.DB_CHANNEL_ID) & (filters.video | filters.document))
async def handle_video(client, message):
    raw_name = message.caption or (message.video.file_name if message.video else "Video File")
    clean_name = get_clean_name(raw_name)
    duration = f"{message.video.duration // 60}m {message.video.duration % 60}s" if message.video else "N/A"
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
        print(f"Update failed: {e}")

# --- STARTUP SEQUENCE ---
async def main():
    await start_web_server()
    await app.start()
    bot_info = await app.get_me()
    print(f"@{bot_info.username} is online.")
    
    # Secure startup message logic
    status_text = "✅ <b>Bot Started/Restarted!</b>\n\nWeb server live on Port 8000."
    try:
        # Check if OWNER_ID exists in Config and is not 0
        target = getattr(Config, 'OWNER_ID', Config.UPDATES_CHANNEL_ID) or Config.UPDATES_CHANNEL_ID
        await app.send_message(target, status_text)
    except:
        await app.send_message(Config.UPDATES_CHANNEL_ID, status_text)
        
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
