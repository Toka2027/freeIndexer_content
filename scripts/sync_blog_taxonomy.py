"""
Seed or sync FreeIndexer blog taxonomy.

Mirrors: captcharank_content/scripts/sync_blog_taxonomy.py

TODO integration:
- confirm blog API endpoint and auth flow
- confirm category and tag taxonomy rules
- seed categories/tags
- write live IDs to reference/blog_taxonomy_live.json

Expected input:
- reference/blog_taxonomy.json
- reference/blog_api.json

Expected output:
- reference/blog_taxonomy_live.json
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "reference" / "blog_taxonomy.json"
LIVE = ROOT / "reference" / "blog_taxonomy_live.json"
BLOG_API = ROOT / "reference" / "blog_api.json"


def main() -> int:
    if not TAXONOMY.exists():
        raise SystemExit("Missing reference/blog_taxonomy.json")
    if not BLOG_API.exists():
        print("Blocked: missing reference/blog_api.json.")
        print("Copy reference/blog_api.example.json and replace FILL_IN_* values.")
        return 2

    api_text = BLOG_API.read_text(encoding="utf-8")
    if "FILL_IN_" in api_text:
        print("Blocked: reference/blog_api.json still contains FILL_IN_* placeholders.")
        return 2

    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    LIVE.write_text(
        json.dumps(
            {
                "status": "not-synced",
                "note": "API integration TODO. Populate live IDs here after taxonomy sync.",
                "source_taxonomy_counts": {
                    "categories": len(taxonomy.get("categories", [])),
                    "tags": len(taxonomy.get("tags", [])),
                },
                "categories": [],
                "tags": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("TODO: taxonomy API sync is not implemented yet.")
    print(f"wrote placeholder live taxonomy to {LIVE.relative_to(ROOT)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

