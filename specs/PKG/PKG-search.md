---
id: "PKG-search"
title: "Search"
parent: "PKG"
order: 12
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "full-text and metadata search, tenant-scoped indexes"
links: []
rev: 3
syncHash: "15675c9e165902ef"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.12 Search

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> full-text and metadata search, tenant-scoped indexes

<!-- section:purpose -->
## Purpose and scope

`@nomology/search` gives users fast full-text and metadata search over cases, parties, documents (extracted text and metadata), hearings and neutrals, scoped to their tenant and filtered by the same permissions as direct access. Indexing is asynchronous from the transactional outbox.

**Decision proposed for phase 2:** start with Postgres full-text search (`tsvector` with language-specific configurations, `pg_trgm` for names and case references) in the regional database, under the same forced RLS as everything else. Move to OpenSearch per region only when measured needs exceed it (document text volume, relevance tuning, multilingual analysis). The public API below is backend-neutral so the switch does not affect consumers.

**Does not:** decide access (calls [[PKG-authorization]] for filters); store documents (reads extracted text produced by OCR in [[WF-long-running-pipelines]]); provide semantic or vector search for AI (that is [[AI-rag]], which must apply the same filters).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Search |
|---|---|
| Secretariat console | Case search by reference, party, counsel, status, dates; full-text over filings |
| Party and counsel portal | Search within own cases' documents |
| Neutral workspace | Search exhibits and transcripts within appointed cases |
| People picker ([[PKG-combobox-and-people-picker]]) | Type-ahead over users, parties, neutrals (tenant-scoped, wall-filtered) |
| Tenant admin | Users and audit (audit search uses the audit package, not this one) |
| Public API | Not exposed at launch |

<!-- section:api -->
## Public API

```ts
// packages/search/src/index.ts (server-only)
export type Index = 'cases' | 'documents' | 'parties' | 'hearings' | 'neutrals' | 'people';

export interface SearchQuery<I extends Index> {
  index: I;
  text?: string;                         // ≤ 200 chars; parsed with websearch_to_tsquery semantics
  filters?: FiltersFor<I>;               // typed metadata filters, e.g. { status: ['HEARING'], caseType: [...], filedBetween: [...] }
  caseId?: string;                       // restrict to one case
  sort?: 'relevance' | 'newest' | 'oldest';
  cursor?: string; limit?: number;       // default 20, max 100
  locale?: string;                       // selects text search configuration
}
export interface SearchHit<I extends Index> { id: string; type: I; score: number; title: string; snippet?: string /* highlighted, sanitised */; fields: HitFieldsFor<I> }

export function search<I extends Index>(tx: TenantTx, q: SearchQuery<I>): Promise<{ hits: SearchHit<I>[]; nextCursor?: string; totalApprox?: number }>;
export function suggest(tx: TenantTx, q: { index: 'people' | 'parties' | 'cases'; prefix: string; limit?: number; purpose: 'appoint' | 'assign' | 'mention' }): Promise<Suggestion[]>;

/** Indexing: registered per entity type by the owning domain; called by the outbox relay. */
export function defineIndexer<E>(def: { index: Index; load: (tx: TenantTx, id: string) => Promise<E | null>; toDocument: (e: E) => IndexDocument }): void;
export function reindex(p: { index: Index; scope: 'tenant' | 'case'; id: string }): Promise<{ jobId: string }>;   // admin / repair
```

`IndexDocument` carries: `tenantId`, `entityId`, `caseId?`, `visibility` tier, `ownerSide?`, `addressedToPartyIds?`, `stage`, metadata fields, and text fields. Permission-relevant attributes are always indexed so filters can be applied in the query.

<!-- section:usage -->
## Usage examples

```ts
const res = await withTenant((tx) => search(tx, {
  index: 'documents', text: 'witness statement Kumar', caseId,
  filters: { documentType: ['WITNESS_STATEMENT'] }, sort: 'relevance', limit: 20,
}));
```

<!-- section:tenant -->
## Tenant context

- Postgres backend: the search tables (`search.document_index`, `search.case_index`, ...) are tenant-owned with forced RLS; queries run in `withTenant`, so a missing tenant filter still returns nothing from other tenants.
- Permission filtering: `search` asks `authz.where(<list action>, index)` for a filter on `caseId`, `visibility`, `ownerSide`, `addressedToPartyIds` and walls, and adds it to the query **before** ranking and limiting, so counts, snippets and facets never reflect inaccessible items.
- OpenSearch backend (if adopted): one cluster per region; index per entity type with a mandatory `tenant_id` term filter added by the package (never by callers) plus the same permission filter translated to OpenSearch query DSL; per-tenant indices for tenants that require it.
- Indexing jobs carry tenant context from the outbox row; an indexer that returns an entity from a different tenant than the job context is rejected.
- Suggestions for appointment and assignment exclude walled people ([[PKG-ethical-walls-conflict-based]]).

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Level |
|---|---|---|
| Text search configurations | `english`, `simple` fallback; Indic and CJK via `simple` plus trigram until a better analyser is chosen | Platform |
| Max extracted text per document indexed | 2 MB | Platform |
| Index lag target | p95 ≤ 30 s from commit | Platform |
| Documents' text indexed for tiers | `case_participants`, `side_restricted`; `tribunal_only` indexed only into a separate table queried only for tribunal principals | Platform |
| Tenant opt-out of full-text over documents | Off (full text on) | Tenant setting `search.documentFullText` |

<!-- section:adapters -->
## Providers and extension points

`SearchBackend` interface: `upsert(doc)`, `delete(entityId)`, `query(compiledQuery)`, `suggest`. Implementations: `PostgresBackend` (phase 2), `OpenSearchBackend` (later, if needed). Both pass the same contract and permission-filter test suite.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `QueryTooComplexError` (too many terms, > 200 chars) | No | Show "Try a shorter search" |
| `SearchUnavailableError` | Yes | Show retry; list pages still work through domain repositories |
| Indexing failure | Retried by BullMQ (5 attempts, exponential); then dead-letter and alert | — |

<!-- section:nfr -->
## Performance and limits

- Query p95 ≤ 300 ms for tenants up to 200,000 cases and 5 million documents (proposed; validated by load test before choosing to stay on Postgres).
- Suggest p95 ≤ 100 ms.
- Index lag p95 ≤ 30 s; full tenant reindex ≤ 4 h for the largest tenant.

<!-- section:versioning -->
## Versioning and compatibility

Semver for the API; index schema version per index — a new version builds in parallel (`*_v2`) and switches when complete, so no consumer sees partial results.

<!-- section:testing -->
## Test contract

- Permission parity: for generated cases with all tiers and capacities, every search hit must pass `authz.can(document.view)`, and every viewable matching item must be findable (no false negatives on a seeded corpus).
- Counts and snippets never include inaccessible items.
- Cross-tenant: tenant B cannot find tenant A content with identical text.
- Deletion: an erased or retention-deleted entity disappears from results within the lag target.

<!-- section:questions -->
## Open questions

- [ ] Confirm Postgres full-text first; define the measurable trigger for OpenSearch (for example p95 > 500 ms at the largest tenant, or need for Indic analysers).
- [ ] Should tribunal-only material be searchable at all? Proposed: yes, for tribunal principals only, in a separate index table.
- [ ] Multilingual analysis for Hindi, Kannada, Chinese and others: which analysers, and is trigram good enough at launch?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Postgres search tables are tenant-owned with forced RLS; OpenSearch (if adopted) gets a mandatory tenant filter added inside the package. Permission filters from `authz.where` are applied before ranking. Indexing jobs reject entities from another tenant.

<!-- check:data-protection -->
### Personal data handling

Indexes contain personal data (names, document text), so they are covered by retention and erasure: deletion of an entity enqueues `search.delete` through the outbox, and rights requests use the same path. KYC and bank fields are never indexed. Tenants can disable document full-text.

<!-- check:residency -->
### Region awareness

Indexes live in the regional database (or a regional OpenSearch cluster); there is no global index. Reindex and backup copies stay in region.

<!-- check:resilience -->
### Failure behaviour

Indexing is idempotent upsert by entity ID and version; out-of-order events are resolved by comparing the entity version. Search unavailability degrades to list pages without full-text.

<!-- check:testing -->
### Testing

Permission parity tests (no false positives, no false negatives on a seeded corpus), cross-tenant tests and deletion-propagation tests run on every change to `packages/search` or any indexer.

<!-- end -->
