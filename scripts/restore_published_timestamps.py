"""Restore publication timestamps shifted by the CMS metadata PUT timezone quirk."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from blog_api_client import BlogApiClient
from content_tools import ROOT
from sync_live_descriptions import preserved_payload, translated

REPORT_SOURCES = [
    ROOT / "pipeline" / "live-description-update-report.json",
]
OUTPUT_PATH = ROOT / "pipeline" / "published-timestamp-restore-report.json"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_z(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def updated_slugs() -> list[str]:
    slugs: list[str] = []
    for path in REPORT_SOURCES:
        data = json.loads(path.read_text(encoding="utf-8"))
        slugs.extend(str(item["slug"]) for item in data.get("updated") or [])
    return list(dict.fromkeys(slugs))


def fetch(client: BlogApiClient, slug: str) -> dict[str, Any]:
    response = client.list_blogs(per_page="1", slug=slug, summary="0")
    data = response.get("data") or {}
    items = data.get("data", []) if isinstance(data, dict) else data
    if not items:
        raise RuntimeError(f"Missing blog record for {slug}")
    return items[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore publication timestamps after metadata sync.")
    parser.add_argument("--apply", action="store_true", help="Apply timestamp restoration.")
    parser.add_argument("--skip", type=int, default=0, help="Skip the first N report records.")
    parser.add_argument("--limit", type=int, default=0, help="Restore at most N records.")
    parser.add_argument("--force", action="store_true", help="Allow a second restoration run.")
    args = parser.parse_args()

    if args.apply and OUTPUT_PATH.exists() and not args.force:
        raise SystemExit(
            f"{OUTPUT_PATH.relative_to(ROOT)} already exists. "
            "Refusing to shift timestamps a second time without --force."
        )

    client = BlogApiClient()
    slugs = updated_slugs()
    if args.skip:
        slugs = slugs[args.skip :]
    if args.limit:
        slugs = slugs[: args.limit]

    restored: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for slug in slugs:
        try:
            remote = fetch(client, slug)
            current = parse_time(str(remote["published_at"]))
            expected_original = current + timedelta(hours=3)
            # The CMS subtracts the application timezone offset from an incoming
            # published_at value on update. Send expected +3h so it stores expected.
            api_input = expected_original + timedelta(hours=3)
            if args.apply:
                payload = preserved_payload(
                    client,
                    remote,
                    translated(remote.get("description")),
                    translated(remote.get("meta_title")),
                    translated(remote.get("meta_description")),
                )
                payload["published_at"] = iso_z(api_input)
                response = client.update_blog(int(remote["id"]), payload)
                if not response.get("success", True):
                    raise RuntimeError(str(response))
                verified = fetch(client, slug)
                stored = parse_time(str(verified["published_at"]))
                if stored != expected_original:
                    raise RuntimeError(
                        f"expected {iso_z(expected_original)}, stored {iso_z(stored)}"
                    )
            restored.append(
                {
                    "slug": slug,
                    "id": int(remote["id"]),
                    "shifted_time": iso_z(current),
                    "restored_time": iso_z(expected_original),
                }
            )
            print(f"{'RESTORED' if args.apply else 'WOULD RESTORE'} {slug}", flush=True)
        except Exception as exc:  # noqa: BLE001
            failed.append({"slug": slug, "error": str(exc)})
            print(f"FAILED {slug}: {exc}", flush=True)

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "selected": len(slugs),
        "restored_count": len(restored) if args.apply else 0,
        "would_restore_count": len(restored) if not args.apply else 0,
        "failed_count": len(failed),
        "restored": restored,
        "failed": failed,
    }
    if args.apply:
        OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in {"restored", "failed"}}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
