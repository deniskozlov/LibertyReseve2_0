import json
with open("user_evolution.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for user, years in data.items():
    print(f"\n=== {user} ===")
    for year, info in years.items():
        if not info["top_words"]: continue
        topics = ", ".join(f"{t}({c})" for t,c in info["top_topics"].items())
        words = ", ".join(info["top_words"][:15])
        print(f"[{year}] Topics: {topics}")
        print(f"[{year}] Words: {words}")
        quotes = info.get("samples", [])
        if quotes:
            print(f"[{year}] Quote: {quotes[0][:150]}...")
