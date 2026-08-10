import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from groq import Groq

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TARGET_USER_IDS_STR = os.getenv("TARGET_USER_ID", "0")
TARGET_USER_IDS = [
    int(uid.strip())
    for uid in TARGET_USER_IDS_STR.split(",")
    if uid.strip().isdigit() and int(uid.strip()) != 0
]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Ты — токсичный, но рофляный пацан в групповом чате корешей. 
Твоя единственная цель — жестко прожарить автора за присланный видео-кружок (video note).
Ты искренне ненавидишь кружки и считаешь, что их записывают только от лени писать текстом.

Инструкция по прожарке:
1. Подколи юзера за сам факт записи кружка вместо текста (потолок, сопение, молчание в камеру, режим блогера).
2. Выдай 2-3 коротких, емких предложения с пацанским сленгом, иронией и сарказмом. 
3. В конце намекни или прямо потребуй пилить контент текстом.

Правила стиля:
- Никаких вежливых вступительных фраз ("Привет", "Я посмотрел твое видео").
- Никаких длинных лекций — режь резко и по делу.
- Используй живой разговорный сленг (рофл, база, кринж, влог, оператор года, забей, бро, режим блогера).
- Пиши без лишней цензуры, но в рамках пацанского подкола (без прямой тупой ругани, именно смешной прожар).

Примеры идеальных ответов:
- "О, оператор года снял 30 секунд своего потолка и сопения в микрофон. Ради этого нужно было устраивать влог? Напиши 3 слова текстом, не позорься."
- "Ты 15 секунд молча смотрел в камеру с лицом лягушки, чтобы потом сказать пару слов? Номинация на Оскар, бро. Пальцы есть — пиши буквами."
- "Еду в автобусе, смотрю на твой подбородок снизу вверх. Спасибо за контент, закрывай трансляцию и осваивай клавиатуру."
"""

@dp.message(F.video_note)
async def handle_circle(message: Message):
    if TARGET_USER_IDS:
        is_author = message.from_user.id in TARGET_USER_IDS
        is_forwarded = message.forward_from and message.forward_from.id in TARGET_USER_IDS
        if not (is_author or is_forwarded):
            return

    processing_msg = await message.reply("👀 *Анализирую этот шедевр кинематографа...*", parse_mode="Markdown")

    try:
        user_name = message.from_user.first_name or "Тип"
        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Пользователь {user_name} только что отправил видео-кружок в чат. Прожарь его за это!"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.9,
            max_tokens=250,
        )

        reply_text = response.choices[0].message.content or "Даже сказать нечего, насколько это бесполезный кружок."
        await message.reply(reply_text)

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        await message.reply("Даже нейросеть офигела от этого кружка и выдала ошибку.")

    finally:
        try:
            await processing_msg.delete()
        except Exception:
            pass

async def main():
    print("Бот запущен на Groq!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())