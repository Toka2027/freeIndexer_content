# FreeIndexer System Docs

These files define how FreeIndexer content should be planned, written, linked, and scaled.

## Core Docs

- [product-positioning.md](product-positioning.md): product facts, value proposition, differentiators, and claims guardrails
- [business-goals.md](business-goals.md): what each article must accomplish commercially
- [icp-language-matrix.md](icp-language-matrix.md): ICPs, pains, preferred language, and article styles
- [editorial-policy.md](editorial-policy.md): tone, risk rules, and claim standards
- [article-blueprint.md](article-blueprint.md): required frontmatter and article structure
- [taxonomy-strategy.md](taxonomy-strategy.md): category/tag decisions and approval rules
- [how-to-create-image.md](how-to-create-image.md): FreeIndexer subject and hero image workflow
- [full-content-flow.md](full-content-flow.md): end-to-end content, image, publishing, and tracker flow
- [keyword-scoring.md](keyword-scoring.md): prioritization logic for article ideas
- [naming-and-markdown-style.md](naming-and-markdown-style.md): file naming, frontmatter, and markdown rules
- [topical-map.md](topical-map.md): hubs, pillars, clusters, and batch priorities
- [internal-linking-map.md](internal-linking-map.md): linking rules and article-to-article map
- [content-roadmap.md](content-roadmap.md): production sequence after the first batch

## Reference Repo Pattern Used

The structure combines two reference patterns:

- CaptchaRank style: hub/pillar/cluster SEO map, strict metadata, internal links, article blueprints.
- CAI style: governed content machine, ICP-first article files, pipeline inventory, editorial guardrails, and reusable templates.

FreeIndexer keeps those patterns but changes the strategy to search discovery
operations for website owners, webmasters, SEO operators, agencies, affiliates,
programmatic SEO builders, SaaS/product teams, and blog/network owners.

## Operational Surfaces

- `content/`: article source markdown
- `images/`: visual identity, templates, and generated exports
- `scripts/`: validation, pipeline, image, taxonomy, draft, and tracker commands
- `reference/`: credential examples, taxonomy, and source notes
- `pipeline/`: article inventory and publishing tracker
