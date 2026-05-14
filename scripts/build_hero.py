"""Composite a FreeIndexer subject PNG onto a branded 1200x630 hero template.

Pipeline:
    1. Load template config from reference/image-templates.json.
    2. Auto-detect title and image zones from images/templates/{N}-v.png.
    3. Remove edge-connected white background from the subject image.
    4. Place the subject inside the image zone with breathing room.
    5. Render the article title with the configured font.
    6. Save canonical, QA, and optional validated overlay outputs.

Usage:
    python scripts/build_hero.py --slug free-url-indexer --template 1 --check-assets
    python scripts/build_hero.py --slug free-url-indexer --template 1 --validator
    python scripts/build_hero.py --slug free-url-indexer --validator
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import deque
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
TEMPLATES_JSON = ROOT / "reference" / "image-templates.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

TITLE_ZONE_COLOR = (30, 90, 210)
IMAGE_ZONE_COLOR = (204, 0, 0)
LEGACY_IMAGE_ZONE_COLOR = (220, 15, 135)


def load_config() -> dict[str, Any]:
    if not TEMPLATES_JSON.exists():
        raise SystemExit(f"Template config not found: {TEMPLATES_JSON.relative_to(ROOT)}")
    cfg = json.loads(TEMPLATES_JSON.read_text(encoding="utf-8"))
    for key in ("canvas", "fonts", "image", "exports", "templates"):
        if key not in cfg:
            raise SystemExit(f"Missing {key!r} in {TEMPLATES_JSON.relative_to(ROOT)}")
    return cfg


def find_article(slug: str) -> Path | None:
    matches = sorted(CONTENT_DIR.rglob(f"{slug}.md"))
    return matches[0] if matches else None


def load_article_title(slug: str) -> str:
    article_path = find_article(slug)
    fallback = slug.replace("-", " ").title()
    if not article_path:
        return fallback
    text = article_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return fallback
    meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(meta, dict):
        return fallback
    seo = meta.get("seo") if isinstance(meta.get("seo"), dict) else {}
    return str(meta.get("title") or seo.get("meta_title") or fallback).strip()


def get_template(cfg: dict[str, Any], template_id: str | int) -> dict[str, Any]:
    key = f"T{int(template_id):02d}" if str(template_id).isdigit() else str(template_id).upper()
    for tpl in cfg["templates"]:
        if str(tpl.get("id", "")).upper() == key:
            return tpl
    raise SystemExit(f"Template {template_id!r} not found in {TEMPLATES_JSON.relative_to(ROOT)}")


def pick_template(cfg: dict[str, Any], template_id: str | int | None, seed: str | None = None) -> dict[str, Any]:
    """Return a configured template, optionally choosing one at random."""
    if template_id is None or str(template_id).lower() in {"random", "rand", "auto"}:
        templates = list(cfg["templates"])
        if not templates:
            raise SystemExit(f"No templates configured in {TEMPLATES_JSON.relative_to(ROOT)}")
        rng = random.Random(seed) if seed else random.SystemRandom()
        return rng.choice(templates)
    return get_template(cfg, template_id)


def _bbox_of_color(
    img: Image.Image,
    target_rgb: tuple[int, int, int],
    tol: int,
) -> tuple[int, int, int, int] | None:
    """Find the bounding box of pixels close to target_rgb within tol."""
    rgb = img.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    tr, tg, tb = target_rgb
    min_x, min_y, max_x, max_y = w, h, -1, -1

    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if abs(r - tr) <= tol and abs(g - tg) <= tol and abs(b - tb) <= tol:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < 0:
        return None
    return (min_x, min_y, max_x, max_y)


def _bbox_of_validator_red(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Find a red validator stroke without matching FreeIndexer orange art."""
    rgb = img.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    min_x, min_y, max_x, max_y = w, h, -1, -1

    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r >= 150 and g <= 80 and b <= 80:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < 0:
        return None
    return (min_x, min_y, max_x, max_y)


def detect_zones(validator_path: Path) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Return (title_box, image_box) from the validator PNG."""
    img = Image.open(validator_path).convert("RGB")
    title_box = _bbox_of_color(img, TITLE_ZONE_COLOR, tol=50)
    image_box = _bbox_of_validator_red(img)
    if image_box is None:
        image_box = _bbox_of_color(img, LEGACY_IMAGE_ZONE_COLOR, tol=25)
    if title_box is None or image_box is None:
        raise SystemExit(
            f"Could not find both validator zones in {validator_path.relative_to(ROOT)}. "
            "Use blue #1E5AD2 for the title zone and red #CC0000 for the image zone."
        )
    return title_box, image_box


def zone_from_pct(canvas_w: int, canvas_h: int, zone: dict[str, Any]) -> tuple[int, int, int, int]:
    x1 = int(round(canvas_w * float(zone["x_pct"]) / 100))
    y1 = int(round(canvas_h * float(zone["y_pct"]) / 100))
    x2 = x1 + int(round(canvas_w * float(zone["width_pct"]) / 100))
    y2 = y1 + int(round(canvas_h * float(zone["height_pct"]) / 100))
    return (x1, y1, x2, y2)


def _is_near_white(pixel: tuple[int, int, int, int], threshold: int) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= threshold and g >= threshold and b >= threshold


def remove_white_bg(img: Image.Image, threshold: int = 245, edge_only: bool = True) -> Image.Image:
    """Make near-white background transparent.

    The FreeIndexer subject often contains white dashboard cards. Edge-only
    removal preserves enclosed white panels while stripping the generated
    white canvas around the subject.
    """
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size

    if not edge_only:
        for y in range(h):
            for x in range(w):
                if _is_near_white(px[x, y], threshold):
                    r, g, b, _a = px[x, y]
                    px[x, y] = (r, g, b, 0)
        return img

    visited = bytearray(w * h)
    queue: deque[tuple[int, int]] = deque()

    def add_if_white(x: int, y: int) -> None:
        idx = y * w + x
        if visited[idx]:
            return
        visited[idx] = 1
        if _is_near_white(px[x, y], threshold):
            queue.append((x, y))

    for x in range(w):
        add_if_white(x, 0)
        add_if_white(x, h - 1)
    for y in range(h):
        add_if_white(0, y)
        add_if_white(w - 1, y)

    while queue:
        x, y = queue.popleft()
        r, g, b, _a = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                add_if_white(nx, ny)

    return img


def crop_to_content(img: Image.Image) -> Image.Image:
    alpha_bbox = img.getchannel("A").getbbox()
    return img.crop(alpha_bbox) if alpha_bbox else img


def fit_subject(
    subject: Image.Image,
    box: tuple[int, int, int, int],
    padding_pct: float,
) -> tuple[Image.Image, tuple[int, int]]:
    x1, y1, x2, y2 = box
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    pad_x = int(box_w * padding_pct / 100)
    pad_y = int(box_h * padding_pct / 100)
    avail_w = max(1, box_w - 2 * pad_x)
    avail_h = max(1, box_h - 2 * pad_y)

    sub_w, sub_h = subject.size
    if sub_w <= 0 or sub_h <= 0:
        raise SystemExit("Subject image has no drawable content.")

    scale = min(avail_w / sub_w, avail_h / sub_h)
    new_w = max(1, int(sub_w * scale))
    new_h = max(1, int(sub_h * scale))
    resized = subject.resize((new_w, new_h), Image.LANCZOS)

    paste_x = x1 + (box_w - new_w) // 2
    paste_y = y1 + (box_h - new_h) // 2
    return resized, (paste_x, paste_y)


def inset_box(box: tuple[int, int, int, int], padding_px: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return (x1 + padding_px, y1 + padding_px, x2 - padding_px, y2 - padding_px)


def _wrap_lines(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
) -> list[str] | None:
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = font.getbbox(candidate)
        if (bbox[2] - bbox[0]) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                return None

    if current:
        lines.append(current)
    if len(lines) > max_lines:
        return None

    for line in lines:
        bbox = font.getbbox(line)
        if (bbox[2] - bbox[0]) > max_width:
            return None
    return lines


def fit_title(
    text: str,
    font_path: Path,
    box_w: int,
    box_h: int,
    min_pt: int,
    max_pt: int,
    line_height: float,
    max_lines: int,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    best: tuple[ImageFont.FreeTypeFont, list[str], int] | None = None
    for pt in range(max_pt, min_pt - 1, -1):
        font = ImageFont.truetype(str(font_path), pt)
        lines = _wrap_lines(text, font, box_w, max_lines)
        if lines is None:
            continue
        ascent, descent = font.getmetrics()
        line_px = int((ascent + descent) * line_height)
        if line_px * len(lines) <= box_h:
            best = (font, lines, line_px)
            break

    if best:
        return best

    font = ImageFont.truetype(str(font_path), min_pt)
    lines = _wrap_lines(text, font, box_w, max_lines) or [text]
    ascent, descent = font.getmetrics()
    line_px = int((ascent + descent) * line_height)
    return font, lines, line_px


def draw_title(
    canvas: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    font_path: Path,
    color: str,
    min_pt: int,
    max_pt: int,
    line_height: float,
    max_lines: int,
    align: str,
) -> None:
    x1, y1, x2, y2 = box
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    font, lines, line_px = fit_title(text, font_path, box_w, box_h, min_pt, max_pt, line_height, max_lines)
    total_h = line_px * len(lines)
    block_top = y1 + (box_h - total_h) // 2

    draw = ImageDraw.Draw(canvas)
    for idx, line in enumerate(lines):
        line_bbox = font.getbbox(line)
        line_w = line_bbox[2] - line_bbox[0]
        if align == "center":
            x = x1 + (box_w - line_w) // 2
        else:
            x = x1
        y = block_top + idx * line_px
        draw.text((x, y), line, font=font, fill=color, anchor="lt")


def draw_validator_overlay(
    hero: Image.Image,
    title_box: tuple[int, int, int, int],
    image_box: tuple[int, int, int, int],
    font_path: Path,
) -> Image.Image:
    overlay = hero.convert("RGBA").copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(title_box, outline=(*TITLE_ZONE_COLOR, 255), width=4)
    draw.rectangle(image_box, outline=(*IMAGE_ZONE_COLOR, 255), width=4)
    try:
        label_font = ImageFont.truetype(str(font_path), 16)
        draw.text((title_box[0] + 8, title_box[1] + 6), "TITLE", font=label_font, fill=(*TITLE_ZONE_COLOR, 255))
        draw.text((image_box[0] + 8, image_box[1] + 6), "IMAGE", font=label_font, fill=(*IMAGE_ZONE_COLOR, 255))
    except Exception:
        pass
    return overlay


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def asset_paths(
    cfg: dict[str, Any],
    tpl: dict[str, Any],
    slug: str,
    subject_override: str | None,
) -> dict[str, Path]:
    subjects_dir = ROOT / str(cfg["exports"]["subjects_dir"])
    subject_path = Path(subject_override) if subject_override else subjects_dir / f"{slug}-subject.png"
    if not subject_path.is_absolute():
        subject_path = ROOT / subject_path
    return {
        "template": ROOT / str(tpl["background_png"]),
        "validator": ROOT / str(tpl["validator_png"]),
        "font": ROOT / str(cfg["fonts"]["title_path"]),
        "subject": subject_path,
    }


def check_assets(
    cfg: dict[str, Any],
    tpl: dict[str, Any] | None,
    slug: str,
    subject_override: str | None,
) -> int:
    if tpl is None:
        status = 0
        for candidate in cfg["templates"]:
            print(f"\nChecking {candidate['id']} ({candidate['name']})")
            status = max(status, check_assets(cfg, candidate, slug, subject_override))
        return status

    paths = asset_paths(cfg, tpl, slug, subject_override)
    missing = [f"{name}: {relative_or_absolute(path)}" for name, path in paths.items() if not path.exists()]

    if missing:
        print("Hero asset check failed; missing:")
        for item in missing:
            print(f"- {item}")
        print("Required: template PNG, validator PNG, title font, and subject PNG.")
        return 2

    canvas_w = int(cfg["canvas"]["width"])
    canvas_h = int(cfg["canvas"]["height"])
    title_box, image_box = detect_zones(paths["validator"])
    print("Hero asset check passed")
    print(f"Template: {relative_or_absolute(paths['template'])}")
    print(f"Validator: {relative_or_absolute(paths['validator'])}")
    print(f"Font: {relative_or_absolute(paths['font'])}")
    print(f"Subject: {relative_or_absolute(paths['subject'])}")
    print(f"Canvas: {canvas_w}x{canvas_h}")
    print(f"Detected title zone: {title_box}")
    print(f"Detected image zone: {image_box}")
    return 0


def build_hero(
    *,
    slug: str,
    subject_path: Path,
    template_id: str,
    title_override: str | None,
    use_validator_detection: bool,
    skip_bg_removal: bool,
    write_validator: bool,
) -> tuple[Path, Path, Path | None]:
    cfg = load_config()
    tpl = get_template(cfg, template_id)
    canvas_w = int(cfg["canvas"]["width"])
    canvas_h = int(cfg["canvas"]["height"])

    template_path = ROOT / str(tpl["background_png"])
    if not template_path.exists():
        raise SystemExit(f"Template background not found: {relative_or_absolute(template_path)}")
    canvas = Image.open(template_path).convert("RGBA")
    if canvas.size != (canvas_w, canvas_h):
        canvas = canvas.resize((canvas_w, canvas_h), Image.LANCZOS)

    if use_validator_detection:
        validator_path = ROOT / str(tpl["validator_png"])
        if not validator_path.exists():
            raise SystemExit(f"Validator PNG not found: {relative_or_absolute(validator_path)}")
        title_box, image_box = detect_zones(validator_path)
    else:
        title_box = zone_from_pct(canvas_w, canvas_h, tpl["title_zone"])
        image_box = zone_from_pct(canvas_w, canvas_h, tpl["image_zone"])

    if not subject_path.exists():
        raise SystemExit(f"Subject image not found: {relative_or_absolute(subject_path)}")
    subject = Image.open(subject_path).convert("RGBA")
    image_cfg = cfg["image"]
    if bool(image_cfg.get("remove_white_bg", True)) and not skip_bg_removal:
        subject = remove_white_bg(
            subject,
            threshold=int(image_cfg.get("white_threshold", 245)),
            edge_only=bool(image_cfg.get("remove_edge_connected_white", True)),
        )
    subject = crop_to_content(subject)
    resized, paste_xy = fit_subject(subject, image_box, float(image_cfg.get("padding_pct", 7)))
    canvas.alpha_composite(resized, dest=paste_xy)

    title = title_override or load_article_title(slug)
    fonts_cfg = cfg["fonts"]
    font_path = ROOT / str(fonts_cfg["title_path"])
    if not font_path.exists():
        raise SystemExit(f"Title font not found: {relative_or_absolute(font_path)}")

    padding_px = int(fonts_cfg.get("title_padding_px", 0))
    title_inner_box = inset_box(title_box, padding_px) if padding_px else title_box
    draw_title(
        canvas,
        title,
        title_inner_box,
        font_path,
        color=str(tpl.get("title_color") or fonts_cfg.get("title_color", "#212529")),
        min_pt=int(fonts_cfg.get("title_min_pt", 32)),
        max_pt=int(fonts_cfg.get("title_max_pt", 52)),
        line_height=float(fonts_cfg.get("title_line_height", 1.08)),
        max_lines=int(fonts_cfg.get("title_max_lines", 4)),
        align=str(tpl.get("title_align") or fonts_cfg.get("title_align", "left")).lower(),
    )

    tpl_suffix = str(tpl["id"]).lower()
    heroes_dir = ROOT / str(cfg["exports"]["heroes_dir"])
    validated_dir = ROOT / str(cfg["exports"]["validated_dir"])
    canonical_dir = ROOT / "images" / "exports"
    heroes_dir.mkdir(parents=True, exist_ok=True)
    validated_dir.mkdir(parents=True, exist_ok=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)

    qa_path = heroes_dir / f"{slug}-{tpl_suffix}-hero.png"
    canonical_path = canonical_dir / f"{slug}-hero.png"
    canvas.convert("RGB").save(qa_path, format="PNG", optimize=True)
    canvas.convert("RGB").save(canonical_path, format="PNG", optimize=True)

    validated_path: Path | None = None
    if write_validator:
        validated_path = validated_dir / f"{slug}-{tpl_suffix}-validated.png"
        overlay = draw_validator_overlay(canvas, title_box, image_box, font_path)
        overlay.convert("RGB").save(validated_path, format="PNG", optimize=True)

    return canonical_path, qa_path, validated_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a FreeIndexer 1200x630 hero from a subject and template.")
    parser.add_argument("--slug", required=True, help="Article slug, matching content/**/{slug}.md")
    parser.add_argument(
        "--template",
        default="random",
        help="Template id: 1, 2, 3, T01... or random (default: random)",
    )
    parser.add_argument("--seed", help="Optional seed for reproducible random template selection")
    parser.add_argument("--subject", help="Subject PNG. Default: images/exports/subjects/{slug}-subject.png")
    parser.add_argument("--title", help="Override the title rendered onto the hero")
    parser.add_argument("--no-validator-detect", action="store_true", help="Use JSON zone percentages instead")
    parser.add_argument("--no-bg-removal", action="store_true", help="Keep the subject's white background")
    parser.add_argument("--validator", action="store_true", help="Write a validated overlay image")
    parser.add_argument("--check-assets", action="store_true", help="Check inputs without writing output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = load_config()
    check_all = str(args.template).lower() in {"all", "*"}
    tpl = None if check_all else pick_template(cfg, args.template, seed=args.seed or args.slug)

    if args.check_assets:
        return check_assets(cfg, tpl, args.slug, args.subject)

    if check_all:
        last_canonical: Path | None = None
        for candidate in cfg["templates"]:
            paths = asset_paths(cfg, candidate, args.slug, args.subject)
            canonical_path, qa_path, validated_path = build_hero(
                slug=args.slug,
                subject_path=paths["subject"],
                template_id=candidate["id"],
                title_override=args.title,
                use_validator_detection=not args.no_validator_detect,
                skip_bg_removal=args.no_bg_removal,
                write_validator=args.validator,
            )
            last_canonical = canonical_path
            print(f"{candidate['id']} -> {qa_path.relative_to(ROOT)}")
            if validated_path:
                print(f"{candidate['id']} validated -> {validated_path.relative_to(ROOT)}")
        if last_canonical:
            print(f"Canonical -> {last_canonical.relative_to(ROOT)}")
        return 0

    paths = asset_paths(cfg, tpl, args.slug, args.subject)
    canonical_path, qa_path, validated_path = build_hero(
        slug=args.slug,
        subject_path=paths["subject"],
        template_id=tpl["id"],
        title_override=args.title,
        use_validator_detection=not args.no_validator_detect,
        skip_bg_removal=args.no_bg_removal,
        write_validator=args.validator,
    )

    print(f"Canonical -> {canonical_path.relative_to(ROOT)}")
    print(f"QA hero -> {qa_path.relative_to(ROOT)}")
    if validated_path:
        print(f"Validated -> {validated_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
