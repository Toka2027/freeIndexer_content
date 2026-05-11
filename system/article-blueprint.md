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

## Article Body Structure

1. Hook and answer
   - State the reader's problem in 2 to 3 sentences.
   - Give the direct answer early.

2. Reader scenario
   - Name the ICP and real workflow.
   - Explain why indexing delay matters to them.

3. Practical workflow
   - Show what to check before submission.
   - Show how FreeIndexer fits into the workflow.
   - Include plan or desktop app guidance when useful.

4. Limitations and expectations
   - Explain that search engines decide what gets indexed.
   - Avoid guaranteed indexing claims.

5. FAQ
   - 3 to 5 questions that match the keyword family.

6. CTA
   - Match CTA to funnel stage.

## Internal Linking Rules

- The first internal link in every cluster article must be its hub pillar.
- Use 2 to 5 internal links per article.
- Link from use-case articles to comparison and pricing content where relevant.
- Link troubleshooting articles to the main indexing hub and relevant use-case article.
- Link commercial pages to pricing and desktop app pages.

