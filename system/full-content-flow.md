# Full FreeIndexer Content Flow

This is the end-to-end workflow from article idea to blog draft with hero image.

The image and publishing engines are implemented. Real network writes are
blocked until the owner provides blog API and object storage details, and until
taxonomy has been synced.

## Quick Reference

| Step | Command | Output |
|---|---|---|
| 1. Create article | Edit `content/**/{slug}.md` | article markdown |
| 2. Score article | Add `content_quality.score` and checks | score must be at least 9/10 |
| 3. Validate article | `python scripts/validate_content.py` | validation report |
| 4. Rebuild pipeline | `python scripts/build_master_articles.py` | `pipeline/master-articles.csv` |
| 5. Generate subject | `python scripts/generate_image.py --slug {slug}` | `images/exports/subjects/{slug}-subject.png` |
| 6. Build hero | `python scripts/build_hero.py --slug {slug}` | canonical and QA hero files |
| 7. Review hero | open `images/exports/{slug}-hero.png` | approved/rejected image |
| 8. Sync taxonomy | `python scripts/sync_blog_taxonomy.py` | live category and tag IDs |
| 9. Upload hero | `python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image` | public image URL |
| 10. Submit draft | `python scripts/prepare_blog_draft.py content/path/{slug}.md` | blog draft |
| 11. Verify live URL | `python scripts/sync_publishing_tracker.py` | updated tracker |

Readiness audit without generating images or uploading anything:

```powershell
python scripts/check_readiness.py
```

## 1. Create Article Markdown

Use the template that matches the article type:

- `templates/article-template.md`
- `templates/pillar-template.md`
- `templates/comparison-template.md`

Article files live under:

- `content/pillars/`
- `content/use-cases/`
- `content/comparisons/`
- `content/troubleshooting/`
- `content/commercial/`

## 2. Validate Article

Before validation, score the article using
[system/editorial-checklist.md](editorial-checklist.md). Any article uploaded
or scheduled through `prepare_blog_draft.py` must have
`content_quality.score >= 9`.

```powershell
python scripts/validate_content.py
```

The validator checks:

- required frontmatter fields
- scored article quality metadata
- at least three depth elements for scored articles
- slug matches filename
- required metadata fields
- no unvalidated guarantee language
- first internal link exists for cluster articles
- no internal planning headings in public body copy
- FAQ questions use `###`

## 3. Rebuild Pipeline CSV

```powershell
python scripts/build_master_articles.py
```

Expected output:

```text
pipeline/master-articles.csv
```

## 4. Generate Hero Subject

```powershell
python scripts/generate_image.py --slug {slug}
```

Expected output:

```text
images/exports/subjects/{slug}-subject.png
```

Dry run:

```powershell
python scripts/generate_image.py --slug {slug} --prompt-only
```

Image config check:

```powershell
python scripts/generate_image.py --slug {slug} --check-config
```

## 5. Build Hero Image

```powershell
python scripts/build_hero.py --slug {slug}
```

By default, the builder chooses a random configured template seeded by the
article slug. This spreads templates among articles while keeping the same
article reproducible. Use `--template 1`, `--template 2`, or `--template 3`
to force one design, or `--template all` for QA examples.

Expected outputs:

```text
images/exports/{slug}-hero.png
images/exports/heroes/{slug}-tNN-hero.png
```

Optional overlay:

```powershell
python scripts/build_hero.py --slug {slug} --template all --validator
```

Asset check without building:

```powershell
python scripts/build_hero.py --slug {slug} --template all --check-assets
```

Validated overlay output:

```text
images/exports/validated/{slug}-tNN-validated.png
```

## 6. Review Hero Image

Check:

- title readability
- subject relevance
- no unsupported search guarantee visual
- no exact unvalidated site-count claim
- no misleading official Google UI

## 7. Sync Blog Taxonomy

```powershell
python scripts/sync_blog_taxonomy.py
```

Dry-run or local validation:

```powershell
python scripts/sync_blog_taxonomy.py --validate-only
python scripts/sync_blog_taxonomy.py --dry-run
```

Expected output after real sync:

```text
reference/blog_taxonomy_live.json
```

Do not upload articles before taxonomy is synced. The draft script requires
live category and tag IDs for real submissions.

## 8. Upload Hero Image

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image
```

Dry-run upload payload:

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image --dry-run
```

Implemented through the object storage config. Blocked until owner provides:

- object storage provider
- bucket
- access key
- secret key
- base public asset URL
- final hero image path convention

Expected output after setup:

```text
uploaded_image_url
```

## 9. Submit Blog Draft

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md
```

Dry-run draft payload:

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md --dry-run
```

Implemented through the signed 99sync API. Blocked until owner provides:

- blog API endpoint
- application_id
- api_key
- secret_key
- author_id
- target blog domain
- confirmation that the same signed 99sync.com API flow is used
- whether Bootstrap 5 post-processing is required
- upload mode confirmation; default is `draft`

## 9. Verify Live URL And Update Tracker

```powershell
python scripts/sync_publishing_tracker.py
```

Expected tracker:

```text
pipeline/publishing-tracker.csv
```

## First-Time Setup

1. Copy `reference/blog_api.example.json` to `reference/blog_api.json`.
2. Copy `reference/hetzner_object_storage.example.json` to `reference/hetzner_object_storage.json`.
3. Replace all `FILL_IN_*` values with owner-provided values.
4. Add `OPENAI_API_KEY` to `.env` if generated subject images are needed.
5. Optionally copy `reference/image_provider.example.json` to `reference/image_provider.json` to override image model, size, quality, or API key environment variable.
6. Run:

```powershell
python scripts/sync_blog_taxonomy.py
python scripts/validate_content.py
python scripts/build_master_articles.py
```

## Current Implementation Status

- `build_master_articles.py`: working local inventory builder.
- `validate_content.py`: working local metadata validator.
- `generate_image.py`: OpenAI subject generation implemented; requires `OPENAI_API_KEY` for real API calls.
- `build_hero.py`: Pillow compositing implemented with template loading, validator zone detection, title rendering, white background removal, canonical output, QA output, and validated overlays.
- `prepare_blog_draft.py`: working draft-prep, hero upload, and signed create/update engine; blocked only by missing FreeIndexer credentials/config for real writes.
- `sync_blog_taxonomy.py`: working category/tag sync engine; blocked only by missing FreeIndexer credentials/config for real writes.
- `sync_publishing_tracker.py`: local tracker audit implemented, with optional `--check-live` URL verification.
