# FreeIndexer Taxonomy Strategy

## Taxonomy Principle

FreeIndexer content should serve the full search discovery operator, not only
people already looking for FreeIndexer or URL indexing tools.

The broad ICP is a hands-on website, webmaster, or SEO operator who wants more
important pages, backlinks, and content assets discovered across search
surfaces. FreeIndexer is the product layer for submission and repeat workflows,
but the blog should first educate, diagnose, and give practical operating
systems.

## Locked Taxonomy Rule

As of the current live taxonomy expansion, the existing category and tag slugs
are protected infrastructure.

Do not modify, rename, delete, merge, or replace existing taxonomy items. This
protects published article relationships, internal links, category/tag archive
URLs, and accumulated SEO value.

Allowed taxonomy work:

- Add a new category only when a durable content hub cannot fit cleanly into an
  existing category.
- Add a new tag only when multiple articles need a reusable topical, audience,
  workflow, platform, provider, or tool label.
- Record a justification for every new category or tag in this document, the
  topical map, or the relevant series roadmap.

Not allowed without explicit owner approval:

- Renaming category or tag slugs.
- Replacing one category/tag with another.
- Merging categories or tags.
- Removing categories or tags from `reference/blog_taxonomy.json`.
- Reassigning existing published articles just to make the taxonomy look tidy.
- Running taxonomy sync in a mode that updates existing live taxonomy records.

The sync script defaults to locked behavior: existing live categories and tags
are preserved, and only missing items are created. Use
`python scripts/sync_blog_taxonomy.py --update-existing` only after explicit
owner approval.

## Category Evaluation

| Candidate | Decision | Why | ICP served | Article examples |
|---|---|---|---|---|
| Indexing Education | Category, keep | Core foundation for crawling, indexing, URL submission, and expectation setting. | Website owners, SEO operators, agencies | indexing basics, indexing delays, URL indexing vs ranking |
| Technical SEO | Category, add | Crawlability, canonicals, robots, sitemaps, and internal links are prerequisites before submission. | Webmasters, technical SEO operators, SaaS teams | technical SEO indexing audit, crawlability checklist |
| Google Search Console | Category, add | Search Console is a recurring workflow surface with enough specific guides to support a hub. | Website owners, webmasters, agencies | URL Inspection guide, sitemap submission, Pages report |
| Backlinks | Category, add | Backlink discovery is a major FreeIndexer-adjacent use case and should not be buried as only a tag. | Affiliates, agencies, blog/network owners | backlink discovery workflow, backlink indexing checklist |
| Webmaster Guides | Category, add | Gives non-agency operators a practical home for repeat website maintenance workflows. | Website owners, webmasters, small teams | new website SEO checklist, weekly webmaster workflow |
| Use Cases | Category, keep | Useful for audience-specific workflows where the ICP changes the process. | Agencies, affiliates, SaaS teams, programmatic SEO builders | agency indexing workflow, SaaS publishing checklist |
| Comparisons | Category, keep | Needed for commercial evaluation and tool/API decisions. | Tool evaluators, agencies, technical teams | indexing tools guide, Search Console vs indexing tool |
| Troubleshooting | Category, keep | Live-problem searches deserve a clear diagnostic category. | All ICPs | why URL is not indexed, sitemap not discovered |
| Bulk Indexing | Change to Bulk SEO Operations category | The need is broader than indexing: inventories, batching, prioritization, QA, and reporting. | Agencies, programmatic SEO builders, networks | bulk URL operations, daily capacity planning |
| Desktop App | Category, keep | Product/support category for users who prefer local software and repeat list workflows. | Agencies, affiliates, blog/network owners | desktop app guide, Windows URL indexing software |
| GEO / AI Search Visibility | Category, add carefully | Relevant emerging topic, but content should stay grounded in discoverability, structured content, and technical foundations. | SaaS teams, content teams, advanced SEOs | AI search visibility basics, LLM visibility checklist |
| Content Marketing | Category, added and now locked | Needed for content clusters, briefs, intent, on-page SEO, publishing checks, and refresh workflows that go beyond indexing only. | Website owners, content teams, SaaS teams, affiliates | content cluster planning, keyword intent checklist |
| Analytics And Reporting | Category, added and now locked | Needed to separate indexing, visibility, traffic, conversions, reporting, and decision-making workflows. | Webmasters, agencies, SaaS teams, growth operators | GA4 SEO reporting, GSC plus GA4 workflow |
| Landing Pages And CRO | Category, added and now locked | Needed to connect search visibility to conversion readiness, CTAs, trust, pricing pages, and lead capture. | SaaS teams, affiliates, agencies, founders | SEO landing page structure, CRO checklist |
| Digital Marketing Operations | Category, added and now locked | Needed for repeatable growth systems: calendars, SEO QA, campaign workflows, vendors, and client reporting. | Agencies, SEO teams, founders, growth operators | SEO QA before publishing, vendor workflow |
| SEO Tools And Providers | Category, added and now locked | Needed for responsible SEO software, automation, provider, campaign service, and tool stack education. | Agencies, SEO operators, affiliates, tool buyers | GSA workflow, SEO provider vs indexing tool |
| Platform SEO | Category, added and now locked | Needed for platform-specific SEO workflows that do not fit generic technical SEO or use-case categories. | Ecommerce owners, webmasters, SaaS teams | Shopify indexing checklist, WordPress indexing checklist |
| SEO | Tag, not category yet | Too broad as a category; better used as a general topic tag until the blog has multiple SEO sub-hubs. | All ICPs | broad SEO articles |
| Crawlability | Tag/subtopic | Important technical concept but narrower than a top-level category. | Webmasters, technical SEOs | crawlability checks |
| Sitemaps | Tag/subtopic | A recurring diagnostic topic under Technical SEO and Search Console. | Website owners, webmasters | sitemap guide |
| Internal Linking | Tag/subtopic | Supports crawlability and indexing but is too narrow for a category now. | Website owners, SEOs | internal link checklist |
| Search Visibility | Tag, not category yet | Useful umbrella language across old and emerging search surfaces, but too broad for a first category. | All ICPs | visibility diagnostics |

## Tag Group Rules

- Topic tags describe the subject: `seo`, `indexing`, `backlinks`,
  `search-visibility`, `content-discovery`.
- Technical SEO tags describe blockers or checks: `crawlability`,
  `robots-txt`, `sitemap`, `canonical-tags`, `noindex`, `internal-linking`.
- Workflow tags describe operating systems: `url-submission`,
  `bulk-url-operations`, `backlink-discovery`, `google-search-console`.
- Audience tags describe the primary reader: `website-owners`, `webmasters`,
  `seo-agencies`, `affiliate-seo`, `programmatic-seo`, `saas-seo`.
- Product tags are used only when the article materially discusses the product:
  `free-indexer`, `desktop-app`.
- AI search tags are used sparingly: `ai-search`, `geo`, `llm-visibility`.
- Content marketing tags describe planning and publishing workflows:
  `content-marketing`, `content-strategy`, `keyword-intent`,
  `content-briefs`, `on-page-seo`, `content-refresh`, `blog-publishing`.
- Analytics and CRO tags describe measurement and conversion workflows:
  `analytics-reporting`, `ga4`, `seo-reporting`, `organic-traffic`,
  `landing-pages`, `cro`, `conversion-optimization`, `lead-capture`.
- Operations and strategy tags describe repeatable marketing systems:
  `digital-marketing-operations`, `marketing-workflows`, `content-calendar`,
  `seo-qa`, `client-reporting`, `seo-strategy`, `growth-workflows`.
- Tool, provider, and platform tags describe reusable article families:
  `seo-software`, `seo-automation`, `seo-campaigns`, `seo-provider`,
  `seoestore`, `link-building-tools`, `backlink-tools`, `gsa-ser`,
  `rankerx`, `platform-seo`, `shopify-seo`, `ecommerce-seo`,
  `wordpress-seo`, `woocommerce-seo`, `tool-stack`,
  `digital-marketing-tools`.

## Approval Rule

Do not add or sync new taxonomy until the owner approves:

1. The exact new category or tag slug.
2. The reason an existing taxonomy item is not enough.
3. The article series or roadmap rows that will use it.
4. The expected ICP and business goal.
5. Whether the item should be created live now or held for a later batch.
