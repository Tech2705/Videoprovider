import os

class Config:
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", "0"))
    UPDATES_CHANNEL_ID = int(os.environ.get("UPDATES_CHANNEL_ID", "0"))
