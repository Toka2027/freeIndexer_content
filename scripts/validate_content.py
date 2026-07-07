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

GENERIC_TEMPLATE_PHRASES = [
    "is a practical workflow guide for",
    "without turning every indexing issue into a product problem",
    "should be handled as a workflow, not as a one-click fix",
    "the exact checks change by topic, but the operating principle stays the same",
    "this kind of example matters because it turns seo advice into an operating habit",
    "keep the workflow honest: check the url",
]

GENERIC_DESCRIPTIONS = {
    "informational",
    "informational-commercial",
    "commercial investigation",
    "troubleshooting",
}

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


def frontmatter_block(frontmatter: str, key: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(key)}:\s*\n(.*?)(?=^[A-Za-z_][A-Za-z0-9_]*:\s*|\Z)",
        frontmatter,
        flags=re.M | re.S,
    )
    return match.group(1) if match else ""


def block_scalar(block: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$", block, flags=re.M)
    return match.group(1).strip().strip('"').strip("'") if match else ""


def block_list(block: str, key: str) -> list[str]:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\n((?:\s+-\s+.+\n?)+)", block, flags=re.M)
    if not match:
        return []
    return [
        line.strip()[2:].strip().strip('"').strip("'")
        for line in match.group(1).splitlines()
        if line.strip().startswith("- ")
    ]


def is_true_in_block(block: str, key: str) -> bool:
    return bool(re.search(rf"^\s*{re.escape(key)}:\s*(true|yes|1)\s*$", block, flags=re.M | re.I))


def validate_content_quality(rel: Path, fm: str, text: str, errors: list[str]) -> None:
    quality = frontmatter_block(fm, "content_quality")
    if not quality:
        return

    promise = block_scalar(quality, "search_promise")
    if not promise:
        errors.append(f"{rel}: content_quality.search_promise is required")

    score_text = block_scalar(quality, "score")
    try:
        score = float(score_text)
    except ValueError:
        errors.append(f"{rel}: content_quality.score must be numeric")
        score = 0.0
    if score < 9:
        errors.append(f"{rel}: content_quality.score must be at least 9 before upload")

    depth_elements = block_list(quality, "depth_elements")
    if len(depth_elements) < 3:
        errors.append(f"{rel}: content_quality.depth_elements must include at least 3 items")

    for check in QUALITY_CHECKS:
        if not is_true_in_block(quality, check):
            errors.append(f"{rel}: content_quality.checks.{check} must be true")

    lower_body = text.lower()
    for phrase in GENERIC_TEMPLATE_PHRASES:
        if phrase in lower_body:
            errors.append(f"{rel}: remove generic template phrase '{phrase}'")

    for slug in frontmatter_list(fm, "internal_links"):
        if f"](/{slug})" not in text:
            errors.append(f"{rel}: internal link '{slug}' must appear as a Markdown body link")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    files = sorted(CONTENT_DIR.rglob("*.md"))
    taxonomy_categories, taxonomy_tags = load_taxonomy()
    descriptions: dict[str, Path] = {}
    meta_descriptions: dict[str, Path] = {}

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

        description = frontmatter_value(fm, "description")
        if description.lower() in GENERIC_DESCRIPTIONS:
            errors.append(f"{rel}: description is a search-intent label, not a public summary")
        if len(description) < 70:
            errors.append(f"{rel}: description is too short ({len(description)} characters)")
        if description and not re.search(r"[.!?]$", description):
            errors.append(f"{rel}: description must end with sentence punctuation")
        description_key = description.casefold()
        if description_key in descriptions:
            errors.append(f"{rel}: duplicate description also used by {descriptions[description_key]}")
        elif description_key:
            descriptions[description_key] = rel

        seo_block = frontmatter_block(fm, "seo")
        meta_description = block_scalar(seo_block, "meta_description")
        if not 120 <= len(meta_description) <= 160:
            errors.append(
                f"{rel}: seo.meta_description must be 120-160 characters "
                f"(found {len(meta_description)})"
            )
        if meta_description and not re.search(r"[.!?]$", meta_description):
            errors.append(f"{rel}: seo.meta_description must end with sentence punctuation")
        meta_key = meta_description.casefold()
        if meta_key in meta_descriptions:
            errors.append(
                f"{rel}: duplicate seo.meta_description also used by {meta_descriptions[meta_key]}"
            )
        elif meta_key:
            meta_descriptions[meta_key] = rel

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

        validate_content_quality(rel, fm, text, errors)

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

