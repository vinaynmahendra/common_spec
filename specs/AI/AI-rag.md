---
id: "AI-rag"
title: "RAG"
parent: "AI"
order: 3
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "document ingestion, embeddings, vector store, tenant-isolated retrieval"
links: []
rev: 2
syncHash: "a781d43f0b4b799e"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 8.3 RAG

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> document ingestion, embeddings, vector store, tenant-isolated retrieval

<!-- section:purpose -->
## Intended use

RAG (retrieval-augmented generation) gives AI features grounded access to the documents of **one case**: pleadings, exhibits, procedural orders, transcripts and eBundles. It ingests document versions, splits them into chunks with page references, embeds them in the tenant's home region, and retrieves the passages a feature needs, filtered by tenant, case and the requesting user's document permissions.

Supported decisions: a secretariat user preparing a case overview, a neutral locating where a fact appears in a bundle, a transcriber checking spellings of names used in filings. Output always cites document, version and page so a person can check it in the document viewer ([[APP-document-viewer-and-sandbox]]).

**Functional requirements**

| ID | Requirement |
|---|---|
| RAG-FR-1 | Ingest each new document version after malware scan and OCR complete ([[PKG-encryption-at-rest-signed-urls]], [[DOM-ebundling]]) via the Temporal workflow `rag-ingest` on task queue `ai-pipelines` |
| RAG-FR-2 | Chunk with page and paragraph anchors; store `document_id`, `document_version_id`, `page_from`, `page_to` per chunk |
| RAG-FR-3 | Embed with the region's `embed.default` route through the gateway ([[AI-ai-gateway]]) |
| RAG-FR-4 | Store chunks and vectors in tenant-owned tables with forced RLS ([[ADR-tenant-isolation]]) |
| RAG-FR-5 | Every retrieval requires `caseId`; results are filtered by the caller's document visibility (for example tribunal-only documents, ethical walls) from [[PKG-rbac-abac-case-level-party]] and [[PKG-ethical-walls-conflict-based]] |
| RAG-FR-6 | Superseded versions are excluded by default; a feature may request a specific version |
| RAG-FR-7 | Deleting, erasing or placing a document out of scope removes its chunks within a proposed 24 hours, and immediately from retrieval results |
| RAG-FR-8 | Hybrid retrieval (vector plus keyword) with re-ranking; top-k and token budget set by the feature |

<!-- section:outofscope -->
## Out-of-scope uses

- **Retrieval across cases**, even within one tenant (for example "find similar past cases"). Not offered: confidentiality between cases is part of arbitration practice. Prevented because the retrieval API has no call without `caseId`, and the SQL always filters on it.
- **Retrieval across tenants** for any purpose, including platform analytics.
- **Public legal research corpora** (statutes, case law): out of scope for this node; if added later it is a separate, non-tenant index with its own node.
- **Using embeddings to train or tune models.**

<!-- section:models -->
## Models and providers

- Embeddings: region's `embed.default` route ([[AI-ai-gateway]]). The embedding model and version are stored on every chunk (`embed_model`, `embed_version`); an index never mixes models.
- Re-ranking: optional `rerank` capability per region, or a lexical re-ranker if no in-region model is available.
- Changing the embedding model requires a re-embedding workflow (`rag-reembed`) per tenant, run in the background with old and new vectors side by side until cut-over.

<!-- section:context -->
## Inputs and context sources

**Sources ingested**

| Source | Trigger event | Notes |
|---|---|---|
| Uploaded document versions | `document.version.scanned` (after malware scan and OCR) | Text from OCR layer for scanned PDFs |
| Generated procedural orders and awards | `document.version.issued` | Only after issue, never drafts of other users |
| eBundles | `bundle.issued` | Bundle page numbers stored alongside source page numbers |
| Approved transcripts | `transcript.approved` | Timestamps stored as anchors |

**Storage sketch (pgvector in the regional Postgres, proposed)**

```sql
create table rag_chunks (
  id                   uuid primary key,
  tenant_id            uuid not null,
  case_id              uuid not null,
  document_id          uuid not null,
  document_version_id  uuid not null,
  visibility_tier      text not null,   -- from SEC-data-classification: case-participants, tribunal-only, ...
  chunk_no             int  not null,
  page_from            int, page_to int,
  text                 text not null,   -- encrypted at rest by the database; consider field-level encryption
  embedding            vector(1024) not null,  -- dimension depends on the chosen model
  embed_model          text not null, embed_version text not null,
  is_current           boolean not null default true,
  created_at           timestamptz not null default now()
);
create index on rag_chunks (tenant_id, case_id, is_current);
-- ANN index (HNSW); tenant and case filters applied with the index, see questions on filtered search
alter table rag_chunks enable row level security;
alter table rag_chunks force row level security;
create policy tenant_isolation on rag_chunks
  using (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Minimisation:** the feature sets `topK` and a token budget; only the selected chunks are sent to the model, never whole bundles by default.

<!-- section:prompts -->
## Prompt design and versioning

RAG prompts follow [[AI-prompt-management]] and must instruct the model to answer only from the supplied passages and to cite passage IDs in the form `[p:<chunkId>]`. The renderer maps passage IDs to `document / version / page` for display.

<!-- section:guardrails -->
## Guardrails

- **Scope enforcement in the data layer:** forced RLS on `tenant_id`, a mandatory `case_id` predicate, and a visibility filter computed from the caller's permissions. The retrieval function is the only code path to `rag_chunks` (restricted import rule).
- **Context check in the gateway:** passages must carry the request's `tenantId` and `caseId` ([[AI-ai-gateway]]).
- **Untrusted content:** document text is untrusted; it is delimited in prompts and never treated as instructions ([[AI-guardrails]]). Addresses OWASP LLM08 Vector and Embedding Weaknesses and LLM01 Prompt Injection [R1].
- **Grounding:** citations in the output must refer to passages actually retrieved for this request; checked by the grounding validator ([[AI-guardrails]]).
- **Legal hold and deletion:** deletion jobs from [[PKG-data-retention-legal-hold-and]] include `rag_chunks`; legal holds block them.

<!-- section:oversight -->
## Human oversight

Retrieval itself has no human approval step; outputs built on it follow [[AI-human-in-the-loop]]. Users always see the cited passages and can open the source page, which is how reviewers check grounding.

<!-- section:evaluation -->
## Evaluation

| Metric | Dataset | Threshold (proposed) |
|---|---|---|
| Cross-tenant and cross-case leakage | Seeded tenants and cases with near-duplicate documents | 0 results from another tenant or case, blocking |
| Permission leakage | Tribunal-only and walled documents queried as party / counsel | 0 results, blocking |
| Recall@10 | Annotated question-passage pairs per document type (pleadings, exhibits, transcripts), English first | At least 0.85 |
| Citation page accuracy | Sample of retrieved chunks checked against source pages | At least 0.98 |
| Deletion propagation | Delete document, query immediately | 0 results |
| Ingestion latency | 500-page bundle | p95 under 15 minutes from `bundle.issued` |

Datasets are synthetic or consented, never live case data copied out of a region ([[TST-evals-and-ai-testing]]).

<!-- section:failure -->
## Failure modes and fallback

| Failure | Handling |
|---|---|
| OCR text poor (scans, handwriting) | Chunks flagged `low_text_quality`; features warn that some pages could not be read |
| Ingestion fails | Temporal retries with backoff; after limit, document marked `rag_status = failed` and visible to the secretariat |
| Embedding route unavailable in region | Ingestion pauses (workflow waits), no fallback to another region |
| Stale index after a new version | `is_current` flipped in the same activity that indexes the new version |
| Retrieval returns nothing relevant | Feature must say so ("No passages found that answer this") rather than generate an answer |

<!-- section:cost -->
## Cost and limits

Embedding cost is roughly proportional to pages ingested. Proposed planning figure: about 500 tokens per page, so a 2,000-page bundle is about 1 million embedding tokens per ingestion (assumption, to be measured). Ingestion is charged to the tenant's AI budget ([[AI-cost-controls]]); bulk re-embedding after a model change is a platform cost.

<!-- section:logging -->
## Logging and audit

Each retrieval records `tenant_id, case_id, user_id, feature, query hash, returned chunk IDs, scores, request_id` in `ai_retrievals` (tenant-owned, RLS), retained with the case. Ingestion events `rag.document.indexed`, `rag.document.removed` go to the audit trail.

<!-- section:questions -->
## Open questions

- [ ] Vector store: pgvector in the regional Postgres (proposed, keeps RLS and backups uniform) or a separate store; record as an ADR. Check filtered ANN search performance with tenant and case filters at expected volume.
- [ ] Embedding model per region and its dimension; multilingual support for Hindi and other Indic-language documents.
- [ ] Field-level encryption for `rag_chunks.text`, or rely on database encryption at rest?
- [ ] Should tribunal-only documents be indexed at all, or only on request by the tribunal?
- [ ] Retention: do chunks follow the document's retention exactly, or are they deleted earlier when the case closes?

<!-- checks -->
## Template checks

<!-- check:privacy -->
### Privacy and redaction

Only chunks selected by `topK` and the token budget are sent. Chunks are stored in-region under RLS, follow the document retention schedule, and are removed by erasure and offboarding jobs. Party data in passages may be pseudonymised per feature policy ([[AI-guardrails]]).

<!-- check:residency -->
### Residency

Ingestion workflow, embeddings, vector tables and retrieval logs all run in the tenant's home region; embedding outages pause ingestion instead of routing elsewhere.

<!-- check:security -->
### AI security and tenant isolation

Scope is enforced in the data layer (RLS, mandatory `case_id`, visibility filter), re-checked by the gateway, and tested with seeded near-duplicate documents across tenants and cases (zero leakage, blocking). Document text is treated as untrusted (OWASP LLM01, LLM08 [R1]).

<!-- check:evals -->
### Evaluation

Blocking leakage and permission tests, recall@10 at least 0.85, citation page accuracy at least 0.98, deletion propagation zero results, and ingestion latency targets, on synthetic or consented datasets.

<!-- check:audit -->
### Audit and traceability

Every retrieval logs returned chunk IDs and scores linked to the `request_id`, so an output can be traced to the exact passages and document versions used.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OWASP Foundation",
    "excerpt": "Risk list including prompt injection, sensitive information disclosure, improper output handling, excessive agency, system prompt leakage, vector and embedding weaknesses, misinformation and unbounded consumption.",
    "id": "R1",
    "ident": "OWASP Top 10 for LLM Applications",
    "kind": "standard",
    "title": "OWASP Top 10 for Large Language Model Applications",
    "url": "https://genai.owasp.org/llm-top-10/",
    "version": "2025"
  }
]
```

<!-- end -->
