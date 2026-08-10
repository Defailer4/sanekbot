import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from google import genai

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID", 0))

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Ты — саркастичный и токсичный пацан в групповом чате. 
Тебе прислали видео-кружок. Твоя задача — высмеять автора за то, что он записал бесполезный кружок вместо текста.

Инструкции по анализу:
1. Посмотри на ВИДЕО: обрати внимание на глупый ракурс (потолок, подбородок, темнота, размытый асфальт, странное лицо).
2. Послушай ЗВУК: оцени наличие воды, вздохов, "ээээ", отсутствия сути или банальности мысли.
3. Ответь кратко (2-4 предложения), используя пацанский сленг.
4. Отругай одновременно и за видеоряд, и за содержание речи. Посоветуй писать текстом.
"""

@dp.message(F.video_note)
async def handle_circle(message: Message):
    if TARGET_USER_ID and message.from_user.id != TARGET_USER_ID:
        return

    processing_msg = await message.reply("👀 *Анализирую этот шедевр кинематографа...*", parse_mode="Markdown")

    file_path = f"circle_{message.message_id}.mp4"

    try:
        tg_file = await bot.get_file(message.video_note.file_id)
        await bot.download_file(tg_file.file_path, file_path)

        uploaded_file = ai_client.files.upload(file=file_path)

        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(1)
            uploaded_file = ai_client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise Exception("Ошибка обработки видео на стороне Google")

        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[uploaded_file, SYSTEM_PROMPT]
        )

        ai_client.files.delete(name=uploaded_file.name)

        await message.reply(response.text)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply("Даже нейросеть офигела от этого кружка и выдала ошибку.")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        await processing_msg.delete()

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())