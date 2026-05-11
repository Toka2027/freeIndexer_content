# Full FreeIndexer Content Flow

This is the end-to-end workflow from article idea to blog draft with hero image.

Direct upload is blocked until the owner provides blog API and object storage details. The commands are still defined now so the repo mirrors the CaptchaRank operating model.

## Quick Reference

| Step | Command | Output |
|---|---|---|
| 1. Create article | Edit `content/**/{slug}.md` | article markdown |
| 2. Validate article | `python scripts/validate_content.py` | validation report |
| 3. Rebuild pipeline | `python scripts/build_master_articles.py` | `pipeline/master-articles.csv` |
| 4. Generate subject | `python scripts/generate_image.py --slug {slug}` | `images/exports/subjects/{slug}-subject.png` |
| 5. Build hero | `python scripts/build_hero.py --slug {slug} --template N` | canonical and QA hero files |
| 6. Review hero | open `images/exports/{slug}-hero.png` | approved/rejected image |
| 7. Upload hero | `python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image` | public image URL |
| 8. Submit draft | `python scripts/prepare_blog_draft.py content/path/{slug}.md` | blog draft |
| 9. Verify live URL | `python scripts/sync_publishing_tracker.py` | updated tracker |

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

```powershell
python scripts/validate_content.py
```

The validator checks:

- required frontmatter fields
- slug matches filename
- required metadata fields
- no unvalidated guarantee language
- first internal link exists for cluster articles

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

## 5. Build Hero Image

```powershell
python scripts/build_hero.py --slug {slug} --template N
```

Expected outputs:

```text
images/exports/{slug}-hero.png
images/exports/heroes/{slug}-tNN-hero.png
```

Optional overlay:

```powershell
python scripts/build_hero.py --slug {slug} --template N --validator
```

Expected output:

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

## 7. Upload Hero Image

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image
```

Blocked until owner provides:

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

## 8. Submit Blog Draft

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md
```

Blocked until owner provides:

- blog API endpoint
- application_id
- api_key
- secret_key
- author_id
- target blog domain
- whether the same 99sync.com API flow is used
- whether Bootstrap 5 post-processing is required
- whether posts should be draft-only or published directly

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
4. Run:

```powershell
python scripts/sync_blog_taxonomy.py
python scripts/validate_content.py
python scripts/build_master_articles.py
```

## Current Implementation Status

- `build_master_articles.py`: working local inventory builder.
- `validate_content.py`: working local metadata validator.
- `generate_image.py`: interface and prompt builder present; provider integration TODO.
- `build_hero.py`: interface present; full visual compositing TODO until templates/assets are approved.
- `prepare_blog_draft.py`: blocked by credentials and API contract.
- `sync_blog_taxonomy.py`: blocked by API contract.
- `sync_publishing_tracker.py`: local tracker checks present; live verification TODO until blog domain/API is provided.

