"""
Prepare FreeIndexer blog draft or upload its hero image.

Mirrors: captcharank_content/scripts/prepare_blog_draft.py

TODO integration:
- confirm whether FreeIndexer uses the same 99sync.com API flow
- implement HMAC/auth signing once credentials and endpoint are provided
- implement object storage upload once storage config is provided
- optionally apply Bootstrap 5 HTML post-processing if required

Expected inputs:
- article path under content/
- optional --upload-image

Expected outputs after setup:
- uploaded hero image URL
- draft blog post ID
- publishing tracker update

Required credentials:
- reference/blog_api.json
- reference/hetzner_object_storage.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_API = ROOT / "reference" / "blog_api.json"
STORAGE = ROOT / "reference" / "hetzner_object_storage.json"


def load_required_config(path: Path, example_name: str) -> dict:
    if not path.exists():
        raise SystemExit(
            f"Missing {path.relative_to(ROOT)}. Copy reference/{example_name} and replace FILL_IN_* values."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    serialized = json.dumps(data)
    if "FILL_IN_" in serialized:
        raise SystemExit(f"{path.relative_to(ROOT)} still contains FILL_IN_* placeholders.")
    return data


def load_config_for_dry_run(path: Path, example_name: str) -> tuple[dict, bool]:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data, "FILL_IN_" in json.dumps(data)

    example = ROOT / "reference" / example_name
    if not example.exists():
        raise SystemExit(f"Missing {path.relative_to(ROOT)} and reference/{example_name}.")
    data = json.loads(example.read_text(encoding="utf-8"))
    return data, True


def read_frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, flags=re.M)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def build_draft_payload(article: Path, blog_config: dict) -> dict:
    text = article.read_text(encoding="utf-8")
    slug = read_frontmatter_value(text, "slug") or article.stem
    title = read_frontmatter_value(text, "title")
    description = read_frontmatter_value(text, "description")
    meta_title = read_frontmatter_value(text, "  meta_title") or title
    meta_description = read_frontmatter_value(text, "  meta_description") or description
    upload_mode = blog_config.get("upload_mode", "draft")
    return {
        "mode": upload_mode,
        "title": title,
        "slug": slug,
        "description": description,
        "seo": {
            "meta_title": meta_title,
            "meta_description": meta_description,
        },
        "author_id": blog_config.get("author_id"),
        "blog_domain": blog_config.get("blog_domain"),
        "featured_image_key": f"FILL_AFTER_UPLOAD/{slug}-hero.png",
        "body_source_path": str(article.relative_to(ROOT)),
        "body_format": "markdown",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article_path")
    parser.add_argument("--upload-image", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the expected upload or draft payload without network calls.")
    parser.add_argument("--check-config", action="store_true", help="Validate required local config files and placeholders.")
    args = parser.parse_args()

    article = ROOT / args.article_path
    if not article.exists():
        raise SystemExit(f"Article not found: {args.article_path}")

    if args.upload_image:
        if args.dry_run:
            storage, has_placeholder = load_config_for_dry_run(STORAGE, "hetzner_object_storage.example.json")
        else:
            storage = load_required_config(STORAGE, "hetzner_object_storage.example.json")
            has_placeholder = False
        slug = read_frontmatter_value(article.read_text(encoding="utf-8"), "slug") or article.stem
        convention = storage.get("hero_upload_path_convention", "")
        object_key = convention.replace("{slug}", slug) if convention else f"FILL_IN_PATH/{slug}-hero.png"
        payload = {
            "dry_run_contains_placeholders": has_placeholder,
            "source": str((ROOT / "images" / "exports" / f"{slug}-hero.png").relative_to(ROOT)),
            "bucket": storage.get("bucket"),
            "object_key": object_key,
            "public_url": f"{storage.get('base_public_asset_url', '').rstrip('/')}/{object_key}",
        }
        if args.dry_run or args.check_config:
            print(json.dumps(payload, indent=2))
            return 0
        print("TODO: object storage upload is not implemented until provider details are confirmed.")
        print(json.dumps(payload, indent=2))
        return 2

    if args.dry_run:
        blog_config, has_placeholder = load_config_for_dry_run(BLOG_API, "blog_api.example.json")
    else:
        blog_config = load_required_config(BLOG_API, "blog_api.example.json")
        has_placeholder = False
    payload = build_draft_payload(article, blog_config)
    payload["dry_run_contains_placeholders"] = has_placeholder
    if args.dry_run or args.check_config:
        print(json.dumps(payload, indent=2))
        return 0
    print("TODO: blog draft submission is not implemented until the FreeIndexer blog API contract is confirmed.")
    print(json.dumps(payload, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
