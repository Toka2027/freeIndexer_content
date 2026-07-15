# FreeIndexer Scripts

This folder mirrors the CaptchaRank content production scripts, adapted for the current FreeIndexer repo.

## Working Locally Now

- `build_master_articles.py`: scans `content/**/*.md` and rebuilds `pipeline/master-articles.csv`.
- `validate_content.py`: validates required frontmatter and basic content rules.
- `check_readiness.py`: audits image, upload, config, and tracker readiness without generating images or uploading anything.

## Image Generation And Hero Building

- `generate_image.py`: generates FreeIndexer subject PNGs with OpenAI when `OPENAI_API_KEY` is available; `--prompt-only` and `--check-config` are safe dry runs.
- `build_hero.py`: composites subject PNGs into 1200x630 FreeIndexer heroes with template backgrounds, detected validator zones, title rendering, white background removal, canonical output, QA output, and optional validated overlays.

## Publishing Interfaces

- `prepare_blog_draft.py`: converts markdown to Bootstrap-friendly HTML, uploads the hero to object storage, and creates or updates a draft through the signed 99sync API.
- `sync_blog_taxonomy.py`: creates or updates FreeIndexer categories and tags, including the Central Blogs API `min_description` and `image` fields when available, then writes live IDs to `reference/blog_taxonomy_live.json`.
- `sync_publishing_tracker.py`: audits tracker rows locally and can verify `published_url` values with `--check-live`. Live checks retry transient network failures, report failed URLs, separate not-yet-live future scheduled URLs, and, when written, store HTTP audit details in `live_check_ok` / `live_check_note` without overwriting publishing notes.

`blog_api_client.py` follows the `blogs_center.postman_collection.json` signing
model and supports both `https://blogs.99sync.com` and
`https://blogs.99sync.com/api` as `base_url` values.

Real network writes require `reference/blog_api.json`,
`reference/hetzner_object_storage.json`, and synced taxonomy IDs. Dry-runs do
not require secrets.

## Standard Commands

```powershell
python scripts/validate_content.py
python scripts/build_master_articles.py
python scripts/check_readiness.py
python scripts/generate_image.py --slug free-url-indexer --prompt-only
python scripts/build_hero.py --slug free-url-indexer --template all --check-assets
python scripts/build_hero.py --slug free-url-indexer
python scripts/build_hero.py --slug free-url-indexer --template all --validator
python scripts/sync_blog_taxonomy.py --validate-only
python scripts/sync_publishing_tracker.py --check-live
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --dry-run
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image --dry-run
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --check-config
```
