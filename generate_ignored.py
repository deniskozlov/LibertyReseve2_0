import os
import re
import glob

# Identify the last year each user was active
last_active = {}

for filepath in glob.glob('chats_raw/*.md'):
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('### ['):
                match = re.search(r'^### \[\d+\] (.*?) · (\d{4})', line)
                if match:
                    user = match.group(1).strip()
                    year = int(match.group(2))
                    
                    if user not in last_active or year > last_active[user]:
                        last_active[user] = year

# Determine who was not active in 2025 or 2026
ignored_users = []
for user, year in last_active.items():
    if year < 2025 and user != "DELETED":
        ignored_users.append(user)

ignored_users.sort()

# Save to ignored_users.txt
with open('ignored_users.txt', 'w', encoding='utf-8') as f:
    for user in ignored_users:
        f.write(user + '\n')

print(f"Identified {len(ignored_users)} ignored users. Saved to ignored_users.txt")
