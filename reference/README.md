# FreeIndexer Reference Setup

This directory contains configuration examples and taxonomy files for direct blog upload.

Direct blog upload is currently blocked until the project owner provides the missing blog API, taxonomy, and object storage details. Do not invent these values.

## Files

| File | Purpose | Status |
|---|---|---|
| `blog_api.example.json` | Example blog API config with `FILL_IN_*` placeholders | Ready for owner values |
| `hetzner_object_storage.example.json` | Example object storage config with `FILL_IN_*` placeholders | Ready for owner values |
| `image_provider.example.json` | Optional OpenAI image provider override template | Ready |
| `blog_taxonomy.json` | Proposed FreeIndexer categories and tags | Draft, needs owner approval |
| `blog_taxonomy_live.json` | Live taxonomy IDs after sync | Not synced |
| `source-notes.md` | Research notes from playbook, public site, and reference repos | Ready |

## Blocked Until Owner Provides

Direct blog upload cannot work until these values are provided:

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
- final visual approval for 1200x630 hero template backgrounds and validator overlays

## Setup Steps After Owner Provides Values

1. Copy `reference/blog_api.example.json` to `reference/blog_api.json`.
2. Replace every `FILL_IN_*` value.
3. Copy `reference/hetzner_object_storage.example.json` to `reference/hetzner_object_storage.json`.
4. Replace every `FILL_IN_*` value.
5. Confirm taxonomy in `reference/blog_taxonomy.json`.
6. Add `OPENAI_API_KEY` to `.env` for generated subject images. Optionally copy `reference/image_provider.example.json` to `reference/image_provider.json` to override the model, quality, size, or API key environment variable.
7. Run:

```powershell
python scripts/check_readiness.py
python scripts/sync_blog_taxonomy.py
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md
```

## Security Rule

Do not commit real `blog_api.json`, `hetzner_object_storage.json`, `image_provider.json`, `.env`, or `.secrets/` files unless the owner explicitly confirms this repository is private and those files should be tracked.
