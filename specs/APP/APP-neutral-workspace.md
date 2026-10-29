---
id: "APP-neutral-workspace"
title: "Neutral workspace"
parent: "APP-route-groups-per-persona"
order: 2
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (neutral) route group: case files, procedural orders, award drafting, AI-assisted drafting panels"
links: []
rev: 2
syncHash: "ffb0cc5d42220dd4"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.2.2 Neutral workspace

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (neutral) route group: case files, procedural orders, award drafting, AI-assisted drafting panels

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(neutral)` route group, prefix `/tribunal`, on tenant hosts. Personas: arbitrators (sole, co-arbitrator, presiding), mediators and conciliators, empanelled by the tenant ([[DOM-neutrals]]). Typically experienced professionals on laptops, often sitting in several tenants (an HKIAC CMP arbitrator who also sits on a SEBI ODR panel).

Covers: appointment acceptance and disclosures, case record (documents, bundles, timeline), procedural orders, award drafting, AI-assisted drafting and summary panels, tribunal-only deliberation notes, signing, and the neutral's hearings list.

Out of scope: the hearing room ([[APP-hearing-room-in-browser]]), the document viewer ([[APP-document-viewer-and-sandbox]]), conflict-check logic ([[DOM-neutrals]]), AI services ([[AI-ai-gateway]], [[AI-human-in-the-loop]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(neutral)/tribunal/
  layout.tsx                         # shell; requirePersona('neutral')
  page.tsx                           # my cases and tasks
  appointments/[appointmentId]/page.tsx   # accept / decline, disclosure statement
  cases/[caseRef]/
    layout.tsx                       # case header incl. tribunal composition
    error.tsx  not-found.tsx
    page.tsx                         # overview, deadlines, pending applications
    record/page.tsx                  # documents and bundles
    record/[docId]/page.tsx
    @modal/(.)record/[docId]/page.tsx
    orders/page.tsx
    orders/[orderId]/edit/page.tsx   # procedural order editor
    award/page.tsx                   # award draft, versions, signing status
    award/edit/page.tsx              # award editor + AI panel
    deliberations/page.tsx           # tribunal-only notes
    hearings/page.tsx
    hearings/[hearingId]/room/page.tsx
  availability/page.tsx              # calendar of availability (DOM-neutrals)
```
The case layout checks tribunal membership for this case through `getCaseHeaderForTribunalMember`. `deliberations` and `award/edit` additionally check that the case is not in a state where the tribunal is functus (award issued), and render read-only after issue.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, nonce CSP, `private, no-store` throughout. The editor routes render a server frame (case header, draft metadata, permissions) and load the editor as a client chunk. The AI panel is a client island that streams responses from a Route Handler (`/api/ai/draft-assist`) that proxies to the AI gateway in region; streamed text is never cached.

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `tribunal.cases.list` | tRPC query | with pending tasks count |
| `acceptAppointment`, `declineAppointment` | Server Action | disclosure statement versioned; starts or signals appointment workflow |
| `tribunal.record.list` | tRPC query | includes bundle versions ([[DOM-ebundling]]) |
| `tribunal.drafts.get` / `tribunal.drafts.save` | tRPC query / mutation | autosave every 10 s and on blur; `baseVersion` for optimistic concurrency; edit lock per draft (see State) |
| `tribunal.drafts.lock` / `release` | tRPC mutation | lock lease 2 minutes, renewed while editing |
| `issueOrder` | Server Action | consequential confirmation, step-up; renders PDF/UA through [[DOM-accessible-documents-and]]; serves on parties ([[DOM-service-of-notices-and-proof]]) |
| `submitAwardForSignature` | Server Action | e-sign envelope via [[INT-e-signature]]; step-up |
| `/api/ai/draft-assist` | Route Handler, streaming | summary of record, chronology, draft paragraph suggestions; tenant must have opted in ([[AI-ai-governance-and-impact]]) |
| `tribunal.deliberations.*` | tRPC | stored with classification `tribunal-only` ([[SEC-data-classification]]) |

<!-- section:state -->
## Client state and URL state

- Draft content lives on the server; the editor keeps an in-memory copy and an IndexedDB shadow (`{userId}:{tenantId}:draft:{draftId}`) only until the server confirms the save.
- Co-arbitrators: one editor at a time per draft (lock lease); others see "Being edited by Presiding Arbitrator" and a read-only view that refreshes on save. Real-time co-editing is not in scope for Phase 4.
- AI panel conversation is held in component state and discarded on leaving the page; accepted suggestions become ordinary draft text with an AI-origin mark in the draft history.

<!-- section:forms -->
## Forms, validation and uploads

Appointment acceptance and disclosure use React Hook Form + Zod. The order and award editors are rich-text editors (choice open, see questions) with a constrained schema: headings, numbered paragraphs, footnotes, tables, cross-references to record pages (`[R-123/45]` links to bundle page), no raw HTML. Paste is sanitised to the schema. Drafts save as structured JSON, and the PDF is generated server-side from it.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Not a tribunal member of this case | `notFound()` |
| Draft lock held by another member | Read-only view with lock holder name and "Request edit" |
| Save conflict (`DRAFT_VERSION_CONFLICT`) | Keep local copy, show diff dialog, never discard silently |
| AI service unavailable or tenant not opted in | Panel shows "Drafting assistance is not available for this case"; editor unaffected |
| E-sign provider down | Award stays "Ready for signature"; retry later; secretariat notified |
| Issue order fails after confirmation | Order remains draft; error with support reference; no partial service (workflow handles compensation) |

<!-- section:performance -->
## Performance budgets

Inherits `(neutral)` budgets: ≤ 250 KB gzip first-load JS excluding the editor chunk; editor chunk ≤ 200 KB gzip loaded on edit routes only. Editor input latency INP ≤ 100 ms on drafts up to 150 pages (proposed); long drafts virtualise rendering of off-screen sections. Record list pages server-side at 50 items.

<!-- section:security -->
## Security headers and browser session

Inherits group defaults. Additions: step-up before issuing an order or submitting an award for signature; `deliberations` content is never included in exports, search results for non-tribunal users or AI calls unless the presiding arbitrator enables it per case. The AI Route Handler sends only the documents the neutral selected, through [[AI-guardrails]] in region.

<!-- section:i18n -->
## Localisation hookup

Namespace `tribunal`. Awards may be drafted in the language of the arbitration, which may differ from the UI language; the editor sets `lang` on the document body from the case language, and spell-check follows it.

<!-- section:theming -->
## Tenant theming hookup

Tenant theme for the shell; the editor uses the print and formal document theme ([[PKG-print-and-formal-document-theme]]) for preview so what the neutral sees matches the PDF.

<!-- section:observability -->
## Frontend observability

Metrics: autosave latency and failures, lock contention, AI panel usage counts (no prompt text), order issue duration. AI usage telemetry is owned by [[OBS-ai-usage]].

<!-- section:testing -->
## Testing strategy

- Playwright: accept appointment; draft and issue a procedural order; two co-arbitrators contend for a lock; award to signature with e-sign sandbox.
- Keyboard and screen-reader tests of the editor (see [[APP-secretariat-console-and-neutral]]).
- Tests that deliberation notes never appear for party or secretariat personas.
- AI panel: disabled-tenant test; prompt-injection document in record does not change panel behaviour (owned with [[TST-evals-and-ai-testing]]).

<!-- section:questions -->
## Open questions

- [ ] Rich-text editor choice (ProseMirror-based such as Tiptap, or Lexical) judged on screen-reader support and structured output (owner: frontend lead; Decision record)
- [ ] Is single-editor locking acceptable to three-member tribunals, or is real-time co-editing needed? (owner: TERES product with HKIAC CMP)
- [ ] Can tribunal secretaries see deliberations at tenants where they assist the tribunal? Varies by institutional rules (owner: legal)
- [ ] Which AI drafting features are allowed per tenant, given ISO 42001 impact assessments ([[AI-ai-governance-and-impact]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Same layers as the app default. Neutrals sitting in several tenants switch host; drafts in IndexedDB are keyed by tenant and user and cleared on sign-out. AI calls go to the tenant's regional AI gateway with tenant ID on the request.

<!-- check:data-exposure -->
### Server boundary and data exposure

Tribunal-only data (deliberations, draft awards) is read only through tribunal procedures that check tribunal membership; party and secretariat view objects never include those fields. The AI handler receives only selected documents and returns text that is labelled as AI-generated until accepted.

<!-- check:session -->
### Sessions in the browser

60 min idle, 12 h absolute for `(neutral)`; drafts autosave so expiry loses at most 10 seconds of typing; step-up before issuing orders and submitting awards.

<!-- check:resilience -->
### Failure, deploys and version skew

Autosave with a local shadow until confirmed; conflict dialog instead of overwrite; issuing an order is an idempotent Server Action keyed by draft version so a retry cannot issue twice.

<!-- check:accessibility -->
### App-level accessibility mechanics

Editor toolbar follows the APG toolbar pattern; headings and numbered paragraphs are real structure; footnotes and record links are keyboard reachable; lock status and save status are announced politely. AI suggestions are inserted only on explicit action and announced.

<!-- end -->
