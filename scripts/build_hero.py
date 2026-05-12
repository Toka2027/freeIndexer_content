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
    parser.add_argument("--check-assets", action="store_true")
    args = parser.parse_args()

    template_doc = ROOT / "images" / "templates" / f"{args.template}-template.md"
    template_png = ROOT / "images" / "templates" / f"{args.template}.png"
    validator_png = ROOT / "images" / "templates" / f"{args.template}-v.png"
    default_subject = ROOT / "images" / "exports" / "subjects" / f"{args.slug}-subject.png"
    subject = Path(args.subject) if args.subject else default_subject

    canonical = ROOT / "images" / "exports" / f"{args.slug}-hero.png"
    qa = ROOT / "images" / "exports" / "heroes" / f"{args.slug}-t{args.template:02d}-hero.png"
    validated = ROOT / "images" / "exports" / "validated" / f"{args.slug}-t{args.template:02d}-validated.png"

    if not template_doc.exists():
        raise SystemExit(f"Template documentation not found: {template_doc.relative_to(ROOT)}")

    missing = []
    if not template_png.exists():
        missing.append(str(template_png.relative_to(ROOT)))
    if not validator_png.exists():
        missing.append(str(validator_png.relative_to(ROOT)))
    if not subject.exists():
        missing.append(str(subject.relative_to(ROOT) if subject.is_absolute() and ROOT in subject.parents else subject))

    if args.check_assets:
        if missing:
            print("hero asset check failed; missing:")
            for item in missing:
                print(f"- {item}")
            print("Required before end-to-end hero building: 1200x630 template PNG, validator overlay PNG, and subject PNG.")
            return 2
        print("hero asset check passed")
        print(f"Template PNG: {template_png.relative_to(ROOT)}")
        print(f"Validator PNG: {validator_png.relative_to(ROOT)}")
        print(f"Subject: {subject.relative_to(ROOT) if subject.is_absolute() and ROOT in subject.parents else subject}")
        return 0

    if missing:
        print("Hero building is blocked; missing required assets:")
        for item in missing:
            print(f"- {item}")
        print("Template docs alone are not enough for real compositing.")
        print("Add real 1200x630 template backgrounds and validator overlays before running build output.")
        return 2

    print("TODO: hero compositing is not implemented yet.")
    print("Assets are present, but Pillow compositing still needs implementation.")
    print(f"Template doc: {template_doc.relative_to(ROOT)}")
    print(f"Expected subject: {subject.relative_to(ROOT) if subject.is_absolute() and ROOT in subject.parents else subject}")
    print(f"Expected canonical hero: {canonical.relative_to(ROOT)}")
    print(f"Expected QA hero: {qa.relative_to(ROOT)}")
    if args.validator:
        print(f"Expected validated overlay: {validated.relative_to(ROOT)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
