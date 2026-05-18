"""Prepare, upload, and submit a FreeIndexer blog draft.

This is the FreeIndexer adaptation of the CaptchaRank publishing engine:
markdown article -> Bootstrap-friendly HTML -> hero upload -> signed 99sync
draft create/update.

Examples:
    python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --dry-run
    python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image --dry-run
    python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image
    python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blog_api_client import (
    BlogApiClient,
    has_placeholders,
    load_blog_api_config,
    resolve_blog_api_config_path,
    validate_blog_api_config,
)
from blog_tools import (
    S3_CONFIG_PATH,
    TAXONOMY_LIVE_PATH,
    load_json,
    load_s3_config,
    load_upload_tracker,
    public_s3_url,
    record_uploaded_image,
    resolve_category_id,
    resolve_featured_image_key,
    resolve_hero_image_source_path,
    resolve_tag_ids,
    sanitize_text,
    update_publishing_tracker,
    upload_file_to_object_storage,
    validate_taxonomy_ids,
    derive_blog_category,
)
from content_tools import (
    BLOG_BASE_URL,
    ROOT,
    derive_blog_tags,
    derive_description,
    derive_meta_description,
    derive_meta_title,
    derive_slug,
    derive_title,
    normalize_blog_target_page,
    read_article_file,
)

BLOG_API_EXAMPLE_PATH = ROOT / "reference" / "blog_api.example.json"
STORAGE_EXAMPLE_PATH = ROOT / "reference" / "hetzner_object_storage.example.json"

QUALITY_CHECKS = [
    "search_intent_match",
    "icp_fit",
    "topic_specific_depth",
    "usefulness",
    "originality",
    "practical_examples",
    "clean_layout",
    "natural_freeindexer_mention",
    "internal_links",
    "seo_metadata",
    "no_unsupported_claims",
]


def slugify(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    return normalized.strip("-")


def safe_int(value: object, default: int = 0) -> int | object:
    if value in (None, ""):
        return default
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return value


def add_classes(tag: Any, classes: list[str]) -> None:
    existing = tag.get("class", []) or []
    if isinstance(existing, str):
        existing = existing.split()
    for cls in classes:
        if cls not in existing:
            existing.append(cls)
    tag["class"] = existing


def has_css_class(value: Any, class_name: str) -> bool:
    if not value:
        return False
    if isinstance(value, str):
        return class_name in value.split()
    try:
        return class_name in value
    except TypeError:
        return False


def build_toc(soup: Any) -> Any | None:
    from bs4 import BeautifulSoup

    headings = soup.find_all(["h2", "h3"])
    if not headings:
        return None

    toc_soup = BeautifulSoup("", "html.parser")
    nav = toc_soup.new_tag("nav")
    nav["aria-label"] = "Table of contents"
    nav["class"] = "article-toc"

    title_p = toc_soup.new_tag("p")
    strong = toc_soup.new_tag("strong")
    strong.string = "Contents"
    title_p.append(strong)
    nav.append(title_p)

    top_ul = toc_soup.new_tag("ul")
    nav.append(top_ul)

    current_h2_li = None
    current_nested_ul = None
    used_ids: dict[str, int] = {}

    for heading in headings:
        base_id = heading.get("id") or slugify(heading.get_text(" ", strip=True)) or str(heading.name)
        used_ids[base_id] = used_ids.get(base_id, 0) + 1
        heading_id = base_id if used_ids[base_id] == 1 else f"{base_id}-{used_ids[base_id]}"
        heading["id"] = heading_id

        li = toc_soup.new_tag("li")
        link = toc_soup.new_tag("a", href=f"#{heading_id}")
        link.string = heading.get_text(" ", strip=True)
        li.append(link)

        if heading.name == "h2":
            top_ul.append(li)
            current_h2_li = li
            current_nested_ul = None
        elif current_h2_li is None:
            top_ul.append(li)
        else:
            if current_nested_ul is None:
                current_nested_ul = toc_soup.new_tag("ul")
                current_h2_li.append(current_nested_ul)
            current_nested_ul.append(li)

    return nav


def apply_bootstrap_classes(soup: Any) -> None:
    """Apply Bootstrap 5 classes without overwriting existing classes."""

    for table in soup.find_all("table"):
        if table.find_parent("div", class_="table-responsive"):
            continue
        add_classes(table, ["table", "table-striped", "table-hover", "align-middle"])
        wrapper = soup.new_tag("div")
        wrapper["class"] = ["table-responsive", "my-4", "shadow-sm", "rounded"]
        table.wrap(wrapper)

    for img in soup.find_all("img"):
        add_classes(img, ["img-fluid", "rounded", "shadow-sm", "my-3"])

    for bq in soup.find_all("blockquote"):
        if bq.find_parent(class_=lambda c: has_css_class(c, "alert")):
            continue
        add_classes(
            bq,
            [
                "blockquote",
                "border-start",
                "border-3",
                "border-primary",
                "ps-3",
                "py-2",
                "my-3",
                "text-muted",
            ],
        )

    for pre in soup.find_all("pre"):
        add_classes(pre, ["bg-dark", "text-light", "p-3", "rounded", "overflow-auto", "my-3"])

    for nav in soup.find_all("nav", class_="article-toc"):
        add_classes(nav, ["card", "bg-light", "border-0", "p-3", "my-4", "shadow-sm"])

    for h2 in soup.find_all("h2"):
        add_classes(h2, ["mt-5", "mb-3"])
    for h3 in soup.find_all("h3"):
        add_classes(h3, ["mt-4", "mb-2"])


def article_to_html(article_path: Path, bootstrap5: bool = True) -> str:
    from bs4 import BeautifulSoup
    import markdown

    article = read_article_file(article_path)
    body_md = article.body.strip()

    # The API receives the title separately, so keep inline H1s out of the body.
    body_md = re.sub(r"^#\s+.+\n?", "", body_md, count=1, flags=re.MULTILINE).lstrip()

    html_body = markdown.markdown(
        body_md,
        extensions=["tables", "fenced_code", "codehilite", "toc", "md_in_html"],
        extension_configs={"codehilite": {"css_class": "highlight"}},
    )

    soup = BeautifulSoup(html_body, "html.parser")
    for h1 in soup.find_all("h1"):
        h1.decompose()

    toc = build_toc(soup)
    if toc:
        first_p = next(
            (
                p
                for p in soup.find_all("p")
                if not p.find_parent(["blockquote", "aside", "nav"])
                and not p.find_parent(class_=lambda c: has_css_class(c, "alert"))
            ),
            None,
        )
        if first_p:
            first_p.insert_after(toc)
        else:
            soup.insert(0, toc)

    if bootstrap5:
        apply_bootstrap_classes(soup)

    html_str = sanitize_text(str(soup))
    return f'<article class="freeindexer-article">\n{html_str}\n</article>'


def load_config_for_dry_run(path: Path, example_path: Path) -> tuple[dict[str, Any], bool, str]:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data, has_placeholders(data), path.relative_to(ROOT).as_posix()
    if not example_path.exists():
        return {}, True, example_path.relative_to(ROOT).as_posix()
    data = json.loads(example_path.read_text(encoding="utf-8-sig"))
    return data, True, example_path.relative_to(ROOT).as_posix()


def load_api_config_for_build(dry_run: bool) -> tuple[dict[str, Any], bool, str]:
    config_path = resolve_blog_api_config_path()
    if dry_run:
        return load_config_for_dry_run(config_path, BLOG_API_EXAMPLE_PATH)
    if not config_path.exists():
        raise SystemExit(
            "Missing reference/blog_api.json. Copy reference/blog_api.example.json and add FreeIndexer blog values."
        )
    api_config = load_blog_api_config(config_path)
    validate_blog_api_config(api_config)
    return api_config, False, config_path.relative_to(ROOT).as_posix()


def load_storage_config_for_dry_run() -> tuple[dict[str, Any], bool, str]:
    return load_config_for_dry_run(S3_CONFIG_PATH, STORAGE_EXAMPLE_PATH)


def load_taxonomy_live() -> dict[str, Any]:
    return load_json(TAXONOMY_LIVE_PATH, {"status": "not-synced", "categories": {}, "tags": {}})


def taxonomy_warnings(article_path: Path, taxonomy_live: dict[str, Any]) -> list[str]:
    article = read_article_file(article_path)
    warnings: list[str] = []
    category = derive_blog_category(article)
    if not resolve_category_id(category["slug"], taxonomy_live):
        warnings.append(f"category '{category['slug']}' has no live ID; run scripts/sync_blog_taxonomy.py")
    missing_tags = [
        slug
        for slug in derive_blog_tags(article)
        if slug and slug not in (taxonomy_live.get("tags") or {})
    ]
    if missing_tags:
        warnings.append("tag IDs missing: " + ", ".join(missing_tags))
    return warnings


def resolve_featured_image_url(slug: str, dry_run: bool, storage_config: dict[str, Any] | None = None) -> str:
    tracker = load_upload_tracker()
    tracked_url = tracker.get(slug, {}).get("public_url", "")
    if tracked_url:
        return tracked_url

    hero_path = resolve_hero_image_source_path(slug)
    if not hero_path.exists() and not dry_run:
        return ""

    object_key = resolve_featured_image_key(slug, storage_config)
    if dry_run and storage_config is not None:
        return public_s3_url(object_key, storage_config)
    return public_s3_url(object_key)


def build_payload(
    article_path: Path,
    featured_image_url: str,
    api_config: dict[str, Any],
    taxonomy_live: dict[str, Any],
    status: str = "draft",
    published_at: str = "",
    bootstrap5: bool = True,
) -> dict[str, Any]:
    article = read_article_file(article_path)
    slug = derive_slug(article)
    title = derive_title(article)
    description = derive_description(article)
    meta_title = derive_meta_title(article)
    meta_description = derive_meta_description(article)
    blog_cat = derive_blog_category(article)
    tag_slugs = derive_blog_tags(article)

    category_id = resolve_category_id(blog_cat["slug"], taxonomy_live)
    tag_ids = resolve_tag_ids(tag_slugs, taxonomy_live)

    payload: dict[str, Any] = {
        "application_id": safe_int(api_config.get("application_id"), 0),
        "application_admin_id": None,
        "category_id": category_id,
        "author_id": safe_int(api_config.get("author_id"), 0),
        "title": title,
        "slug": slug,
        "content": article_to_html(article_path, bootstrap5=bootstrap5),
        "featured_image": featured_image_url,
        "allow_comments": False,
        "comment_default_status": "pending",
        "status": status,
        "meta_title": meta_title,
        "meta_description": meta_description,
        "description": description or meta_description,
        "tags": tag_ids,
    }
    if published_at:
        payload["published_at"] = published_at
    return payload


def enforce_quality_gate(article_path: Path) -> None:
    article = read_article_file(article_path)
    quality = article.frontmatter_data.get("content_quality")
    if not isinstance(quality, dict):
        raise SystemExit(
            f"{article.relative_path}: missing content_quality frontmatter. "
            "Score the article with system/editorial-checklist.md before upload."
        )

    raw_score = quality.get("score")
    try:
        score = float(str(raw_score))
    except (TypeError, ValueError):
        raise SystemExit(f"{article.relative_path}: content_quality.score must be numeric.") from None
    if score < 9:
        raise SystemExit(
            f"{article.relative_path}: content_quality.score is {score:g}. "
            "Do not upload articles below 9/10."
        )

    depth_elements = quality.get("depth_elements")
    if not isinstance(depth_elements, list) or len(depth_elements) < 3:
        raise SystemExit(
            f"{article.relative_path}: content_quality.depth_elements must include at least 3 items."
        )

    checks = quality.get("checks")
    if not isinstance(checks, dict):
        raise SystemExit(f"{article.relative_path}: content_quality.checks is required.")
    missing = [name for name in QUALITY_CHECKS if checks.get(name) is not True]
    if missing:
        raise SystemExit(
            f"{article.relative_path}: quality checks must be true before upload: "
            + ", ".join(missing)
        )


def upload_image(slug: str, dry_run: bool = False) -> str:
    hero_path = resolve_hero_image_source_path(slug)
    if dry_run:
        storage_config, storage_has_placeholders, storage_source = load_storage_config_for_dry_run()
        object_key = resolve_featured_image_key(slug, storage_config)
        public_url = public_s3_url(object_key, storage_config)
        report = {
            "dry_run": True,
            "config_source": storage_source,
            "config_contains_placeholders": storage_has_placeholders,
            "source": hero_path.relative_to(ROOT).as_posix(),
            "source_exists": hero_path.exists(),
            "bucket": storage_config.get("bucket"),
            "object_key": object_key,
            "public_url": public_url,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return public_url

    if not hero_path.exists():
        raise SystemExit(f"Hero image not found: {hero_path.relative_to(ROOT).as_posix()}")

    object_key = resolve_featured_image_key(slug)
    public_url = upload_file_to_object_storage(hero_path, object_key, dry_run=False)
    record_uploaded_image(slug, public_url, object_key)
    print(f"Uploaded hero: {object_key}")
    print(f"Image URL: {public_url}")
    return public_url


def get_existing_blog_id(client: BlogApiClient, slug: str) -> int | None:
    existing_resp = client.list_blogs(slug=slug, per_page="1")
    data = existing_resp.get("data", [])
    if isinstance(data, dict):
        items = data.get("data", [])
    else:
        items = data
    if not items:
        return None
    return int(items[0]["id"])


def extract_response_post(resp: dict[str, Any]) -> dict[str, Any]:
    data = resp.get("data") or {}
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and data:
        first = data[0]
        return first if isinstance(first, dict) else {}
    return {}


def submit_payload(client: BlogApiClient, payload: dict[str, Any]) -> dict[str, Any]:
    slug = str(payload["slug"])
    existing_id = get_existing_blog_id(client, slug)
    if existing_id:
        print(f"Updating blog draft id={existing_id} slug={slug}")
        return client.update_blog(existing_id, payload)
    print(f"Creating blog draft slug={slug}")
    return client.create_blog(payload)


def check_config(article_path: Path | None = None) -> int:
    statuses: dict[str, Any] = {}
    exit_code = 0

    api_path = resolve_blog_api_config_path()
    if not api_path.exists():
        statuses["blog_api"] = {
            "status": "blocked",
            "reason": "missing reference/blog_api.json",
            "example": BLOG_API_EXAMPLE_PATH.relative_to(ROOT).as_posix(),
        }
        exit_code = 2
    else:
        try:
            api_config = load_blog_api_config(api_path)
            validate_blog_api_config(api_config)
            statuses["blog_api"] = {
                "status": "ready",
                "config": api_path.relative_to(ROOT).as_posix(),
                "base_url": api_config.get("base_url"),
                "api_flow": api_config.get("api_flow", "99sync"),
            }
        except SystemExit as exc:
            statuses["blog_api"] = {"status": "blocked", "reason": str(exc)}
            exit_code = 2

    if not S3_CONFIG_PATH.exists():
        statuses["object_storage"] = {
            "status": "blocked",
            "reason": "missing reference/hetzner_object_storage.json",
            "example": STORAGE_EXAMPLE_PATH.relative_to(ROOT).as_posix(),
        }
        exit_code = 2
    else:
        try:
            storage_config = load_s3_config()
            statuses["object_storage"] = {
                "status": "ready",
                "bucket": storage_config.get("bucket"),
                "endpoint_url": storage_config.get("endpoint_url") or storage_config.get("endpoint"),
                "base_public_asset_url": storage_config.get("base_public_asset_url")
                or storage_config.get("public_url_base"),
                "hero_upload_path_convention": storage_config.get("hero_upload_path_convention")
                or storage_config.get("featured_image_key_pattern")
                or storage_config.get("path_convention"),
            }
        except SystemExit as exc:
            statuses["object_storage"] = {"status": "blocked", "reason": str(exc)}
            exit_code = 2

    taxonomy_live = load_taxonomy_live()
    statuses["taxonomy_live"] = {
        "status": taxonomy_live.get("status", "unknown"),
        "categories": len(taxonomy_live.get("categories") or {}),
        "tags": len(taxonomy_live.get("tags") or {}),
    }

    if article_path is not None:
        article = read_article_file(article_path)
        slug = derive_slug(article)
        statuses["article"] = {
            "slug": slug,
            "hero_exists": resolve_hero_image_source_path(slug).exists(),
            "taxonomy_warnings": taxonomy_warnings(article_path, taxonomy_live),
        }
        if statuses["article"]["taxonomy_warnings"]:
            exit_code = 2

    print(json.dumps(statuses, indent=2, ensure_ascii=False))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or submit a FreeIndexer blog draft.")
    parser.add_argument("article", nargs="?", help="Path to article markdown file")
    parser.add_argument("--dry-run", action="store_true", help="Build payload but do not upload or submit.")
    parser.add_argument("--upload-image", action="store_true", help="Upload the canonical hero image and exit.")
    parser.add_argument("--check-config", action="store_true", help="Validate local API, storage, and taxonomy config.")
    parser.add_argument("--show-html", action="store_true", help="Print generated HTML and exit.")
    parser.add_argument("--status", choices=["draft", "published", "scheduled"], help="Override upload mode.")
    parser.add_argument("--published-at", default="", help="ISO timestamp, for scheduled/published posts.")
    args = parser.parse_args()

    article_path: Path | None = None
    if args.article:
        article_path = Path(args.article)
        if not article_path.is_absolute():
            article_path = ROOT / article_path
        if not article_path.exists():
            raise SystemExit(f"Article not found: {article_path}")

    if args.check_config:
        return check_config(article_path)

    if article_path is None:
        parser.error("article is required unless --check-config is used")

    article = read_article_file(article_path)
    slug = derive_slug(article)

    if args.show_html:
        api_config, _, _ = load_api_config_for_build(dry_run=True)
        bootstrap5 = bool(api_config.get("bootstrap5_post_processing_required", True))
        print(article_to_html(article_path, bootstrap5=bootstrap5))
        return 0

    if args.upload_image:
        if not args.dry_run:
            enforce_quality_gate(article_path)
        upload_image(slug, dry_run=args.dry_run)
        return 0

    api_config, api_has_placeholders, api_source = load_api_config_for_build(dry_run=args.dry_run)
    storage_config = None
    storage_has_placeholders = False
    storage_source = ""
    if args.dry_run:
        storage_config, storage_has_placeholders, storage_source = load_storage_config_for_dry_run()

    taxonomy_live = load_taxonomy_live()
    if not args.dry_run:
        enforce_quality_gate(article_path)
        validate_taxonomy_ids(article, taxonomy_live)

    upload_mode = str(api_config.get("upload_mode") or "draft")
    status = args.status or upload_mode
    bootstrap5 = bool(api_config.get("bootstrap5_post_processing_required", True))
    featured_image_url = resolve_featured_image_url(slug, dry_run=args.dry_run, storage_config=storage_config)

    payload = build_payload(
        article_path=article_path,
        featured_image_url=featured_image_url,
        api_config=api_config,
        taxonomy_live=taxonomy_live,
        status=status,
        published_at=args.published_at,
        bootstrap5=bootstrap5,
    )

    if args.dry_run:
        target_page = normalize_blog_target_page("", slug)
        report = {
            "dry_run": True,
            "api_config_source": api_source,
            "api_config_contains_placeholders": api_has_placeholders,
            "storage_config_source": storage_source,
            "storage_config_contains_placeholders": storage_has_placeholders,
            "taxonomy_status": taxonomy_live.get("status", "unknown"),
            "warnings": taxonomy_warnings(article_path, taxonomy_live),
            "expected_blog_url": target_page or f"{BLOG_BASE_URL.rstrip('/')}/{slug}",
            "payload": payload,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    client = BlogApiClient(config=api_config)
    resp = submit_payload(client, payload)
    if not resp.get("success", True) and "data" not in resp:
        raise RuntimeError(f"Blog API error for {slug}: {resp}")

    post = extract_response_post(resp)
    post_id = post.get("id") or post.get("blog_id") or ""
    published_url = (
        post.get("url")
        or post.get("public_url")
        or post.get("permalink")
        or normalize_blog_target_page("", slug)
    )
    update_publishing_tracker(
        slug,
        {
            "draft_status": status,
            "blog_post_id": post_id,
            "published_url": published_url,
            "live_date": args.published_at if status == "scheduled" else "",
            "notes": "Draft synced through signed 99sync API.",
        },
    )
    print(f"OK: {resp.get('message', 'draft synced')}")
    if post_id:
        print(f"Blog post ID: {post_id}")
    if published_url:
        print(f"Blog URL: {published_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
