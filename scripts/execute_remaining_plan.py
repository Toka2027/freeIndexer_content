"""Execute the remaining 100-plan articles through image, upload, and schedule.

This is intentionally resumable. It reads pipeline/master-plan-100.csv and
pipeline/publishing-schedule.csv, skips rows that are already scheduled or
published, and processes the remaining created rows in article-number order.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from blog_api_client import BlogApiClient

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "pipeline" / "master-plan-100.csv"
ROADMAP_PATH = ROOT / "pipeline" / "series-roadmap.csv"
SCHEDULE_PATH = ROOT / "pipeline" / "publishing-schedule.csv"
TRACKER_PATH = ROOT / "pipeline" / "publishing-tracker.csv"
UPLOAD_TRACKER_PATH = ROOT / "pipeline" / "upload-tracker.json"
SERIES_API_TRACKER_PATH = ROOT / "pipeline" / "series-api-tracker.csv"
CONTENT_DIR = ROOT / "content"
SUBJECT_DIR = ROOT / "images" / "exports" / "subjects"
HERO_DIR = ROOT / "images" / "exports"
SLOT_HOURS_UTC = (6, 9, 12)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ensure_fields(fieldnames: list[str], fields: list[str]) -> list[str]:
    merged = list(fieldnames)
    for field in fields:
        if field not in merged:
            merged.append(field)
    return merged


def article_path(slug: str) -> Path:
    matches = sorted(CONTENT_DIR.rglob(f"{slug}.md"))
    if not matches:
        raise FileNotFoundError(f"missing article file for {slug}")
    return matches[0]


def subject_path(slug: str) -> Path:
    return SUBJECT_DIR / f"{slug}-subject.png"


def hero_path(slug: str) -> Path:
    return HERO_DIR / f"{slug}-hero.png"


def load_upload_tracker() -> dict[str, dict[str, str]]:
    if not UPLOAD_TRACKER_PATH.exists():
        return {}
    return json.loads(UPLOAD_TRACKER_PATH.read_text(encoding="utf-8"))


def load_tracker() -> dict[str, dict[str, str]]:
    if not TRACKER_PATH.exists():
        return {}
    rows, _ = read_csv(TRACKER_PATH)
    return {row.get("slug", ""): row for row in rows}


def run_step(args: list[str], env: dict[str, str], dry_run: bool = False) -> None:
    printable = " ".join(args)
    print(f"RUN {printable}", flush=True)
    if dry_run:
        return
    completed = subprocess.run(args, cwd=ROOT, env=env, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {printable}")


def parse_iso(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def next_slots(existing_times: list[datetime], count: int) -> list[str]:
    latest = max(existing_times) if existing_times else datetime(2026, 5, 22, 6, tzinfo=timezone.utc)
    day = latest.date()
    slots: list[datetime] = []
    cursor = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    while len(slots) < count:
        for hour in SLOT_HOURS_UTC:
            candidate = cursor.replace(hour=hour)
            if candidate > latest and candidate not in existing_times:
                slots.append(candidate)
                if len(slots) == count:
                    break
        cursor += timedelta(days=1)
    return [slot.strftime("%Y-%m-%dT%H:%M:%SZ") for slot in slots]


def row_status(row: dict[str, str]) -> str:
    return (row.get("planned_status") or row.get("publish_status") or "").strip()


def sync_execution_state() -> None:
    upload_tracker = load_upload_tracker()
    tracker = load_tracker()

    for path in (PLAN_PATH, ROADMAP_PATH):
        rows, fields = read_csv(path)
        fields = ensure_fields(fields, ["series_api_id", "series_api_status"])
        for row in rows:
            slug = row["slug"]
            tracked = tracker.get(slug, {})
            uploaded = upload_tracker.get(slug, {})
            status = tracked.get("draft_status") or row.get("planned_status") or ""
            if status in {"published", "scheduled"}:
                row["planned_status"] = status
                row["execution_blocker"] = ""
            elif hero_path(slug).exists() and uploaded.get("public_url"):
                row["planned_status"] = "hero_uploaded"
            elif hero_path(slug).exists():
                row["planned_status"] = "hero_generated"
            elif row.get("planned_status") not in {"blocked"}:
                row["planned_status"] = row.get("planned_status") or "cluster_created"
        write_csv(path, rows, fields)

    schedule_rows, schedule_fields = read_csv(SCHEDULE_PATH)
    schedule_fields = ensure_fields(
        schedule_fields,
        [
            "actual_status",
            "actual_published_at",
            "blog_url",
            "hero_image_url",
            "content_status",
            "hero_status",
            "hero_upload_status",
            "publish_status",
            "execution_status",
            "execution_blocker",
            "series_api_id",
            "series_api_status",
        ],
    )
    for row in schedule_rows:
        slug = row["slug"]
        tracked = tracker.get(slug, {})
        uploaded = upload_tracker.get(slug, {})
        row["content_status"] = "created"
        if hero_path(slug).exists():
            row["hero_status"] = "hero_generated"
        if uploaded.get("public_url"):
            row["hero_upload_status"] = "hero_uploaded"
            row["hero_image_url"] = uploaded["public_url"]
        if tracked.get("blog_post_id"):
            status = tracked.get("draft_status") or "scheduled"
            row["planned_status"] = status
            row["actual_status"] = status
            row["publish_status"] = status
            row["execution_status"] = status
            row["actual_published_at"] = tracked.get("live_date") or row.get("actual_published_at", "")
            row["blog_url"] = tracked.get("published_url") or row.get("blog_url", "")
            row["execution_blocker"] = ""
        elif row.get("planned_status") == "blocked":
            row["execution_status"] = "blocked"
        elif row.get("hero_upload_status") == "hero_uploaded":
            row["planned_status"] = "hero_uploaded"
            row["execution_status"] = "hero_uploaded"
        elif row.get("hero_status") == "hero_generated":
            row["planned_status"] = "hero_generated"
            row["execution_status"] = "hero_generated"
        else:
            row["publish_status"] = row.get("publish_status") or "created"
            row["execution_status"] = row.get("execution_status") or "created"
    write_csv(SCHEDULE_PATH, schedule_rows, schedule_fields)


def update_series_api() -> None:
    plan_rows, _ = read_csv(PLAN_PATH)
    tracker = load_tracker()
    by_series: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in plan_rows:
        by_series[row["series_name"]].append(row)
    for rows in by_series.values():
        rows.sort(key=lambda item: int(item["series_order"]))

    client = BlogApiClient()
    existing_resp = client.list_series(per_page="100")
    raw_data = existing_resp.get("data") or []
    existing_list = raw_data.get("data") if isinstance(raw_data, dict) else raw_data
    existing: dict[str, dict[str, object]] = {}
    for item in existing_list or []:
        name = item.get("name") if isinstance(item, dict) else ""
        if isinstance(name, dict):
            name = name.get("en") or next(iter(name.values()), "")
        if name:
            existing[str(name)] = item

    output_rows: list[dict[str, str]] = []
    for series_name, rows in by_series.items():
        submitted = []
        missing = []
        for row in rows:
            blog_id = (tracker.get(row["slug"], {}).get("blog_post_id") or "").strip()
            if blog_id:
                submitted.append((row, blog_id))
            else:
                missing.append(row["slug"])
        items = [
            {
                "blog_id": str(blog_id),
                "sort_order": int(row["series_order"]),
                "name": {"en": row["title"]},
                "description": {"en": f"Part {row['series_order']} of {series_name}."},
                "is_active": True,
            }
            for row, blog_id in submitted
        ]
        description = (
            f"Visible series for FreeIndexer Blog. Full sequence has {len(rows)} articles; "
            f"{len(items)} uploaded, scheduled, or published articles are attached."
        )
        if series_name in existing:
            series_id = int(existing[series_name]["id"])
            result = client.update_series(series_id, series_name, description, items, is_active=True)
            api_status = "updated" if result.get("success") else "blocked"
        else:
            result = client.create_series(series_name, description, items, is_active=True)
            series_id = int((result.get("data") or {}).get("id") or 0)
            api_status = "created" if result.get("success") else "blocked"
        output_rows.append(
            {
                "series_name": series_name,
                "series_id": str(series_id or ""),
                "api_status": api_status,
                "item_count": str(len(items)),
                "total_article_count": str(len(rows)),
                "missing_blog_id_count": str(len(missing)),
                "missing_blog_ids": "|".join(missing),
                "notes": "" if api_status != "blocked" else str(result)[:240],
            }
        )

    series_fields = [
        "series_name",
        "series_id",
        "api_status",
        "item_count",
        "total_article_count",
        "missing_blog_id_count",
        "missing_blog_ids",
        "notes",
    ]
    write_csv(SERIES_API_TRACKER_PATH, output_rows, series_fields)

    api_by_series = {row["series_name"]: row for row in output_rows}
    for path in (PLAN_PATH, ROADMAP_PATH, SCHEDULE_PATH):
        rows, fields = read_csv(path)
        fields = ensure_fields(fields, ["series_api_id", "series_api_status"])
        for row in rows:
            api = api_by_series.get(row.get("series_name", ""), {})
            row["series_api_id"] = api.get("series_id", "")
            row["series_api_status"] = api.get("api_status", "")
        write_csv(path, rows, fields)


def process(args: argparse.Namespace) -> int:
    if not os.environ.get("OPENAI_API_KEY", "").strip() and not args.skip_generate:
        raise SystemExit("OPENAI_API_KEY is not set in the current process.")

    sync_execution_state()
    schedule_rows, _ = read_csv(SCHEDULE_PATH)
    existing_times = [dt for dt in (parse_iso(row.get("actual_published_at", "")) for row in schedule_rows) if dt]
    remaining = [
        row
        for row in schedule_rows
        if row_status(row) not in {"scheduled", "published"}
        and row.get("execution_status") not in {"scheduled", "published"}
    ]
    remaining.sort(key=lambda row: int(row["article_number"]))
    if args.limit:
        remaining = remaining[: args.limit]
    slots = next_slots(existing_times, len(remaining))
    env = os.environ.copy()
    processed = 0
    blocked: list[tuple[str, str]] = []

    for row, publish_at in zip(remaining, slots):
        slug = row["slug"]
        template = row.get("hero_template") or row.get("hero_template_number") or "1"
        print(f"\n=== {row['article_number']} {slug} -> {publish_at} ===", flush=True)
        try:
            path = article_path(slug)
            if not subject_path(slug).exists() and not args.skip_generate:
                run_step([sys.executable, "scripts/generate_image.py", "--slug", slug], env, args.dry_run)
            if not hero_path(slug).exists():
                run_step(
                    [
                        sys.executable,
                        "scripts/build_hero.py",
                        "--slug",
                        slug,
                        "--template",
                        str(template),
                        "--validator",
                    ],
                    env,
                    args.dry_run,
                )
            run_step([sys.executable, "scripts/prepare_blog_draft.py", str(path), "--upload-image"], env, args.dry_run)
            run_step(
                [
                    sys.executable,
                    "scripts/prepare_blog_draft.py",
                    str(path),
                    "--status",
                    "scheduled",
                    "--published-at",
                    publish_at,
                ],
                env,
                args.dry_run,
            )
            sync_execution_state()
            processed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"BLOCKED {slug}: {exc}", flush=True)
            blocked.append((slug, str(exc)))
            for path_obj in (PLAN_PATH, ROADMAP_PATH, SCHEDULE_PATH):
                rows, fields = read_csv(path_obj)
                fields = ensure_fields(fields, ["execution_blocker"])
                for item in rows:
                    if item.get("slug") == slug:
                        item["planned_status"] = "blocked"
                        item["execution_status"] = "blocked"
                        item["execution_blocker"] = str(exc)[:240]
                write_csv(path_obj, rows, fields)

    sync_execution_state()
    update_series_api()
    print(f"\nProcessed: {processed}")
    print(f"Blocked: {len(blocked)}")
    for slug, reason in blocked:
        print(f"- {slug}: {reason}")
    return 1 if blocked else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute remaining 100-plan articles.")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N remaining rows.")
    parser.add_argument("--skip-generate", action="store_true", help="Skip missing subject generation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return process(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
