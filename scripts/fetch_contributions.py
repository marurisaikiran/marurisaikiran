"""Scrape the public contribution calendar into data/contributions.json.

No token needed: reads https://github.com/users/<user>/contributions.
Runs daily in GitHub Actions (see .github/workflows/update-profile-art.yml).
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USER = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "marurisaikiran"


def count_of(text: str) -> int:
    m = re.match(r"\s*([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def fetch() -> list[dict]:
    r = requests.get(f"https://github.com/users/{USER}/contributions",
                     headers={"User-Agent": "profile-readme-heatmap"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): count_of(t.get_text()) for t in soup.select("tool-tip[for]")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        c = tips.get(td.get("id"))
        if c is None:
            c = int(td.get("data-count", 0))
        days.append({"date": td["data-date"], "count": c, "level": int(td.get("data-level", 0))})
    if not days:
        raise SystemExit("no contribution cells found - GitHub may have changed its markup")
    return sorted(days, key=lambda d: d["date"])


def stats(days: list[dict]) -> dict:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["count"]:
            current += 1
        elif i == 0:          # an empty today doesn't break the streak
            continue
        else:
            break
    best = max(days, key=lambda d: d["count"])
    return {
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"]),
    }


def main() -> None:
    days = fetch()
    data = {"username": USER, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "stats": stats(days), "days": days}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{USER}: {data['stats']['total']} contributions over {len(days)} days")


if __name__ == "__main__":
    main()
