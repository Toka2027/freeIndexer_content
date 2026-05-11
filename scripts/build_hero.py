"""
Build a FreeIndexer hero image from a subject and template.

Mirrors: captcharank_content/scripts/build_hero.py

TODO integration:
- add approved 1200x630 template PNG backgrounds
- implement Pillow compositing for title + subject zones
- write canonical, QA, and optional validated overlay images

Expected inputs:
- --slug article slug
- --template template number
- optional --subject path
- optional --validator

Expected outputs:
- images/exports/{slug}-hero.png
- images/exports/heroes/{slug}-tNN-hero.png
- images/exports/validated/{slug}-tNN-validated.png when --validator is used
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--template", required=True, type=int)
    parser.add_argument("--subject")
    parser.add_argument("--validator", action="store_true")
    args = parser.parse_args()

    template_doc = ROOT / "images" / "templates" / f"{args.template}-template.md"
    default_subject = ROOT / "images" / "exports" / "subjects" / f"{args.slug}-subject.png"
    subject = Path(args.subject) if args.subject else default_subject

    canonical = ROOT / "images" / "exports" / f"{args.slug}-hero.png"
    qa = ROOT / "images" / "exports" / "heroes" / f"{args.slug}-t{args.template:02d}-hero.png"
    validated = ROOT / "images" / "exports" / "validated" / f"{args.slug}-t{args.template:02d}-validated.png"

    if not template_doc.exists():
        raise SystemExit(f"Template documentation not found: {template_doc.relative_to(ROOT)}")

    print("TODO: hero compositing is not implemented yet.")
    print("This script mirrors the CaptchaRank interface and is blocked until template PNG assets are approved.")
    print(f"Template doc: {template_doc.relative_to(ROOT)}")
    print(f"Expected subject: {subject.relative_to(ROOT) if subject.is_absolute() and ROOT in subject.parents else subject}")
    print(f"Expected canonical hero: {canonical.relative_to(ROOT)}")
    print(f"Expected QA hero: {qa.relative_to(ROOT)}")
    if args.validator:
        print(f"Expected validated overlay: {validated.relative_to(ROOT)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

