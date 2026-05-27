from build_wiki import analyze, generate


if __name__ == "__main__":
    totals, participants, days, topics = analyze()
    generate(totals, participants, days, topics)
    print(
        f"messages={totals['messages']} "
        f"participants={len(participants)} "
        f"days={len(days)} "
        f"topics={len(topics)}"
    )
