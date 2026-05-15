"""Content utility functions for FreeIndexer publishing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
BLOG_BASE_URL = "https://blog.freeindexer.com"
CONTENT_DIRS = ("content",)

TYPE_ALIASES = {
    "commercial guide": "Commercial Guide",
    "comparison": "Comparison",
    "buying guide": "Buying Guide",
    "pillar": "Pillar",
    "troubleshooting guide": "Troubleshooting Guide",
    "use case guide": "Use Case Guide",
    "workflow guide": "Workflow Guide",
    "advanced workflow guide": "Advanced Workflow Guide",
}


@dataclass
class ArticleFile:
    path: Path
    relative_path: str
    frontmatter: str
    body: str
    fields: dict[str, str]
    frontmatter_data: dict[str, object]
    raw_text: str
    frontmatter_error: str = ""


def scalar_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def list_content_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for directory in CONTENT_DIRS:
        base = root / directory
        if base.exists():
            files.extend(sorted(base.rglob("*.md")))
    return sorted(files)


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", text, re.DOTALL)
    if not match:
        return "", text
    return match.group(1), match.group(2)


def parse_frontmatter_yaml(frontmatter: str) -> tuple[dict[str, object], str]:
    if not frontmatter.strip():
        return {}, ""
    try:
        parsed = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        return {}, str(exc)
    if parsed is None:
        return {}, ""
    if not isinstance(parsed, dict):
        return {}, "frontmatter is not a YAML mapping."
    return parsed, ""


def scalar_fields_from_data(data: dict[str, object]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            fields[key] = str(value)
    return fields


def read_article_file(path: Path, root: Path = ROOT) -> ArticleFile:
    if not path.is_absolute():
        path = root / path
    raw_text = path.read_text(encoding="utf-8-sig")
    frontmatter, body = split_frontmatter(raw_text)
    frontmatter_data, frontmatter_error = parse_frontmatter_yaml(frontmatter)
    relative_path = path.relative_to(root).as_posix()
    return ArticleFile(
        path=path.relative_to(root),
        relative_path=relative_path,
        frontmatter=frontmatter,
        body=body,
        fields=scalar_fields_from_data(frontmatter_data),
        frontmatter_data=frontmatter_data,
        raw_text=raw_text,
        frontmatter_error=frontmatter_error,
    )


def derive_title(article: ArticleFile) -> str:
    return scalar_to_text(article.frontmatter_data.get("title")).strip()


def derive_slug(article: ArticleFile) -> str:
    slug = scalar_to_text(article.frontmatter_data.get("slug")).strip()
    if not slug:
        slug = article.path.stem
    return re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")


def derive_description(article: ArticleFile) -> str:
    return scalar_to_text(article.frontmatter_data.get("description")).strip()


def derive_meta_title(article: ArticleFile) -> str:
    seo = article.frontmatter_data.get("seo") or {}
    if isinstance(seo, dict):
        value = scalar_to_text(seo.get("meta_title")).strip()
        if value:
            return value
    return derive_title(article)


def derive_meta_description(article: ArticleFile) -> str:
    seo = article.frontmatter_data.get("seo") or {}
    if isinstance(seo, dict):
        value = scalar_to_text(seo.get("meta_description")).strip()
        if value:
            return value
    return derive_description(article)


def derive_type(article: ArticleFile) -> str:
    raw = scalar_to_text(article.frontmatter_data.get("type")).strip()
    return TYPE_ALIASES.get(raw.lower(), raw)


def derive_blog_meta(article: ArticleFile) -> dict[str, object]:
    meta = article.frontmatter_data.get("meta") or {}
    return meta if isinstance(meta, dict) else {}


def derive_target_page(article: ArticleFile) -> str:
    return scalar_to_text(derive_blog_meta(article).get("target_page")).strip()


def normalize_blog_target_page(target: str, slug: str) -> str:
    if not target:
        return f"{BLOG_BASE_URL}/{slug}"
    if target.startswith("/"):
        return f"{BLOG_BASE_URL.rstrip('/')}{target}"
    parsed = urlparse(target)
    if parsed.scheme and parsed.netloc:
        return target
    return f"{BLOG_BASE_URL.rstrip('/')}/{target.lstrip('/')}"


def derive_cta(article: ArticleFile) -> str:
    return scalar_to_text(derive_blog_meta(article).get("cta")).strip()


def derive_blog_category_slug(article: ArticleFile) -> str:
    return scalar_to_text(derive_blog_meta(article).get("blog_category")).strip()


def derive_blog_tags(article: ArticleFile) -> list[str]:
    tags = derive_blog_meta(article).get("blog_tags") or []
    if isinstance(tags, list):
        return [scalar_to_text(tag).strip() for tag in tags if scalar_to_text(tag).strip()]
    return []
