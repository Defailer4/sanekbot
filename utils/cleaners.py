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


def extract_final_response(text: str) -> str:
    if not text:
        return ""

    quotes = re.findall(r'["«]([^"»]+)["»]', text)
    if quotes:
        for q in reversed(quotes):
            if re.search(r'[а-яА-ЯёЁ]', q) and len(q.strip()) > 10:
                return q.strip()

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for p in reversed(paragraphs):
        if re.search(r'[а-яА-ЯёЁ]', p) and not p.lower().startswith(('we need', "let's", 'possible', 'draft', 'better:')):
            return p.strip('"\n ')

    return text.strip()