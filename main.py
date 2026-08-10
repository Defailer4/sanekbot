import os
import re
import random
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

HALLUCINATIONS = [
    "продолжение следует",
    "спасибо за просмотр",
    "подпишитесь на канал",
    "субтитры",
    "редактор субтитров",
    "перевод",
    "dima torzok",
    "dimatorzok",
    "продолжение",
    "продолжение следует...",
    "subtitles",
    "thanks for watching",
]

ROAST_STYLES = [
    "Жестко зацепись за абсурдность, логические дыры и тупость сказанных фраз.",
    "Высмеивай его нарциссизм, режим блогера и то, как бесполезно он тратит время чата.",
    "Придерись к словам-паразитам (э-э, ну, короче), тупым паузам, сопению и заиканию.",
    "Сравни эту запись с самым кринжовым тиктоком, блогерским влогом или речью под кайфом."
]

SYSTEM_PROMPT = """
Ты — циничный, максимально язвительный и токсичный пацан в групповом чате.
Твоя цель — жестко, смешно, дерзко и безжалостно прожарить автора за присланный видео-кружок (video note).
Ты искренне презираешь видео-кружки, считаешь их предельным кринжем, нарциссизмом и проявлением лени.

ЖЕСТКИЕ ПРАВИЛА И СТИЛЬ:
1. ТОЛЬКО РУССКИЙ ЯЗЫК. Никакой латиницы, английских слов, иероглифов или чужеродных символов.
2. АКТУАЛЬНЫЙ СЛЕНГ И ЮМОР: Используй живую лексику (кринж, база, деф, рофл, чушпан, влогер, тиктокер, режим блогера, не позорься, клавиатуру купи, слейся, снимись с ручника). Разрешен мат, сарказм и черный юмор.
3. БЕЙ ПО КОНТЕКСТУ И СЛОВАМ:
   - Тебе даны: ИМЯ, ДЛИТЕЛЬНОСТЬ, ТЕКСТ РЕЧИ и СТИЛЬ ПРОЖАРКИ.
   - Если в тексте есть слова — уничтожай за их ТУПОСТЬ, логику, эканье и косноязычие.
   - Если кружок короткий (1-4 сек) — стеби за то, что ради одной секунды мычания он включал камеру.
   - Если длинный (15+ сек) — стеби за душный влог и часовую Санта-Барбару.
   - Если в тексте указано молчание/сопение — уничтожай за то, что он записал видео ради игры в гляделки с объективом.
4. РАЗНООБРАЗИЕ КОНЦОВОК: Забудь постоянную формулу "купи клавиатуру". Иногда требовательно посылай писать текстом, иногда сравнивай с блогерами, иногда просто высмеивай интеллект. Каждый раз новый поворот.
5. ФОРМАТ: 2-3 коротких, емких, злых и смешных предложения. Никакой вежливости ("привет", "без обид" — ЗАПРЕЩЕНО).
"""


def clean_transcript(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    lowered = cleaned.lower()

    if re.search(r'[\u4e00-\u9fff\u3040-\u30ff]', cleaned):
        return ""

    for hallucination in HALLUCINATIONS:
        if hallucination in lowered:
            return ""

    return cleaned


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
        tg_file = await bot.get_file(message.video_note.file_id)
        await bot.download_file(tg_file.file_path, file_path)

        user_name = message.from_user.first_name or "Тип"
        raw_duration = message.video_note.duration
        duration = max(1, raw_duration - 1) if raw_duration > 2 else raw_duration

        transcript_text = ""
        try:
            with open(file_path, "rb") as file:
                transcription = await asyncio.to_thread(
                    groq_client.audio.transcriptions.create,
                    file=(file_path, file.read()),
                    model="whisper-large-v3-turbo",
                    language="ru",
                    prompt="Разговорная речь пацанов в чате, сленг, мат, повседневный разговор.",
                    response_format="text"
                )
                raw_text = str(transcription).strip()
                transcript_text = clean_transcript(raw_text)

        except Exception as transcript_err:
            print(f"Whisper error: {transcript_err}")
            transcript_text = ""

        if not transcript_text:
            transcript_text = "[Абсолютное молчание, сопение в микрофон или фоновый шум]"

        current_style = random.choice(ROAST_STYLES)

        user_prompt = (
            f"Автор: {user_name}\n"
            f"Длительность: около {duration} сек.\n"
            f"Расшифровка сказанного: \"{transcript_text}\"\n"
            f"Направление удара: {current_style}\n\n"
            f"Прожарь автора на русском языке с учетом всех вводных!"
        )

        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=1.2,
            top_p=0.92,
            max_tokens=160,
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
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())