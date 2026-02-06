import re
from pyrogram import Client, filters
from config import Config

app = Client(
    "video_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Helper: Name Cleaning
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

# Helper: Time Formatting
def format_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

# Notification Logic
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

# Startup and Restart Notification
async def start_bot():
    await app.start()
    bot_info = await app.get_me()
    print(f"@{bot_info.username} started successfully!")
    
    # Send a message to the owner or the updates channel when the bot starts
    startup_msg = "✅ <b>Bot Started Successfully!</b>\n\n<i>The video provider service is now active and monitoring the database channel.</i>"
    try:
        await app.send_message(Config.OWNER_ID or Config.UPDATES_CHANNEL_ID, startup_msg)
    except Exception:
        pass # Fallback if IDs are not set correctly

if __name__ == "__main__":
    app.run(start_bot())
