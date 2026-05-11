# How To Create A FreeIndexer Hero Image

FreeIndexer follows the CaptchaRank two-step image model: generate a subject image, then composite it into a branded 1200x630 hero template.

```text
content/**/{slug}.md
        ↓
scripts/generate_image.py --slug {slug}
        ↓
images/exports/subjects/{slug}-subject.png
        ↓
scripts/build_hero.py --slug {slug} --template N
        ↓
images/exports/{slug}-hero.png
images/exports/heroes/{slug}-tNN-hero.png
images/exports/validated/{slug}-tNN-validated.png
```

## 1. Read Article Metadata

Start with the article markdown file under `content/`.

Required fields:

- `title`
- `slug`
- `description`
- `icp`
- `type`
- `meta.blog_category`
- `seo.meta_title`

The title becomes the hero title. The ICP, type, and category guide the subject prompt and template selection.

## 2. Generate The Subject Image

Expected command:

```powershell
python scripts/generate_image.py --slug {slug}
```

Expected output:

```text
images/exports/subjects/{slug}-subject.png
```

Useful dry run:

```powershell
python scripts/generate_image.py --slug {slug} --prompt-only
```

The script currently defines the expected interface and prompt rules. Actual image API integration is blocked until the team chooses the image provider and supplies credentials.

## 3. Build The Hero Image

Expected command:

```powershell
python scripts/build_hero.py --slug {slug} --template 1
```

Expected outputs:

```text
images/exports/{slug}-hero.png
images/exports/heroes/{slug}-t01-hero.png
```

With validation overlay:

```powershell
python scripts/build_hero.py --slug {slug} --template 1 --validator
```

Expected overlay:

```text
images/exports/validated/{slug}-t01-validated.png
```

## 4. Template Selection

| Template | Best for |
|---|---|
| 1 | education and troubleshooting |
| 2 | agency, bulk, and programmatic workflows |
| 3 | comparisons and buying guides |
| 4 | desktop app and product workflow articles |

Template docs live in `images/templates/`.

## 5. QA Checklist

- Title is readable at 1200x630 and social-card size.
- Subject reinforces the article topic.
- No fake Google logo or official Search Console screenshot.
- No `100% indexed`, guaranteed ranking, or exact unvalidated site-count claim.
- CTA-like text is not added to the hero.
- The canonical file exists at `images/exports/{slug}-hero.png`.

## 6. Upload

After approval, upload with:

```powershell
python scripts/prepare_blog_draft.py content/path/{slug}.md --upload-image
```

Direct upload is blocked until `reference/blog_api.json` and `reference/hetzner_object_storage.json` are created from the example files with owner-provided values.

## TODO

- Implement real image provider integration in `scripts/generate_image.py`.
- Add actual 1200x630 PNG template backgrounds and validator overlays if the team wants pixel-perfect compositing.
- Implement full Pillow-based compositing in `scripts/build_hero.py` after template art is approved.

