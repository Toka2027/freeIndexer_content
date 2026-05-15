"""
Build FreeIndexer article inventory.

Mirrors: captcharank_content/scripts/build_master_articles.py

What this script does:
- scans content/**/*.md
- extracts key frontmatter fields
- writes pipeline/master-articles.csv
- keeps the inventory rebuildable from source markdown

Expected input:
- content/**/*.md with YAML-like frontmatter

Expected output:
- pipeline/master-articles.csv
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
OUTPUT = ROOT / "pipeline" / "master-articles.csv"


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^\ufeff?---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not match:
        return {}

    frontmatter = match.group(1)
    data: dict[str, str] = {}
    current_parent = ""

    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("- "):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        value = value.strip().strip('"').strip("'")
        if indent == 0:
            current_parent = key
            if value:
                data[key] = value
        elif current_parent:
            data[f"{current_parent}.{key}"] = value
    return data


def main() -> int:
    rows = []
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        meta = read_frontmatter(path)
        slug = meta.get("slug", path.stem)
        rows.append(
            {
                "slug": slug,
                "title": meta.get("title", ""),
                "category": meta.get("meta.blog_category", ""),
                "icp": meta.get("icp", ""),
                "funnel_stage": meta.get("funnel_stage", ""),
                "intent": meta.get("intent", ""),
                "status": meta.get("meta.status", "draft"),
                "priority": "P1" if len(rows) < 5 else "P2",
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "slug",
                "title",
                "category",
                "icp",
                "funnel_stage",
                "intent",
                "status",
                "priority",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

