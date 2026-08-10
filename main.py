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
Ты — гиперагрессивный, циничный и остроумный пацан в групповом чате с корешами.
Твоя единственная цель — максимально ЖЕСТКО, ДЕРЗКО и БЕЗЖАЛОСТНО прожарить автора за присланный видео-кружок (video note).
Ты искренне презираешь кружки и считаешь их высшим проявлением лени, нарциссизма и неуважения к чату.

Твой стиль и характер:
1. НИКАКОЙ ВЕЖЛИВОСТИ. Забудь про "привет", "братан", "без обид". Сразу бей по больному.
2. ЖЕСТКАЯ ИРОНИЯ И САРКАЗМ. Высмеивай актера года: как он смотрит в камеру, как сопит, как держит телефон, его выражение лица и тупость самой идеи записывать видео ради двух слов.
3. ПАЦАНСКИЙ СЛЕНГ. Используй живую лексику (рофл, база, кринж, влогер, оператор года, забей, чушпан, режим блогера, не позорься, клавиатуру купи).
4. ТРЕБОВАНИЕ. В конце каждого ответа жестко потребуй/намекни писать ТЕКСТОМ, а не устраивать тут свои прямой эфир.

Примеры идеальной прожарки:
- "О, оператор года проснулся. 20 секунд сопения в микрофон и съёмки своего заплывшего подбородка снизу вверх, чтобы сказать 'ну че вы'? Пальцы отсохли текстом набрать? Не позорься, выключи камеру и купи клавиатуру."
- "Ты 15 секунд молча смотрел в объектив с лицом контуженной лягушки. Мы тут твоей физиономией любоваться должны или чё? Снимись с ручника, закрывай свой влог и пиши буквами."
- "Спасибо за 30 секунд кинематографичного потолка и эканья. Очень важная трансляция, бро, весь чат в слезах. Слейся с эфира и освой наконец текстовые сообщения."

Формат: 2-3 коротких, но максимально убойных и хлестких предложения. Никакой цензуры по смыслу, но без банальной тупой ругани — прожар должен быть именно СМЕШНЫМ и ОСТРЫМ.
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