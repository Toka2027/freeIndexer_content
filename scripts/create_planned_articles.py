"""Create publish-ready FreeIndexer article drafts from the 30-article plan.

The script intentionally reads the approved planning JSON and writes markdown
files with complete frontmatter, reader-facing headings, real markdown links,
and conservative claim language.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "pipeline" / "production-plan-30.json"
CONTENT_DIR = ROOT / "content"

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
}

CATEGORY_NAME = {
    "indexing-education": "Indexing Education",
    "technical-seo": "Technical SEO",
    "google-search-console": "Google Search Console",
    "backlinks": "Backlinks",
    "webmaster-guides": "Webmaster Guides",
    "use-cases": "Use Cases",
    "comparisons": "Comparisons",
    "troubleshooting": "Troubleshooting",
    "bulk-seo-operations": "Bulk SEO Operations",
    "desktop-app": "Desktop App",
    "ai-search-visibility": "AI Search Visibility",
}

TYPE_BY_CATEGORY = {
    "indexing-education": "Indexing Guide",
    "technical-seo": "Technical SEO Guide",
    "google-search-console": "Search Console Guide",
    "backlinks": "Backlink Workflow Guide",
    "webmaster-guides": "Webmaster Guide",
    "use-cases": "Use Case Guide",
    "comparisons": "Comparison",
    "troubleshooting": "Troubleshooting Guide",
    "bulk-seo-operations": "Advanced Workflow Guide",
    "desktop-app": "Desktop App Guide",
    "ai-search-visibility": "AI Search Visibility Guide",
}

WORD_TARGET_BY_CATEGORY = {
    "indexing-education": 1300,
    "technical-seo": 1400,
    "google-search-console": 1300,
    "backlinks": 1300,
    "webmaster-guides": 1200,
    "use-cases": 1300,
    "comparisons": 1400,
    "troubleshooting": 1400,
    "bulk-seo-operations": 1300,
    "desktop-app": 1100,
    "ai-search-visibility": 1200,
}

TARGET_PAGE_BY_CATEGORY = {
    "comparisons": "https://freeindexer.com/pricing",
    "bulk-seo-operations": "https://freeindexer.com/pricing",
    "desktop-app": "https://freeindexer.com/",
}

PILLAR_SLUGS = {
    "bulk-url-operations-workflow",
    "ai-search-visibility-for-seo-operators",
    "freeindexer-desktop-app-guide",
}


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").title()


def link_text(slug: str) -> str:
    replacements = {
        "seo": "SEO",
        "url": "URL",
        "api": "API",
        "ai": "AI",
        "llm": "LLM",
        "geo": "GEO",
        "google": "Google",
        "freeindexer": "FreeIndexer",
    }
    words = []
    for word in slug.split("-"):
        words.append(replacements.get(word, word))
    return " ".join(words)


def md_link(slug: str) -> str:
    return f"[{link_text(slug)}](/{slug})"


def sentence_list(items: list[str]) -> str:
    clean = [item for item in items if item]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    return ", ".join(clean[:-1]) + ", and " + clean[-1]


def meta_description(article: dict) -> str:
    keyword = article["primary_keyword"]
    category = CATEGORY_NAME[article["category"]]
    return (
        f"Learn a practical {category.lower()} workflow for {keyword}, including "
        "checks, prioritization, realistic expectations, and where submission tools fit."
    )


def frontmatter(article: dict) -> str:
    slug = article["slug"]
    secondary_icp = article.get("secondary_icp", "")
    target_page = TARGET_PAGE_BY_CATEGORY.get(article["category"], "https://freeindexer.com/")
    pillar = "true" if slug in PILLAR_SLUGS else "false"
    lines = [
        "---",
        f'title: "{article["title"]}"',
        f"slug: {slug}",
        f'description: "{article["search_intent"]}"',
        "keywords:",
        f"  primary: {article['primary_keyword']}",
        "  secondary:",
    ]
    lines.extend(f"    - {kw}" for kw in article["secondary_keywords"])
    lines.extend(
        [
            f"intent: {intent_for(article)}",
            f'search_intent: "{article["search_intent"]}"',
            f"icp: {article['primary_icp']}",
            f"secondary_icp: {secondary_icp}",
            f"funnel_stage: {article['funnel_stage']}",
            f"type: {TYPE_BY_CATEGORY[article['category']]}",
            "business_goal: Build topical authority and support practical search discovery workflows",
            "meta:",
            f"  target_page: {target_page}",
            "  internal_links:",
        ]
    )
    lines.extend(f"    - {link}" for link in article["internal_links"])
    lines.extend(
        [
            f"  blog_category: {article['category']}",
            "  blog_tags:",
        ]
    )
    lines.extend(f"    - {tag}" for tag in article["tags"])
    lines.extend(
        [
            f"  pillar: {pillar}",
            f'  cta: "{article["target_cta"]}"',
            "  status: ready-for-publish",
            f"  word_target: {WORD_TARGET_BY_CATEGORY[article['category']]}",
            "seo:",
            f'  meta_title: "{article["title"]}"',
            f'  meta_description: "{meta_description(article)}"',
            "editorial_review: standard",
            "---",
        ]
    )
    return "\n".join(lines)


def intent_for(article: dict) -> str:
    category = article["category"]
    stage = article["funnel_stage"]
    if category == "comparisons":
        return "commercial"
    if category == "troubleshooting":
        return "troubleshooting"
    if stage == "bottom":
        return "commercial investigation"
    if stage == "middle":
        return "informational-commercial"
    return "informational"


def intro(article: dict) -> str:
    first = article["internal_links"][0]
    return (
        f"{article['title']} is a practical workflow guide for {article['primary_icp'].lower()}s "
        f"who need better search discovery without turning every indexing issue into a product problem.\n\n"
        f"If you need the wider context first, start with the {md_link(first)}. This guide focuses on "
        f"{article['primary_keyword']} and shows how to diagnose the issue, prioritize the work, and "
        "choose the next step with realistic expectations."
    )


def short_answer(article: dict) -> str:
    return (
        f"The short answer: {article['primary_keyword']} should be handled as a workflow, not as a one-click fix. "
        "The useful sequence is to confirm that the page or asset is accessible, check the signals that affect "
        "discovery, decide whether the URL deserves attention, and only then use submission or tracking tools.\n\n"
        "FreeIndexer can help when the work becomes repetitive, especially for priority URLs, known backlinks, "
        "bulk lists, or client queues. It should not replace crawlability checks, quality review, Search Console "
        "diagnostics, internal linking, or sitemap hygiene."
    )


def when_it_matters(article: dict) -> str:
    secondary = article.get("secondary_icp") or "SEO teams"
    return (
        f"This matters most for {article['primary_icp'].lower()}s and {secondary.lower()} when search visibility "
        "depends on repeatable operating habits. A single URL can usually be checked manually. A recurring workflow "
        "needs clearer rules: what enters the queue, what gets fixed first, what is worth tracking, and what should "
        "not be submitted again without a meaningful change.\n\n"
        "Use this article when you are dealing with new pages, updated pages, technical fixes, backlink discovery, "
        "content launches, site migrations, or recurring client work. The goal is to reduce guesswork and make the "
        "next action obvious."
    )


def checks_section(article: dict) -> str:
    category = article["category"]
    if category == "technical-seo":
        items = [
            "the URL returns a successful status code",
            "robots.txt is not blocking important paths",
            "no accidental noindex directive is present",
            "the canonical tag points to the preferred URL",
            "the page is included in the right sitemap",
            "internal links point to the page from relevant places",
        ]
    elif category == "google-search-console":
        items = [
            "inspect the exact canonical URL",
            "review sitemap fetch and discovery status",
            "compare indexed and not-indexed patterns",
            "look for crawling and canonical messages",
            "separate site-wide patterns from one-off URL problems",
        ]
    elif category == "backlinks":
        items = [
            "verify that the linking URL is live",
            "confirm the link is visible on the page",
            "remove broken, blocked, or low-value URLs",
            "group links by campaign, client, or target page",
            "track submitted links without promising a fixed indexing outcome",
        ]
    elif category == "comparisons":
        items = [
            "how often the workflow runs",
            "whether the team can maintain a technical setup",
            "how many URLs or backlinks need handling",
            "whether diagnostics or submission is the main problem",
            "what reporting language the team needs",
        ]
    else:
        items = [
            "the page or backlink is live",
            "the URL is crawlable and indexable",
            "the content is useful and not duplicated",
            "internal links or supporting signals exist",
            "the URL is important enough to track",
        ]
    bullets = "\n".join(f"- {item}" for item in items)
    return (
        "Before using any submission workflow, check the basics. The exact checks change by topic, but the operating "
        "principle stays the same: do not put broken or low-value URLs into the queue and expect the queue to solve "
        "the underlying issue.\n\n"
        f"{bullets}\n\n"
        "If one of these checks fails, fix that issue first. Submission is most useful after the URL has a clean path "
        "to discovery."
    )


def workflow_section(article: dict) -> str:
    link_bits = [md_link(slug) for slug in article["internal_links"][1:4]]
    link_sentence = ""
    if link_bits:
        link_sentence = f" Related next reads: {sentence_list(link_bits)}."
    return (
        "A practical workflow has four parts.\n\n"
        "1. Build the list. Collect the URLs, backlinks, pages, reports, or sitemap entries that need review.\n"
        "2. Qualify the list. Remove URLs that are blocked, duplicated, redirected, low value, or not ready.\n"
        "3. Prioritize the list. Put business-critical pages, important updates, and verified backlinks ahead of noise.\n"
        "4. Act and track. Submit, fix, or monitor based on the issue type, then record what changed.\n\n"
        "This workflow keeps the team from treating every not-indexed URL the same way. Some URLs need technical "
        "repair. Some need stronger internal links. Some need content improvement. Some should not be indexed at all."
        + link_sentence
    )


def category_specific(article: dict) -> str:
    category = article["category"]
    if category == "comparisons":
        return dedent(
            """\
            ## Decision Framework

            Use the comparison through a workflow lens, not a feature-count lens.

            | Question | Why it matters |
            |---|---|
            | Is the problem diagnostic or operational? | Search Console and audits help diagnose; tools help operate repeat queues. |
            | How often does the work repeat? | Rare work can stay manual; recurring work needs a system. |
            | Who owns the workflow? | Website owners, agencies, and technical teams need different levels of control. |
            | What needs reporting? | Client work needs clear status language and evidence of process. |
            | What happens when a URL fails? | The best workflow routes failures back to technical or content checks. |

            A good choice should reduce manual work without hiding the checks that make discovery more likely.
            """
        ).strip()
    if category == "troubleshooting":
        return (
            "## How To Diagnose The Problem\n\n"
            "Start by narrowing the problem. Is the URL unknown, blocked, crawled but not indexed, canonicalized "
            "elsewhere, or simply not strong enough to deserve search visibility yet? Each answer leads to a different "
            "next step.\n\n"
            "Check the live URL, then inspect it in Search Console if available. Review robots rules, noindex, canonicals, "
            "internal links, sitemap inclusion, and page quality. If the issue affects many URLs, look for a template, "
            "CMS, sitemap, or site architecture pattern instead of fixing one page at a time."
        )
    if category == "desktop-app":
        return (
            "## When A Desktop Workflow Helps\n\n"
            "A desktop workflow helps when you work with repeated URL lists, client batches, backlink exports, or local "
            "campaign files. It is less useful when you only submit one occasional page.\n\n"
            "The key benefit is control. You can keep lists organized locally, prepare batches, and handle recurring "
            "submission work without rebuilding the same queue every day. That makes sense for agencies, affiliates, "
            "and blog or network owners who already work from structured URL files."
        )
    if category == "ai-search-visibility":
        return (
            "## How AI Search Changes The Visibility Conversation\n\n"
            "AI search does not remove the need for technical foundations. Crawlable pages, clear structure, strong "
            "internal links, consistent entities, helpful content, and accessible source pages still matter. The newer "
            "question is how content becomes findable, understandable, and trustworthy across search surfaces.\n\n"
            "Treat AI visibility as an extension of search visibility. Do not chase speculative tactics before fixing "
            "the basics that make content discoverable in the first place."
        )
    if category == "bulk-seo-operations":
        return (
            "## Batch Rules\n\n"
            "Bulk work needs rules before it needs more volume. Separate URLs into tiers: business-critical, important, "
            "supporting, experimental, and low priority. Each tier should have a different review and submission rhythm.\n\n"
            "For large sites, the quality gate is the most important part of the workflow. If a URL set is thin, duplicated, "
            "blocked, or poorly linked, submitting more of it only creates more tracking noise."
        )
    return (
        "## Practical Operating Notes\n\n"
        "Keep the workflow simple enough to repeat. A good process should tell you what to check, what to fix, what to "
        "submit, and what to ignore for now. If the process depends on memory or one person's private spreadsheet, it "
        "will break as soon as the volume increases.\n\n"
        "Document the decision rules. This is especially useful for agencies, webmasters, and product teams because it "
        "makes the work easier to explain later."
    )


def freeindexer_section(article: dict) -> str:
    category = article["category"]
    if category == "ai-search-visibility":
        return (
            "## Where Submission Work Fits\n\n"
            "Submission tools are not the center of AI search visibility. They are useful only for the web discovery layer: "
            "important pages should be crawlable, linked, and visible before any broader visibility work can build on them."
        )
    if category in {"technical-seo", "troubleshooting"}:
        return (
            "## When FreeIndexer Fits\n\n"
            "FreeIndexer fits after the technical checks are clean. Use it for URLs or backlinks that are live, indexable, "
            "important, and worth tracking. Do not use it as a way to avoid fixing robots, noindex, canonical, sitemap, "
            "internal-linking, or quality problems."
        )
    if category == "comparisons":
        return (
            "## When FreeIndexer Is Worth Considering\n\n"
            "FreeIndexer is worth considering when you want a repeatable URL and backlink submission workflow without "
            "building a custom system. It is a practical fit for website owners, agencies, affiliates, and operators who "
            "need a queue rather than one-off manual submission."
        )
    if category == "desktop-app":
        return (
            "## How FreeIndexer Fits\n\n"
            "The desktop app is the product layer for users who prefer local list handling and repeat batches. It works best "
            "when you already know which URLs or backlinks should enter the queue and need a comfortable way to process them."
        )
    return (
        "## When FreeIndexer Fits\n\n"
        "FreeIndexer fits when the workflow becomes repetitive. It can help with priority URL submission, backlink discovery "
        "queues, agency batches, desktop-style lists, and recurring search discovery operations. The best use case is not "
        "blind submission; it is organized submission after the right checks are done."
    )


def mistakes_section(article: dict) -> str:
    mistakes = [
        "submitting the same URL repeatedly without changing anything",
        "ignoring crawlability or indexability blockers",
        "treating low-value URLs as high-priority work",
        "confusing indexing with ranking",
        "using absolute promises in reports",
    ]
    if article["category"] == "backlinks":
        mistakes[2] = "submitting unverified or irrelevant backlink URLs"
    if article["category"] == "google-search-console":
        mistakes[0] = "reading one Search Console status without checking the exact URL"
    if article["category"] == "comparisons":
        mistakes[2] = "choosing a tool before defining the workflow"
    bullets = "\n".join(f"- {item}" for item in mistakes)
    return (
        "The most common mistakes are workflow mistakes, not tool mistakes.\n\n"
        f"{bullets}\n\n"
        "Avoiding these mistakes keeps the workflow practical and makes the outcome easier to explain."
    )


def example_workflow(article: dict) -> str:
    category = article["category"]
    if category == "comparisons":
        example = (
            "Imagine a team that publishes a few important pages each month and checks Search Console manually. "
            "That team may not need a heavy workflow. Now compare that with an agency managing client pages, "
            "backlink lists, and recurring updates. The agency needs clearer ownership, batch rules, and a tool "
            "or system that keeps the queue visible."
        )
    elif category == "backlinks":
        example = (
            "A practical backlink workflow might start with a campaign sheet. The operator verifies each linking URL, "
            "removes broken placements, groups links by target page, and submits only the links that are live and worth "
            "tracking. The report then says what was verified and submitted instead of making an outcome promise."
        )
    elif category == "technical-seo":
        example = (
            "For a technical SEO audit, start with a sample of important URLs. If one template has the wrong canonical, "
            "do not fix only one URL. Fix the template, regenerate the affected pages if needed, update the sitemap, "
            "and then decide which URLs deserve submission or follow-up monitoring."
        )
    elif category == "google-search-console":
        example = (
            "A Search Console workflow works best when you inspect one URL, then look for the pattern behind it. If "
            "many similar pages have the same status, treat it as a site or template problem. If only one page is "
            "affected, the next step may be page-specific content, linking, or submission work."
        )
    elif category == "bulk-seo-operations":
        example = (
            "For a large URL set, do not begin with the full export. Take a sample, identify the patterns, remove URLs "
            "that should not be indexed, and split the remaining list by priority. The first batch should teach you "
            "whether the workflow is working before the team processes the rest."
        )
    else:
        example = (
            "A simple example is a website owner publishing a new service page. The page should be live, internally "
            "linked, present in the sitemap, and useful enough to deserve search visibility. Only after those checks "
            "does submission become a sensible final step rather than a guess."
        )
    return (
        f"{example}\n\n"
        "This kind of example matters because it turns SEO advice into an operating habit. The operator knows what "
        "to check, what to fix, what to record, and when to stop repeating the same action."
    )


def quality_bar(article: dict) -> str:
    return (
        "Before a URL enters the workflow, set a quality bar. The URL should have a clear purpose, a useful page, "
        "a crawlable path, and a reason to be tracked. If the item is a backlink, the linking page should be live "
        "and the link should be visible. If the item is a sitemap URL, it should be canonical and indexable.\n\n"
        "This quality bar protects the workflow from noise. It also makes reporting more honest. Instead of saying "
        "that every URL was treated equally, the team can explain which URLs were ready, which needed repair, and "
        "which should not be pushed further until the underlying problem changes."
    )


def tracking_section(article: dict) -> str:
    category = article["category"]
    if category == "comparisons":
        focus = "decision owner, workflow cost, technical burden, setup time, recurring effort, and failure handling"
    elif category == "google-search-console":
        focus = "inspection date, Search Console status, sitemap status, canonical result, crawl message, and next action"
    elif category == "backlinks":
        focus = "linking URL, target URL, campaign, verification date, submission date, and whether the link is still present"
    elif category == "bulk-seo-operations":
        focus = "batch name, URL tier, quality gate result, submission date, follow-up date, and reason for priority"
    else:
        focus = "URL, reason for review, checks completed, issue found, action taken, follow-up date, and owner"
    return (
        f"Track {focus}. You do not need a complicated system at the start. A spreadsheet, project board, or simple "
        "queue is enough as long as the fields are consistent.\n\n"
        "The most useful tracking habit is writing down why the action happened. A URL submitted because it is a new "
        "priority page is different from a URL resubmitted after a canonical fix. That context helps future reviews "
        "and keeps the team from repeating work without learning from it."
    )


def faq(article: dict) -> str:
    keyword = article["primary_keyword"]
    category = article["category"]
    q2 = "Should I use FreeIndexer for this workflow?"
    a2 = (
        "Use FreeIndexer when you have qualified URLs or backlinks that deserve repeat submission and tracking. "
        "Do the diagnostic checks first."
    )
    if category == "ai-search-visibility":
        q2 = "Does FreeIndexer directly control AI search visibility?"
        a2 = "No. It can support the web discovery layer, but AI visibility depends on broader content, structure, and authority signals."
    questions = [
        (
            f"What is the first step for {keyword}?",
            "Start by confirming the URL, page, backlink, or report item is real, accessible, and worth action. Then check the technical and workflow signals that affect discovery.",
        ),
        (q2, a2),
        (
            "Can this process force Google to index a page?",
            "No. The process can improve discovery and reduce obvious blockers, but search engines decide what gets indexed.",
        ),
        (
            "How often should this workflow be repeated?",
            "Repeat it when new pages, updated pages, new backlinks, sitemap changes, or technical fixes create a real reason to review the URL set again.",
        ),
        (
            "What should be tracked?",
            "Track the URL, reason for action, checks completed, submission date if relevant, follow-up status, and notes about any blockers or improvements.",
        ),
    ]
    rendered = ["## FAQ"]
    for question, answer in questions:
        rendered.append(f"\n### {question}\n\n{answer}")
    return "\n".join(rendered)


def next_step(article: dict) -> str:
    return (
        f"## Next Step\n\n{article['target_cta']} Keep the workflow honest: check the URL, fix the blockers, prioritize the work, "
        "and use submission tools only when they support a clear operating process."
    )


def body(article: dict) -> str:
    return "\n\n".join(
        [
            intro(article),
            "## The Short Answer\n\n" + short_answer(article),
            "## When This Matters\n\n" + when_it_matters(article),
            "## What To Check First\n\n" + checks_section(article),
            "## Recommended Workflow\n\n" + workflow_section(article),
            category_specific(article),
            freeindexer_section(article),
            "## Example Workflow\n\n" + example_workflow(article),
            "## Quality Bar Before Submission\n\n" + quality_bar(article),
            "## What To Track\n\n" + tracking_section(article),
            "## Common Mistakes\n\n" + mistakes_section(article),
            faq(article),
            next_step(article),
        ]
    )


def write_article(article: dict, overwrite: bool = True) -> Path:
    folder = CONTENT_DIR / CATEGORY_DIR[article["category"]]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{article['slug']}.md"
    if path.exists() and not overwrite:
        return path
    text = frontmatter(article) + "\n\n" + body(article) + "\n"
    # Keep generated markdown ASCII-only and avoid accidental extra spaces.
    text = re.sub(r"\n{3,}", "\n\n", text)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    paths = []
    for article in plan["articles"]:
        paths.append(write_article(article))
    print(f"wrote {len(paths)} planned articles")
    for path in paths:
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
