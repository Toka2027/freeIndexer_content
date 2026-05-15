# FreeIndexer Article Blueprint

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
---
```

## Public Article Body Structure

1. Introduction and quick answer
   - State the reader's problem in 2 to 3 sentences.
   - Give the direct answer early.
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
- Link from use-case articles to comparison and pricing content where relevant.
- Link troubleshooting articles to the main indexing hub and relevant use-case article.
- Link commercial pages to pricing and desktop app pages.

