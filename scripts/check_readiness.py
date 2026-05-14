"""
Audit FreeIndexer execution readiness without generating images or uploading drafts.

This script is intentionally local-only. It checks files, configs, assets, and
known blockers against system/full-content-flow.md.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def has_placeholders(path: str) -> bool:
    target = ROOT / path
    return (not target.exists()) or ("FILL_IN_" in target.read_text(encoding="utf-8"))


def count_files(path: str, pattern: str) -> int:
    return len(list((ROOT / path).glob(pattern))) if exists(path) else 0


def audit_image() -> list[tuple[str, str]]:
    rows = []
    checks = [
        ("brand file", "images/brand.md"),
        ("template docs", "images/templates"),
        ("exports folder", "images/exports"),
        ("subjects folder", "images/exports/subjects"),
        ("heroes folder", "images/exports/heroes"),
        ("validated folder", "images/exports/validated"),
        ("image guide", "system/how-to-create-image.md"),
        ("generate script", "scripts/generate_image.py"),
        ("hero build script", "scripts/build_hero.py"),
    ]
    for label, path in checks:
        rows.append((label, "present" if exists(path) else f"missing: {path}"))

    rows.append(("template PNG backgrounds", f"{count_files('images/templates', '[1-9].png')} found; required for real heroes"))
    rows.append(("validator overlay PNGs", f"{count_files('images/templates', '*-v.png')} found; required for zone validation"))
    rows.append(("title fonts", f"{count_files('images/templates/fonts', '*.ttf')} found; required for title rendering"))
    rows.append((
        "image provider config",
        "custom config ready"
        if exists("reference/image_provider.json") and not has_placeholders("reference/image_provider.json")
        else "using built-in OpenAI defaults; OPENAI_API_KEY still required for generation",
    ))
    return rows


def audit_blog() -> list[tuple[str, str]]:
    rows = []
    checks = [
        ("reference README", "reference/README.md"),
        ("blog API example", "reference/blog_api.example.json"),
        ("storage example", "reference/hetzner_object_storage.example.json"),
        ("taxonomy", "reference/blog_taxonomy.json"),
        ("live taxonomy", "reference/blog_taxonomy_live.json"),
        ("prepare draft script", "scripts/prepare_blog_draft.py"),
        ("taxonomy sync script", "scripts/sync_blog_taxonomy.py"),
        ("tracker sync script", "scripts/sync_publishing_tracker.py"),
        ("publishing tracker", "pipeline/publishing-tracker.csv"),
    ]
    for label, path in checks:
        rows.append((label, "present" if exists(path) else f"missing: {path}"))

    rows.append(("blog API config", "ready" if exists("reference/blog_api.json") and not has_placeholders("reference/blog_api.json") else "blocked"))
    rows.append(("object storage config", "ready" if exists("reference/hetzner_object_storage.json") and not has_placeholders("reference/hetzner_object_storage.json") else "blocked"))
    return rows


def audit_tracker() -> list[str]:
    tracker = ROOT / "pipeline" / "publishing-tracker.csv"
    if not tracker.exists():
        return ["missing pipeline/publishing-tracker.csv"]
    with tracker.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    missing_articles = [row["article_path"] for row in rows if not (ROOT / row["article_path"]).exists()]
    missing_heroes = [row["hero_image_path"] for row in rows if not (ROOT / row["hero_image_path"]).exists()]
    notes = [f"tracker rows: {len(rows)}"]
    if missing_articles:
        notes.append(f"missing article paths: {len(missing_articles)}")
    if missing_heroes:
        notes.append(f"hero files not generated yet: {len(missing_heroes)}")
    return notes


def print_rows(title: str, rows: list[tuple[str, str]]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for label, status in rows:
        print(f"{label}: {status}")


def main() -> int:
    print_rows("Image readiness", audit_image())
    print_rows("Blog upload readiness", audit_blog())
    print("\nPublishing tracker")
    print("------------------")
    for note in audit_tracker():
        print(note)
    print("\nNo images generated. No uploads attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
