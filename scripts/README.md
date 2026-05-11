# FreeIndexer Scripts

This folder mirrors the CaptchaRank content production scripts, adapted for the current FreeIndexer repo.

## Working Locally Now

- `build_master_articles.py`: scans `content/**/*.md` and rebuilds `pipeline/master-articles.csv`.
- `validate_content.py`: validates required frontmatter and basic content rules.

## Interfaces Defined, Blocked By Setup

- `generate_image.py`: builds the expected FreeIndexer image prompt and output path; real provider integration is TODO.
- `build_hero.py`: defines the canonical hero build interface; real compositing is TODO until template PNGs are approved.
- `prepare_blog_draft.py`: direct upload/draft submission interface; blocked until owner provides blog API and storage config.
- `sync_blog_taxonomy.py`: taxonomy seeding interface; blocked until owner confirms API flow and taxonomy rules.
- `sync_publishing_tracker.py`: tracker sync interface; live verification blocked until blog URL/API details are provided.

## Standard Commands

```powershell
python scripts/validate_content.py
python scripts/build_master_articles.py
python scripts/generate_image.py --slug free-url-indexer --prompt-only
python scripts/build_hero.py --slug free-url-indexer --template 1
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image
```

