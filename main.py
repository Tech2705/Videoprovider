import re
from pyrogram import Client, filters
from config import Config

app = Client(
    "video_provider_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Helper: Remove unwanted tags and extensions
def get_clean_name(text):
    if not text: return "New Video"
    # Regex to strip @tags and "Join:" phrases
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

# Helper: Format seconds to HH:MM:SS
def format_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

@app.on_message(filters.chat(Config.DB_CHANNEL_ID) & (filters.video | filters.document))
async def handle_notification(client, message):
    # 1. Extract and Clean Name
    raw_name = message.caption or (message.video.file_name if message.video else "Video File")
    clean_name = get_clean_name(raw_name)
    
    # 2. Get Duration and Thumbnail
    duration = format_duration(message.video.duration) if message.video else "N/A"
    thumb = message.video.thumbs[0].file_id if (message.video and message.video.thumbs) else None
    
    # 3. Create Link
    bot = await client.get_me()
    share_link = f"https://t.me/{bot.username}?start={message.id}"
    
    # 4. Construct Caption
    caption = (
        f"🎬 <b>New Video Uploaded!</b>\n\n"
        f"📌 <b>Title:</b> {clean_name}\n"
        f"⏳ <b>Duration:</b> {duration}\n\n"
        f"🚀 <b>Watch Now:</b> <a href='{share_link}'>Click Here</a>"
    )

    # 5. Send to Updates Channel
    try:
        if thumb:
            await client.send_photo(Config.UPDATES_CHANNEL_ID, photo=thumb, caption=caption)
        else:
            await client.send_message(Config.UPDATES_CHANNEL_ID, text=caption)
    except Exception as e:
        print(f"Error: {e}")

print("Bot is running...")
app.run()
