"""
Sync FreeIndexer publishing tracker.

Mirrors: captcharank_content/scripts/sync_publishing_tracker.py

TODO integration:
- verify live URLs against the real FreeIndexer blog domain
- optionally query blog API for draft/live state
- update pipeline/publishing-tracker.csv with live dates and post IDs

Expected input:
- pipeline/publishing-tracker.csv
- owner-provided blog domain/API details

Expected output:
- updated pipeline/publishing-tracker.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "pipeline" / "publishing-tracker.csv"


def main() -> int:
    if not TRACKER.exists():
        raise SystemExit("Missing pipeline/publishing-tracker.csv")

    with TRACKER.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    missing_articles = []
    missing_heroes = []
    for row in rows:
        article = ROOT / row["article_path"]
        hero = ROOT / row["hero_image_path"]
        if not article.exists():
            missing_articles.append(row["article_path"])
        if not hero.exists():
            missing_heroes.append(row["hero_image_path"])

    print(f"checked {len(rows)} tracker rows")
    if missing_articles:
        print("Missing article paths:")
        for item in missing_articles:
            print(f"- {item}")
    if missing_heroes:
        print("Hero files not generated yet:")
        for item in missing_heroes:
            print(f"- {item}")

    print("Live URL/API sync is TODO until owner provides blog target and API details.")
    return 0 if not missing_articles else 1


if __name__ == "__main__":
    raise SystemExit(main())

