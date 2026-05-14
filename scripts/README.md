# FreeIndexer Scripts

This folder mirrors the CaptchaRank content production scripts, adapted for the current FreeIndexer repo.

## Working Locally Now

- `build_master_articles.py`: scans `content/**/*.md` and rebuilds `pipeline/master-articles.csv`.
- `validate_content.py`: validates required frontmatter and basic content rules.
- `check_readiness.py`: audits image, upload, config, and tracker readiness without generating images or uploading anything.

## Image Generation And Hero Building

- `generate_image.py`: generates FreeIndexer subject PNGs with OpenAI when `OPENAI_API_KEY` is available; `--prompt-only` and `--check-config` are safe dry runs.
- `build_hero.py`: composites subject PNGs into 1200x630 FreeIndexer heroes with template backgrounds, detected validator zones, title rendering, white background removal, canonical output, QA output, and optional validated overlays.

## Publishing Interfaces Blocked By Setup

- `prepare_blog_draft.py`: direct upload/draft submission interface; blocked until owner provides blog API and storage config.
- `sync_blog_taxonomy.py`: taxonomy seeding interface; blocked until owner confirms API flow and taxonomy rules.
- `sync_publishing_tracker.py`: tracker sync interface; live verification blocked until blog URL/API details are provided.

## Standard Commands

```powershell
python scripts/validate_content.py
python scripts/build_master_articles.py
python scripts/check_readiness.py
python scripts/generate_image.py --slug free-url-indexer --prompt-only
python scripts/build_hero.py --slug free-url-indexer --template all --check-assets
python scripts/build_hero.py --slug free-url-indexer
python scripts/build_hero.py --slug free-url-indexer --template all --validator
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --dry-run
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image --dry-run
```
