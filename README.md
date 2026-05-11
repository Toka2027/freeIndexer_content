# FreeIndexer Content System

This repository is the content operating system for FreeIndexer.

FreeIndexer helps website owners, SEO teams, affiliate operators, programmatic SEO builders, and product teams submit URLs and backlinks for faster search discovery. The content system is built around ICP problems first, then SEO demand.

## What This Repo Contains

```text
freeIndexer_content/
├── content/              # Source article briefs organized by hub/category
├── briefs/               # Batch-level production briefs
├── templates/            # Reusable article templates
├── system/               # Strategy, editorial rules, ICPs, maps, roadmap
├── pipeline/             # Article inventory and production state
├── reference/            # Source notes and validation reminders
└── assumptions.md        # Explicit assumptions and validation items
```

## Start Here

Read these files in order:

1. [system/product-positioning.md](system/product-positioning.md)
2. [system/icp-language-matrix.md](system/icp-language-matrix.md)
3. [system/topical-map.md](system/topical-map.md)
4. [system/article-blueprint.md](system/article-blueprint.md)
5. [system/keyword-scoring.md](system/keyword-scoring.md)
6. [system/naming-and-markdown-style.md](system/naming-and-markdown-style.md)
7. [briefs/batch-01/README.md](briefs/batch-01/README.md)

## Content Rule

Every article must have one primary ICP, one funnel stage, one search intent, one clear CTA, and a first internal link that points to its hub pillar.

Do not make unvalidated claims such as guaranteed Google indexing, "100% indexed", or a specific number of submission/statistic sites unless the product owner has confirmed the current claim. See [assumptions.md](assumptions.md).

## Production Flow

1. Pick the next article from [pipeline/master-articles.csv](pipeline/master-articles.csv).
2. Open the matching file under `content/`.
3. Use the frontmatter as the source of truth.
4. Expand the brief into a full article using the matching template in `templates/`.
5. Keep the first internal link pointed to the hub pillar.
6. Add evidence, screenshots, examples, or product screenshots where available.
7. Keep the CTA aligned with the reader's funnel stage.

## Current First Batch

The first batch focuses on ICP-led acquisition:

- website owners with indexing delays
- SEO agencies managing many URLs
- affiliate marketers publishing money pages and supporting content
- programmatic SEO builders with large page sets
- SaaS/product teams publishing docs, changelogs, and landing pages
- users comparing indexing tools and APIs

This is intentionally not a generic "SEO tips" blog. It is a FreeIndexer acquisition and education system.
