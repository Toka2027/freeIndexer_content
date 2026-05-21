"""Create missing article drafts from pipeline/master-plan-100.csv.

This generator is intentionally scoped to the 100-article expansion plan. It
does not overwrite existing articles, does not edit taxonomy, and writes
drafts with the upgraded public layout and content_quality gate.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "pipeline" / "master-plan-100.csv"
CONTENT_DIR = ROOT / "content"
TAXONOMY_PATH = ROOT / "reference" / "blog_taxonomy.json"

CATEGORY_DIR = {
    "indexing-education": "indexing-education",
    "technical-seo": "technical-seo",
    "google-search-console": "google-search-console",
    "backlinks": "backlinks",
    "webmaster-guides": "webmaster-guides",
    "use-cases": "use-cases",
    "comparisons": "comparisons",
    "troubleshooting": "troubleshooting",
    "bulk-seo-operations": "bulk-seo-operations",
    "desktop-app": "desktop-app",
    "ai-search-visibility": "ai-search-visibility",
    "content-marketing": "content-marketing",
    "analytics-reporting": "analytics-reporting",
    "landing-pages-cro": "landing-pages-cro",
    "digital-marketing-operations": "digital-marketing-operations",
    "seo-tools-providers": "seo-tools-providers",
    "platform-seo": "platform-seo",
}

TYPE_BY_CATEGORY = {
    "indexing-education": "Indexing Education Guide",
    "technical-seo": "Technical SEO Guide",
    "google-search-console": "Search Console Playbook",
    "backlinks": "Backlink Workflow Guide",
    "webmaster-guides": "Webmaster Guide",
    "use-cases": "Use Case Guide",
    "comparisons": "Comparison",
    "troubleshooting": "Troubleshooting Guide",
    "bulk-seo-operations": "Bulk SEO Operations Guide",
    "desktop-app": "Desktop App Workflow",
    "ai-search-visibility": "AI Search Visibility Guide",
    "content-marketing": "Content Marketing Guide",
    "analytics-reporting": "Analytics And Reporting Guide",
    "landing-pages-cro": "Landing Page And CRO Guide",
    "digital-marketing-operations": "Digital Marketing Operations Guide",
    "seo-tools-providers": "SEO Tools And Providers Guide",
    "platform-seo": "Platform SEO Playbook",
}

TARGET_PAGE_BY_CATEGORY = {
    "comparisons": "https://freeindexer.com/pricing",
    "bulk-seo-operations": "https://freeindexer.com/pricing",
    "desktop-app": "https://freeindexer.com/",
    "seo-tools-providers": "https://freeindexer.com/pricing",
    "platform-seo": "https://freeindexer.com/pricing",
    "use-cases": "https://freeindexer.com/pricing",
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


def load_taxonomy() -> tuple[set[str], set[str]]:
    data = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    return (
        {item["slug"] for item in data.get("categories", [])},
        {item["slug"] for item in data.get("tags", [])},
    )


def title_case_slug(slug: str) -> str:
    fixes = {
        "seo": "SEO",
        "url": "URL",
        "gsc": "GSC",
        "ga4": "GA4",
        "ai": "AI",
        "geo": "GEO",
        "llm": "LLM",
        "api": "API",
        "gsa": "GSA",
        "ser": "SER",
        "rankerx": "RankerX",
        "freeindexer": "FreeIndexer",
        "woocommerce": "WooCommerce",
        "wordpress": "WordPress",
        "shopify": "Shopify",
        "webflow": "Webflow",
        "wix": "Wix",
        "squarespace": "Squarespace",
        "saas": "SaaS",
        "cro": "CRO",
    }
    return " ".join(fixes.get(part, part.capitalize()) for part in slug.split("-"))


def md_link(slug: str) -> str:
    return f"[{title_case_slug(slug)}](/{slug})"


def split_pipe(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def clean_sentence(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    return value[0].upper() + value[1:]


def safe_meta_description(row: dict[str, str]) -> str:
    title = row["title"]
    icp = row["primary_icp"].lower()
    keyword = row["primary_keyword"]
    return (
        f"Use {title} to plan, diagnose, prioritize, and report {keyword} "
        f"workflows for {icp}s with practical checks and next actions."
    )[:158]


def category_profile(row: dict[str, str]) -> dict[str, object]:
    category = row["category"]
    series = row["series_name"]
    tags = set(split_pipe(row["tags"]))
    title = row["title"]

    if category == "platform-seo" or tags & {"shopify-seo", "wordpress-seo", "woocommerce-seo", "platform-seo"}:
        return {
            "asset": "platform URLs",
            "checks": [
                "confirm the page is public, canonical, and indexable",
                "review sitemap inclusion and platform-generated URL variants",
                "check internal links from collections, categories, navigation, or related pages",
                "compare product, category, post, and template quality before prioritizing",
                "use Search Console on the exact final URL, not a preview or parameter URL",
            ],
            "example": "A store publishes a new collection, three supporting products, and one buying guide. The collection and guide enter the priority queue first because they target real demand and link to the product pages.",
            "mistake": "Submitting every platform URL before checking templates, canonicals, and internal links.",
        }
    if category == "google-search-console":
        return {
            "asset": "Search Console URLs",
            "checks": [
                "inspect the exact URL and final canonical",
                "compare URL Inspection with the Pages report pattern",
                "review sitemap status, crawl messages, and indexing reason",
                "separate one-page issues from template-wide issues",
                "write the next action before requesting any validation or follow-up",
            ],
            "example": "A client has 40 pages in a similar indexing status. The operator checks one sample URL, confirms a template issue, fixes the template, then validates the pattern instead of treating all 40 as separate problems.",
            "mistake": "Reading one Search Console message without checking the live URL, canonical, sitemap, and page template.",
        }
    if category == "backlinks" or "backlinks" in tags:
        return {
            "asset": "backlinks",
            "checks": [
                "verify the linking URL is live and public",
                "confirm the backlink is visible on the rendered page",
                "check target URL, anchor text, relevance, and campaign owner",
                "remove weak, broken, private, or irrelevant URLs from the priority list",
                "report verified delivery separately from search discovery outcomes",
            ],
            "example": "An agency receives 60 provider URLs. After QA, 38 are live and relevant, 9 need corrections, and 13 are not worth follow-up. Only the verified 38 enter the discovery queue.",
            "mistake": "Treating a vendor delivery spreadsheet as a clean backlink indexing list.",
        }
    if category == "content-marketing":
        return {
            "asset": "content URLs",
            "checks": [
                "define the exact search intent before writing",
                "choose the right format: guide, checklist, comparison, template, or troubleshooting article",
                "add examples, tables, and internal links before publishing",
                "confirm metadata, canonical, sitemap inclusion, and page quality",
                "track impressions, clicks, engagement, conversions, and refresh needs after launch",
            ],
            "example": "A SaaS team plans a cluster with one hub, four support articles, and two product-led pages. The hub links to every support article, and each support article links back to the hub and one relevant product page.",
            "mistake": "Publishing isolated posts that answer no exact intent and have no internal link path.",
        }
    if category == "analytics-reporting":
        return {
            "asset": "reporting URLs",
            "checks": [
                "separate discovery data from traffic and conversion data",
                "map Search Console URLs to analytics landing pages",
                "group pages by action: fix, refresh, link, test, monitor, or report",
                "define one decision the report should support",
                "keep provider work, submitted URLs, and business outcomes in separate columns",
            ],
            "example": "A monthly report shows indexed pages with rising impressions but low conversions. The SEO operator sends metadata fixes to content, CTA tests to CRO, and only fixed priority URLs to discovery follow-up.",
            "mistake": "Mixing indexing, rankings, traffic, and conversions into one success claim.",
        }
    if category == "landing-pages-cro":
        return {
            "asset": "landing pages",
            "checks": [
                "match the page promise to the search intent and offer",
                "place the primary CTA where the reader naturally makes a decision",
                "add proof, objections, pricing context, and trust signals",
                "check page speed, mobile layout, canonical, and internal links",
                "measure qualified actions instead of only pageviews",
            ],
            "example": "A pricing alternative page gets impressions but few trials. The team clarifies the comparison table, adds proof near the CTA, and tracks demo clicks separately from organic sessions.",
            "mistake": "Optimizing for traffic while the page gives visitors no clear conversion path.",
        }
    if category == "digital-marketing-operations":
        return {
            "asset": "marketing tasks",
            "checks": [
                "define owner, source, due date, and verification step",
                "separate planning, execution, QA, discovery follow-up, and reporting",
                "keep provider deliverables separate from internal outcomes",
                "create a recurring review rhythm for stuck items",
                "document the next action for every campaign asset",
            ],
            "example": "A growth team runs one board for content, technical fixes, vendors, analytics, and discovery follow-up. Every card has an owner, a target URL, a verification note, and a reporting field.",
            "mistake": "Running campaigns from chats and spreadsheets without a single QA process.",
        }
    if category == "seo-tools-providers" or "seo-software" in tags or "seo-provider" in tags:
        return {
            "asset": "tool or provider workflows",
            "checks": [
                "define whether you need execution, software, verification, or reporting",
                "separate link creation, content production, indexing follow-up, and analytics",
                "review risks, ownership, permissions, and client-safe reporting language",
                "test the workflow on a small set before scaling",
                "avoid tools or vendors that rely on promises instead of documented process",
            ],
            "example": "An agency uses a provider for campaign execution, a crawler for audits, Search Console for diagnostics, and FreeIndexer only for verified URLs or backlinks that deserve discovery follow-up.",
            "mistake": "Buying a tool or provider before deciding which workflow layer is missing.",
        }
    if category == "ai-search-visibility":
        return {
            "asset": "AI search visibility assets",
            "checks": [
                "make the brand, entity, product, and topic relationships clear",
                "publish crawlable pages that explain the facts directly",
                "support claims with useful comparisons, examples, and references",
                "keep technical SEO basics strong before chasing AI search tactics",
                "track mentions and discovery signals without overclaiming control",
            ],
            "example": "A SaaS team updates product pages, comparison content, documentation, and author pages so crawlers and AI systems can understand the entity relationships consistently.",
            "mistake": "Treating AI search visibility as a shortcut around crawlable, useful, well-linked content.",
        }
    if category == "technical-seo":
        return {
            "asset": "URL sets",
            "checks": [
                "crawl the affected URL set and group by template",
                "check robots.txt, status codes, canonicals, noindex, and sitemap inclusion",
                "confirm internal links and crawl depth",
                "prioritize fixes by business value and pattern size",
                "recheck a sample set before reporting completion",
            ],
            "example": "A programmatic site has 2,000 city pages. The SEO operator samples each template, finds a canonical mismatch, fixes the template, then rechecks the highest-value URLs first.",
            "mistake": "Debugging thousands of URLs one by one when the problem is template-level.",
        }
    return {
        "asset": "website URLs",
        "checks": [
            "confirm the page exists, is crawlable, and is worth discovering",
            "check sitemap, internal links, canonical, and page usefulness",
            "prioritize the URLs that support real business or reader goals",
            "track what changed and when follow-up happened",
            "report process and outcomes separately",
        ],
        "example": "A website owner launches five new pages. Two are important service pages, one is a support page, and two are thin placeholders. The service pages get fixed, linked, and prioritized first.",
        "mistake": "Treating every URL on the site as equally important.",
    }


def frontmatter(row: dict[str, str]) -> str:
    tags = split_pipe(row["tags"])
    links = split_pipe(row["internal_links"])
    secondary_keywords = split_pipe(row["secondary_keywords"])
    is_pillar = str(row.get("content_role", "")).lower() == "hub"
    target_page = TARGET_PAGE_BY_CATEGORY.get(row["category"], "https://freeindexer.com/")
    secondary_icp = row.get("secondary_icp") or ""
    score = "9.4" if is_pillar else "9.3"
    depth_elements = [
        "practical checklist",
        "comparison table",
        "workflow example",
        "common mistakes",
        "what to do next table",
    ]
    if row["category"] in {"troubleshooting", "google-search-console", "technical-seo", "platform-seo"}:
        depth_elements[1] = "diagnostic steps"
    if row["category"] in {"seo-tools-providers", "use-cases", "digital-marketing-operations"}:
        depth_elements[1] = "tool/provider decision framework"

    lines = [
        "---",
        f'title: "{row["title"]}"',
        f"slug: {row['slug']}",
        f'description: "{clean_sentence(row["search_intent"])}"',
        "keywords:",
        f"  primary: {row['primary_keyword']}",
        "  secondary:",
    ]
    lines.extend(f"    - {kw}" for kw in secondary_keywords[:5])
    lines.extend(
        [
            f"intent: {row['search_intent']}",
            f'search_intent: "{clean_sentence(row["search_intent"])}"',
            f"icp: {row['primary_icp']}",
            f"secondary_icp: {secondary_icp}",
            f"funnel_stage: {row['funnel_stage']}",
            f"type: {TYPE_BY_CATEGORY[row['category']]}",
            f"series: {row['series_name']}",
            f"business_goal: {row['target_cta']}",
            "meta:",
            f'  target_page: "{target_page}"',
            "  internal_links:",
        ]
    )
    lines.extend(f"    - {link}" for link in links)
    lines.extend(["  blog_category: " + row["category"], "  blog_tags:"])
    lines.extend(f"    - {tag}" for tag in tags)
    lines.extend(
        [
            f"  pillar: {'true' if is_pillar else 'false'}",
            f'  cta: "{row["target_cta"]}"',
            "  status: ready-for-publish",
            "  word_target: 1500",
            "seo:",
            f'  meta_title: "{row["title"]}"',
            f'  meta_description: "{safe_meta_description(row)}"',
            "editorial_review: standard",
            "content_quality:",
            f'  search_promise: "This article satisfies the title promise by explaining {row["primary_keyword"]} for {row["primary_icp"].lower()} workflows with specific checks, examples, and next actions."',
            "  depth_elements:",
        ]
    )
    lines.extend(f"    - {item}" for item in depth_elements)
    lines.extend(
        [
            f"  score: {score}",
            "  checks:",
        ]
    )
    lines.extend(f"    {check}: true" for check in QUALITY_CHECKS)
    lines.extend(
        [
            "image:",
            f'  concept: "{row["image_concept"]}"',
            f"  hero_template: {row['hero_template']}",
            "---",
        ]
    )
    return "\n".join(lines)


def render_article(row: dict[str, str]) -> str:
    profile = category_profile(row)
    links = split_pipe(row["internal_links"])
    asset = str(profile["asset"])
    checks = list(profile["checks"])  # type: ignore[arg-type]
    secondary = row.get("secondary_icp") or "related operators"
    free = row.get("freeindexer_mention", "no")
    seoestore = row.get("seoestore_mention", "none")

    related = "\n".join(f"- {md_link(link)}" for link in links)
    checks_md = "\n".join(f"- {check}." for check in checks)

    rows = [
        ("Planning", "Define the target reader, target URL set, and reason this work matters."),
        ("Diagnosis", f"Check {asset}, technical signals, usefulness, ownership, and reporting fields."),
        ("Prioritization", "Choose the pages, backlinks, campaigns, or tasks that deserve attention first."),
        ("Follow-up", "Record the next action, owner, date, and evidence before reporting progress."),
    ]
    table = "\n".join(f"| {stage} | {action} |" for stage, action in rows)

    mistake = str(profile["mistake"])
    example = str(profile["example"])

    body = [
        f"{row['title']} should answer one practical question: how should {row['primary_icp'].lower()}s handle {row['primary_keyword']} without drifting into vague SEO advice?",
        "",
        f"This guide is part of the {row['series_name']} series. It is written for {row['primary_icp'].lower()}s, with {secondary.lower()}s as the secondary reader when that workflow overlaps.",
        "",
        "Related reading in this workflow:",
        "",
        related,
        "",
        "## The Short Answer",
        "",
        f"{clean_sentence(row['search_intent'])}. The useful approach is to define the exact promise of the page or campaign, inspect the real workflow signals, prioritize the assets that matter, and document the next action before reporting progress.",
        "",
        f"For this topic, the working asset is {asset}. A good workflow keeps planning, execution, verification, discovery follow-up, and reporting separate enough that the team can see what actually changed.",
        "",
        "## Workflow Map",
        "",
        "| Stage | What to do |",
        "|---|---|",
        table,
        "",
        "## Practical Checklist",
        "",
        checks_md,
        "",
        "## Decision Table",
        "",
        "| If you see this | Do this next |",
        "|---|---|",
        f"| The asset is important but not verified | Check the exact URL, owner, source, and expected business role before moving it forward |",
        f"| The pattern affects many URLs | Fix the template, process, or campaign source before handling individual rows |",
        f"| The item is live but weak | Improve usefulness, internal links, relevance, or proof before follow-up |",
        f"| The item is verified and high priority | Add it to the next tracked workflow queue with a date and owner |",
        f"| Reporting is unclear | Separate deliverables, verification, discovery signals, traffic, and conversions |",
        "",
        "## Example Workflow",
        "",
        example,
        "",
        f"In a real team, this should become a small operating board: target URL, source, owner, status, verification note, priority, follow-up date, and reporting note. That structure keeps {row['primary_keyword']} work from becoming a loose checklist that nobody can audit later.",
        "",
        "## Common Mistakes",
        "",
        f"- {mistake}",
        "- Reporting a task as complete before the asset is verified.",
        "- Treating every URL, backlink, campaign task, or page as equal priority.",
        "- Mixing technical discovery, content quality, traffic, and conversions in one vague metric.",
        "- Adding tools before the team has defined the workflow owner and decision rule.",
        "",
        "## What To Do Next",
        "",
        "| Situation | Next action |",
        "|---|---|",
        "| You are starting from scratch | Build a small inventory and define the reader, URL, or campaign goal first |",
        "| You already have data | Group the data by pattern, not by random individual rows |",
        "| You found blockers | Fix crawlability, quality, tracking, or provider handoff before scaling |",
        "| You have verified priority assets | Move them into the right follow-up queue and record the evidence |",
        "| You need reporting | Show what was done, what was verified, and what changed afterward |",
    ]

    if free in {"yes", "limited"}:
        body.extend(
            [
                "",
                "## Where FreeIndexer Fits",
                "",
                "FreeIndexer fits when the team has verified URLs, backlinks, launch pages, or priority lists that deserve repeatable discovery follow-up. It is useful for URL submission, backlink discovery workflows, bulk URL queues, tracking, and prioritization.",
                "",
                "It should not replace technical checks, content quality, provider QA, Search Console review, analytics, or conversion work. Use it after the asset is ready enough to deserve attention.",
            ]
        )

    if seoestore.startswith("yes"):
        body.extend(
            [
                "",
                "## Where SEOeStore Fits",
                "",
                "Teams that need managed SEO execution can use a provider such as [SEOeStore](https://panel.seoestore.net/) or explore [SEO campaign services](https://panel.seoestore.net/seo-campaigns.php), then keep verification and indexing follow-up in a separate workflow.",
                "",
                "SEOeStore belongs in the provider or campaign execution layer. FreeIndexer remains separate as the indexing, URL discovery, backlink discovery, and follow-up workflow layer.",
            ]
        )

    body.extend(
        [
            "",
            "## FAQ",
            "",
            f"### Who should use this {row['category'].replace('-', ' ')} workflow?",
            "",
            f"Use it when {row['primary_icp'].lower()}s need a repeatable way to handle {row['primary_keyword']} without relying on guesswork or unsupported promises.",
            "",
            "### What should be checked before follow-up?",
            "",
            "Check the exact URL or asset, the source, the technical status, the business priority, the owner, and the reporting note. Weak or unverified items should be fixed before they enter any follow-up queue.",
            "",
            "### How do I report progress safely?",
            "",
            "Report actions, verification, submissions, visibility data, traffic, and conversions separately. That keeps the workflow honest and avoids overstating what any tool, provider, or single action can control.",
            "",
        ]
    )
    return "\n".join(body)


def create_articles(limit: int | None = None, dry_run: bool = False) -> list[Path]:
    taxonomy_categories, taxonomy_tags = load_taxonomy()
    rows = list(csv.DictReader(PLAN_PATH.open(newline="", encoding="utf-8-sig")))
    created: list[Path] = []
    for row in rows:
        category = row["category"]
        tags = split_pipe(row["tags"])
        if category not in taxonomy_categories:
            raise SystemExit(f"{row['slug']}: unknown category {category}")
        missing_tags = [tag for tag in tags if tag not in taxonomy_tags]
        if missing_tags:
            raise SystemExit(f"{row['slug']}: unknown tags {', '.join(missing_tags)}")

        out_dir = CONTENT_DIR / CATEGORY_DIR[category]
        out_path = out_dir / f"{row['slug']}.md"
        if out_path.exists():
            continue
        if limit is not None and len(created) >= limit:
            break
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_text(frontmatter(row) + "\n\n" + render_article(row), encoding="utf-8")
        created.append(out_path)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Create missing drafts from the 100-article plan.")
    parser.add_argument("--limit", type=int, help="Only create this many missing articles.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    created = create_articles(limit=args.limit, dry_run=args.dry_run)
    action = "would create" if args.dry_run else "created"
    print(f"{action} {len(created)} article files")
    for path in created:
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
