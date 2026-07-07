"""Sync repaired article descriptions to existing live blog records safely."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from blog_api_client import BlogApiClient
from content_tools import (
    ROOT,
    derive_description,
    derive_meta_description,
    derive_meta_title,
    derive_slug,
    list_content_files,
    read_article_file,
)

REPORT_PATH = ROOT / "pipeline" / "live-description-update-report.json"


def translated(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("en") is not None:
            return str(value["en"])
        if value:
            return str(next(iter(value.values())))
        return ""
    return "" if value is None else str(value)


def list_all_published(client: BlogApiClient) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    page = 1
    while True:
        response = client.list_blogs(
            per_page="100",
            page=str(page),
            status="published",
            summary="0",
        )
        data = response.get("data") or {}
        items = data.get("data", []) if isinstance(data, dict) else data
        output.extend(item for item in items or [] if isinstance(item, dict))
        last_page = int(data.get("last_page") or 1) if isinstance(data, dict) else 1
        if page >= last_page:
            return output
        page += 1


def tag_ids(item: dict[str, Any]) -> list[int]:
    values: list[int] = []
    for tag in item.get("tags") or []:
        if isinstance(tag, dict) and tag.get("id"):
            values.append(int(tag["id"]))
        elif isinstance(tag, int):
            values.append(tag)
    return values


def preserved_payload(
    client: BlogApiClient,
    remote: dict[str, Any],
    description: str,
    meta_title: str,
    meta_description: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "application_id": client.application_id,
        "application_admin_id": remote.get("application_admin_id"),
        "category_id": remote.get("category_id"),
        "author_id": remote.get("author_id"),
        "title": translated(remote.get("title")),
        "slug": translated(remote.get("slug")),
        "content": translated(remote.get("content")),
        "featured_image": remote.get("featured_image") or "",
        "allow_comments": bool(remote.get("allow_comments")),
        "comment_default_status": remote.get("comment_default_status") or "pending",
        "status": remote.get("status") or "published",
        "meta_title": meta_title or translated(remote.get("meta_title")),
        "meta_description": meta_description,
        "description": description,
        "tags": tag_ids(remote),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync repaired descriptions to published blog records.")
    parser.add_argument("--apply", action="store_true", help="Perform API updates.")
    parser.add_argument("--limit", type=int, default=0, help="Update at most N mismatched records.")
    parser.add_argument("--report", default=str(REPORT_PATH), help="JSON report path.")
    args = parser.parse_args()

    client = BlogApiClient()
    published = list_all_published(client)
    remote_by_slug = {translated(item.get("slug")): item for item in published}

    mismatches: list[dict[str, Any]] = []
    for path in list_content_files():
        article_file = read_article_file(path)
        slug = derive_slug(article_file)
        remote = remote_by_slug.get(slug)
        if not remote:
            continue
        description = derive_description(article_file)
        meta_description = derive_meta_description(article_file)
        current_description = translated(remote.get("description"))
        current_meta = translated(remote.get("meta_description"))
        if description == current_description and meta_description == current_meta:
            continue
        mismatches.append(
            {
                "slug": slug,
                "id": int(remote["id"]),
                "old_description": current_description,
                "new_description": description,
                "old_meta_description": current_meta,
                "new_meta_description": meta_description,
                "remote": remote,
                "meta_title": derive_meta_title(article_file),
            }
        )

    if args.limit:
        mismatches = mismatches[: args.limit]

    updated: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for item in mismatches:
        result = {"slug": item["slug"], "id": item["id"]}
        if args.apply:
            payload = preserved_payload(
                client,
                item["remote"],
                str(item["new_description"]),
                str(item["meta_title"]),
                str(item["new_meta_description"]),
            )
            response = client.update_blog(int(item["id"]), payload)
            if response.get("success", True):
                updated.append(result)
                print(f"UPDATED {item['id']} {item['slug']}", flush=True)
            else:
                result["response"] = response
                failed.append(result)
                print(f"FAILED {item['id']} {item['slug']}: {response}", file=sys.stderr, flush=True)
        else:
            updated.append(result)

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "published_records_scanned": len(published),
        "mismatches_selected": len(mismatches),
        "updated_count": len(updated) if args.apply else 0,
        "would_update_count": len(updated) if not args.apply else 0,
        "failed_count": len(failed),
        "updated": updated,
        "failed": failed,
    }
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    if args.apply:
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in {"updated", "failed"}}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
