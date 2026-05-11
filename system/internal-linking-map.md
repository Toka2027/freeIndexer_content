# FreeIndexer Internal Linking Map

## Global Rules

1. Every cluster article links to its pillar first.
2. Every pillar article links down to all clusters in its hub.
3. Use-case articles link to the comparison hub when the reader is close to choosing a tool.
4. Troubleshooting articles link to the education hub first, then the most relevant use case.
5. Commercial articles link to pricing, desktop app, and product pages through CTA copy.

## Current Article Link Map

| Article | First internal link | Supporting links |
|---|---|---|
| `indexing-education-hub` | none, pillar | `why-google-is-not-indexing-my-url`, `free-url-indexer`, `faster-google-indexing-for-website-owners`, `best-google-indexing-tools` |
| `faster-google-indexing-for-website-owners` | `indexing-education-hub` | `why-google-is-not-indexing-my-url`, `free-url-indexer`, `best-google-indexing-tools` |
| `url-indexing-for-seo-agencies` | `indexing-education-hub` | `programmatic-seo-indexing-workflow`, `best-google-indexing-tools`, `freeindexer-vs-indexing-api` |
| `indexing-workflow-for-affiliate-sites` | `indexing-education-hub` | `free-url-indexer`, `best-google-indexing-tools`, `freeindexer-vs-indexing-api` |
| `programmatic-seo-indexing-workflow` | `indexing-education-hub` | `url-indexing-for-seo-agencies`, `freeindexer-vs-indexing-api`, `best-google-indexing-tools` |
| `indexing-for-saas-product-pages` | `indexing-education-hub` | `why-google-is-not-indexing-my-url`, `best-google-indexing-tools`, `free-url-indexer` |
| `why-google-is-not-indexing-my-url` | `indexing-education-hub` | `faster-google-indexing-for-website-owners`, `free-url-indexer`, `best-google-indexing-tools` |
| `best-google-indexing-tools` | none, pillar | `freeindexer-vs-indexing-api`, `free-url-indexer`, `url-indexing-for-seo-agencies` |
| `freeindexer-vs-indexing-api` | `best-google-indexing-tools` | `programmatic-seo-indexing-workflow`, `url-indexing-for-seo-agencies`, `free-url-indexer` |
| `free-url-indexer` | `indexing-education-hub` | `faster-google-indexing-for-website-owners`, `best-google-indexing-tools`, `why-google-is-not-indexing-my-url` |

## URL Style

Internal links in article bodies should use root-relative paths:

- `/indexing-education-hub`
- `/why-google-is-not-indexing-my-url`
- `/best-google-indexing-tools`

The markdown source should also keep slugs in `meta.internal_links` as bare slugs for workflow parsing.

