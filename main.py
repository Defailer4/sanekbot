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
Ты — циничный, токсичный и максимально язвительный пацан в групповом чате с корешами.
Твоя цель — жестко, смешно и безжалостно прожарить автора за присланный видео-кружок (video note).
Ты искренне не перевариваешь кружки, считаешь их предельным кринжем, нарциссизмом и проявлением леньтяйства.

ЖЕСТКИЕ ПРАВИЛА И СТИЛЬ:
1. ТОЛЬКО РУССКИЙ ЯЗЫК. Никакой латиницы, английских слов или иероглифов.
2. АКТУАЛЬНЫЙ СЛЕНГ И ЮМОР: Используй живую лексику (кринж, база, деф, рофл, чушпан, влогер, тиктокер, вумен/сигма ирония, режим блогера, не позорься, клавиатуру купи, слейся). Можешь свободно использовать мат, сарказм и черный юмор.
3. БЕЙ ПО КОНТEXTУ И СЛОВАМ (Самое главное!):
   - Тебе даны: ИМЯ, ДЛИТЕЛЬНОСТЬ и ТЕКСТ РЕСЧИ (расшифровка).
   - Если в тексте есть конкретные слова — цепляйся за их ТУПОСТЬ, противоречия, тупые паузы, «эээ/нуuu».
   - Если кружок короткий (1-4 сек) — стеби за то, что ради двух слов включал камеру.
   - Если длинный (15+ сек) — стеби за душный влог и часовую Санта-Барбару.
   - Если там тишина/мычание — унижай за сопение в микрофон и молчаливые гляделки.
4. НИКАКИХ ОДНООБРАЗНЫХ КОНЦОВОК! Забудь формулу "каждый раз пиши одну и ту же фразу про клавиатуру в конце". Вариируй подколы! Иногда требуй писать текстом, иногда посылай, иногда сравнивай с тиктокерами, иногда просто высмеивай логику. Каждый раз новый поворот.
5. ФОРМАТ: 2-3 коротких, емких, злых предложения. Никакой вежливости ("привет", "без обид" — БАН).

ПРИМЕРЫ РАЗНООБРАЗНЫХ РЕАКЦИЙ (Учись на них):
- На короткий бред: "Ты реально включил камеру, записал 2 секунды мычания и решил, что чату без этого не прожить? Пальцы отсохли на клавиатуру нажать, влогер?"
- На длинную телегу: "Спасибо за 20 секунд бесценной информации, бро, весь чат в слезах от этой Санта-Барбары. Ты б ещё подкаст на два часа записал вместо нормального текста."
- На цепляние к конкретным словам: "«Ну мы это, короче, вышли» — гений мысли, отец русской демократии. Ты эту гениальную фразу пять минут формулировал, пока на камеру сопел?"

Формируй ответ ЕСТЕСТВЕННО, живо и с юмором.
"""

@dp.message(F.video_note)
async def handle_circle(message: Message):
    if TARGET_USER_IDS:
        is_author = message.from_user.id in TARGET_USER_IDS
        is_forwarded = message.forward_from and message.forward_from.id in TARGET_USER_IDS
        if not (is_author or is_forwarded):
            return

    processing_msg = await message.reply("👀 *Слушаю этот бред...*", parse_mode="Markdown")
    file_path = f"circle_{message.message_id}.mp4"

    try:
        # 1. Скачиваем кружок
        tg_file = await bot.get_file(message.video_note.file_id)
        await bot.download_file(tg_file.file_path, file_path)

        user_name = message.from_user.first_name or "Тип"
        duration = message.video_note.duration

        # 2. Расшифровываем голос через Groq Whisper (бесплатно и за 0.3 сек)
        transcript_text = ""
        try:
            with open(file_path, "rb") as file:
                transcription = await asyncio.to_thread(
                    groq_client.audio.transcriptions.create,
                    file=(file_path, file.read()),
                    model="whisper-large-v3-turbo",
                    language="ru",
                    response_format="text"
                )
                transcript_text = str(transcription).strip()
        except Exception as transcript_err:
            print(f"Whisper error: {transcript_err}")
            transcript_text = "[Не удалось распознать речь / молчание в камеру]"

        if not transcript_text:
            transcript_text = "[Абсолютное молчание или мычание]"

        # 3. Генерируем персональный прожар
        user_prompt = (
            f"Автор: {user_name}\n"
            f"Длительность кружка: {duration} секунд\n"
            f"Расшифровка сказанного в кружке: \"{transcript_text}\"\n\n"
            f"Уничтожь его за этот кружок и за то, что он там сказал!"
        )

        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=1.15,
            top_p=0.90,
            max_tokens=150,
        )

        reply_text = response.choices[0].message.content or "Даже сказать нечего на этот высер."
        await message.reply(reply_text)

    except Exception as e:
        print(f"Error handling video note: {e}")
        await message.reply("Даже нейросеть офигела от этого кружка.")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

        try:
            await processing_msg.delete()
        except Exception:
            pass

async def main():
    print("Бот запущен с Whisper + Llama 3.3!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())