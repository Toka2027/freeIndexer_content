"""Create or refresh FreeIndexer blog taxonomy through the 99sync API."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blog_api_client import BlogApiClient, load_blog_api_config, validate_blog_api_config

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_SPEC_PATH = ROOT / "reference" / "blog_taxonomy.json"
TAXONOMY_LIVE_PATH = ROOT / "reference" / "blog_taxonomy_live.json"
BLOG_API_PATH = ROOT / "reference" / "blog_api.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_taxonomy_live(live: dict[str, Any]) -> None:
    TAXONOMY_LIVE_PATH.write_text(json.dumps(live, indent=2, ensure_ascii=False), encoding="utf-8")


def unwrap_localized(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("en") or next(iter(value.values()), ""))
    return str(value or "")


def truncate(value: str, limit: int = 255) -> str:
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def validate_taxonomy(taxonomy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for group in ("categories", "tags"):
        seen: set[str] = set()
        for item in taxonomy.get(group, []):
            slug = str(item.get("slug", "")).strip()
            name = str(item.get("name", "")).strip()
            if not slug:
                errors.append(f"{group}: item missing slug")
            if not name:
                errors.append(f"{group}: {slug or '[missing slug]'} missing name")
            if slug in seen:
                errors.append(f"{group}: duplicate slug {slug}")
            seen.add(slug)
    return errors


def derive_category_meta(name: str, description: str) -> tuple[str, str]:
    return (
        truncate(f"{name} | FreeIndexer"),
        truncate(description or f"{name} articles from FreeIndexer."),
    )


def derive_tag_meta(name: str, group: str) -> tuple[str, str, str]:
    descriptions = {
        "topic": f"FreeIndexer articles about {name.lower()} workflows, checks, and expectations.",
        "workflow": f"Workflow guides for {name.lower()} with FreeIndexer.",
        "audience": f"FreeIndexer guidance for {name.lower()} and related SEO operators.",
        "product": f"FreeIndexer product and workflow articles related to {name.lower()}.",
        "comparison": f"Comparisons and buying guidance for {name.lower()}.",
        "content-type": f"{name} articles from the FreeIndexer content library.",
        "technical-seo": f"Technical SEO checks and diagnostics for {name.lower()}.",
        "commercial": f"Commercial evaluation and pricing guidance for FreeIndexer workflows.",
    }
    description = truncate(descriptions.get(group, f"{name} articles from FreeIndexer."))
    meta_title = truncate(f"{name} | FreeIndexer")
    meta_description = truncate(description)
    return description, meta_title, meta_description


def fetch_existing(client: BlogApiClient) -> tuple[dict[str, int], dict[str, int]]:
    cats_resp = client.list_categories()
    cats_data = cats_resp.get("data") or []
    if isinstance(cats_data, dict):
        cats_data = cats_data.get("data", [])
    existing_cats = {unwrap_localized(cat.get("slug")): int(cat["id"]) for cat in cats_data if cat.get("id")}

    tags_resp = client.list_tags()
    tags_data = tags_resp.get("data") or []
    if isinstance(tags_data, dict):
        tags_data = tags_data.get("data", [])
    existing_tags = {unwrap_localized(tag.get("slug")): int(tag["id"]) for tag in tags_data if tag.get("id")}
    return existing_cats, existing_tags


def print_offline_dry_run(taxonomy: dict[str, Any], reason: str) -> None:
    print(reason)
    print("Dry-run taxonomy plan without live API lookup:")
    print("\nCategories")
    for cat in taxonomy.get("categories", []):
        print(f"  would create or update category {cat['slug']}")
    print("\nTags")
    for tag in taxonomy.get("tags", []):
        print(f"  would create or update tag {tag['slug']}")
    print("\nDry run complete. No taxonomy IDs written.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync FreeIndexer blog categories and tags.")
    parser.add_argument("--dry-run", action="store_true", help="Preview intended sync without API writes.")
    parser.add_argument("--validate-only", action="store_true", help="Validate taxonomy JSON only.")
    args = parser.parse_args()

    taxonomy = load_json(TAXONOMY_SPEC_PATH, {})
    errors = validate_taxonomy(taxonomy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"taxonomy: {len(taxonomy.get('categories', []))} categories, {len(taxonomy.get('tags', []))} tags")
    if args.validate_only:
        print("taxonomy validation passed")
        return 0

    if not BLOG_API_PATH.exists():
        if args.dry_run:
            print_offline_dry_run(
                taxonomy,
                "reference/blog_api.json is missing, so live existing IDs were not checked.",
            )
            return 0
        print("Blocked: missing reference/blog_api.json.")
        print("Copy reference/blog_api.example.json and add FreeIndexer application_id, author_id, api_key, secret_key, and blog_domain.")
        return 2

    config = load_blog_api_config(BLOG_API_PATH)
    try:
        validate_blog_api_config(config)
    except SystemExit as exc:
        if args.dry_run:
            print_offline_dry_run(taxonomy, str(exc))
            return 0
        print(exc)
        return 2

    client = BlogApiClient(config=config)
    print("Fetching existing categories and tags...")
    existing_cats, existing_tags = fetch_existing(client)
    live: dict[str, Any] = {"status": "synced" if not args.dry_run else "dry-run", "categories": {}, "tags": {}}

    print("\nCategories")
    for cat in taxonomy.get("categories", []):
        slug = cat["slug"]
        name = cat["name"]
        description = truncate(cat.get("description", ""))
        meta_title, meta_description = derive_category_meta(name, description)
        if slug in existing_cats:
            cat_id = existing_cats[slug]
            live["categories"][slug] = cat_id
            if args.dry_run:
                print(f"  would update category {slug} (id={cat_id})")
            else:
                client.update_category(cat_id, name, slug, description, meta_title, meta_description)
                print(f"  updated {slug} -> id={cat_id}")
                time.sleep(0.25)
        elif args.dry_run:
            print(f"  would create category {slug}")
        else:
            resp = client.create_category(name, slug, description, meta_title, meta_description)
            cat_id = (resp.get("data") or {}).get("id")
            if not cat_id:
                raise RuntimeError(f"Unexpected create_category response for {slug}: {resp}")
            live["categories"][slug] = int(cat_id)
            print(f"  created {slug} -> id={cat_id}")
            time.sleep(0.25)

    print("\nTags")
    for tag in taxonomy.get("tags", []):
        slug = tag["slug"]
        name = tag["name"]
        group = tag.get("group", "")
        description, meta_title, meta_description = derive_tag_meta(name, group)
        if slug in existing_tags:
            tag_id = existing_tags[slug]
            live["tags"][slug] = tag_id
            if args.dry_run:
                print(f"  would update tag {slug} (id={tag_id})")
            else:
                client.update_tag(tag_id, name, slug, description, meta_title, meta_description)
                print(f"  updated {slug} -> id={tag_id}")
                time.sleep(0.25)
        elif args.dry_run:
            print(f"  would create tag {slug}")
        else:
            resp = client.create_tag(name, slug, description, meta_title, meta_description)
            tag_id = (resp.get("data") or {}).get("id")
            if not tag_id:
                raise RuntimeError(f"Unexpected create_tag response for {slug}: {resp}")
            live["tags"][slug] = int(tag_id)
            print(f"  created {slug} -> id={tag_id}")
            time.sleep(0.25)

    if args.dry_run:
        print("\nDry run complete. No taxonomy IDs written.")
        return 0

    save_taxonomy_live(live)
    print(f"\nSaved {TAXONOMY_LIVE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
