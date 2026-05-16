"""Publishing helpers for FreeIndexer blog articles."""

from __future__ import annotations

import csv
import json
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

from content_tools import (
    ROOT,
    ArticleFile,
    derive_blog_category_slug,
    derive_blog_tags,
    derive_slug,
    derive_type,
    read_article_file,
    scalar_to_text,
)

REFERENCE_DIR = ROOT / "reference"
TAXONOMY_SPEC_PATH = REFERENCE_DIR / "blog_taxonomy.json"
TAXONOMY_LIVE_PATH = REFERENCE_DIR / "blog_taxonomy_live.json"
S3_CONFIG_PATH = REFERENCE_DIR / "hetzner_object_storage.json"
BLOG_API_BASE_URL = "https://blogs.99sync.com/api"
IMAGE_EXPORTS_ROOT = (
    Path(os.environ["IMAGE_EXPORTS_ROOT"])
    if os.environ.get("IMAGE_EXPORTS_ROOT")
    else ROOT / "images" / "exports"
)
UPLOAD_TRACKER_PATH = ROOT / "pipeline" / "upload-tracker.json"
PUBLISHING_TRACKER_PATH = ROOT / "pipeline" / "publishing-tracker.csv"

CATEGORY_BY_TYPE = {
    "Pillar": ("indexing-education", "Indexing Education"),
    "Commercial Guide": ("indexing-education", "Indexing Education"),
    "Troubleshooting Guide": ("troubleshooting", "Troubleshooting"),
    "Comparison": ("comparisons", "Comparisons"),
    "Buying Guide": ("comparisons", "Comparisons"),
    "Use Case Guide": ("use-cases", "Use Cases"),
    "Workflow Guide": ("use-cases", "Use Cases"),
    "Advanced Workflow Guide": ("use-cases", "Use Cases"),
}

MOJIBAKE_REPLACEMENTS = {
    "\u00e2\u20ac\u201d": "-",
    "\u00e2\u20ac\u201c": "-",
    "\u00e2\u2020\u2019": "->",
    "\u00c3\u2014": "x",
    "\u00e2\u2030\u00a5": ">=",
    "\u00e2\u2030\u00a4": "<=",
    "\u00e2\u20ac\u02dc": "'",
    "\u00e2\u20ac\u2122": "'",
    "\u00e2\u20ac\u0153": '"',
    "\u00e2\u20ac\u009d": '"',
}


def sanitize_text(text: str) -> str:
    result = text
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        result = result.replace(bad, good)
    return result


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_s3_config() -> dict[str, Any]:
    data = load_json(S3_CONFIG_PATH, {})
    if "FILL_IN_" in json.dumps(data):
        raise SystemExit("reference/hetzner_object_storage.json still contains FILL_IN_* placeholders.")
    required = ("bucket", "access_key", "secret_key")
    missing = [key for key in required if not data.get(key)]
    if not (data.get("base_public_asset_url") or data.get("public_url_base") or data.get("base_url")):
        missing.append("base_public_asset_url")
    if not (data.get("endpoint_url") or data.get("endpoint") or data.get("region")):
        missing.append("endpoint_url or region")
    if missing:
        raise SystemExit(f"Missing object storage config values: {', '.join(missing)}")
    return data


def load_taxonomy_spec() -> dict[str, Any]:
    return load_json(TAXONOMY_SPEC_PATH, {"categories": [], "tags": []})


def public_s3_url(key: str, config: dict[str, Any] | None = None) -> str:
    cfg = config or load_s3_config()
    base = (
        cfg.get("public_url_base")
        or cfg.get("base_public_asset_url")
        or cfg.get("base_url")
        or ""
    )
    base = str(base).rstrip("/")
    if not base:
        return key
    return f"{base}/{quote(key.lstrip('/'), safe='/')}"


def resolve_hero_image_source_path(slug: str) -> Path:
    return IMAGE_EXPORTS_ROOT / f"{slug}-hero.png"


def resolve_featured_image_key(slug: str, config: dict[str, Any] | None = None) -> str:
    cfg = config or load_json(S3_CONFIG_PATH, {})
    convention = (
        cfg.get("hero_upload_path_convention")
        or cfg.get("featured_image_key_pattern")
        or cfg.get("path_convention")
        or "freeindexer/blog/{slug}-hero.png"
    )
    return str(convention).replace("{slug}", slug).lstrip("/")


def featured_image_alt(article_title: str) -> str:
    return f"Hero image for {article_title}"


def load_slug_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in (ROOT / "content").rglob("*.md"):
        article = read_article_file(path)
        slug = derive_slug(article)
        if slug:
            mapping[path.relative_to(ROOT).as_posix()] = slug
            mapping[path.name] = slug
    return mapping


def derive_blog_category(article: ArticleFile) -> dict[str, str]:
    taxonomy = load_taxonomy_spec()
    valid = {item["slug"]: item["name"] for item in taxonomy.get("categories", [])}
    category_slug = derive_blog_category_slug(article)
    if category_slug and category_slug in valid:
        return {"slug": category_slug, "name": valid[category_slug]}
    fallback = CATEGORY_BY_TYPE.get(derive_type(article), ("indexing-education", "Indexing Education"))
    return {"slug": fallback[0], "name": fallback[1]}


def resolve_category_id(category_slug: str, taxonomy_live: dict[str, Any]) -> int | None:
    categories = taxonomy_live.get("categories") or {}
    if isinstance(categories, dict):
        value = categories.get(category_slug)
        return int(value) if value else None
    return None


def resolve_tag_ids(tag_slugs: list[str], taxonomy_live: dict[str, Any]) -> list[int]:
    tags_live = taxonomy_live.get("tags") or {}
    ids: list[int] = []
    if not isinstance(tags_live, dict):
        return ids
    for slug in tag_slugs:
        tag_id = tags_live.get(slug)
        if tag_id:
            ids.append(int(tag_id))
    return ids


def validate_taxonomy_ids(article: ArticleFile, taxonomy_live: dict[str, Any]) -> None:
    category = derive_blog_category(article)
    category_id = resolve_category_id(category["slug"], taxonomy_live)
    if not category_id:
        raise SystemExit(
            f"Category '{category['slug']}' is not synced. Run scripts/sync_blog_taxonomy.py before publishing."
        )
    missing_tags = [
        slug
        for slug in derive_blog_tags(article)
        if slug and slug not in (taxonomy_live.get("tags") or {})
    ]
    if missing_tags:
        raise SystemExit(
            "Tag IDs missing from reference/blog_taxonomy_live.json: "
            + ", ".join(missing_tags)
            + ". Run scripts/sync_blog_taxonomy.py before publishing."
        )


def load_upload_tracker() -> dict[str, Any]:
    return load_json(UPLOAD_TRACKER_PATH, {})


def save_upload_tracker(tracker: dict[str, Any]) -> None:
    UPLOAD_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_TRACKER_PATH.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")


def record_uploaded_image(slug: str, public_url: str, object_key: str) -> None:
    tracker = load_upload_tracker()
    tracker[slug] = {"public_url": public_url, "object_key": object_key}
    save_upload_tracker(tracker)
    update_publishing_tracker(slug, {"uploaded_image_url": public_url})


def resolve_article_path_for_slug(slug: str) -> str:
    for path in sorted((ROOT / "content").rglob("*.md")):
        article = read_article_file(path)
        if derive_slug(article) == slug:
            return path.relative_to(ROOT).as_posix()
    return ""


def default_publishing_tracker_row(slug: str, fieldnames: list[str]) -> dict[str, str]:
    row = {field: "" for field in fieldnames}
    row["slug"] = slug
    if "article_path" in row:
        row["article_path"] = resolve_article_path_for_slug(slug)
    if "hero_image_path" in row:
        row["hero_image_path"] = f"images/exports/{slug}-hero.png"
    return row


def update_publishing_tracker(slug: str, updates: dict[str, Any]) -> None:
    if not PUBLISHING_TRACKER_PATH.exists():
        return
    with PUBLISHING_TRACKER_PATH.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    changed = False
    for key in updates:
        if key not in fieldnames:
            fieldnames.append(key)
    for row in rows:
        row.pop(None, None)
        if row.get("slug") == slug:
            for key, value in updates.items():
                row[key] = scalar_to_text(value)
            changed = True
            break
    if not changed:
        row = default_publishing_tracker_row(slug, fieldnames)
        for key, value in updates.items():
            row[key] = scalar_to_text(value)
        rows.append(row)
        changed = True
    with PUBLISHING_TRACKER_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upload_file_to_object_storage(source_path: Path, object_key: str, dry_run: bool = False) -> str:
    cfg = load_s3_config()
    public_url = public_s3_url(object_key, cfg)
    if dry_run:
        return public_url

    endpoint_url = cfg.get("endpoint_url") or cfg.get("endpoint")
    if not endpoint_url and cfg.get("region"):
        endpoint_url = f"https://{cfg['region']}.your-objectstorage.com"

    import boto3  # type: ignore

    client_kwargs = {
        "aws_access_key_id": cfg["access_key"],
        "aws_secret_access_key": cfg["secret_key"],
    }
    if endpoint_url:
        client_kwargs["endpoint_url"] = str(endpoint_url)
    if cfg.get("region"):
        client_kwargs["region_name"] = str(cfg["region"])

    s3 = boto3.client("s3", **client_kwargs)
    content_type, _ = mimetypes.guess_type(str(source_path))
    extra_args: dict[str, str] = {"ContentType": content_type or "image/png"}
    if cfg.get("acl", "public-read"):
        extra_args["ACL"] = str(cfg.get("acl", "public-read"))
    s3.upload_file(str(source_path), str(cfg["bucket"]), object_key, ExtraArgs=extra_args)
    return public_url
