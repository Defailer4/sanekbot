import os
import random
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from groq import Groq

# Импорты
from config.settings import BOT_TOKEN, GROQ_API_KEY, TARGET_USER_IDS
from config.prompts import SYSTEM_PROMPT, ROAST_STYLES, MOCKERY_PASTAS
from utils.cleaners import clean_transcript, clean_llm_response

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)


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
        sample_pasta = random.choice(MOCKERY_PASTAS)

        user_prompt = (
            f"Автор: {user_name}\n"
            f"Длительность: около {duration} сек.\n"
            f"Расшифровка сказанного: \"{transcript_text}\"\n"
            f"Направление удара: {current_style}\n"
            f"Пример вайба/пасты для вдохновения: \"{sample_pasta}\"\n\n"
            f"Прожарь автора на русском языке, переняв подачу из примера, но адаптировав под его слова! Отвечай СРАЗУ готовым текстом прожарки без тегов <think> и рассуждений."
        )

        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + "\nВАЖНО: Выдавай только финальный текст ответа, не используй блок <think>."},
                {"role": "user", "content": user_prompt}
            ],
            model="qwen/qwen3.6-27b",
            temperature=0.8,
            top_p=0.9,
            max_tokens=600,
        )

        raw_content = response.choices[0].message.content or ""
        reply_text = clean_llm_response(raw_content) or "Даже сказать нечего на этот высер."
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