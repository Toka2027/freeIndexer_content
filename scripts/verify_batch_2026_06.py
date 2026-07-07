"""Verify and sync the June 2026 30-article scheduled batch."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from blog_api_client import BlogApiClient
from content_tools import ROOT

PLAN_PATH = ROOT / "pipeline" / "batch-2026-06-30.csv"
SCHEDULE_PATH = ROOT / "pipeline" / "batch-2026-06-30-schedule.csv"
REPORT_PATH = ROOT / "pipeline" / "batch-2026-06-verification.json"
CAIRO = timezone(timedelta(hours=3), name="Africa/Cairo summer time")


def translated(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("en") is not None:
            return str(value["en"])
        if value:
            return str(next(iter(value.values())))
        return ""
    return "" if value is None else str(value)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def all_scheduled(client: BlogApiClient) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    page = 1
    while True:
        response = client.list_blogs(per_page="100", page=str(page), status="scheduled", summary="0")
        data = response.get("data") or {}
        items = data.get("data", []) if isinstance(data, dict) else data
        output.extend(item for item in items or [] if isinstance(item, dict))
        last_page = int(data.get("last_page") or 1) if isinstance(data, dict) else 1
        if page >= last_page:
            return output
        page += 1


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    plan_rows, plan_fields = read_csv(PLAN_PATH)
    schedule_rows, schedule_fields = read_csv(SCHEDULE_PATH)
    batch_slugs = {row["slug"] for row in schedule_rows}

    client = BlogApiClient()
    scheduled = all_scheduled(client)
    by_slug = {translated(item.get("slug")): item for item in scheduled}

    errors: list[str] = []
    verified: list[dict[str, Any]] = []
    expected_dates = [row["publish_date"] for row in schedule_rows]
    if len(expected_dates) != len(set(expected_dates)):
        errors.append("Batch schedule contains duplicate publish dates.")

    other_scheduled = [
        item for slug, item in by_slug.items() if slug not in batch_slugs
    ]
    other_dates = {
        parse_utc(str(item["scheduled_at"])).astimezone(CAIRO).date().isoformat()
        for item in other_scheduled
        if item.get("scheduled_at")
    }

    meta_values: set[str] = set()
    description_values: set[str] = set()
    for row in schedule_rows:
        slug = row["slug"]
        item = by_slug.get(slug)
        if not item:
            errors.append(f"{slug}: not found in scheduled API records")
            continue
        scheduled_at = str(item.get("scheduled_at") or "")
        if not scheduled_at:
            errors.append(f"{slug}: missing scheduled_at")
            continue
        utc_dt = parse_utc(scheduled_at)
        cairo_dt = utc_dt.astimezone(CAIRO)
        actual_date = cairo_dt.date().isoformat()
        if actual_date != row["publish_date"]:
            errors.append(
                f"{slug}: expected local date {row['publish_date']}, found {actual_date}"
            )
        if actual_date in other_dates:
            errors.append(f"{slug}: local date conflicts with another scheduled post")

        description = translated(item.get("description"))
        meta = translated(item.get("meta_description"))
        if not 120 <= len(meta) <= 160:
            errors.append(f"{slug}: live meta description length is {len(meta)}")
        if meta.casefold() in meta_values:
            errors.append(f"{slug}: duplicate live meta description")
        meta_values.add(meta.casefold())
        if description.casefold() in description_values:
            errors.append(f"{slug}: duplicate live description")
        description_values.add(description.casefold())
        expected_image = (
            "https://cen-public-st.nbg1.your-objectstorage.com/"
            f"freeindexer/blog/{slug}-hero.png"
        )
        if item.get("featured_image") != expected_image:
            errors.append(f"{slug}: featured image does not match uploaded hero")

        row["status"] = str(item.get("status") or "")
        row["blog_post_id"] = str(item.get("id") or "")
        row["blog_url"] = f"https://blog.freeindexer.com/{slug}"
        row["cms_scheduled_at_utc"] = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        row["publish_time_cairo"] = cairo_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        verified.append(
            {
                "order": int(row["batch_order"]),
                "slug": slug,
                "blog_post_id": int(item["id"]),
                "status": item.get("status"),
                "scheduled_at_utc": row["cms_scheduled_at_utc"],
                "publish_time_cairo": row["publish_time_cairo"],
                "publish_date": actual_date,
                "featured_image": item.get("featured_image"),
                "meta_description_length": len(meta),
            }
        )

    for field in ("cms_scheduled_at_utc", "publish_time_cairo"):
        if field not in schedule_fields:
            schedule_fields.append(field)
    write_csv(SCHEDULE_PATH, schedule_rows, schedule_fields)

    plan_by_slug = {row["slug"]: row for row in plan_rows}
    for item in verified:
        plan = plan_by_slug[item["slug"]]
        plan["hero_status"] = "uploaded"
        plan["publish_status"] = "scheduled"
    write_csv(PLAN_PATH, plan_rows, plan_fields)

    report = {
        "verified_at": datetime.now(tz=CAIRO).isoformat(),
        "batch_size": len(schedule_rows),
        "scheduled_records_found": len(verified),
        "other_scheduled_records": len(other_scheduled),
        "unique_publish_dates": len({item["publish_date"] for item in verified}),
        "first_publish_date": min((item["publish_date"] for item in verified), default=""),
        "last_publish_date": max((item["publish_date"] for item in verified), default=""),
        "template_distribution": {
            template: sum(row["hero_template"] == template for row in plan_rows)
            for template in ("1", "2", "3")
        },
        "errors": errors,
        "items": verified,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
