"""Repair public descriptions and SEO meta descriptions in article frontmatter.

The 100-article generator previously copied search-intent labels into the
public description field and sliced meta descriptions at a fixed character
offset. This script repairs every locally affected article without rewriting
otherwise healthy metadata.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from content_tools import ROOT, read_article_file, scalar_to_text

CONTENT_DIR = ROOT / "content"
GENERIC_DESCRIPTIONS = {
    "informational",
    "informational-commercial",
    "commercial investigation",
    "troubleshooting",
}

CATEGORY_DETAILS = {
    "indexing-education": ["crawlability", "discovery signals", "sitemaps", "internal links"],
    "technical-seo": ["status codes", "robots directives", "canonical signals", "sitemaps"],
    "google-search-console": ["URL Inspection", "Page indexing reports", "sitemaps", "live tests"],
    "backlinks": ["link verification", "source-page quality", "discovery status", "reporting"],
    "webmaster-guides": ["crawlability", "sitemaps", "internal links", "Search Console"],
    "use-cases": ["URL quality", "workflow ownership", "prioritization", "reporting"],
    "comparisons": ["setup effort", "workflow control", "verification", "reporting"],
    "troubleshooting": ["live URL checks", "crawl access", "canonical signals", "content quality"],
    "bulk-seo-operations": ["URL inventory fields", "quality gates", "priority tiers", "reporting"],
    "desktop-app": ["local URL lists", "batch controls", "verification", "tracking"],
    "ai-search-visibility": ["crawlable content", "entity clarity", "structured information", "internal links"],
    "content-marketing": ["search intent", "content structure", "internal links", "publishing QA"],
    "analytics-reporting": ["indexing status", "Search Console data", "landing pages", "conversions"],
    "landing-pages-cro": ["search intent", "page structure", "trust signals", "conversion tracking"],
    "digital-marketing-operations": ["owners", "quality gates", "due dates", "reporting loops"],
    "seo-tools-providers": ["workflow roles", "quality control", "verification", "client reporting"],
    "platform-seo": ["template settings", "canonical URLs", "sitemaps", "internal links"],
}

ICP_PLURALS = {
    "Website Owner": "website owners",
    "Webmaster": "webmasters",
    "SEO Operator": "SEO operators",
    "SEO Agency": "SEO agencies",
    "Affiliate Marketer": "affiliate marketers",
    "Programmatic SEO Builder": "programmatic SEO teams",
    "SaaS Or Product Team": "SaaS and product teams",
    "Blog Or Network Owner": "blog and network owners",
    "Ecommerce Store Owner": "ecommerce teams",
    "Growth Operator": "growth teams",
    "Founder": "founders",
    "Content Marketer": "content teams",
    "Tool/API Evaluator": "tool evaluators",
}


def nested_text(data: dict[str, object], path: str, default: str = "") -> str:
    value: object = data
    for part in path.split("."):
        if not isinstance(value, dict):
            return default
        value = value.get(part)
    text = scalar_to_text(value).strip()
    return text or default


def normalize_terms(text: str) -> str:
    replacements = {
        r"\bseo\b": "SEO",
        r"\burl\b": "URL",
        r"\bgsc\b": "GSC",
        r"\bga4\b": "GA4",
        r"\bapi\b": "API",
        r"\bai\b": "AI",
        r"\bgeo\b": "GEO",
        r"\bsaas\b": "SaaS",
        r"\bfreeindexer\b": "FreeIndexer",
        r"\bwordpress\b": "WordPress",
        r"\bwoocommerce\b": "WooCommerce",
        r"\bshopify\b": "Shopify",
        r"\bwebflow\b": "Webflow",
        r"\bgoogle\b": "Google",
    }
    result = text.strip()
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.I)
    return result


def join_items(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def is_clean_sentence(value: str) -> bool:
    return bool(value and re.search(r"[.!?]$", value))


def description_needs_fix(value: str) -> bool:
    return (
        not value
        or value.strip().lower() in GENERIC_DESCRIPTIONS
        or value.startswith("A practical guide to ")
        or len(value.strip()) < 70
        or not is_clean_sentence(value.strip())
    )


def meta_needs_fix(value: str) -> bool:
    lower = value.lower()
    return (
        len(value) < 120
        or len(value) > 160
        or not is_clean_sentence(value)
        or lower.startswith("learn a practical ")
        or " to plan, diagnose, prioritize, and report " in lower
    )


def build_description(data: dict[str, object]) -> str:
    primary = normalize_terms(nested_text(data, "keywords.primary", nested_text(data, "title")))
    category = nested_text(data, "meta.blog_category", "indexing-education")
    details = CATEGORY_DETAILS.get(category, CATEGORY_DETAILS["indexing-education"])
    icp = ICP_PLURALS.get(nested_text(data, "icp"), "SEO teams")
    cta = normalize_terms(nested_text(data, "meta.cta", "choose the next practical action"))
    cta = cta[:1].lower() + cta[1:] if cta else "choose the next practical action"
    return (
        f"A practical guide for {icp} to {cta}, covering "
        f"{join_items(details[:3])} and {primary}."
    )


def build_meta_description(data: dict[str, object], clean_description: str) -> str:
    title = nested_text(data, "title")
    title_lower = title.lower()
    primary = normalize_terms(nested_text(data, "keywords.primary", title))
    category = nested_text(data, "meta.blog_category", "indexing-education")
    details = CATEGORY_DETAILS.get(category, CATEGORY_DETAILS["indexing-education"])
    cta = normalize_terms(nested_text(data, "meta.cta", "choose the next practical action"))
    cta = cta[:1].lower() + cta[1:] if cta else "choose the next practical action"

    candidates: list[str] = []
    if 120 <= len(clean_description) <= 160 and is_clean_sentence(clean_description):
        candidates.append(clean_description)

    for count in (4, 3, 2, 1):
        detail = join_items(details[:count])
        if " vs " in title_lower or category == "comparisons" or title_lower.startswith("compare "):
            candidates.extend(
                [
                    f"Compare {primary} by {detail} to choose a practical workflow with realistic limits and clear reporting.",
                    f"Compare {primary} across {detail}, then choose the workflow that fits your indexing and reporting needs.",
                ]
            )
        elif "checklist" in title_lower:
            candidates.extend(
                [
                    f"Use this {primary} to review {detail}, prioritize fixes, and plan reliable indexing follow-up.",
                    f"Follow this {primary} for {detail}, practical fixes, and clearer indexing follow-up.",
                ]
            )
        elif category == "troubleshooting" or any(
            phrase in title_lower
            for phrase in ("not indexing", "not indexed", "error", "fixing", "wrong canonical", "disappeared")
        ):
            candidates.extend(
                [
                    f"Troubleshoot {primary} with checks for {detail}, then prioritize fixes and indexing follow-up.",
                    f"Diagnose {primary} by reviewing {detail}, practical fixes, and the next indexing action.",
                ]
            )
        else:
            candidates.extend(
                [
                    f"Learn {primary} and {cta}, using practical checks for {detail} and clear next actions.",
                    f"Learn about {primary}, covering {detail}, common mistakes, and clear next actions for search discovery.",
                ]
            )

    valid = [candidate for candidate in candidates if 120 <= len(candidate) <= 160]
    if not valid:
        raise ValueError(f"Could not create a 120-160 character meta description for {title}")
    return min(valid, key=lambda candidate: abs(len(candidate) - 150))


def replace_scalar(text: str, key: str, value: str, indent: str = "") -> str:
    pattern = rf"^{re.escape(indent)}{re.escape(key)}:\s*.*$"
    replacement = f"{indent}{key}: {json.dumps(value, ensure_ascii=False)}"
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
    if count != 1:
        raise ValueError(f"Could not replace {key}")
    return updated


def process_file(path: Path, apply_changes: bool) -> dict[str, object] | None:
    article = read_article_file(path)
    data = article.frontmatter_data
    current_description = nested_text(data, "description")
    current_meta = nested_text(data, "seo.meta_description")

    next_description = (
        build_description(data) if description_needs_fix(current_description) else current_description
    )
    next_meta = (
        build_meta_description(data, next_description) if meta_needs_fix(current_meta) else current_meta
    )
    if next_description == current_description and next_meta == current_meta:
        return None

    updated = article.raw_text
    if next_description != current_description:
        updated = replace_scalar(updated, "description", next_description)
    if next_meta != current_meta:
        updated = replace_scalar(updated, "meta_description", next_meta, indent="  ")
    if apply_changes:
        path.write_text(updated, encoding="utf-8")

    return {
        "slug": nested_text(data, "slug", path.stem),
        "description_changed": next_description != current_description,
        "meta_description_changed": next_meta != current_meta,
        "description": next_description,
        "meta_description": next_meta,
        "meta_length": len(next_meta),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair article description metadata.")
    parser.add_argument("--apply", action="store_true", help="Write the repaired metadata to article files.")
    parser.add_argument("--report", default="", help="Optional JSON report path.")
    args = parser.parse_args()

    changed: list[dict[str, object]] = []
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        result = process_file(path, apply_changes=args.apply)
        if result:
            changed.append(result)

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "articles_updated": len(changed),
        "descriptions_updated": sum(bool(item["description_changed"]) for item in changed),
        "meta_descriptions_updated": sum(bool(item["meta_description_changed"]) for item in changed),
        "items": changed,
    }
    if args.report:
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = ROOT / report_path
        if args.apply:
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
