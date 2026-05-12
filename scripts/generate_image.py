"""
Generate a FreeIndexer subject image prompt and expected output.

Mirrors: captcharank_content/scripts/generate_image.py

TODO integration:
- connect to the approved image generation provider
- read API key from the approved secrets location
- write PNG output to images/exports/subjects/{slug}-subject.png

Expected inputs:
- --slug article slug
- optional --prompt-only
- optional --quality

Expected output:
- images/exports/subjects/{slug}-subject.png

Required credentials:
- image provider API key, not yet selected/provided
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
IMAGE_CONFIG = ROOT / "reference" / "image_provider.json"
IMAGE_CONFIG_EXAMPLE = ROOT / "reference" / "image_provider.example.json"


def find_article(slug: str) -> Path:
    matches = list(CONTENT_DIR.rglob(f"{slug}.md"))
    if not matches:
        raise SystemExit(f"Article not found for slug: {slug}")
    return matches[0]


def read_field(text: str, field: str) -> str:
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.M)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def build_prompt(article_path: Path) -> str:
    text = article_path.read_text(encoding="utf-8")
    title = read_field(text, "title")
    icp = read_field(text, "icp")
    article_type = read_field(text, "type")

    return (
        "Create a clean product-style subject image for a FreeIndexer blog hero. "
        f"Article title: {title}. Primary reader: {icp}. Article type: {article_type}. "
        "Visual theme: SEO indexing workflow, URL submission queue, backlink discovery, "
        "search discovery dashboard, browser interface abstraction. Use blue, green, white, "
        "and slate tones. No real Google logo, no fake official Search Console screenshot, "
        "no 100% indexed claim, no guaranteed rankings, no exaggerated growth chart. "
        "No text inside the subject image except generic UI labels like Submitted, Pending, "
        "Discovered, Queue."
    )


def load_image_config() -> dict:
    if not IMAGE_CONFIG.exists():
        raise SystemExit(
            "Image generation is blocked: missing reference/image_provider.json. "
            "Copy reference/image_provider.example.json and replace FILL_IN_* values."
        )
    data = json.loads(IMAGE_CONFIG.read_text(encoding="utf-8"))
    serialized = json.dumps(data)
    if "FILL_IN_" in serialized:
        raise SystemExit("Image generation is blocked: reference/image_provider.json still contains FILL_IN_* placeholders.")

    api_key_env = data.get("api_key_env", "")
    api_key = data.get("api_key", "")
    if api_key_env and not os.getenv(api_key_env) and not api_key:
        raise SystemExit(
            f"Image generation is blocked: environment variable {api_key_env} is not set "
            "and no approved api_key value is present in reference/image_provider.json."
        )
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--quality", default="low", choices=["low", "medium", "high"])
    parser.add_argument("--prompt-only", action="store_true")
    parser.add_argument("--check-config", action="store_true")
    args = parser.parse_args()

    article = find_article(args.slug)
    prompt = build_prompt(article)
    output = ROOT / "images" / "exports" / "subjects" / f"{args.slug}-subject.png"

    if args.prompt_only:
        print(prompt)
        print(f"expected output: {output.relative_to(ROOT)}")
        return 0

    if args.check_config:
        data = load_image_config()
        print("image provider config present")
        print(f"provider: {data.get('provider')}")
        print(f"model: {data.get('model')}")
        print(f"expected output: {output.relative_to(ROOT)}")
        return 0

    try:
        data = load_image_config()
    except SystemExit as exc:
        print(exc)
        print(f"Example config: {IMAGE_CONFIG_EXAMPLE.relative_to(ROOT)}")
        print(f"Prompt:\n{prompt}")
        print(f"Expected output: {output.relative_to(ROOT)}")
        return 2

    print("TODO: real image API call is not implemented yet.")
    print("Config is present, but provider-specific generation code still needs implementation.")
    print(f"Provider: {data.get('provider')}")
    print(f"Model: {data.get('model')}")
    print(f"Prompt:\n{prompt}")
    print(f"Expected output: {output.relative_to(ROOT)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
