"""
Validate FreeIndexer content metadata and basic editorial rules.

Mirrors: captcharank_content/scripts/validate_content.py

What this script does:
- scans content/**/*.md
- validates required frontmatter fields
- checks slug matches filename
- checks cluster articles have internal links
- flags forbidden guarantee-style claims

Expected input:
- content/**/*.md

Expected output:
- console validation report
- exit code 0 when valid, 1 when errors are found
"""

from __future__ import annotations

import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
TAXONOMY_FILE = ROOT / "reference" / "blog_taxonomy.json"

REQUIRED_PATTERNS = {
    "title": r"^title:\s*.+",
    "slug": r"^slug:\s*.+",
    "description": r"^description:\s*.+",
    "keywords": r"^keywords:",
    "primary keyword": r"^\s*primary:\s*.+",
    "intent": r"^intent:\s*.+",
    "search_intent": r"^search_intent:\s*.+",
    "icp": r"^icp:\s*.+",
    "funnel_stage": r"^funnel_stage:\s*.+",
    "type": r"^type:\s*.+",
    "business_goal": r"^business_goal:\s*.+",
    "meta": r"^meta:",
    "internal_links": r"^\s*internal_links:",
    "cta": r"^\s*cta:\s*.+",
    "seo": r"^seo:",
    "meta_title": r"^\s*meta_title:\s*.+",
    "meta_description": r"^\s*meta_description:\s*.+",
    "editorial_review": r"^editorial_review:\s*.+",
}

FORBIDDEN = [
    "100% indexed",
    "guaranteed indexing",
    "guaranteed google indexing",
    "guaranteed rankings",
    "instant rankings",
]

FORBIDDEN_HEADINGS = [
    "Search Promise",
    "Reader Scenario",
    "Article Angle",
    "CTA",
    "Claim Guardrails",
    "Required Sections",
    "Draft Notes",
    "Internal Notes",
]


def extract_frontmatter(text: str) -> str | None:
    match = re.match(r"^\ufeff?---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    return match.group(1) if match else None


def frontmatter_value(frontmatter: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$", frontmatter, flags=re.M)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def is_pillar(frontmatter: str) -> bool:
    return bool(re.search(r"^\s*pillar:\s*true\s*$", frontmatter, flags=re.M | re.I))


def has_internal_link_item(frontmatter: str) -> bool:
    match = re.search(r"^\s*internal_links:\s*\n((?:\s+-\s+.+\n?)+)", frontmatter, flags=re.M)
    return bool(match)


def load_taxonomy() -> tuple[set[str], set[str]]:
    if not TAXONOMY_FILE.exists():
        return set(), set()
    data = json.loads(TAXONOMY_FILE.read_text(encoding="utf-8"))
    categories = {item["slug"] for item in data.get("categories", [])}
    tags = {item["slug"] for item in data.get("tags", [])}
    return categories, tags


def frontmatter_list(frontmatter: str, key: str) -> list[str]:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\n((?:\s+-\s+.+\n?)+)", frontmatter, flags=re.M)
    if not match:
        return []
    values = []
    for line in match.group(1).splitlines():
        item = line.strip()
        if item.startswith("- "):
            values.append(item[2:].strip().strip('"').strip("'"))
    return values


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    files = sorted(CONTENT_DIR.rglob("*.md"))
    taxonomy_categories, taxonomy_tags = load_taxonomy()

    for path in files:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        fm = extract_frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: missing frontmatter")
            continue

        for label, pattern in REQUIRED_PATTERNS.items():
            if not re.search(pattern, fm, flags=re.M):
                errors.append(f"{rel}: missing {label}")

        slug = frontmatter_value(fm, "slug")
        if slug and slug != path.stem:
            errors.append(f"{rel}: slug '{slug}' does not match filename '{path.stem}'")

        if not is_pillar(fm) and not has_internal_link_item(fm):
            errors.append(f"{rel}: cluster article must have at least one internal link")

        category = frontmatter_value(fm, "blog_category")
        if taxonomy_categories and category and category not in taxonomy_categories:
            errors.append(f"{rel}: blog_category '{category}' is not in reference/blog_taxonomy.json")

        if taxonomy_tags:
            for tag in frontmatter_list(fm, "blog_tags"):
                if tag not in taxonomy_tags:
                    errors.append(f"{rel}: blog_tag '{tag}' is not in reference/blog_taxonomy.json")

        lower = text.lower()
        for phrase in FORBIDDEN:
            if phrase in lower:
                warnings.append(f"{rel}: review unvalidated claim phrase '{phrase}'")

        for heading in FORBIDDEN_HEADINGS:
            if re.search(rf"^##\s+{re.escape(heading)}\s*$", text, flags=re.M):
                errors.append(f"{rel}: remove internal/publication label heading '## {heading}'")

        faq_match = re.search(r"^##\s+FAQ\s*$([\s\S]*?)(?=^##\s+|\Z)", text, flags=re.M)
        if faq_match:
            for question in re.finditer(r"^##\s+(.+)$", faq_match.group(1), flags=re.M):
                errors.append(
                    f"{rel}: FAQ question '{question.group(1).strip()}' must use ###, not ##"
                )

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    print(f"checked {len(files)} content files")
    if errors:
        print(f"validation failed with {len(errors)} errors")
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

