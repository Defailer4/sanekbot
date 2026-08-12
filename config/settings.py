import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TARGET_USER_IDS_STR = os.getenv("TARGET_USER_ID", "0")
TARGET_USER_IDS = [
    int(uid.strip())
    for uid in TARGET_USER_IDS_STR.split(",")
    if uid.strip().isdigit() and int(uid.strip()) != 0
]