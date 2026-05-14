# FreeIndexer Content Production System

This repository is the content production system for FreeIndexer.

FreeIndexer helps website owners, SEO teams, affiliate operators, programmatic SEO builders, and product teams submit URLs and backlinks for faster search discovery. The content system is built around ICP problems first, then SEO demand.

The repo now follows the CaptchaRank operating model closely: source markdown, image workflow, validation scripts, pipeline CSVs, reference taxonomy, publishing tracker, and direct blog draft preparation once credentials are provided.

## What This Repo Contains

```text
freeIndexer_content/
├── content/              # Source article briefs organized by hub/category
├── briefs/               # Batch-level production briefs
├── templates/            # Reusable article templates
├── images/               # Brand image rules, templates, exports
├── scripts/              # Validation, pipeline, image, taxonomy, draft scripts
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
7. [system/how-to-create-image.md](system/how-to-create-image.md)
8. [system/full-content-flow.md](system/full-content-flow.md)
9. [reference/README.md](reference/README.md)
10. [briefs/batch-01/README.md](briefs/batch-01/README.md)

## Content Rule

Every article must have one primary ICP, one funnel stage, one search intent, one clear CTA, and a first internal link that points to its hub pillar.

Do not make unvalidated claims such as guaranteed Google indexing, "100% indexed", or a specific number of submission/statistic sites unless the product owner has confirmed the current claim. See [assumptions.md](assumptions.md).

## Production Flow

1. Pick the next article from [pipeline/master-articles.csv](pipeline/master-articles.csv).
2. Open the matching file under `content/`.
3. Expand the brief into a full article using the matching template in `templates/`.
4. Validate content:

```powershell
python scripts/validate_content.py
```

5. Rebuild the inventory:

```powershell
python scripts/build_master_articles.py
```

6. Generate the hero subject:

```powershell
python scripts/generate_image.py --slug {slug}
```

7. Build the branded hero:

```powershell
python scripts/build_hero.py --slug {slug}
```

The hero builder defaults to random template selection across configured templates, seeded by the article slug for reproducible article-to-template assignment.

8. Upload the hero and prepare a draft after credentials are provided:

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image
python scripts/prepare_blog_draft.py content/path/{slug}.md
```

9. Verify live status and update the tracker:

```powershell
python scripts/sync_publishing_tracker.py
```

## Current First Batch

The first batch focuses on ICP-led acquisition:

- website owners with indexing delays
- SEO agencies managing many URLs
- affiliate marketers publishing money pages and supporting content
- programmatic SEO builders with large page sets
- SaaS/product teams publishing docs, changelogs, and landing pages
- users comparing indexing tools and APIs

This is intentionally not a generic "SEO tips" blog. It is a FreeIndexer acquisition and education system.

## Image System

Image production lives under `images/`.

- [images/brand.md](images/brand.md): FreeIndexer image identity, colors, typography, allowed/forbidden visuals
- `images/templates/`: reusable hero template specs
- `images/exports/subjects/`: generated subject images
- `images/exports/heroes/`: per-template QA hero images
- `images/exports/validated/`: validated overlays
- `images/exports/{slug}-hero.png`: canonical hero uploaded to the blog

See [system/how-to-create-image.md](system/how-to-create-image.md).

## Publishing And Taxonomy

Publishing support lives in:

- [reference/README.md](reference/README.md)
- [reference/blog_api.example.json](reference/blog_api.example.json)
- [reference/hetzner_object_storage.example.json](reference/hetzner_object_storage.example.json)
- [reference/blog_taxonomy.json](reference/blog_taxonomy.json)
- [pipeline/publishing-tracker.csv](pipeline/publishing-tracker.csv)

Direct upload is intentionally blocked until owner-provided values are available.

## Blocked Until Owner Provides

Direct blog upload and hero upload need:

- blog API endpoint
- application_id
- api_key
- secret_key
- author_id
- blog domain or target blog URL
- category/taxonomy rules
- tag taxonomy rules
- S3/object storage provider
- bucket name
- access key
- secret key
- base public asset URL
- final hero image upload path convention
- whether FreeIndexer blog uses the same 99sync.com API flow as CaptchaRank
- whether Bootstrap 5 HTML post-processing is required
- whether posts should be uploaded as draft only or published directly

Use `FILL_IN_*` placeholders until those values are provided.
