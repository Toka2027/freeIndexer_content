# FreeIndexer Article Blueprint

## Upgraded Writing Sequence

Every new article must be written from a specific promise, not from a generic
workflow shell. Complete this sequence before the public draft is finished:

1. Define the exact title promise.
   - Write one sentence that says what the title promises the reader will
     understand or be able to do.
   - The article body must satisfy that exact promise. If the title says
     "statuses explained," explain the statuses, meanings, examples, and next
     actions. If the title says "checklist," include a usable checklist.

2. Choose one primary ICP.
   - Use one of: website owner, webmaster, SEO operator, SEO agency, affiliate
     marketer, programmatic SEO builder, SaaS/product team, or blog/network
     owner.
   - Write to that workflow directly. Avoid generic "marketers and businesses"
     language unless it is truly the reader's workflow.

3. Pick at least three topic-specific depth elements.
   - practical checklist
   - comparison table
   - real workflow example
   - common mistakes
   - diagnostic steps
   - decision tree
   - example URL/backlink scenario
   - "what to do next" table
   - tool/process recommendation section

4. Draft the article around the title, not the template.
   - Use section headings that are unique to the topic.
   - Include concrete examples, fields, statuses, URL patterns, campaign
     scenarios, or operating rules where relevant.
   - Remove any paragraph that could be dropped into ten unrelated articles.

5. Add product mentions only where useful.
   - The article must help the reader even if they never use FreeIndexer.
   - Mention FreeIndexer where it naturally fits: URL submission, backlink
     discovery, bulk submission, desktop app workflows, repeatable indexing
     operations, tracking, and prioritization.
   - Do not force FreeIndexer into every section.

6. Score before upload.
   - A new article must score at least 9/10 before hero upload, draft upload, or
     scheduling.
   - If the article scores below 9, revise it. Do not upload it.

## Pillar vs Cluster

Each article is either a pillar or a cluster.

- Pillar: the main article for a hub. It links to all cluster articles in that hub.
- Cluster: a focused article. The first internal link must point to the hub pillar.

Set `meta.pillar: true` for pillar articles.

## Required Frontmatter

```yaml
---
title:
slug:
description:
keywords:
  primary:
  secondary: []
intent:
search_intent:
icp:
secondary_icp:
funnel_stage:
type:
business_goal:
meta:
  target_page:
  internal_links: []
  blog_category:
  blog_tags: []
  pillar:
  cta:
  status:
  word_target:
seo:
  meta_title:
  meta_description:
editorial_review:
content_quality:
  search_promise:
  depth_elements: []
  score:
  checks:
    search_intent_match:
    icp_fit:
    topic_specific_depth:
    usefulness:
    originality:
    practical_examples:
    clean_layout:
    natural_freeindexer_mention:
    internal_links:
    seo_metadata:
    no_unsupported_claims:
image:
  concept:
  hero_template:
---
```

## Public Article Body Structure

1. Introduction and exact answer
   - State the reader's problem in 2 to 3 sentences.
   - Give the direct answer early and match the exact title promise.
   - Use reader-facing headings such as `## Introduction` and
     `## Quick Answer`, or keep the opening unheaded and use
     `## The Short Answer`.

2. Reader situation
   - Name the ICP and real workflow.
   - Explain why the problem matters to their work.
   - Use reader-facing headings such as `## When This Matters`,
     `## Who This Helps`, or `## Why This Happens`.

3. Practical workflow
   - Show what to check before submission or tool use.
   - Cover relevant SEO, Search Console, crawlability, sitemap, internal link,
     backlink, and workflow checks.
   - Include at least three topic-specific depth elements from the upgraded
     writing sequence.
   - Mention FreeIndexer only where it naturally fits.
   - Include plan or desktop app guidance when useful.

4. Limitations and expectations
   - Explain that search engines decide what gets indexed.
   - Avoid guaranteed indexing claims.

5. FAQ
   - 3 to 5 questions that match the keyword family.
   - `## FAQ` is the section heading.
   - Each FAQ question must use `###`, not `##`.

6. Reader-facing next step
   - Match the next step to funnel stage.
   - Use `## Next Step`, `## Final Recommendation`, or another public heading.

Do not leave production planning labels in article bodies. Forbidden public
headings include `## Search Promise`, `## Reader Scenario`,
`## Article Angle`, `## CTA`, `## Claim Guardrails`,
`## Required Sections`, `## Draft Notes`, and `## Internal Notes`.

Store planning and review data in frontmatter only. Public bodies should not
include `Search Promise`, `Reader Scenario`, `Article Angle`, `CTA`,
`Claim Guardrails`, `Required Sections`, `Draft Notes`, or `Internal Notes`
as headings or visible labels.

## Product Mention Rules

- The article must help the reader even if they never use FreeIndexer.
- Educate first, diagnose second, give the workflow third.
- Mention FreeIndexer where it solves a specific submission, batching,
  backlink discovery, desktop, or repeat-operations problem.
- Avoid forcing FreeIndexer into every section.
- Keep claims honest: no guaranteed indexing, no ranking promises, no exact
  unvalidated network numbers.

## Internal Linking Rules

- The first internal link in every cluster article must be its hub pillar.
- Use 2 to 5 internal links per article.
- Body copy must use real Markdown links, such as
  `[indexing education hub](/indexing-education-hub)`.
- `meta.internal_links` may use bare slugs because it is machine-readable
  frontmatter. Public body copy must not show raw slugs as links.
- Link from use-case articles to comparison and pricing content where relevant.
- Link troubleshooting articles to the main indexing hub and relevant use-case article.
- Link commercial pages to pricing and desktop app pages.

## Quality Score Rubric

Score each new article out of 10 before upload. A score of 9 or higher requires
all of these checks to pass:

| Check | Requirement |
|---|---|
| Search intent match | The body fulfills the exact promise of the title and keyword. |
| ICP fit | One primary ICP is obvious in examples, workflows, and language. |
| Topic-specific depth | At least three required depth elements are present and useful. |
| Usefulness | The reader can take a practical next action without buying anything. |
| Originality | The article avoids reusable filler and repeated generic phrasing. |
| Practical examples | Includes concrete URLs, backlink scenarios, statuses, fields, or process examples where relevant. |
| Clean layout | Uses public headings only, `## FAQ`, and `###` FAQ questions. |
| Natural FreeIndexer mention | Product appears only where it supports submission, tracking, bulk, desktop, or repeat workflows. |
| Internal links | Frontmatter slugs are represented as real Markdown body links. |
| SEO metadata | Title, description, primary keyword, secondary keywords, meta title, and meta description are complete. |
| No unsupported claims | No guaranteed indexing, ranking, or unvalidated scale claims. |

