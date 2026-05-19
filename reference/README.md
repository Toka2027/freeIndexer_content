# FreeIndexer Reference Setup

This directory contains configuration examples and taxonomy files for direct blog upload.

The publishing engine is implemented. Live upload is intentionally blocked until
the project owner provides the FreeIndexer blog API, taxonomy approval, and
object storage values. Do not invent these values.

## Files

| File | Purpose | Status |
|---|---|---|
| `blog_api.example.json` | Example blog API config with `FILL_IN_*` placeholders | Ready for owner values |
| `hetzner_object_storage.example.json` | Example object storage config with `FILL_IN_*` placeholders | Ready for owner values |
| `image_provider.example.json` | Optional OpenAI image provider override template | Ready |
| `blog_taxonomy.json` | Expanded FreeIndexer categories and tags to sync after approval | Draft, needs owner approval |
| `blog_taxonomy_live.json` | Live taxonomy IDs after sync | Existing live snapshot; do not treat as approved for new taxonomy |
| `source-notes.md` | Research notes from playbook, public site, and reference repos | Ready |

## Required Owner Values

Real upload cannot run until these values are provided:

- blog API endpoint, usually `https://blogs.99sync.com`; configs that already
  include `/api` are still supported.
- application_id
- api_key
- secret_key
- author_id
- blog domain or target blog URL
- category approval
- tag approval
- S3/object storage provider
- bucket name
- access key
- secret key
- base public asset URL
- final hero image upload path convention
- confirmation that FreeIndexer uses the same signed 99sync API flow as CaptchaRank
- whether Bootstrap 5 HTML post-processing is required
- upload mode confirmation; default is `draft`
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
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --dry-run
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image --dry-run
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md
```

You can keep API secrets out of `reference/blog_api.json` by putting them in
`.env` instead. Supported overrides:

```text
BLOG_API_APPLICATION_ID=
BLOG_API_KEY=
BLOG_API_SECRET_KEY=
BLOG_API_AUTHOR_ID=
BLOG_API_DOMAIN=
```

The local `reference/blog_api.json` in this workspace now has the non-secret
FreeIndexer values that were provided: application ID `29`, author ID `20`,
draft mode, and `https://blog.freeindexer.com/`. The API key/secret should be
supplied through `.env` or filled locally in the ignored config file.

## Central Blogs API Notes

`blogs_center.postman_collection.json` documents the current signed API shape.
The Python client supports the collection's `{{baseUrl}}/api/...` convention and
the older `base_url` value that already ends with `/api`.

Available signed resources in the collection:

- `blogs`: list/create/update through the existing publishing flow.
- `categories`: list/create/update/delete, including `min_description` and
  `image` fields.
- `tags`: list/create/update/delete, including `min_description` and `image`
  fields.
- `authors`: list/create/show/update/delete.
- `series`: list/create/show/update/delete with ordered blog items.

Taxonomy sync now sends `min_description` and `image` when present in
`blog_taxonomy.json`, and derives a short description when it is missing.

## Publishing Flow

1. Confirm `reference/blog_taxonomy.json` and `system/taxonomy-strategy.md`.
2. Run `python scripts/sync_blog_taxonomy.py` to write live category and tag IDs to `reference/blog_taxonomy_live.json`.
3. Build a canonical hero at `images/exports/{slug}-hero.png`.
4. Run `python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image`.
5. Run `python scripts/prepare_blog_draft.py content/path/{slug}.md`.

Draft submission stays `draft` by default. The script resolves existing posts by
slug and updates them instead of creating duplicates.

Do not sync the expanded taxonomy until the owner approves the new categories,
especially `bulk-seo-operations` and `ai-search-visibility`.

## Security Rule

Do not commit real `blog_api.json`, `hetzner_object_storage.json`, `image_provider.json`, `.env`, or `.secrets/` files unless the owner explicitly confirms this repository is private and those files should be tracked.
