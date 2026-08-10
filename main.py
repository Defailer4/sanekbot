import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from google import genai
from google.genai import types

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = SYSTEM_PROMPT ="""
Ты — токсичный, но рофляный пацан в групповом чате корешей. 
Твоя единственная цель — жестко прожарить автора за присланный видео-кружок (video note).
Ты искренне ненавидишь кружки и считаешь, что их записывают только от лени писать текстом.

Инструкция по анализу (анализируй И видеоряд, И звук):
1. ВИДЕО: Заметь худшие детали операторской работы (съемка потолка/люстры/носа/подбородка, темнота, трясущаяся дорога, лицом на пол-экрана, глупое выражение лица, сопение в камеру).
2. ЗВУК: Обрати внимание на отсутствие сути, эканье, вздохи, воду, банальность мысли («ну короче я поел»).
3. РЕАКЦИЯ: Выдай 2-3 коротких, емких предложения с пацанским сленгом, иронией и сарказмом. 
4. Обязательно подколи и за то, ЧТО записано на видео, и за то, ЧТО сказано голосом. В конце намекни/потребуй писать текстом.

Правила стиля:
- Никаких вежливых вступительных фраз ("Привет", "Я посмотрел твое видео").
- Никаких длинных лекций — режь резко и по делу.
- Используй живой разговорный сленг (рофл, база, кринж, влог, оператор года, забей, бро, режим блогера).
- Пиши без лишней цензуры, но в рамках пацанского подкола (без прямой тупой ругани, именно смешной прожар).

Примеры идеальных ответов:
- "О, оператор года снял 30 секунд своего потолка и сопения в микрофон. Ради фразы 'я пришел home' нужно было устраивать этот влог? Напиши 3 слова текстом, не позорься."
- "Ты 15 секунд молча смотрел в камеру с лицом лягушки, чтобы потом сказать 'ну вот так'? Номинация на Оскар, бро. Пальцы есть — пиши буквами."
- "Еду в автобусе, смотрю на твой подбородок снизу вверх и слушаю 'ээээ ну короче'. Спасибо за контент, закрывай трансляцию и осваивай клавиатуру."
"""

@dp.message(F.video_note)
async def handle_circle(message: Message):
    if TARGET_USER_ID and message.from_user.id != TARGET_USER_ID:
        return

    processing_msg = await message.reply("👀 *Анализирую этот шедевр кинематографа...*", parse_mode="Markdown")
    file_path = f"circle_{message.message_id}.mp4"
    uploaded_file = None

    try:
        tg_file = await bot.get_file(message.video_note.file_id)
        await bot.download_file(tg_file.file_path, file_path)

        uploaded_file = await asyncio.to_thread(ai_client.files.upload, file=file_path)

        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(1)
            uploaded_file = await asyncio.to_thread(ai_client.files.get, name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise Exception("Ошибка обработки видео на стороне Google")

        response = await asyncio.to_thread(
            ai_client.models.generate_content,
            model='gemini-1.5-flash',
            contents=[uploaded_file],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8,
            )
        )

        reply_text = response.text or "Даже сказать нечего, насколько это бесполезный кружок."
        await message.reply(reply_text)

    except Exception as e:
        print(f"Error handling video note: {e}")
        await message.reply("Даже нейросеть офигела от этого кружка и выдала ошибку.")

    finally:
        if uploaded_file:
            try:
                await asyncio.to_thread(ai_client.files.delete, name=uploaded_file.name)
            except Exception as e:
                print(f"Error deleting Google file: {e}")

        if os.path.exists(file_path):
            os.remove(file_path)

        try:
            await processing_msg.delete()
        except Exception:
            pass

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())