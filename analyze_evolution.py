import collections
import json
import random
from build_wiki import iter_messages, tokenize, topic_matches

target_users = {
    "Усам Тахаев", "Денис Козлов", "Данил Щеглов", "Степа Степанов", 
    "Богдан Шеломанов", "Дмитрий Караваев", "Мария Бобиренко", 
    "Роман Чернецкий", "Женя Игнатов", "Илья Задорожный"
}

user_year_words = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
user_year_topics = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
user_year_quotes = collections.defaultdict(lambda: collections.defaultdict(list))

# Deterministic random for reproducibility
rng = random.Random(42)

for msg in iter_messages():
    if msg.user in target_users:
        year = msg.date[:4]
        text = msg.text
        if not text:
            continue
            
        words = list(tokenize(text))
        user_year_words[msg.user][year].update(words)
        
        topics = list(topic_matches(text))
        for topic in topics:
            user_year_topics[msg.user][year][topic] += 1
            
        if 50 <= len(text) <= 300 and rng.random() < 0.05:
            if len(user_year_quotes[msg.user][year]) < 10:
                user_year_quotes[msg.user][year].append(text.replace('\n', ' '))

result = {}
for user in target_users:
    result[user] = {}
    for year in sorted(user_year_words[user].keys()):
        result[user][year] = {
            "top_words": [w for w, c in user_year_words[user][year].most_common(20)],
            "top_topics": {t: c for t, c in user_year_topics[user][year].most_common(5)},
            "samples": user_year_quotes[user][year]
        }

with open("user_evolution.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Evolution analysis complete.")
