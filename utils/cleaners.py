import re

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

def clean_llm_response(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()