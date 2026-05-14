# Template Example

Use this structure when adding a new `images/templates/{N}-template.md` file.
The markdown file should mirror the matching object in
`reference/image-templates.json`.

## JSON Definition

```json
{
  "id": "TNN",
  "name": "Template Name",
  "background_png": "images/templates/N.png",
  "validator_png": "images/templates/N-v.png",
  "doc": "images/templates/N-template.md",
  "best_for": "article type, workflow, or use case",
  "title_color": "#212529",
  "title_max_lines": 3,
  "title_zone": {
    "x_pct": 0,
    "y_pct": 0,
    "width_pct": 0,
    "height_pct": 0
  },
  "image_zone": {
    "x_pct": 0,
    "y_pct": 0,
    "width_pct": 0,
    "height_pct": 0
  }
}
```

## Design Notes

- Title must fit within 3 lines.
- Use `#FFFFFF` for title text only when the title sits on the orange field.
- Subject image is placed in the red validator zone with configured padding.
- Validator source should use a blue title zone and red image zone.
