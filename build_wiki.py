import collections
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime


CHATS_DIR = "chats_raw"
WIKI_DIR = "Liberty_Reserve_Wiki"

HEADER_RE = re.compile(r"^### \[(\d+)\] (.*?) · (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9+#.]{2,}")
URL_RE = re.compile(r"https?://\S+")

STOPWORDS = {
    "это", "как", "что", "все", "всё", "для", "тебя", "меня", "есть", "нет", "тут", "там",
    "если", "или", "мне", "тебе", "они", "она", "оно", "его", "еще", "ещё", "уже", "был",
    "была", "были", "будет", "буду", "будешь", "просто", "очень", "только", "надо", "можно",
    "когда", "почему", "потому", "даже", "вообще", "блять", "нахуй", "хуй", "пиздец", "типа",
    "короче", "кстати", "ладно", "сейчас", "сегодня", "завтра", "вчера", "from", "photo",
    "userapi", "quality", "post", "wall", "video", "audio", "club", "vk", "com", "https",
    "sticker", "link", "так", "вот", "тоже", "было", "про", "где", "кто", "чем", "щас",
    "тогда", "раз", "может", "сам", "сама", "себя", "него", "нас", "вам", "без", "норм",
    "какой", "какая", "какие", "такое", "вроде", "потом", "бля",
}

STALE_TOPIC_FILES = {
    "C# _ .NET.md",
    "C++ _ C.md",
    "DevOps _ Инфраструктура.md",
    "Go _ Rust.md",
    "JavaScript _ Frontend.md",
    "Архитектура и Паттерны.md",
    "Карьера и Работа.md",
    "Мобильная разработка.md",
}

TOPICS = {
    "Программирование": [
        r"\bкод\b", r"\bcode\b", r"\bapi\b", r"\bbug\b", r"\bбаг", r"\bпрограм", r"\bразраб",
        r"\bbackend\b", r"\bfrontend\b", r"\bфронтенд", r"\bбэкенд",
    ],
    "C# и .NET": [r"\bc#\b", r"\b\.net\b", r"\basp\.net\b", r"\bdotnet\b", r"\bдотнет", r"\bшарп"],
    "C++": [r"\bc\+\+\b", r"\bcpp\b", r"\bплюсах\b", r"\bплюсы\b", r"\bплюсовик"],
    "JavaScript и Frontend": [
        r"\bjavascript\b", r"\btypescript\b", r"\breact\b", r"\bvue\b", r"\bangular\b",
        r"\bjs\b", r"\bts\b", r"\bhtml\b", r"\bcss\b", r"\bnode\b", r"\bfrontend\b", r"\bфронтенд",
    ],
    "Python": [r"\bpython\b", r"\bпитон", r"\bпайтон", r"\bdjango\b", r"\bfastapi\b", r"\bflask\b"],
    "Java": [r"\bjava\b", r"\bджава", r"\bspring\b", r"\bjvm\b"],
    "Go и Rust": [r"\bgolang\b", r"\brust\b", r"\bраст\b", r"\bcargo\b"],
    "PHP": [r"\bphp\b", r"\blaravel\b", r"\bsymfony\b", r"\bпхп\b", r"\bпых"],
    "Базы данных": [r"\bsql\b", r"\bpostgres", r"\bmysql\b", r"\bredis\b", r"\bmongodb\b", r"\bбд\b", r"\bбаза данных"],
    "DevOps и инфраструктура": [
        r"\bdocker\b", r"\bkubernetes\b", r"\bk8s\b", r"\blinux\b", r"\bnginx\b", r"\baws\b",
        r"\bazure\b", r"\bgitlab\b", r"\bgithub\b", r"\bdevops\b", r"\bci/cd\b",
    ],
    "Архитектура и паттерны": [
        r"\bsolid\b", r"\bооп\b", r"\bmvc\b", r"\bddd\b", r"\bпаттерн", r"\bархитект",
        r"\bмикросервис", r"\bмонолит",
    ],
    "AI и нейросети": [
        r"\bchatgpt\b", r"\bgpt\b", r"\bopenai\b", r"\bllm\b", r"\bнейросет", r"\bии\b", r"\bai\b",
    ],
    "Карьера и работа": [
        r"\bработ", r"\bсобес", r"\bоффер", r"\bзарплат", r"\bзп\b", r"\bджун", r"\bмидл",
        r"\bсеньор", r"\bsenior\b", r"\bmiddle\b", r"\bjunior\b", r"\bрелокац", r"\bфриланс",
    ],
    "Учеба": [r"\bунивер", r"\bвуз\b", r"\bколледж", r"\bэкзамен", r"\bдиплом", r"\bкурс", r"\bучеб"],
    "Финансы и крипта": [
        r"\bкрипт", r"\bбитко", r"\bbtc\b", r"\beth\b", r"\bрубл", r"\bдоллар", r"\bевро",
        r"\bбанк", r"\bакци", r"\bинвест", r"\bтрейд", r"\bденьг",
    ],
    "Политика и война": [r"\bполит", r"\bвойн", r"\bукраин", r"\bросси", r"\bпутин", r"\bзеленск", r"\bсанкц"],
    "Мемы и внутренний лор": [
        r"\bмем", r"\bлор\b", r"\bлегенд", r"\bэто база\b", r"\bкринж", r"\bрофл", r"\bугар",
        r"\bсникерс", r"\bгойд", r"\bгой\b",
    ],
    "Игры": [r"\bsteam\b", r"\bdota\b", r"\bдота\b", r"\bcs2\b", r"\bкс\b", r"\bмайн", r"\bminecraft\b", r"\bигр"],
    "Кино, музыка и медиа": [
        r"\bфильм", r"\bсериал", r"\bаниме", r"\bмузык", r"\bтрек", r"\bальбом", r"\byoutube\b", r"\bютуб",
    ],
    "Техника и гаджеты": [
        r"\biphone\b", r"\bайфон", r"\bandroid\b", r"\bноут", r"\bпроцессор", r"\bвидюх",
        r"\bssd\b", r"\bмонитор", r"\bтелефон",
    ],
    "Авто": [r"\bмашин", r"\bавто\b", r"\bмерсед", r"\bbmw\b", r"\bбмв\b", r"\bтойот", r"\bдиски\b"],
    "Здоровье и быт": [r"\bздоров", r"\bврач", r"\bбол", r"\bсон\b", r"\bспать", r"\bеда\b", r"\bкофе\b"],
}

TOPIC_REGEX = {
    name: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for name, patterns in TOPICS.items()
}

LORE_TERMS = {
    "это база": re.compile(r"\bэто база\b", re.IGNORECASE),
    "мем": re.compile(r"\bмем\w*", re.IGNORECASE),
    "кринж": re.compile(r"\bкринж\w*", re.IGNORECASE),
    "рофл": re.compile(r"\bрофл\w*", re.IGNORECASE),
    "сникерс": re.compile(r"\bсникерс\w*", re.IGNORECASE),
    "клоун": re.compile(r"\bклоун\w*", re.IGNORECASE),
    "легенда": re.compile(r"\bлегенд\w*", re.IGNORECASE),
    "гойда": re.compile(r"\bгойд\w*", re.IGNORECASE),
    "бобик": re.compile(r"\bбобик\w*", re.IGNORECASE),
    "окошко": re.compile(r"\bокошк[аоеи]?\w*", re.IGNORECASE),
    "коврик": re.compile(r"\bковрик\w*", re.IGNORECASE),
    "перекладочка": re.compile(r"\bперекладочк\w*", re.IGNORECASE),
    "10 iq": re.compile(r"\b10\s*iq\b", re.IGNORECASE),
}


@dataclass
class Message:
    msg_id: str
    user: str
    date: str
    time: str
    filename: str
    text: str
    has_attachment: bool
    has_reply: bool


def safe_filename(name: str) -> str:
    return (
        name.replace("/", "_")
        .replace(":", "_")
        .replace("|", "_")
        .replace("[", "(")
        .replace("]", ")")
    )


def link_to(filename: str, msg_id: str, depth: int) -> str:
    prefix = "../" * depth
    return f"{prefix}{CHATS_DIR}/{filename}#{msg_id}"


def wiki_topic(topic: str) -> str:
    return f"[[Темы/{safe_filename(topic)}|{topic}]]"


def wiki_person(name: str) -> str:
    return f"[[Участники/{safe_filename(name)}|{name}]]"


def clean_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped == "---":
        return ""
    if stripped.startswith("<a id="):
        return ""
    if stripped.startswith("*Reply to:*") or stripped.startswith("*Forwarded") or stripped.startswith("*Attachments:*"):
        return ""
    if stripped.startswith("*Action:*"):
        return ""
    if stripped.startswith("- photo") or stripped.startswith("- video") or stripped.startswith("- audio"):
        return ""
    return stripped


def iter_messages():
    for filename in sorted(f for f in os.listdir(CHATS_DIR) if f.endswith(".md")):
        path = os.path.join(CHATS_DIR, filename)
        current = None
        text_lines = []
        has_attachment = False
        has_reply = False
        in_attachment_block = False
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                match = HEADER_RE.match(line)
                if match:
                    if current:
                        yield Message(*current, " ".join(text_lines).strip(), has_attachment, has_reply)
                    current = (match.group(1), match.group(2), match.group(3), match.group(4), filename)
                    text_lines = []
                    has_attachment = False
                    has_reply = False
                    in_attachment_block = False
                    continue

                if current:
                    if line.startswith("*Attachments:*"):
                        has_attachment = True
                        in_attachment_block = True
                    if line.startswith("*Reply to:*"):
                        has_reply = True
                    if in_attachment_block and not line.strip():
                        in_attachment_block = False
                    if in_attachment_block and line.strip().startswith("- "):
                        continue
                    cleaned = clean_line(line)
                    if cleaned:
                        text_lines.append(cleaned)

        if current:
            yield Message(*current, " ".join(text_lines).strip(), has_attachment, has_reply)


def tokenize(text: str):
    text = URL_RE.sub(" ", text.lower())
    for word in WORD_RE.findall(text):
        word = word.strip(".#").lower()
        if len(word) < 3 or word in STOPWORDS:
            continue
        if word.isdigit():
            continue
        yield word


def normalize_quote(text: str, limit: int = 170) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("|", "\\|")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "..."
    return text


def topic_matches(text: str):
    lower = text.lower()
    for topic, regexes in TOPIC_REGEX.items():
        if any(regex.search(lower) for regex in regexes):
            yield topic


def add_sample(bucket, sample, max_items=24):
    if len(bucket) < max_items:
        bucket.append(sample)


def analyze():
    participants = collections.defaultdict(lambda: {
        "count": 0,
        "text_count": 0,
        "attachment_count": 0,
        "reply_count": 0,
        "first": None,
        "last": None,
        "years": collections.Counter(),
        "topics": collections.Counter(),
        "words": collections.Counter(),
        "samples_by_year": collections.defaultdict(list),
        "question_samples": [],
        "first_link": None,
        "last_link": None,
    })
    days = collections.defaultdict(lambda: {
        "count": 0,
        "users": collections.Counter(),
        "topics": collections.Counter(),
        "words": collections.Counter(),
        "samples": [],
        "filename": None,
    })
    topics = collections.defaultdict(lambda: {
        "count": 0,
        "users": collections.Counter(),
        "years": collections.Counter(),
        "samples_by_year": collections.defaultdict(list),
        "lore_terms": collections.defaultdict(list),
    })
    totals = {"messages": 0, "text_messages": 0, "attachments": 0, "replies": 0}

    ignored_users = set()
    if os.path.exists("ignored_users.txt"):
        with open("ignored_users.txt", "r", encoding="utf-8") as f:
            ignored_users = {line.strip() for line in f if line.strip()}

    for msg in iter_messages():
        if msg.user == "DELETED" or msg.user in ignored_users:
            continue
        totals["messages"] += 1
        if msg.text:
            totals["text_messages"] += 1
        if msg.has_attachment:
            totals["attachments"] += 1
        if msg.has_reply:
            totals["replies"] += 1

        year = msg.date[:4]
        participant = participants[msg.user]
        participant["count"] += 1
        participant["years"][year] += 1
        if msg.text:
            participant["text_count"] += 1
        if msg.has_attachment:
            participant["attachment_count"] += 1
        if msg.has_reply:
            participant["reply_count"] += 1
        if not participant["first"] or f"{msg.date} {msg.time}" < participant["first"]:
            participant["first"] = f"{msg.date} {msg.time}"
            participant["first_link"] = (msg.filename, msg.msg_id)
        if not participant["last"] or f"{msg.date} {msg.time}" > participant["last"]:
            participant["last"] = f"{msg.date} {msg.time}"
            participant["last_link"] = (msg.filename, msg.msg_id)

        day = days[msg.date]
        day["count"] += 1
        day["users"][msg.user] += 1
        day["filename"] = msg.filename

        words = list(tokenize(msg.text))
        participant["words"].update(words)
        day["words"].update(words)

        if msg.text and 30 <= len(msg.text) <= 220 and len(participant["samples_by_year"][year]) < 2:
            participant["samples_by_year"][year].append((msg.date, msg.time, msg.filename, msg.msg_id, normalize_quote(msg.text)))
        if "?" in msg.text and 30 <= len(msg.text) <= 220 and len(participant["question_samples"]) < 4:
            participant["question_samples"].append((msg.date, msg.time, msg.filename, msg.msg_id, normalize_quote(msg.text)))

        matched_topics = list(topic_matches(msg.text))
        for topic in matched_topics:
            participant["topics"][topic] += 1
            day["topics"][topic] += 1
            topic_data = topics[topic]
            topic_data["count"] += 1
            topic_data["users"][msg.user] += 1
            topic_data["years"][year] += 1
            if msg.text and 35 <= len(msg.text) <= 240:
                add_sample(topic_data["samples_by_year"][year], (msg.date, msg.time, msg.user, msg.filename, msg.msg_id, normalize_quote(msg.text)), max_items=4)
                if topic == "Мемы и внутренний лор":
                    for term, regex in LORE_TERMS.items():
                        if regex.search(msg.text) and len(topic_data["lore_terms"][term]) < 10:
                            topic_data["lore_terms"][term].append((msg.date, msg.time, msg.user, msg.filename, msg.msg_id, normalize_quote(msg.text)))

        if msg.text and 40 <= len(msg.text) <= 240:
            add_sample(day["samples"], (msg.time, msg.user, msg.filename, msg.msg_id, normalize_quote(msg.text)), max_items=10)

    return totals, participants, days, topics


def fmt_count(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def top_list(counter, n=8):
    return ", ".join(f"{name} ({fmt_count(count)})" for name, count in counter.most_common(n))


def write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def render_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def generate(totals, participants, days, topics):
    os.makedirs(WIKI_DIR, exist_ok=True)
    os.makedirs(os.path.join(WIKI_DIR, "Участники"), exist_ok=True)
    os.makedirs(os.path.join(WIKI_DIR, "Темы"), exist_ok=True)
    os.makedirs(os.path.join(WIKI_DIR, "История"), exist_ok=True)
    os.makedirs(os.path.join(WIKI_DIR, "Лор"), exist_ok=True)

    expected_files = {
        "Участники": {"Топ Участников.md", "Игнорируемые участники.md", "Усам Тахаев (2026 год).md", "Усам Тахаев (2025 год).md", "Усам Тахаев (2024 год).md", "Усам Тахаев (2023 год).md", "Усам Тахаев (2022 год).md", "Усам Тахаев (2021 год).md", "Усам Тахаев (2020 год).md", "Усам Тахаев (2019 год).md", "Денис Козлов (2026 год).md", "Денис Козлов (2025 год).md", "Денис Козлов (2024 год).md", "Денис Козлов (2023 год).md", "Денис Козлов (2022 год).md", "Денис Козлов (2021 год).md", "Денис Козлов (2020 год).md", "Денис Козлов (2019 год).md", "Богдан Шеломанов (2026 год).md", "Богдан Шеломанов (2025 год).md", "Богдан Шеломанов (2024 год).md", "Богдан Шеломанов (2023 год).md", "Богдан Шеломанов (2022 год).md", "Богдан Шеломанов (2021 год).md", "Богдан Шеломанов (2020 год).md", "Богдан Шеломанов (2019 год).md", "Степан Степанов (2026 год).md", "Степан Степанов (2025 год).md", "Степан Степанов (2024 год).md", "Степан Степанов (2023 год).md", "Степан Степанов (2022 год).md", "Степан Степанов (2021 год).md", "Степан Степанов (2020 год).md", "Роман Нечунаев (2026 год).md", "Роман Нечунаев (2025 год).md", "Роман Нечунаев (2024 год).md", "Роман Нечунаев (2023 год).md", "Роман Нечунаев (2022 год).md", "Роман Нечунаев (2021 год).md", "Данил Щеглов (2026 год).md", "Данил Щеглов (2025 год).md", "Данил Щеглов (2024 год).md", "Данил Щеглов (2023 год).md", "Данил Щеглов (2022 год).md", "Дмитрий Ерохин (2026 год).md", "Дмитрий Ерохин (2025 год).md", "Дмитрий Ерохин (2024 год).md", "Дмитрий Ерохин (2023 год).md", "Дмитрий Ерохин (2022 год).md", "Дмитрий Ерохин (2021 год).md", "Дмитрий Ерохин (2020 год).md", "Дмитрий Караваев (2026 год).md", "Дмитрий Караваев (2025 год).md", "Дмитрий Караваев (2024 год).md", "Дмитрий Караваев (2023 год).md", "Дмитрий Караваев (2022 год).md", "Дмитрий Караваев (2021 год).md", "Женя Игнатов (2026 год).md", "Женя Игнатов (2025 год).md", "Женя Игнатов (2024 год).md", "Женя Игнатов (2023 год).md", "Мария Бобиренко (2026 год).md", "Мария Бобиренко (2025 год).md", "Мария Бобиренко (2024 год).md", "Мария Бобиренко (2023 год).md", "Мария Бобиренко (2022 год).md", "Мария Бобиренко (2021 год).md", "Мария Бобиренко (2020 год).md"} | {f"{safe_filename(name)}.md" for name in participants},
        "Темы": {"Популярные темы.md"} | {f"{safe_filename(topic)}.md" for topic in topics},
        "История": {"Хронология.md", "Ключевые моменты.md", "Как читать источники.md", "Эволюция и психоанализ.md", "Итоги 2026 года.md", "Итоги 2025 года.md", "Итоги 2024 года.md", "Итоги 2023 года.md", "Итоги 2022 года.md", "Итоги 2021 года.md", "Итоги 2020 года.md", "Итоги 2019 года.md"},
        "Лор": {"Внутренний лор.md", "Словарь чата.md", "Дед.md", "Усам.md", "Бобик.md", "Данил.md", "Роман Нечунаев.md", "Кирилл Гриненко.md", "Дмитрий Ерохин.md", "Дмитрий Караваев.md", "Степа Степанов.md", "Мария Бобиренко.md", "Лучшие Пары.md"},
    }
    expected_files["Темы"].difference_update(STALE_TOPIC_FILES)
    for folder, expected in expected_files.items():
        folder_path = os.path.join(WIKI_DIR, folder)
        for filename in os.listdir(folder_path):
            if filename.endswith(".md") and filename not in expected:
                os.remove(os.path.join(folder_path, filename))

    years = collections.Counter()
    for data in participants.values():
        years.update(data["years"])
    active_days = len(days)
    first_day = min(days)
    last_day = max(days)

    index = [
        "# Liberty Reserve 2.0 Wiki",
        "",
        f"База знаний по экспортам чата за период **{first_day} — {last_day}**.",
        "",
        "## Навигация",
        "- [[Участники/Топ Участников|Участники и роли]]",
        "- [[Участники/Усам Тахаев (2026 год)|Усам Тахаев (Итоги 2026)]]",
        "- [[Участники/Дмитрий Караваев (2026 год)|Дмитрий Караваев (Итоги 2026)]]",
        "- [[Участники/Женя Игнатов (2026 год)|Женя Игнатов (Итоги 2026)]]",
        "- [[Участники/Мария Бобиренко (2026 год)|Мария Бобиренко (Итоги 2026)]]",
        "- [[Участники/Женя Игнатов (2025 год)|Женя Игнатов (Итоги 2025)]]",
        "- [[Участники/Мария Бобиренко (2025 год)|Мария Бобиренко (Итоги 2025)]]",
        "- [[Участники/Женя Игнатов (2024 год)|Женя Игнатов (Итоги 2024)]]",
        "- [[Участники/Мария Бобиренко (2024 год)|Мария Бобиренко (Итоги 2024)]]",
        "- [[Участники/Женя Игнатов (2023 год)|Женя Игнатов (Итоги 2023)]]",
        "- [[Участники/Мария Бобиренко (2023 год)|Мария Бобиренко (Итоги 2023)]]",
        "- [[Участники/Мария Бобиренко (2022 год)|Мария Бобиренко (Итоги 2022)]]",
        "- [[Участники/Мария Бобиренко (2021 год)|Мария Бобиренко (Итоги 2021)]]",
        "- [[Участники/Мария Бобиренко (2020 год)|Мария Бобиренко (Итоги 2020)]]",
        "- [[Участники/Дмитрий Караваев (2025 год)|Дмитрий Караваев (Итоги 2025)]]",
        "- [[Участники/Дмитрий Караваев (2024 год)|Дмитрий Караваев (Итоги 2024)]]",
        "- [[Участники/Дмитрий Караваев (2023 год)|Дмитрий Караваев (Итоги 2023)]]",
        "- [[Участники/Дмитрий Караваев (2022 год)|Дмитрий Караваев (Итоги 2022)]]",
        "- [[Участники/Дмитрий Караваев (2021 год)|Дмитрий Караваев (Итоги 2021)]]",
        "- [[Участники/Усам Тахаев (2025 год)|Усам Тахаев (Итоги 2025)]]",
        "- [[Участники/Усам Тахаев (2024 год)|Усам Тахаев (Итоги 2024)]]",
        "- [[Участники/Усам Тахаев (2023 год)|Усам Тахаев (Итоги 2023)]]",
        "- [[Участники/Усам Тахаев (2022 год)|Усам Тахаев (Итоги 2022)]]",
        "- [[Участники/Усам Тахаев (2021 год)|Усам Тахаев (Итоги 2021)]]",
        "- [[Участники/Усам Тахаев (2020 год)|Усам Тахаев (Итоги 2020)]]",
        "- [[Участники/Усам Тахаев (2019 год)|Усам Тахаев (Итоги 2019)]]",
        "- [[Участники/Денис Козлов (2026 год)|Денис Козлов (Итоги 2026)]]",
        "- [[Участники/Денис Козлов (2025 год)|Денис Козлов (Итоги 2025)]]",
        "- [[Участники/Денис Козлов (2024 год)|Денис Козлов (Итоги 2024)]]",
        "- [[Участники/Денис Козлов (2023 год)|Денис Козлов (Итоги 2023)]]",
        "- [[Участники/Денис Козлов (2022 год)|Денис Козлов (Итоги 2022)]]",
        "- [[Участники/Денис Козлов (2021 год)|Денис Козлов (Итоги 2021)]]",
        "- [[Участники/Денис Козлов (2020 год)|Денис Козлов (Итоги 2020)]]",
        "- [[Участники/Денис Козлов (2019 год)|Денис Козлов (Итоги 2019)]]",
        "- [[Участники/Богдан Шеломанов (2026 год)|Богдан Шеломанов (Итоги 2026)]]",
        "- [[Участники/Богдан Шеломанов (2025 год)|Богдан Шеломанов (Итоги 2025)]]",
        "- [[Участники/Богдан Шеломанов (2024 год)|Богдан Шеломанов (Итоги 2024)]]",
        "- [[Участники/Богдан Шеломанов (2023 год)|Богдан Шеломанов (Итоги 2023)]]",
        "- [[Участники/Богдан Шеломанов (2022 год)|Богдан Шеломанов (Итоги 2022)]]",
        "- [[Участники/Богдан Шеломанов (2021 год)|Богдан Шеломанов (Итоги 2021)]]",
        "- [[Участники/Богдан Шеломанов (2020 год)|Богдан Шеломанов (Итоги 2020)]]",
        "- [[Участники/Богдан Шеломанов (2019 год)|Богдан Шеломанов (Итоги 2019)]]",
        "- [[Участники/Степан Степанов (2026 год)|Степан Степанов (Итоги 2026)]]",
        "- [[Участники/Степан Степанов (2025 год)|Степан Степанов (Итоги 2025)]]",
        "- [[Участники/Степан Степанов (2024 год)|Степан Степанов (Итоги 2024)]]",
        "- [[Участники/Степан Степанов (2023 год)|Степан Степанов (Итоги 2023)]]",
        "- [[Участники/Степан Степанов (2022 год)|Степан Степанов (Итоги 2022)]]",
        "- [[Участники/Степан Степанов (2021 год)|Степан Степанов (Итоги 2021)]]",
        "- [[Участники/Степан Степанов (2020 год)|Степан Степанов (Итоги 2020)]]",
        "- [[Участники/Роман Нечунаев (2026 год)|Роман Нечунаев (Итоги 2026)]]",
        "- [[Участники/Роман Нечунаев (2025 год)|Роман Нечунаев (Итоги 2025)]]",
        "- [[Участники/Роман Нечунаев (2024 год)|Роман Нечунаев (Итоги 2024)]]",
        "- [[Участники/Роман Нечунаев (2023 год)|Роман Нечунаев (Итоги 2023)]]",
        "- [[Участники/Роман Нечунаев (2022 год)|Роман Нечунаев (Итоги 2022)]]",
        "- [[Участники/Роман Нечунаев (2021 год)|Роман Нечунаев (Итоги 2021)]]",
        "- [[Участники/Данил Щеглов (2026 год)|Данил Щеглов (Итоги 2026)]]",
        "- [[Участники/Данил Щеглов (2025 год)|Данил Щеглов (Итоги 2025)]]",
        "- [[Участники/Данил Щеглов (2024 год)|Данил Щеглов (Итоги 2024)]]",
        "- [[Участники/Данил Щеглов (2023 год)|Данил Щеглов (Итоги 2023)]]",
        "- [[Участники/Данил Щеглов (2022 год)|Данил Щеглов (Итоги 2022)]]",
        "- [[Участники/Дмитрий Ерохин (2026 год)|Дмитрий Ерохин (Итоги 2026)]]",
        "- [[Участники/Дмитрий Ерохин (2025 год)|Дмитрий Ерохин (Итоги 2025)]]",
        "- [[Участники/Дмитрий Ерохин (2024 год)|Дмитрий Ерохин (Итоги 2024)]]",
        "- [[Участники/Дмитрий Ерохин (2023 год)|Дмитрий Ерохин (Итоги 2023)]]",
        "- [[Участники/Дмитрий Ерохин (2022 год)|Дмитрий Ерохин (Итоги 2022)]]",
        "- [[Участники/Дмитрий Ерохин (2021 год)|Дмитрий Ерохин (Итоги 2021)]]",
        "- [[Участники/Дмитрий Ерохин (2020 год)|Дмитрий Ерохин (Итоги 2020)]]",
        "- [[Участники/Игнорируемые участники|Игнорируемые участники (неактивные в 2025-2026)]]",
        "- [[Темы/Популярные темы|Темы и обсуждения]]",
        "- [[История/Хронология|Хронология и всплески активности]]",
        "- [[История/Ключевые моменты|Ключевые моменты]]",
        "- [[История/Итоги 2026 года|Итоги 2026 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2025 года|Итоги 2025 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2024 года|Итоги 2024 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2023 года|Итоги 2023 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2022 года|Итоги 2022 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2021 года|Итоги 2021 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2020 года|Итоги 2020 года: Звезды и Горячие обсуждения]]",
        "- [[История/Итоги 2019 года|Итоги 2019 года: Звезды и Горячие обсуждения]]",
        "- [[История/Эволюция и психоанализ|Эволюция участников и психоанализ]]",
        "- [[Лор/Внутренний лор|Внутренний лор]]",
        "- [[Лор/Словарь чата|Словарь чата]]",
        "- [[Лор/Дед|Кто такой Дед? (Денис Козлов)]]",
        "- [[Лор/Усам|Усам Тахаев (Стабилизирующее Эго)]]",
        "- [[Лор/Бобик|Богдан Шеломанов (бобик)]]",
        "- [[Лор/Данил|Данил Щеглов (Поиск братства)]]",
        "- [[Лор/Роман Нечунаев|Роман Нечунаев (QA и Интроверт)]]",
        "- [[Лор/Кирилл Гриненко|Кирилл Гриненко (Прожженный Шарпист)]]",
        "- [[Лор/Дмитрий Ерохин|Дмитрий Ерохин (JS-Боярин из Саратова)]]",
        "- [[Лор/Дмитрий Караваев|Дмитрий Караваев (Приземленный Реалист)]]",
        "- [[Лор/Степа Степанов|Степа Степанов (Хаотик-JDM и Русская Община)]]",
        "- [[Лор/Мария Бобиренко|Мария Бобиренко (Нейросети и Владивосток)]]",
        "- [[История/Как читать источники|Как читать источники]]",
        "",
        "## Масштаб архива",
        f"- Сообщений: **{fmt_count(totals['messages'])}**",
        f"- Сообщений с текстом: **{fmt_count(totals['text_messages'])}**",
        f"- Сообщений с вложениями: **{fmt_count(totals['attachments'])}**",
        f"- Ответов на сообщения: **{fmt_count(totals['replies'])}**",
        f"- Активных дней: **{fmt_count(active_days)}**",
        f"- Участников: **{fmt_count(len(participants))}**",
        "",
        "## По годам",
        render_table(["Год", "Сообщений"], [[year, fmt_count(count)] for year, count in sorted(years.items())]),
        "",
        "## Что важно",
        "- Wiki теперь устроена как навигатор: каждая крупная сводка ведет к конкретным сообщениям в `chats_raw`.",
        "- Персональные страницы показывают период активности, вклад, характерные темы и проверяемые примеры из диалога.",
        "- Тематические страницы не пытаются заменить чтение чата, а дают входные точки в обсуждения.",
        "- Хронология выделяет дни с наибольшей активностью и показывает, кто и о чем говорил в эти дни.",
        "",
    ]
    write(os.path.join(WIKI_DIR, "index.md"), "\n".join(index))

    source_help = [
        "# Как читать источники",
        "",
        "Ссылки вида `контекст -> ../../chats_raw/Файл.md#123456` открывают исходный годовой экспорт и ведут к HTML-якорю сообщения.",
        "",
        "Уровни ссылок отличаются по папкам:",
        "- из `Liberty_Reserve_Wiki/index.md` ссылка идет через `../chats_raw/...`;",
        "- из `Участники`, `Темы` и `История` ссылка идет через `../../chats_raw/...`.",
        "",
        "Если Obsidian не прыгает к якорю автоматически, открой файл по ссылке и найди номер сообщения через поиск по `### [123456]`.",
        "",
        "Сводки сгенерированы статистически: они хороши для навигации и первичного лора, но спорные формулировки стоит проверять по исходным сообщениям.",
        "",
    ]
    write(os.path.join(WIKI_DIR, "История", "Как читать источники.md"), "\n".join(source_help))

    top_participants = sorted(participants.items(), key=lambda item: item[1]["count"], reverse=True)
    rows = []
    for rank, (name, data) in enumerate(top_participants[:80], 1):
        first_file, first_id = data["first_link"]
        last_file, last_id = data["last_link"]
        main_topics = ", ".join(wiki_topic(topic) for topic, _ in data["topics"].most_common(3)) or "нет явного профиля"
        rows.append([
            rank,
            wiki_person(name),
            fmt_count(data["count"]),
            data["first"][:10],
            data["last"][:10],
            main_topics,
            f"[первое]({link_to(first_file, first_id, 2)}) / [последнее]({link_to(last_file, last_id, 2)})",
        ])

    top_page = [
        "# Топ Участников",
        "",
        "Рейтинг по числу сообщений. Темы показывают не профессию участника, а статистически заметные зоны обсуждений.",
        "",
        render_table(["#", "Участник", "Сообщений", "Первое", "Последнее", "Заметные темы", "Источники"], rows),
        "",
    ]
    write(os.path.join(WIKI_DIR, "Участники", "Топ Участников.md"), "\n".join(top_page))

    ignored_users_list = []
    if os.path.exists("ignored_users.txt"):
        with open("ignored_users.txt", "r", encoding="utf-8") as f:
            ignored_users_list = sorted([line.strip() for line in f if line.strip()])
    
    ignored_page = [
        "# Игнорируемые участники",
        "",
        "В этот список автоматически добавлены участники, которые покинули чат или не проявляли никакой активности в 2025 и 2026 годах.",
        "Они полностью исключены из анализа и их сообщения не учитываются в общей статистике.",
        "",
    ]
    for u in ignored_users_list:
        ignored_page.append(f"- {u}")
    ignored_page.append("")
    write(os.path.join(WIKI_DIR, "Участники", "Игнорируемые участники.md"), "\n".join(ignored_page))

    for name, data in top_participants:
        years_rows = [[year, fmt_count(count)] for year, count in sorted(data["years"].items())]
        topic_rows = [[wiki_topic(topic), fmt_count(count)] for topic, count in data["topics"].most_common(10)]
        if not topic_rows:
            topic_rows = [["-", "-"]]
        words = ", ".join(word for word, _ in data["words"].most_common(18)) or "-"
        first_file, first_id = data["first_link"]
        last_file, last_id = data["last_link"]
        text_share = round(100 * data["text_count"] / data["count"], 1) if data["count"] else 0
        reply_share = round(100 * data["reply_count"] / data["count"], 1) if data["count"] else 0
        attachment_share = round(100 * data["attachment_count"] / data["count"], 1) if data["count"] else 0

        samples = []
        for year in sorted(data["samples_by_year"]):
            for date, time, filename, msg_id, quote in data["samples_by_year"][year]:
                samples.append(f"- {date} {time}: “{quote}” [контекст]({link_to(filename, msg_id, 2)})")
                if len(samples) >= 10:
                    break
            if len(samples) >= 10:
                break
        if not samples:
            samples = ["- Недостаточно коротких текстовых примеров для автоматической выдержки."]

        question_samples = []
        for date, time, filename, msg_id, quote in data["question_samples"][:4]:
            question_samples.append(f"- {date} {time}: “{quote}” [контекст]({link_to(filename, msg_id, 2)})")
        if not question_samples:
            question_samples = ["- Явных коротких вопросов в выборке не найдено."]

        # Check if there are year-end summary files for this participant
        annual_summaries = []
        for fn in sorted(expected_files["Участники"]):
            m = re.match(re.escape(name) + r" \((\d{4}) год\)\.md", fn)
            if m:
                year = m.group(1)
                annual_summaries.append(f"[[Участники/{name} ({year} год)|Итоги {year} года]]")

        profile = [
            f"# {name}",
            "",
            "## Сводка",
            f"- Сообщений: **{fmt_count(data['count'])}**",
            f"- Первое появление: **{data['first']}** ([контекст]({link_to(first_file, first_id, 2)}))",
            f"- Последняя активность: **{data['last']}** ([контекст]({link_to(last_file, last_id, 2)}))",
            f"- Текстовые сообщения: **{text_share}%**, ответы: **{reply_share}%**, вложения: **{attachment_share}%**",
        ]
        if annual_summaries:
            profile.append(f"- **Годовые отчеты:** {', '.join(annual_summaries)}")
        if "Богдан Шел" in name:
            profile.insert(3, "- **Локальный мем/прозвище:** бобик")
        profile.extend([
            "",
            "## Роль в чате",
            f"Автоматический портрет: участник дал {fmt_count(data['count'])} сообщений, активен в {len(data['years'])} годах. ",
            f"Наиболее заметные темы: {top_list(data['topics'], 5) if data['topics'] else 'без устойчивого тематического профиля'}.",
            "",
            "## Характерные слова",
            words,
            "",
            "## Активность по годам",
            render_table(["Год", "Сообщений"], years_rows),
            "",
            "## Тематический профиль",
            render_table(["Тема", "Сообщений"], topic_rows),
            "",
            "## Примеры реплик",
            *samples,
            "",
            "## Вопросы и входы в обсуждения",
            *question_samples,
            "",
        ])
        write(os.path.join(WIKI_DIR, "Участники", f"{safe_filename(name)}.md"), "\n".join(profile))

    sorted_topics = sorted(topics.items(), key=lambda item: item[1]["count"], reverse=True)
    topic_rows = []
    for topic, data in sorted_topics:
        topic_rows.append([
            wiki_topic(topic),
            fmt_count(data["count"]),
            top_list(data["users"], 5),
            top_list(data["years"], 4),
        ])
    topics_page = [
        "# Популярные темы",
        "",
        "Тематические счетчики построены по ключевым словам и регулярным выражениям, поэтому это карта обсуждений, а не строгая разметка всех сообщений.",
        "",
        render_table(["Тема", "Сообщений", "Кто чаще говорил", "Годы"], topic_rows),
        "",
    ]
    write(os.path.join(WIKI_DIR, "Темы", "Популярные темы.md"), "\n".join(topics_page))

    for topic, data in sorted_topics:
        rows = []
        for year in sorted(data["samples_by_year"]):
            for date, time, user, filename, msg_id, quote in data["samples_by_year"][year]:
                rows.append([date, time, wiki_person(user), quote, f"[контекст]({link_to(filename, msg_id, 2)})"])
                if len(rows) >= 28:
                    break
            if len(rows) >= 28:
                break
        if not rows:
            rows = [["-", "-", "-", "Недостаточно коротких примеров.", "-"]]
        page = [
            f"# {topic}",
            "",
            f"Сообщений по теме: **{fmt_count(data['count'])}**.",
            "",
            "## Участники",
            top_list(data["users"], 12) or "-",
            "",
            "## Динамика по годам",
            render_table(["Год", "Сообщений"], [[year, fmt_count(count)] for year, count in sorted(data["years"].items())]),
            "",
            "## Входы в обсуждения",
            render_table(["Дата", "Время", "Автор", "Фрагмент", "Источник"], rows),
            "",
        ]
        write(os.path.join(WIKI_DIR, "Темы", f"{safe_filename(topic)}.md"), "\n".join(page))

    top_days = sorted(days.items(), key=lambda item: item[1]["count"], reverse=True)[:60]
    top_days_chrono = sorted(top_days, key=lambda item: item[0])
    rows = []
    for date, data in top_days_chrono:
        first_sample = data["samples"][0] if data["samples"] else None
        source = f"[день]({link_to(data['filename'], first_sample[3] if first_sample else '', 2)})" if first_sample else "-"
        rows.append([
            date,
            fmt_count(data["count"]),
            top_list(data["users"], 5),
            top_list(data["topics"], 5),
            ", ".join(word for word, _ in data["words"].most_common(10)),
            source,
        ])
    chronology = [
        "# Хронология",
        "",
        "Ниже собраны самые активные дни архива. Это хороший слой для поиска холиваров, резких поворотов и массовых обсуждений.",
        "",
        render_table(["Дата", "Сообщений", "Главные участники", "Темы", "Слова дня", "Источник"], rows),
        "",
    ]
    write(os.path.join(WIKI_DIR, "История", "Хронология.md"), "\n".join(chronology))

    moments = [
        "# Ключевые моменты",
        "",
        "Автоматически выделенные точки входа: самые плотные дни, где сходятся активность, несколько участников и заметные темы.",
        "",
    ]
    for date, data in top_days[:25]:
        moments.append(f"## {date}")
        moments.append(f"- Сообщений: **{fmt_count(data['count'])}**")
        moments.append(f"- Главные участники: {top_list(data['users'], 7)}")
        moments.append(f"- Темы: {top_list(data['topics'], 7) or 'без явной тематической доминанты'}")
        moments.append(f"- Слова дня: {', '.join(word for word, _ in data['words'].most_common(14))}")
        if data["samples"]:
            moments.append("- Входы в диалог:")
            for time, user, filename, msg_id, quote in data["samples"][:5]:
                moments.append(f"  - {time}, {wiki_person(user)}: “{quote}” [контекст]({link_to(filename, msg_id, 2)})")
        moments.append("")
    write(os.path.join(WIKI_DIR, "История", "Ключевые моменты.md"), "\n".join(moments))

    lore = topics.get("Мемы и внутренний лор")
    if lore:
        lore_rows = []
        for year in sorted(lore["samples_by_year"]):
            for date, time, user, filename, msg_id, quote in lore["samples_by_year"][year]:
                lore_rows.append([date, time, wiki_person(user), quote, f"[контекст]({link_to(filename, msg_id, 2)})"])
                if len(lore_rows) >= 32:
                    break
            if len(lore_rows) >= 32:
                break
        lore_page = [
            "# Внутренний лор",
            "",
            "Эта страница собирает входы в мемные и самоописательные фрагменты чата. Автоматическая разметка не дает окончательных определений, поэтому каждый пункт привязан к исходному контексту.",
            "",
            "## Масштаб",
            f"- Сообщений по теме: **{fmt_count(lore['count'])}**",
            f"- Главные участники: {top_list(lore['users'], 12)}",
            f"- Годы: {top_list(lore['years'], 8)}",
            "",
            "## Входы в диалоги",
            render_table(["Дата", "Время", "Автор", "Фрагмент", "Источник"], lore_rows),
            "",
        ]
        write(os.path.join(WIKI_DIR, "Лор", "Внутренний лор.md"), "\n".join(lore_page))

        dictionary_rows = []
        for term, samples in sorted(lore["lore_terms"].items()):
            for date, time, user, filename, msg_id, quote in samples[:6]:
                dictionary_rows.append([term, date, wiki_person(user), quote, f"[контекст]({link_to(filename, msg_id, 2)})"])
        if not dictionary_rows:
            dictionary_rows = [["-", "-", "-", "Недостаточно совпадений по словарным маркерам.", "-"]]
        dictionary = [
            "# Словарь чата",
            "",
            "Словарь не трактует мемы за участников, а показывает повторяющиеся маркеры и места, где можно прочитать их употребление.",
            "",
            render_table(["Маркер", "Дата", "Автор", "Фрагмент", "Источник"], dictionary_rows),
            "",
        ]
        write(os.path.join(WIKI_DIR, "Лор", "Словарь чата.md"), "\n".join(dictionary))


if __name__ == "__main__":
    totals_, participants_, days_, topics_ = analyze()
    generate(totals_, participants_, days_, topics_)
    print(f"messages={totals_['messages']} participants={len(participants_)} days={len(days_)} topics={len(topics_)}")
