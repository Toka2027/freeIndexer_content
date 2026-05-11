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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("article_path")
    parser.add_argument("--upload-image", action="store_true")
    args = parser.parse_args()

    article = ROOT / args.article_path
    if not article.exists():
        raise SystemExit(f"Article not found: {args.article_path}")

    if args.upload_image:
        load_required_config(STORAGE, "hetzner_object_storage.example.json")
        print("TODO: object storage upload is not implemented until provider details are confirmed.")
        return 2

    load_required_config(BLOG_API, "blog_api.example.json")
    print("TODO: blog draft submission is not implemented until the FreeIndexer blog API contract is confirmed.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

