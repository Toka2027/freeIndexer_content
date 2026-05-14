# How To Create A FreeIndexer Hero Image

FreeIndexer uses a two-step image pipeline:

```text
content/**/{slug}.md
        |
        v
scripts/generate_image.py --slug {slug}
        |
        v
images/exports/subjects/{slug}-subject.png
        |
        v
scripts/build_hero.py --slug {slug}
        |
        v
images/exports/{slug}-hero.png
images/exports/heroes/{slug}-tNN-hero.png
images/exports/validated/{slug}-tNN-validated.png
```

The generated subject image is provider-created. The final hero is a local
Pillow composite using a FreeIndexer template, the article title, and the
subject PNG.

## 0. Prerequisites

Install the publishing/image dependencies:

```powershell
pip install -r scripts/requirements-publishing.txt
```

For real image generation, add the API key to `.env`:

```text
OPENAI_API_KEY=sk-...
```

`reference/image_provider.json` is optional. If it is absent, the generator
uses the OpenAI defaults from `reference/image_provider.example.json`.

Do not commit `.env`, `.secrets/`, or `reference/image_provider.json`.

## 1. Generate The Subject Image

Dry run:

```powershell
python scripts/generate_image.py --slug free-url-indexer --prompt-only
```

Check provider readiness:

```powershell
python scripts/generate_image.py --slug free-url-indexer --check-config
```

Generate:

```powershell
python scripts/generate_image.py --slug free-url-indexer
```

Output:

```text
images/exports/subjects/free-url-indexer-subject.png
```

The prompt is FreeIndexer-specific. It asks for clean indexing workflow
subjects such as URL queues, backlink discovery graphs, submitted/pending/
discovered states, browser panels, desktop app windows, and SEO workflow
dashboards.

Prompt restrictions:

- no real Google logos
- no real Search Console screenshots
- no 100% indexed claims
- no guaranteed indexing or ranking claims
- no fake exact numbers such as 15,000 sites or 300 sites
- no spammy backlink blast visuals
- no dark hacker visual language
- no CaptchaRank mint/green branding

## 2. Build The Hero Image

Check local assets first:

```powershell
python scripts/build_hero.py --slug free-url-indexer --template all --check-assets
```

Build one hero with random template selection:

```powershell
python scripts/build_hero.py --slug free-url-indexer
```

The default template selection is `random`, seeded by the article slug so
templates vary among articles while staying reproducible for the same slug.
Use `--seed VALUE` to change the selection, or pass `--template 1`, `2`, or
`3` to force a specific template.

Build all template examples with QA overlays:

```powershell
python scripts/build_hero.py --slug free-url-indexer --template all --validator
```

Outputs:

```text
images/exports/free-url-indexer-hero.png
images/exports/heroes/free-url-indexer-t01-hero.png
images/exports/validated/free-url-indexer-t01-validated.png
```

The builder:

1. Loads `reference/image-templates.json`.
2. Loads `images/templates/{N}.png`.
3. Auto-detects the title zone and image zone from `images/templates/{N}-v.png`.
4. Removes edge-connected white background from the subject image.
5. Places the subject inside the image zone with breathing room.
6. Renders the article title in Poppins SemiBold using max 3 lines.
7. Writes the canonical hero, per-template QA hero, and optional validated overlay.

## 3. Template Selection

| Template | Best for |
|---|---|
| 1 | education and troubleshooting |
| 2 | agency, bulk, and programmatic workflows |
| 3 | comparisons, buying guides, and product workflow articles; white title text |

Template docs live in `images/templates/`.

## 4. Template Assets

Each template needs:

- `images/templates/{N}.png`: 1200x630 background
- `images/templates/{N}-v.png`: same background with validator rectangles
- `images/templates/{N}-template.md`: usage notes

Validator colors:

- title zone: blue `#1E5AD2`
- image zone: red `#CC0000`

The validator PNG is the source of truth. The percentage zones in
`reference/image-templates.json` are fallback values for `--no-validator-detect`.

## 5. QA Checklist

- Title is readable at social-card size.
- Subject reinforces the article topic.
- Orange `#f96332` appears as the main FreeIndexer accent.
- Charcoal `#212529` is used for title and strong contrast.
- No CaptchaRank mint/green branding.
- No fake Google UI, indexing guarantees, ranking guarantees, or exact
  unvalidated numbers.
- Canonical hero exists at `images/exports/{slug}-hero.png`.

## 6. Upload

After visual approval, upload through the publishing pipeline only:

```powershell
python scripts/prepare_blog_draft.py content/commercial/free-url-indexer.md --upload-image
```

Direct upload still depends on owner-provided blog API and object storage
configuration.
