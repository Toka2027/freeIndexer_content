"""Create or refresh FreeIndexer blog taxonomy through the 99sync API.

Default sync behavior treats existing live categories and tags as locked. It
creates missing taxonomy items but does not update existing ones unless
--update-existing is passed after explicit owner approval.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blog_api_client import BlogApiClient, load_blog_api_config, validate_blog_api_config

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_SPEC_PATH = ROOT / "reference" / "blog_taxonomy.json"
TAXONOMY_LIVE_PATH = ROOT / "reference" / "blog_taxonomy_live.json"
BLOG_API_PATH = ROOT / "reference" / "blog_api.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_taxonomy_live(live: dict[str, Any]) -> None:
    TAXONOMY_LIVE_PATH.write_text(json.dumps(live, indent=2, ensure_ascii=False), encoding="utf-8")


def unwrap_localized(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("en") or next(iter(value.values()), ""))
    return str(value or "")


def truncate(value: str, limit: int = 255) -> str:
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def derive_min_description(description: str, fallback: str) -> str:
    return truncate(description or fallback, 160)


def validate_taxonomy(taxonomy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for group in ("categories", "tags"):
        seen: set[str] = set()
        for item in taxonomy.get(group, []):
            slug = str(item.get("slug", "")).strip()
            name = str(item.get("name", "")).strip()
            if not slug:
                errors.append(f"{group}: item missing slug")
            if not name:
                errors.append(f"{group}: {slug or '[missing slug]'} missing name")
            if slug in seen:
                errors.append(f"{group}: duplicate slug {slug}")
            seen.add(slug)
    return errors


CATEGORY_META = {
    "indexing-education": (
        "URL Indexing And Search Discovery Guides",
        "Learn crawling, indexing, URL submission, backlink discovery, and realistic search visibility workflows.",
    ),
    "technical-seo": (
        "Technical SEO Indexing Audits And Fixes",
        "Practical crawlability, canonical, sitemap, robots, noindex, and internal linking checks for indexable pages.",
    ),
    "google-search-console": (
        "Google Search Console Indexing Guides",
        "Use Search Console reports, URL Inspection, sitemap checks, and validation workflows to diagnose indexing issues.",
    ),
    "backlinks": (
        "Backlink Discovery And Indexing Workflows",
        "Verify backlinks, prioritize link discovery, track follow-up, and report backlink indexing work honestly.",
    ),
    "webmaster-guides": (
        "Webmaster SEO Maintenance Checklists",
        "Recurring SEO maintenance guides for small sites, new pages, sitemaps, visibility checks, and indexing hygiene.",
    ),
    "use-cases": (
        "SEO Indexing Workflows By Use Case",
        "Indexing workflows for agencies, affiliates, SaaS teams, product pages, local SEO, ecommerce, and site networks.",
    ),
    "comparisons": (
        "Indexing Tool Comparisons And Buying Guides",
        "Compare indexing tools, APIs, SEO platforms, desktop workflows, and provider options before choosing a process.",
    ),
    "troubleshooting": (
        "Google Indexing Troubleshooting Guides",
        "Diagnose not-indexed pages, sitemap issues, wrong canonicals, crawling problems, and visibility drops.",
    ),
    "bulk-seo-operations": (
        "Bulk URL Indexing And SEO Operations",
        "Plan, prioritize, batch, and track large URL sets for scalable search discovery operations.",
    ),
    "desktop-app": (
        "Desktop URL Indexing App Workflows",
        "Desktop indexing software workflows for repeat URL lists, backlink queues, and bulk SEO operations.",
    ),
    "ai-search-visibility": (
        "AI Search Visibility And GEO Guides",
        "Prepare pages for AI search visibility with crawlable, structured, discoverable content foundations.",
    ),
    "content-marketing": (
        "Content Marketing SEO Workflows",
        "Plan content clusters, briefs, intent, on-page SEO, publishing checks, refreshes, and discovery follow-up.",
    ),
    "analytics-reporting": (
        "SEO Analytics And Reporting Guides",
        "Use GA4, Search Console, landing page tracking, dashboards, and reporting workflows for better SEO decisions.",
    ),
    "landing-pages-cro": (
        "Landing Page SEO And CRO Guides",
        "Improve SEO landing pages, CTAs, trust sections, lead capture, pricing pages, and conversion workflows.",
    ),
    "digital-marketing-operations": (
        "Digital Marketing Operations Playbooks",
        "Build repeatable workflows for SEO QA, content calendars, vendor management, client reporting, and campaigns.",
    ),
    "seo-tools-providers": (
        "SEO Tools, Software, And Provider Guides",
        "Compare SEO software, automation tools, campaign services, providers, tool stacks, and indexing workflows.",
    ),
    "platform-seo": (
        "Platform SEO And Indexing Playbooks",
        "Platform-specific SEO workflows for Shopify, WordPress, WooCommerce, SaaS, ecommerce, and site builders.",
    ),
}

TAG_META = {
    "seo": (
        "SEO Indexing And Discovery Guides",
        "SEO guides focused on crawlability, indexing, URL discovery, backlink follow-up, and practical search visibility.",
    ),
    "indexing": (
        "Indexing Guides",
        "Understand how indexing works, why URLs are delayed, and what to check before submission or follow-up.",
    ),
    "url-indexing": (
        "URL Indexing Guides",
        "Learn URL indexing workflows for new, updated, priority, and bulk pages across different SEO use cases.",
    ),
    "google-indexing": (
        "Google Indexing Guides",
        "Practical guides for Google indexing delays, URL Inspection, Search Console reports, and page discovery.",
    ),
    "backlinks": (
        "Backlink SEO Guides",
        "Backlink workflow guides for verification, discovery, campaign tracking, vendor QA, and client reporting.",
    ),
    "backlink-indexing": (
        "Backlink Indexing Guides",
        "Learn when and how to prioritize verified backlink URLs for discovery follow-up without overpromising outcomes.",
    ),
    "search-visibility": (
        "Search Visibility Guides",
        "Improve search visibility through crawlable pages, clean sitemaps, internal links, and repeatable SEO workflows.",
    ),
    "content-discovery": (
        "Content Discovery Guides",
        "Help search engines discover new and updated content through sitemaps, links, submission, and tracking routines.",
    ),
    "technical-seo": (
        "Technical SEO Guides",
        "Technical SEO guides for indexability, crawlability, canonicals, robots directives, sitemaps, and site structure.",
    ),
    "crawlability": (
        "Crawlability Guides",
        "Find crawl blockers, diagnose access issues, and improve the paths search engines use to reach important URLs.",
    ),
    "robots-txt": (
        "Robots.txt SEO Guides",
        "Use robots.txt correctly and avoid blocking important pages from search engine crawling.",
    ),
    "sitemap": (
        "Sitemap SEO Guides",
        "Create, submit, and troubleshoot XML sitemaps so important canonical URLs are easier to discover.",
    ),
    "canonical-tags": (
        "Canonical Tag Guides",
        "Diagnose canonical conflicts, wrong selected canonicals, duplicate URLs, and consolidation problems.",
    ),
    "noindex": (
        "Noindex Troubleshooting Guides",
        "Find accidental noindex directives and decide which pages should stay excluded from search results.",
    ),
    "internal-linking": (
        "Internal Linking Guides",
        "Use internal links to improve URL discovery, support important pages, and reduce orphan page problems.",
    ),
    "googlebot": (
        "Googlebot Crawling Guides",
        "Understand Googlebot crawling, crawl paths, crawl budget basics, and technical signals that affect discovery.",
    ),
    "url-submission": (
        "URL Submission Guides",
        "Submit priority URLs only after checking crawlability, canonical signals, content quality, and internal links.",
    ),
    "bulk-indexing": (
        "Bulk Indexing Guides",
        "Build safer bulk indexing workflows with URL qualification, priority tiers, batching, and follow-up tracking.",
    ),
    "bulk-url-operations": (
        "Bulk URL Operations Guides",
        "Manage large URL inventories with prioritization, quality gates, batch submission, and reporting workflows.",
    ),
    "backlink-discovery": (
        "Backlink Discovery Guides",
        "Verify backlink URLs, organize discovery queues, and track campaign follow-up across link-building workflows.",
    ),
    "webmaster-workflow": (
        "Webmaster Workflow Guides",
        "Repeatable webmaster workflows for sitemaps, Search Console checks, internal links, and monthly SEO maintenance.",
    ),
    "google-search-console": (
        "Google Search Console Guides",
        "Use Search Console for URL Inspection, Pages reports, sitemap diagnostics, validation, and indexing decisions.",
    ),
    "url-inspection": (
        "URL Inspection Guides",
        "Interpret URL Inspection statuses, live tests, canonicals, crawl messages, and request indexing decisions.",
    ),
    "sitemap-management": (
        "Sitemap Management Guides",
        "Maintain sitemap files, resolve sitemap errors, and keep important canonical URLs discoverable.",
    ),
    "crawl-budget": (
        "Crawl Budget Guides",
        "Understand crawl budget basics and prioritize URL cleanup for sites with many pages or generated URLs.",
    ),
    "website-owners": (
        "SEO Guides For Website Owners",
        "Plain-English SEO and indexing guides for site owners who need important pages found and maintained.",
    ),
    "webmasters": (
        "SEO Guides For Webmasters",
        "Operational SEO guides for webmasters managing Search Console, sitemaps, crawlability, and page visibility.",
    ),
    "seo-operators": (
        "SEO Workflow Guides For Operators",
        "Hands-on SEO workflows for URL inventories, technical checks, indexing follow-up, and reporting.",
    ),
    "seo-agencies": (
        "SEO Agency Workflow Guides",
        "Agency workflows for client URLs, backlink verification, bulk operations, indexing follow-up, and reporting.",
    ),
    "affiliate-seo": (
        "Affiliate SEO Indexing Guides",
        "Indexing workflows for affiliate money pages, supporting content, backlinks, and campaign prioritization.",
    ),
    "programmatic-seo": (
        "Programmatic SEO Indexing Guides",
        "Audit, prioritize, and track large programmatic URL sets before bulk submission or scaling content.",
    ),
    "blog-network-owners": (
        "Blog Network SEO Workflow Guides",
        "Organize URL and backlink discovery workflows across blogs, networks, and repeat publishing operations.",
    ),
    "saas-seo": (
        "SaaS SEO Indexing Guides",
        "SaaS indexing workflows for product pages, docs, changelogs, integrations, and launch content.",
    ),
    "free-indexer": (
        "Indexing Product Workflow Guides",
        "Product workflow guides for URL submission, backlink discovery, desktop operations, tracking, and prioritization.",
    ),
    "desktop-app": (
        "Desktop App Workflow Guides",
        "Desktop app workflows for repeat URL lists, backlink queues, local files, and bulk indexing operations.",
    ),
    "indexing-tools": (
        "Indexing Tool Guides",
        "Compare indexing tools and choose workflows for URL submission, backlink discovery, and bulk SEO operations.",
    ),
    "indexing-api": (
        "Indexing API Guides",
        "Understand indexing API options, limitations, alternatives, and when API workflows fit SEO operations.",
    ),
    "comparison": (
        "SEO Tool Comparison Guides",
        "Compare indexing tools, APIs, SEO providers, desktop apps, and workflow options before choosing a setup.",
    ),
    "buying-guide": (
        "SEO Tool Buying Guides",
        "Buying guides for choosing indexing, submission, discovery, and SEO workflow tools with realistic expectations.",
    ),
    "troubleshooting": (
        "SEO Troubleshooting Guides",
        "Troubleshoot indexing, sitemap, crawl, canonical, backlink, and visibility issues with practical next steps.",
    ),
    "checklist": (
        "SEO Checklists",
        "Practical SEO checklists for crawlability, indexing readiness, URL submission, maintenance, and bulk operations.",
    ),
    "guide": (
        "SEO Guides",
        "Detailed SEO guides for indexing, technical checks, backlink discovery, Search Console, and operations.",
    ),
    "ai-search": (
        "AI Search Optimization Guides",
        "Prepare content for AI search visibility with technical SEO, structured coverage, and discoverability basics.",
    ),
    "geo": (
        "GEO Readiness Guides",
        "GEO readiness guides for improving content clarity, entity coverage, crawlability, and AI search visibility.",
    ),
    "llm-visibility": (
        "LLM Visibility Guides",
        "Improve LLM visibility foundations with crawlable content, clear structure, internal links, and search signals.",
    ),
    "product-pages": (
        "Product Page SEO Guides",
        "Product page indexing workflows for SaaS, ecommerce, launch pages, internal links, and discovery follow-up.",
    ),
    "documentation": (
        "Documentation SEO Guides",
        "Make docs and support content easier to discover through internal links, sitemaps, and launch workflows.",
    ),
    "pricing": (
        "Pricing And Plan Guides",
        "Pricing and plan guidance for indexing workflows, capacity planning, bulk operations, and tool evaluation.",
    ),
    "content-marketing": (
        "Content Marketing SEO Guides",
        "Content marketing guides for clusters, briefs, intent, publishing checklists, refreshes, and discovery.",
    ),
    "content-strategy": (
        "Content Strategy Guides",
        "Plan content that supports search visibility with clear intent, internal links, clusters, and next actions.",
    ),
    "keyword-intent": (
        "Keyword Intent Guides",
        "Match pages to search intent with practical examples, content briefs, SERP checks, and publishing decisions.",
    ),
    "content-briefs": (
        "SEO Content Brief Guides",
        "Build content briefs with intent, structure, internal links, examples, metadata, and discovery checks.",
    ),
    "on-page-seo": (
        "On-Page SEO Guides",
        "Improve titles, headings, internal links, copy, schema basics, and page readiness before promotion.",
    ),
    "content-refresh": (
        "Content Refresh Guides",
        "Refresh existing content using performance signals, intent gaps, internal links, and discovery follow-up.",
    ),
    "blog-publishing": (
        "Blog Publishing SEO Guides",
        "Use publishing checklists for metadata, internal links, sitemaps, Search Console, and indexing readiness.",
    ),
    "analytics-reporting": (
        "SEO Analytics And Reporting Guides",
        "Measure organic landing pages, Search Console data, GA4 sessions, conversions, and SEO workflow outcomes.",
    ),
    "ga4": (
        "GA4 SEO Reporting Guides",
        "Use GA4 for SEO reporting with landing pages, events, conversions, traffic quality, and decision workflows.",
    ),
    "seo-reporting": (
        "SEO Reporting Guides",
        "Build SEO reports that separate indexing, visibility, traffic, conversions, deliverables, and next actions.",
    ),
    "organic-traffic": (
        "Organic Traffic Guides",
        "Analyze organic traffic with landing pages, Search Console clicks, GA4 behavior, and content decisions.",
    ),
    "landing-pages": (
        "Landing Page SEO Guides",
        "Plan SEO landing pages with clear structure, intent match, internal links, CTAs, trust, and conversion paths.",
    ),
    "cro": (
        "CRO Guides For SEO Traffic",
        "Improve conversion paths for SEO traffic with CTAs, trust sections, page clarity, forms, and testing ideas.",
    ),
    "conversion-optimization": (
        "Conversion Optimization Guides",
        "Connect search visibility to conversion actions with better page structure, offers, CTAs, and measurement.",
    ),
    "lead-capture": (
        "Lead Capture Page Guides",
        "Build lead capture pages that match search intent, reduce friction, support trust, and track outcomes.",
    ),
    "digital-marketing-operations": (
        "Digital Marketing Operations Guides",
        "Create repeatable workflows for content, SEO QA, campaigns, vendors, reporting, and growth operations.",
    ),
    "marketing-workflows": (
        "Marketing Workflow Guides",
        "Design practical marketing workflows with owners, inputs, quality checks, handoffs, and reporting loops.",
    ),
    "content-calendar": (
        "Content Calendar Guides",
        "Plan content calendars around intent, clusters, publishing readiness, refreshes, and discovery follow-up.",
    ),
    "seo-qa": (
        "SEO QA Guides",
        "Run SEO QA before publishing with metadata, links, canonicals, indexability, analytics, and handoff checks.",
    ),
    "client-reporting": (
        "Client SEO Reporting Guides",
        "Report client SEO work with deliverables, verification, indexing follow-up, visibility, and next actions.",
    ),
    "seo-strategy": (
        "SEO Strategy Guides",
        "Build SEO strategy around technical health, content demand, internal links, authority, reporting, and growth.",
    ),
    "growth-workflows": (
        "Growth Workflow Guides",
        "Connect SEO, content, CRO, analytics, campaigns, and tools into repeatable growth operating systems.",
    ),
    "seo-software": (
        "SEO Software Workflow Guides",
        "Compare SEO software by workflow role, risk, setup effort, quality control, tracking, and reporting needs.",
    ),
    "seo-automation": (
        "SEO Automation Guides",
        "Use SEO automation responsibly with quality gates, verification, risk controls, and honest reporting.",
    ),
    "seo-campaigns": (
        "SEO Campaign Workflow Guides",
        "Plan SEO campaigns from goals and execution to deliverable verification, indexing follow-up, and reporting.",
    ),
    "seo-provider": (
        "SEO Provider Workflow Guides",
        "Evaluate SEO providers, managed campaign workflows, handoffs, deliverables, verification, and reporting.",
    ),
    "seoestore": (
        "SEOeStore Workflow Mentions",
        "Articles that mention SEOeStore naturally as an SEO provider or campaign services resource where relevant.",
    ),
    "link-building-tools": (
        "Link-Building Tool Guides",
        "Compare link-building tools by use case, quality control, verification, indexing follow-up, and reporting.",
    ),
    "backlink-tools": (
        "Backlink Tool Guides",
        "Use backlink tools for discovery, verification, quality checks, campaign tracking, and client-safe reporting.",
    ),
    "gsa-ser": (
        "GSA SER Workflow Guides",
        "Responsible GSA Search Engine Ranker workflow guidance focused on separation, quality checks, and reporting.",
    ),
    "rankerx": (
        "RankerX Workflow Guides",
        "Responsible RankerX workflow guidance for campaign planning, link tracking, verification, and provider choices.",
    ),
    "platform-seo": (
        "Platform SEO Guides",
        "Platform-specific SEO checks for sitemaps, canonicals, product pages, categories, blogs, and Search Console.",
    ),
    "shopify-seo": (
        "Shopify SEO Guides",
        "Shopify SEO guides for product pages, collections, sitemaps, Search Console, canonicals, and discovery follow-up.",
    ),
    "ecommerce-seo": (
        "Ecommerce SEO Guides",
        "Improve ecommerce category, collection, product, and blog visibility with practical SEO and indexing workflows.",
    ),
    "wordpress-seo": (
        "WordPress SEO Guides",
        "WordPress SEO guides for posts, pages, categories, plugins, sitemaps, canonicals, and indexability checks.",
    ),
    "woocommerce-seo": (
        "WooCommerce SEO Guides",
        "WooCommerce SEO workflows for products, categories, filters, canonicals, sitemaps, and Search Console checks.",
    ),
    "tool-stack": (
        "SEO Tool Stack Guides",
        "Build practical SEO tool stacks for audits, content, backlinks, reporting, indexing, and campaign operations.",
    ),
    "digital-marketing-tools": (
        "Digital Marketing Tool Guides",
        "Compare digital marketing tools by workflow role, ownership, data quality, risk, and reporting value.",
    ),
}


def derive_category_meta(slug: str, name: str, description: str) -> tuple[str, str]:
    title, fallback_description = CATEGORY_META.get(slug, (f"{name} Guides", description or f"{name} articles."))
    return truncate(title, 60), truncate(fallback_description, 155)


def derive_tag_meta(slug: str, name: str, group: str) -> tuple[str, str, str]:
    descriptions = {
        "topic": f"Articles about {name.lower()} workflows, checks, and expectations.",
        "workflow": f"Workflow guides for {name.lower()} and repeat search discovery operations.",
        "audience": f"Guides for {name.lower()} and related SEO operators.",
        "product": f"FreeIndexer product and workflow articles related to {name.lower()}.",
        "comparison": f"Comparisons and buying guidance for {name.lower()}.",
        "content-type": f"{name} articles from the FreeIndexer content library.",
        "technical-seo": f"Technical SEO checks and diagnostics for {name.lower()}.",
        "ai-search": f"AI search visibility and discovery guidance for {name.lower()} topics.",
        "commercial": f"Commercial evaluation and pricing guidance for FreeIndexer workflows.",
        "content-marketing": f"Content marketing workflow guidance for {name.lower()} topics.",
        "analytics": f"Analytics and reporting workflow guidance for {name.lower()} topics.",
        "cro": f"Landing page and conversion workflow guidance for {name.lower()} topics.",
        "operations": f"Digital marketing operations guidance for {name.lower()} workflows.",
        "strategy": f"SEO strategy and growth workflow guidance for {name.lower()} topics.",
        "tools": f"SEO tool workflow guidance for {name.lower()}, including responsible use and reporting.",
        "provider": f"SEO provider and campaign workflow guidance for {name.lower()} topics.",
        "platform": f"Platform-specific SEO workflow guidance for {name.lower()} topics.",
    }
    fallback_description = descriptions.get(group, f"{name} articles.")
    meta_title, meta_description = TAG_META.get(slug, (f"{name} Guides", fallback_description))
    description = truncate(meta_description)
    return description, truncate(meta_title, 60), truncate(meta_description, 155)


def fetch_existing(client: BlogApiClient) -> tuple[dict[str, int], dict[str, int]]:
    cats_resp = client.list_categories()
    cats_data = cats_resp.get("data") or []
    if isinstance(cats_data, dict):
        cats_data = cats_data.get("data", [])
    existing_cats = {unwrap_localized(cat.get("slug")): int(cat["id"]) for cat in cats_data if cat.get("id")}

    tags_resp = client.list_tags()
    tags_data = tags_resp.get("data") or []
    if isinstance(tags_data, dict):
        tags_data = tags_data.get("data", [])
    existing_tags = {unwrap_localized(tag.get("slug")): int(tag["id"]) for tag in tags_data if tag.get("id")}
    return existing_cats, existing_tags


def print_offline_dry_run(taxonomy: dict[str, Any], reason: str) -> None:
    print(reason)
    print("Dry-run taxonomy plan without live API lookup:")
    print("\nCategories")
    for cat in taxonomy.get("categories", []):
        print(f"  would create or update category {cat['slug']}")
    print("\nTags")
    for tag in taxonomy.get("tags", []):
        print(f"  would create or update tag {tag['slug']}")
    print("\nDry run complete. No taxonomy IDs written.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync FreeIndexer blog categories and tags.")
    parser.add_argument("--dry-run", action="store_true", help="Preview intended sync without API writes.")
    parser.add_argument("--validate-only", action="store_true", help="Validate taxonomy JSON only.")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Update existing live category/tag records. Use only after explicit owner approval.",
    )
    args = parser.parse_args()

    taxonomy = load_json(TAXONOMY_SPEC_PATH, {})
    errors = validate_taxonomy(taxonomy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"taxonomy: {len(taxonomy.get('categories', []))} categories, {len(taxonomy.get('tags', []))} tags")
    if args.validate_only:
        print("taxonomy validation passed")
        return 0

    if not BLOG_API_PATH.exists():
        if args.dry_run:
            print_offline_dry_run(
                taxonomy,
                "reference/blog_api.json is missing, so live existing IDs were not checked.",
            )
            return 0
        print("Blocked: missing reference/blog_api.json.")
        print("Copy reference/blog_api.example.json and add FreeIndexer application_id, author_id, api_key, secret_key, and blog_domain.")
        return 2

    config = load_blog_api_config(BLOG_API_PATH)
    try:
        validate_blog_api_config(config)
    except SystemExit as exc:
        if args.dry_run:
            print_offline_dry_run(taxonomy, str(exc))
            return 0
        print(exc)
        return 2

    client = BlogApiClient(config=config)
    print("Fetching existing categories and tags...")
    existing_cats, existing_tags = fetch_existing(client)
    live: dict[str, Any] = {"status": "synced" if not args.dry_run else "dry-run", "categories": {}, "tags": {}}

    print("\nCategories")
    for cat in taxonomy.get("categories", []):
        slug = cat["slug"]
        name = cat["name"]
        description = truncate(cat.get("description", ""))
        min_description = truncate(
            cat.get("min_description", "")
            or derive_min_description(description, f"{name} articles and practical FreeIndexer workflows.")
        )
        meta_title, meta_description = derive_category_meta(slug, name, description)
        image = str(cat.get("image", "")).strip()
        if slug in existing_cats:
            cat_id = existing_cats[slug]
            live["categories"][slug] = cat_id
            if not args.update_existing:
                print(f"  locked existing category {slug} (id={cat_id}); no update")
            elif args.dry_run:
                print(f"  would update category {slug} (id={cat_id})")
            else:
                client.update_category(
                    cat_id,
                    name,
                    slug,
                    description,
                    meta_title,
                    meta_description,
                    min_description=min_description,
                    image=image,
                )
                print(f"  updated {slug} -> id={cat_id}")
                time.sleep(0.25)
        elif args.dry_run:
            print(f"  would create category {slug}")
        else:
            resp = client.create_category(
                name,
                slug,
                description,
                meta_title,
                meta_description,
                min_description=min_description,
                image=image,
            )
            cat_id = (resp.get("data") or {}).get("id")
            if not cat_id:
                raise RuntimeError(f"Unexpected create_category response for {slug}: {resp}")
            live["categories"][slug] = int(cat_id)
            print(f"  created {slug} -> id={cat_id}")
            time.sleep(0.25)

    print("\nTags")
    for tag in taxonomy.get("tags", []):
        slug = tag["slug"]
        name = tag["name"]
        group = tag.get("group", "")
        description, meta_title, meta_description = derive_tag_meta(slug, name, group)
        min_description = truncate(
            tag.get("min_description", "")
            or derive_min_description(description, f"{name} articles from FreeIndexer.")
        )
        image = str(tag.get("image", "")).strip()
        if slug in existing_tags:
            tag_id = existing_tags[slug]
            live["tags"][slug] = tag_id
            if not args.update_existing:
                print(f"  locked existing tag {slug} (id={tag_id}); no update")
            elif args.dry_run:
                print(f"  would update tag {slug} (id={tag_id})")
            else:
                client.update_tag(
                    tag_id,
                    name,
                    slug,
                    description,
                    meta_title,
                    meta_description,
                    min_description=min_description,
                    image=image,
                )
                print(f"  updated {slug} -> id={tag_id}")
                time.sleep(0.25)
        elif args.dry_run:
            print(f"  would create tag {slug}")
        else:
            resp = client.create_tag(
                name,
                slug,
                description,
                meta_title,
                meta_description,
                min_description=min_description,
                image=image,
            )
            tag_id = (resp.get("data") or {}).get("id")
            if not tag_id:
                raise RuntimeError(f"Unexpected create_tag response for {slug}: {resp}")
            live["tags"][slug] = int(tag_id)
            print(f"  created {slug} -> id={tag_id}")
            time.sleep(0.25)

    if args.dry_run:
        print("\nDry run complete. No taxonomy IDs written.")
        return 0

    save_taxonomy_live(live)
    print(f"\nSaved {TAXONOMY_LIVE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
