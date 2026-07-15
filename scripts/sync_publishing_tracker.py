"""Audit and optionally refresh FreeIndexer publishing tracker rows.

Default mode is local-only. Use --check-live to verify published_url values over
HTTP, and --write to persist live-check timestamps and live-check details.
Publishing notes are preserved.
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "pipeline" / "publishing-tracker.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_retryable_note(note: str) -> bool:
    return "failed:" in note and "HTTP " not in note


def check_url_once(url: str, timeout: int = 15) -> tuple[bool, str]:
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


def check_url(url: str, timeout: int = 15, retries: int = 1, retry_delay: float = 1.0) -> tuple[bool, str]:
    attempts = max(retries, 0) + 1
    last_note = ""
    for attempt in range(1, attempts + 1):
        ok, note = check_url_once(url, timeout)
        if ok:
            if attempt > 1:
                return ok, f"{note} after {attempt} attempts"
            return ok, note
        last_note = note
        if attempt == attempts or not is_retryable_note(note):
            break
        time.sleep(max(retry_delay, 0))
    if attempts > 1 and is_retryable_note(last_note):
        return False, f"{last_note} after {attempts} attempts"
    return False, last_note


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
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout per request, default: 15 seconds.")
    parser.add_argument("--retries", type=int, default=1, help="Retries for transient network failures, default: 1.")
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Delay between retries for transient network failures, default: 1.0 seconds.",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.1,
        help="Delay between live URL checks to reduce remote connection resets, default: 0.1 seconds.",
    )
    parser.add_argument(
        "--failure-limit",
        type=int,
        default=50,
        help="Maximum failed live-check rows to print, default: 50.",
    )
    parser.add_argument(
        "--mark-live-published",
        action="store_true",
        help=(
            "With --check-live --write, mark scheduled rows as published when their URL is live "
            "and their live_date is not in the future."
        ),
    )
    args = parser.parse_args()

    if args.mark_live_published and not (args.check_live and args.write):
        raise SystemExit("--mark-live-published requires --check-live --write")

    if not TRACKER.exists():
        raise SystemExit("Missing pipeline/publishing-tracker.csv")

    with TRACKER.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for field in ("last_checked_live", "live_check_ok", "live_check_note", "notes"):
        if field not in fieldnames:
            fieldnames.append(field)

    missing_articles = []
    missing_heroes = []
    scheduled_blank_live_date = 0
    scheduled_past_live_date = 0
    scheduled_due_now = 0
    scheduled_future_live_date = 0
    live_ok = 0
    live_failed = 0
    live_pending_future = 0
    live_failures = []
    future_pending_rows = []
    marked_published = 0
    now = datetime.now(timezone.utc)
    checked_at = utc_now()

    for row in rows:
        article = ROOT / row.get("article_path", "")
        hero = ROOT / row.get("hero_image_path", "")
        if not article.exists():
            missing_articles.append(row.get("article_path", ""))
        if not hero.exists():
            missing_heroes.append(row.get("hero_image_path", ""))

        live_date = parse_utc_datetime(row.get("live_date", ""))
        is_future_scheduled = row.get("draft_status") == "scheduled" and live_date is not None and live_date > now

        if row.get("draft_status") == "scheduled":
            if live_date is None:
                scheduled_blank_live_date += 1
            elif is_future_scheduled:
                scheduled_future_live_date += 1
            else:
                scheduled_due_now += 1
                if live_date.date() < now.date():
                    scheduled_past_live_date += 1

        if args.check_live:
            ok, note = check_url(
                row.get("published_url", ""),
                timeout=args.timeout,
                retries=args.retries,
                retry_delay=args.retry_delay,
            )
            row["last_checked_live"] = checked_at
            row["live_check_ok"] = "yes" if ok else "pending" if is_future_scheduled else "no"
            row["live_check_note"] = note
            if ok:
                live_ok += 1
                if (
                    args.mark_live_published
                    and row.get("draft_status") == "scheduled"
                    and (live_date is None or live_date <= now)
                ):
                    row["draft_status"] = "published"
                    marked_published += 1
            else:
                if is_future_scheduled:
                    live_pending_future += 1
                    future_pending_rows.append(row)
                else:
                    live_failed += 1
                    live_failures.append(row)
            if args.request_delay > 0:
                time.sleep(args.request_delay)

    print(f"checked {len(rows)} tracker rows")
    print(f"missing article paths: {len(missing_articles)}")
    print(f"missing hero files: {len(missing_heroes)}")
    print(f"scheduled rows with blank live_date: {scheduled_blank_live_date}")
    print(f"scheduled rows due now or earlier: {scheduled_due_now}")
    print(f"scheduled rows with past live_date: {scheduled_past_live_date}")
    print(f"scheduled rows with future live_date: {scheduled_future_live_date}")

    if missing_articles:
        for item in missing_articles:
            print(f"- missing article: {item}")
    if missing_heroes:
        for item in missing_heroes:
            print(f"- missing hero: {item}")

    if args.check_live:
        print(f"live checks ok: {live_ok}")
        print(f"future scheduled URLs not live yet: {live_pending_future}")
        print(f"live checks failed: {live_failed}")
        if live_failures:
            print("failed live checks:")
            for row in live_failures[: max(args.failure_limit, 0)]:
                print(
                    "- "
                    f"{row.get('slug', '')} | "
                    f"status={row.get('draft_status', '')} | "
                    f"live_date={row.get('live_date', '') or 'blank'} | "
                    f"post_id={row.get('blog_post_id', '')} | "
                    f"{row.get('live_check_note', '')} | "
                    f"{row.get('published_url', '')}"
                )
            remaining = live_failed - max(args.failure_limit, 0)
            if remaining > 0:
                print(f"... {remaining} more failed live checks not shown")
        if future_pending_rows:
            print("future scheduled URLs not live yet:")
            for row in future_pending_rows[: max(args.failure_limit, 0)]:
                print(
                    "- "
                    f"{row.get('slug', '')} | "
                    f"live_date={row.get('live_date', '')} | "
                    f"post_id={row.get('blog_post_id', '')} | "
                    f"{row.get('live_check_note', '')} | "
                    f"{row.get('published_url', '')}"
                )
            remaining = live_pending_future - max(args.failure_limit, 0)
            if remaining > 0:
                print(f"... {remaining} more future scheduled URLs not shown")
        if args.mark_live_published:
            print(f"scheduled rows marked published: {marked_published}")
        if args.write:
            write_tracker(rows, fieldnames)
            print("tracker updated")
        else:
            print("tracker not written; add --write to persist live-check results")

    return 0 if not missing_articles else 1


if __name__ == "__main__":
    raise SystemExit(main())
