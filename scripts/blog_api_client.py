"""HMAC-SHA256 signed client for the 99sync Blogs API.

Credentials are loaded from reference/blog_api.json by default. The client
does not print credentials and keeps request signing contained in one place.

Auth model:
  Headers: X-Application-Key, X-Timestamp, X-Signature
  Payload: {METHOD}\n{PATH}\n{TIMESTAMP}\n{RAW_BODY}
  Signature: HMAC-SHA256(payload, secret_key)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BLOG_API_CONFIG_PATH = ROOT / "reference" / "blog_api.json"
DEFAULT_API_BASE_URL = "https://blogs.99sync.com/api"

ENV_OVERRIDES = {
    "BLOG_API_FLOW": "api_flow",
    "BLOG_API_BASE_URL": "base_url",
    "BLOG_API_APPLICATION_ID": "application_id",
    "BLOG_APPLICATION_ID": "application_id",
    "BLOG_API_KEY": "api_key",
    "BLOG_API_SECRET_KEY": "secret_key",
    "BLOG_SECRET_KEY": "secret_key",
    "BLOG_API_AUTHOR_ID": "author_id",
    "BLOG_AUTHOR_ID": "author_id",
    "BLOG_API_DOMAIN": "blog_domain",
    "BLOG_DOMAIN": "blog_domain",
    "BLOG_UPLOAD_MODE": "upload_mode",
}


def load_dotenv_safely() -> None:
    env_path = ROOT / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(env_path)
        return
    except Exception:
        pass

    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    load_dotenv_safely()
    merged = dict(data)
    for env_key, config_key in ENV_OVERRIDES.items():
        value = os.environ.get(env_key, "").strip()
        if value:
            merged[config_key] = value
    return merged


def resolve_blog_api_config_path(config_path: str | Path | None = None) -> Path:
    if config_path:
        path = Path(config_path)
    else:
        env_path = os.environ.get("BLOG_API_CONFIG_PATH", "").strip()
        path = Path(env_path) if env_path else DEFAULT_BLOG_API_CONFIG_PATH
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def load_blog_api_config(config_path: str | Path | None = None) -> dict[str, Any]:
    resolved_path = resolve_blog_api_config_path(config_path)
    data = json.loads(resolved_path.read_text(encoding="utf-8-sig"))
    if "base_url" not in data and "blog_api_endpoint" in data:
        data["base_url"] = data["blog_api_endpoint"]
    data.setdefault("base_url", DEFAULT_API_BASE_URL)
    data.setdefault("api_flow", "99sync")
    return apply_env_overrides(data)


def has_placeholders(data: dict[str, Any]) -> bool:
    return "FILL_IN_" in json.dumps(data)


def validate_blog_api_config(data: dict[str, Any]) -> None:
    missing = []
    for key in ("application_id", "api_key", "secret_key", "author_id", "blog_domain"):
        if data.get(key) in (None, ""):
            missing.append(key)
    if missing:
        raise SystemExit(f"Missing blog API config values: {', '.join(missing)}")
    if has_placeholders(data):
        raise SystemExit("reference/blog_api.json still contains FILL_IN_* placeholders.")


def _sign(method: str, path: str, body: str, secret_key: str) -> tuple[str, str]:
    ts = str(int(time.time()))
    payload = f"{method}\n{path}\n{ts}\n{body}"
    sig = hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return ts, sig


class BlogApiClient:
    """Signed HTTP client for the 99sync Blogs API."""

    def __init__(self, config: dict[str, Any] | None = None, config_path: str | Path | None = None):
        cfg = config or load_blog_api_config(config_path)
        validate_blog_api_config(cfg)
        self.base_url: str = str(cfg["base_url"]).rstrip("/")
        self.application_id: int = int(cfg["application_id"])
        self.api_key: str = str(cfg["api_key"])
        self.secret_key: str = str(cfg["secret_key"])
        self.author_id: int = int(cfg.get("author_id", 7))

    def _request(
        self,
        method: str,
        endpoint: str,
        body: str = "",
        query: dict[str, str] | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if query:
            qs = parse.urlencode({k: v for k, v in query.items() if v is not None and v != ""})
            url = f"{url}?{qs}"

        parsed = parse.urlparse(self.base_url)
        api_prefix = parsed.path.rstrip("/") or "/api"
        path = f"{api_prefix}/{endpoint.lstrip('/')}"
        path = path.split("?", 1)[0]

        ts, sig = _sign(method.upper(), path, body, self.secret_key)
        headers = {
            "Accept": "application/json",
            "X-Application-Key": self.api_key,
            "X-Timestamp": ts,
            "X-Signature": sig,
        }
        if method.upper() in {"POST", "PUT", "PATCH"}:
            headers["Content-Type"] = "application/json"

        req = request.Request(
            url,
            data=body.encode("utf-8") if body else None,
            headers=headers,
            method=method.upper(),
        )
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {exc.code}: {body_text[:500]}") from exc

    def list_blogs(
        self,
        per_page: str = "15",
        page: str = "1",
        status: str = "",
        slug: str = "",
        search: str = "",
        category_id: str = "",
        summary: str = "0",
        with_trashed: str = "0",
        only_trashed: str = "0",
        blog_id: str = "",
    ) -> dict[str, Any]:
        q: dict[str, str] = {
            "application_id": str(self.application_id),
            "per_page": per_page,
            "page": page,
        }
        if status:
            q["status"] = status
        if slug:
            q["slug"] = slug
        if search:
            q["search"] = search
        if category_id:
            q["category_id"] = category_id
        if summary:
            q["summary"] = summary
        if with_trashed != "0":
            q["with_trashed"] = with_trashed
        if only_trashed != "0":
            q["only_trashed"] = only_trashed
        if blog_id:
            q["id"] = blog_id
        return self._request("GET", "blogs", query=q)

    def create_blog(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "blogs", body=json.dumps(payload, ensure_ascii=False))

    def update_blog(self, blog_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", f"blogs/{blog_id}", body=json.dumps(payload, ensure_ascii=False))

    def list_categories(self, per_page: str = "100") -> dict[str, Any]:
        return self._request("GET", "categories", query={"application_id": str(self.application_id), "per_page": per_page})

    def create_category(
        self,
        name: str,
        slug: str,
        description: str = "",
        meta_title: str = "",
        meta_description: str = "",
        is_active: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "application_id": str(self.application_id),
            "categories_name": {"en": name},
            "slug": {"en": slug},
            "description": {"en": description},
            "is_active": is_active,
        }
        if meta_title:
            payload["meta_title"] = {"en": meta_title}
        if meta_description:
            payload["meta_description"] = {"en": meta_description}
        return self._request("POST", "categories", body=json.dumps(payload, ensure_ascii=False))

    def update_category(
        self,
        cat_id: int,
        name: str,
        slug: str,
        description: str = "",
        meta_title: str = "",
        meta_description: str = "",
        is_active: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "application_id": str(self.application_id),
            "categories_name": {"en": name},
            "slug": {"en": slug},
            "description": {"en": description},
            "is_active": is_active,
        }
        if meta_title:
            payload["meta_title"] = {"en": meta_title}
        if meta_description:
            payload["meta_description"] = {"en": meta_description}
        return self._request("PUT", f"categories/{cat_id}", body=json.dumps(payload, ensure_ascii=False))

    def list_tags(self, per_page: str = "100") -> dict[str, Any]:
        return self._request("GET", "tags", query={"application_id": str(self.application_id), "per_page": per_page})

    def create_tag(
        self,
        name: str,
        slug: str,
        description: str = "",
        meta_title: str = "",
        meta_description: str = "",
        is_active: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "application_id": str(self.application_id),
            "name": {"en": name},
            "slug": {"en": slug},
            "is_active": is_active,
        }
        if description:
            payload["description"] = {"en": description}
        if meta_title:
            payload["meta_title"] = {"en": meta_title}
        if meta_description:
            payload["meta_description"] = {"en": meta_description}
        return self._request("POST", "tags", body=json.dumps(payload, ensure_ascii=False))

    def update_tag(
        self,
        tag_id: int,
        name: str,
        slug: str,
        description: str = "",
        meta_title: str = "",
        meta_description: str = "",
        is_active: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "application_id": str(self.application_id),
            "name": {"en": name},
            "slug": {"en": slug},
            "is_active": is_active,
        }
        if description:
            payload["description"] = {"en": description}
        if meta_title:
            payload["meta_title"] = {"en": meta_title}
        if meta_description:
            payload["meta_description"] = {"en": meta_description}
        return self._request("PUT", f"tags/{tag_id}", body=json.dumps(payload, ensure_ascii=False))
