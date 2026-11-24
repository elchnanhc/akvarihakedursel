import json
import re
import time
import urllib.request
from bs4 import BeautifulSoup

# רשימת הליגות לסריקה אוטומטית (אפשר להוסיף כאן כל ליגה מ-Proballers)
LEAGUES = [
    {"id": "nba", "name": "NBA", "path": "/basketball/league/3/nba"},
    {"id": "euroleague", "name": "יורוליג (EuroLeague)", "path": "/basketball/league/177/euroleague"},
    {"id": "eurocup", "name": "יורוקאפ (EuroCup)", "path": "/basketball/league/192/eurocup"},
    {"id": "bcl", "name": "ליגת האלופות (BCL)", "path": "/basketball/league/422/basketball-champions-league"},
    {"id": "spain", "name": "ספרד (Liga Endesa)", "path": "/basketball/league/30/spain-liga-endesa"},
    {"id": "france", "name": "צרפת (Betclic Elite)", "path": "/basketball/league/1/france-betclic-elite"},
    {"id": "turkey", "name": "טורקיה (BSL)", "path": "/basketball/league/168/turkey-bsl"},
    {"id": "italy", "name": "איטליה (LBA Serie A)", "path": "/basketball/league/40/italy-lba-serie-a"},
    {"id": "greece", "name": "יוון (GBL)", "path": "/basketball/league/50/greece-gbl"},
    {"id": "germany", "name": "גרמניה (easyCredit BBL)", "path": "/basketball/league/118/germany-easycredit-bbl"},
    {"id": "australia", "name": "אוסטרליה (NBL)", "path": "/basketball/league/226/australia-nbl"},
    {"id": "aba", "name": "הליגה האדריאטית (ABA)", "path": "/basketball/league/182/adriatic-liga-aba"},
]

SEASONS = [
    {"label": "16/17", "suffix": "/2016"},
    {"label": "17/18", "suffix": "/2017"},
    {"label": "18/19", "suffix": "/2018"},
    {"label": "19/20", "suffix": "/2019"},
    {"label": "20/21", "suffix": "/2020"},
    {"label": "21/22", "suffix": "/2021"},
    {"label": "22/23", "suffix": "/2022"},
    {"label": "23/24", "suffix": "/2023"},
    {"label": "24/25", "suffix": "/2024"},
    {"label": "25/26", "suffix": "/2025"},
    {"label": "*26/27", "suffix": ""},
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_season(path, suffix):
    url = f"https://www.proballers.com{path}/schedule{suffix}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    diffs = []
    for el in soup.find_all(["a", "td", "span", "div"]):
        if not el.find():
            txt = el.get_text(strip=True)
            m = re.match(r"^(\d{2,3})\s*-\s*(\d{2,3})$", txt)
            if m:
                s1, s2 = int(m.group(1)), int(m.group(2))
                if s1 >= 40 and s2 >= 40 and s1 != s2:
                    diffs.append(abs(s1 - s2))

    games = len(diffs)
    if games == 0:
        return None

    avg = round(sum(diffs) / games, 2)
    u5 = sum(1 for d in diffs if d <= 5)
    b6_10 = sum(1 for d in diffs if 6 <= d <= 10)
    b11_19 = sum(1 for d in diffs if 11 <= d <= 19)
    p20 = sum(1 for d in diffs if d >= 20)
    return {
        "season": "",
        "games": games,
        "avg": avg,
        "u5": u5,
        "b6_10": b6_10,
        "b11_19": b11_19,
        "p20": p20,
        "u10": u5 + b6_10,
    }

def main():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            existing = {item["id"]: item for item in json.load(f)}
    except FileNotFoundError:
        existing = {}

    output = []
    for lg in LEAGUES:
        prev_seasons = {s["season"]: s for s in existing.get(lg["id"], {}).get("seasons", [])}
        updated_seasons = []
        for s in SEASONS:
            # סורק מחדש רק את העונה הפעילה (*26/27) או עונות שטרם נאספו
            if s["label"] != "*26/27" and s["label"] in prev_seasons:
                updated_seasons.append(prev_seasons[s["label"]])
                continue

            print(f"Fetching {lg['name']} - {s['label']}...")
            stats = fetch_season(lg["path"], s["suffix"])
            if stats:
                stats["season"] = s["label"]
                updated_seasons.append(stats)
            elif s["label"] in prev_seasons:
                updated_seasons.append(prev_seasons[s["label"]])
            time.sleep(0.5)

        output.append({"id": lg["id"], "league": lg["name"], "seasons": updated_seasons})

    if "israel" in existing:
        output.insert(0, existing["israel"])

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
