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

# --- WEB SERVER (For Koyeb Health Check) ---
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
    # Removes the specific tags you mentioned
    patterns = [r"(?i)Join\s*:\s*@\w+", r"(?i)by\s*@\w+", r"@Hanime_universe", r"@hanimeUniverse", r"\.mp4|\.mkv"]
    for p in patterns:
        text = re.sub(p, "", text)
    return text.strip()

# --- HANDLERS ---

# 1. Database Monitor Handler
@app.on_message(filters.chat(Config.DB_CHANNEL_ID) & (filters.video | filters.document))
async def handle_video_upload(client, message):
    # This will show in Koyeb logs to confirm the bot 'sees' the file
    print(f"DEBUG: New file detected in DB Channel! Message ID: {message.id}")

    try:
        raw_name = message.caption or (message.video.file_name if message.video else "Video File")
        clean_name = get_clean_name(raw_name)
        
        # Format duration safely
        duration = "N/A"
        if message.video and message.video.duration:
            m, s = divmod(message.video.duration, 60)
            h, m = divmod(m, 60)
            duration = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
        
        thumb = message.video.thumbs[0].file_id if (message.video and message.video.thumbs) else None
        
        bot = await client.get_me()
        share_link = f"https://t.me/{bot.username}?start={message.id}"
        
        caption = (
            f"🎬 <b>New Video Uploaded!</b>\n\n"
            f"📌 <b>Title:</b> {clean_name}\n"
            f"⏳ <b>Duration:</b> {duration}\n\n"
            f"🚀 <b>Watch Now:</b> <a href='{share_link}'>Click Here</a>"
        )

        await client.send_photo(
            chat_id=Config.UPDATES_CHANNEL_ID,
            photo=thumb if thumb else "https://telegra.ph/file/default_thumbnail.jpg",
            caption=caption
        )
        print("DEBUG: Notification successfully sent to Updates Channel!")

    except Exception as e:
        print(f"DEBUG ERROR: {e}")

# 2. Start Command Handler
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if len(message.command) > 1:
        msg_id = message.command[1]
        try:
            await client.copy_message(
                chat_id=message.from_user.id,
                from_chat_id=Config.DB_CHANNEL_ID,
                message_id=int(msg_id)
            )
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")
    else:
        await message.reply_text("👋 Hello! Send me a link from the updates channel to get your video.")

# --- STARTUP ---
async def main():
    await start_web_server()
    await app.start()
    bot_info = await app.get_me()
    print(f"Bot @{bot_info.username} is fully active!")
    
    # Send status to Updates Channel
    try:
        await app.send_message(Config.UPDATES_CHANNEL_ID, "✅ <b>Bot is Online and Monitoring DB Channel!</b>")
    except:
        pass
        
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
