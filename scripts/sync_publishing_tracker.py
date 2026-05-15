"""Audit and optionally refresh FreeIndexer publishing tracker rows.

Default mode is local-only. Use --check-live to verify published_url values over
HTTP, and --write to persist live-check timestamps/status notes.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "pipeline" / "publishing-tracker.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_url(url: str, timeout: int = 15) -> tuple[bool, str]:
    if not url:
        return False, "missing published_url"
    req = request.Request(url, headers={"User-Agent": "FreeIndexerContentAudit/1.0"}, method="HEAD")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 400:
                return True, f"HTTP {resp.status}"
            return check_url_get(url, timeout)
    except error.HTTPError as exc:
        ok, note = check_url_get(url, timeout)
        if ok:
            return ok, note
        return False, f"HEAD HTTP {exc.code}; {note}"
    except Exception as exc:  # noqa: BLE001
        ok, note = check_url_get(url, timeout)
        if ok:
            return ok, note
        return False, f"HEAD failed: {exc}; {note}"


def check_url_get(url: str, timeout: int = 15) -> tuple[bool, str]:
    get_req = request.Request(url, headers={"User-Agent": "FreeIndexerContentAudit/1.0"}, method="GET")
    try:
        with request.urlopen(get_req, timeout=timeout) as resp:
            return 200 <= resp.status < 400, f"GET HTTP {resp.status}"
    except error.HTTPError as exc:
        return False, f"GET HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, f"GET failed: {exc}"


def write_tracker(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with TRACKER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit FreeIndexer publishing tracker rows.")
    parser.add_argument("--check-live", action="store_true", help="Verify published_url values over HTTP.")
    parser.add_argument("--write", action="store_true", help="Persist live-check timestamps and notes.")
    args = parser.parse_args()

    if not TRACKER.exists():
        raise SystemExit("Missing pipeline/publishing-tracker.csv")

    with TRACKER.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for field in ("last_checked_live", "notes"):
        if field not in fieldnames:
            fieldnames.append(field)

    missing_articles = []
    missing_heroes = []
    live_ok = 0
    live_failed = 0

    for row in rows:
        article = ROOT / row.get("article_path", "")
        hero = ROOT / row.get("hero_image_path", "")
        if not article.exists():
            missing_articles.append(row.get("article_path", ""))
        if not hero.exists():
            missing_heroes.append(row.get("hero_image_path", ""))

        if args.check_live:
            ok, note = check_url(row.get("published_url", ""))
            row["last_checked_live"] = utc_now()
            row["notes"] = note
            if ok:
                live_ok += 1
            else:
                live_failed += 1

    print(f"checked {len(rows)} tracker rows")
    print(f"missing article paths: {len(missing_articles)}")
    print(f"missing hero files: {len(missing_heroes)}")

    if missing_articles:
        for item in missing_articles:
            print(f"- missing article: {item}")
    if missing_heroes:
        for item in missing_heroes:
            print(f"- missing hero: {item}")

    if args.check_live:
        print(f"live checks ok: {live_ok}")
        print(f"live checks failed: {live_failed}")
        if args.write:
            write_tracker(rows, fieldnames)
            print("tracker updated")
        else:
            print("tracker not written; add --write to persist live-check results")

    return 0 if not missing_articles else 1


if __name__ == "__main__":
    raise SystemExit(main())
