"""Generate a FreeIndexer subject image via the configured image provider.

The output of this script is the small subject PNG used by
scripts/build_hero.py. It intentionally generates only the subject on a
pure white background; the final 1200x630 article hero is composed by the
template builder.

Usage:
    python scripts/generate_image.py --slug free-url-indexer --prompt-only
    python scripts/generate_image.py --slug free-url-indexer --check-config
    python scripts/generate_image.py --slug free-url-indexer

Configuration:
    - Loads .env from the repo root.
    - Uses reference/image_provider.json when present.
    - Falls back to OpenAI defaults when the config file is absent.
    - Never prints API keys.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
ENV_FILE = ROOT / ".env"
IMAGE_CONFIG = ROOT / "reference" / "image_provider.json"
IMAGE_CONFIG_EXAMPLE = ROOT / "reference" / "image_provider.example.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-image-1.5",
    "api_key_env": "OPENAI_API_KEY",
    "api_key": "",
    "default_size": "1024x1024",
    "default_quality": "low",
    "subject_output_path": "images/exports/subjects/{slug}-subject.png",
}


def load_env(env_path: Path = ENV_FILE) -> None:
    """Small .env loader so prompt-only works without extra dependencies."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _contains_placeholder(value: Any) -> bool:
    return isinstance(value, str) and "FILL_IN_" in value


def load_provider_config(config_path: Path = IMAGE_CONFIG) -> tuple[dict[str, Any], Path | None]:
    """Load provider settings, overlaying repo defaults.

    reference/image_provider.json is gitignored and optional. If it exists,
    it may override model, size, quality, output path, or api_key_env. Tracked
    configs must not contain real secrets.
    """
    cfg = dict(DEFAULT_CONFIG)
    if not config_path.exists():
        return cfg, None

    data = json.loads(config_path.read_text(encoding="utf-8"))
    for key, value in data.items():
        if _contains_placeholder(value):
            raise SystemExit(
                f"{config_path.relative_to(ROOT)} still contains placeholder value for {key!r}. "
                f"Use {IMAGE_CONFIG_EXAMPLE.relative_to(ROOT)} as a template and remove FILL_IN_* values."
            )
        cfg[key] = value

    provider = str(cfg.get("provider", "")).lower()
    if provider != "openai":
        raise SystemExit(f"Unsupported image provider {cfg.get('provider')!r}. Supported provider: openai.")

    return cfg, config_path


def resolve_api_key(cfg: dict[str, Any], api_key_env_override: str | None = None) -> tuple[str, str]:
    env_name = api_key_env_override or str(cfg.get("api_key_env") or "OPENAI_API_KEY")
    api_key = os.environ.get(env_name, "").strip()
    source = f"environment variable {env_name}"

    if not api_key:
        configured_key = str(cfg.get("api_key") or "").strip()
        if _contains_placeholder(configured_key):
            configured_key = ""
        if configured_key:
            api_key = configured_key
            source = "reference/image_provider.json api_key"

    return api_key, source


def find_article(slug: str) -> Path:
    matches = sorted(CONTENT_DIR.rglob(f"{slug}.md"))
    if not matches:
        raise SystemExit(f"Article not found for slug: {slug}")
    return matches[0]


def load_article_meta(slug: str) -> dict[str, Any]:
    article_path = find_article(slug)
    text = article_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SystemExit(f"No YAML frontmatter found in {article_path.relative_to(ROOT)}")
    meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(meta, dict):
        raise SystemExit(f"Invalid YAML frontmatter in {article_path.relative_to(ROOT)}")
    return meta


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default


def _article_summary(meta: dict[str, Any]) -> str:
    seo = meta.get("seo") if isinstance(meta.get("seo"), dict) else {}
    description = (
        _as_text(meta.get("description"))
        or _as_text(seo.get("meta_description"))
        or _as_text(meta.get("search_intent"))
    )
    return description[:360]


def build_prompt(meta: dict[str, Any], slug: str) -> str:
    title = _as_text(meta.get("title")) or slug.replace("-", " ").title()
    summary = _article_summary(meta)
    icp = _as_text(meta.get("icp")) or "SEO operator"
    article_type = _as_text(meta.get("type")) or "blog guide"

    subject_line = (
        f"Create a clean product-style subject illustration for a FreeIndexer blog hero titled: {title!r}. "
        f"Primary reader: {icp}. Article type: {article_type}."
    )
    if summary:
        subject_line += f" Article summary: {summary}"

    return (
        "STRICT TEXT RULE: zero readable text in the image. No words, letters, numbers, labels, "
        "badges, pseudo-text, UI copy, or marks that resemble writing. Represent states with abstract "
        "status dots, rows, bars, icons, checkmarks, connectors, and geometric UI shapes only.\n\n"
        f"{subject_line}\n\n"
        "Visual concepts to choose from: URL submission queue, backlink discovery graph, indexing "
        "workflow dashboard, submitted/pending/discovered state cards shown without text, browser "
        "panels, desktop app window, crawl/discovery path, SEO workflow checklist, or a tidy pipeline "
        "of URL cards moving toward search discovery. Use one clear central subject that reads at "
        "thumbnail size. Keep the style practical, technical, SaaS-like, and workflow-focused.\n\n"
        "FreeIndexer color direction: pure white (#FFFFFF) background only; charcoal #212529 for "
        "primary UI structure; orange #f96332 as the main action/accent color; cloud #F8FAFC, "
        "border #E5E7EB, and slate #475569 for neutral interface detail. A tiny amount of success "
        "green #10B981 is allowed only for status dots or checkmarks. Avoid mint/green branding, "
        "blue-heavy themes, dark hacker visuals, neon effects, casino/crypto styling, and warm "
        "orange overload.\n\n"
        "Safety and claims: no real Google logos, no Search Console screenshots, no third-party "
        "logos, no 100% indexed claims, no guaranteed indexing or ranking claims, no fake exact "
        "numbers such as 15,000 sites or 300 sites, and no spammy backlink blast imagery.\n\n"
        "Framing rule: background must be PURE WHITE (#FFFFFF) only, with no tint, wash, gradient, "
        "pattern, floor, or scene backdrop. Keep the full subject entirely inside the canvas with at "
        "least 10% pure white margin on every side. Nothing may touch or be clipped by any canvas edge. "
        "The subject sits centered as a single composed group on a white field."
    )


def output_path_for(cfg: dict[str, Any], slug: str) -> Path:
    pattern = str(cfg.get("subject_output_path") or DEFAULT_CONFIG["subject_output_path"])
    return ROOT / pattern.format(slug=slug)


def call_openai_images_api(
    *,
    prompt: str,
    api_key: str,
    model: str,
    size: str,
    quality: str,
    timeout: int,
) -> bytes:
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": "png",
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Images API error HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Images API connection error: {exc}") from exc

    try:
        first = body["data"][0]
        if first.get("b64_json"):
            return base64.b64decode(first["b64_json"])
        if first.get("url"):
            with urllib.request.urlopen(first["url"], timeout=timeout) as img_resp:
                return img_resp.read()
    except (AttributeError, KeyError, IndexError, TypeError, ValueError, urllib.error.URLError) as exc:
        raise RuntimeError(f"Unexpected Images API response: {body}") from exc

    raise RuntimeError(f"Unexpected Images API response: {body}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a FreeIndexer subject PNG via OpenAI Images.")
    parser.add_argument("--slug", required=True, help="Article slug, matching content/**/{slug}.md")
    parser.add_argument("--quality", choices=["low", "medium", "high"], help="Override configured image quality")
    parser.add_argument(
        "--size",
        choices=["1024x1024", "1536x1024", "1024x1536"],
        help="Override configured image size",
    )
    parser.add_argument("--model", help="Override configured OpenAI image model")
    parser.add_argument(
        "--api-key-env",
        help="Override the environment variable used for the API key, default from config",
    )
    parser.add_argument("--timeout", type=int, default=240, help="Request timeout in seconds")
    parser.add_argument("--prompt-only", action="store_true", help="Print the prompt and exit")
    parser.add_argument("--check-config", action="store_true", help="Validate provider config without generation")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env()

    cfg, config_source = load_provider_config()
    if args.model:
        cfg["model"] = args.model
    if args.size:
        cfg["default_size"] = args.size
    if args.quality:
        cfg["default_quality"] = args.quality

    meta = load_article_meta(args.slug)
    prompt = build_prompt(meta, args.slug)
    output_path = output_path_for(cfg, args.slug)
    api_key, key_source = resolve_api_key(cfg, args.api_key_env)

    if args.prompt_only:
        print(f"--- prompt for {args.slug} ---")
        print(prompt)
        print(f"Expected output: {output_path.relative_to(ROOT)}")
        return 0

    if args.check_config:
        print("Image provider config:")
        print(f"  source: {config_source.relative_to(ROOT) if config_source else 'built-in OpenAI defaults'}")
        print(f"  provider: {cfg.get('provider')}")
        print(f"  model: {cfg.get('model')}")
        print(f"  size: {cfg.get('default_size')}")
        print(f"  quality: {cfg.get('default_quality')}")
        print(f"  api key source: {key_source}")
        print(f"  api key available: {'yes' if api_key else 'no'}")
        print(f"  output: {output_path.relative_to(ROOT)}")
        return 0 if api_key else 2

    if not api_key:
        raise SystemExit(
            "Missing image API key. Add OPENAI_API_KEY to .env or set the configured api_key_env "
            "in the shell. Real keys must stay out of git."
        )

    title = _as_text(meta.get("title")) or args.slug.replace("-", " ").title()
    model = str(cfg.get("model") or DEFAULT_CONFIG["model"])
    size = str(cfg.get("default_size") or DEFAULT_CONFIG["default_size"])
    quality = str(cfg.get("default_quality") or DEFAULT_CONFIG["default_quality"])

    print(f"Generating FreeIndexer subject for: {title}")
    print(f"  provider: openai  model: {model}  size: {size}  quality: {quality}")

    image_bytes = call_openai_images_api(
        prompt=prompt,
        api_key=api_key,
        model=model,
        size=size,
        quality=quality,
        timeout=args.timeout,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    print(f"Saved: {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
