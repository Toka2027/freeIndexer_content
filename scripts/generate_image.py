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
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--quality", default="low", choices=["low", "medium", "high"])
    parser.add_argument("--prompt-only", action="store_true")
    args = parser.parse_args()

    article = find_article(args.slug)
    prompt = build_prompt(article)
    output = ROOT / "images" / "exports" / "subjects" / f"{args.slug}-subject.png"

    if args.prompt_only:
        print(prompt)
        print(f"expected output: {output.relative_to(ROOT)}")
        return 0

    print("TODO: image generation provider integration is not implemented yet.")
    print("Blocked until owner/team provides the approved image provider and credentials.")
    print(f"Prompt:\n{prompt}")
    print(f"Expected output: {output.relative_to(ROOT)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

