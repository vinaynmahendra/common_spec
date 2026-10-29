---
id: "APP-party-and-counsel-portal"
title: "Party and counsel portal"
parent: "APP-route-groups-per-persona"
order: 1
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (counsel) route group: case list, filings, documents, payments, hearing join"
links: []
rev: 2
syncHash: "a2b5012761af9054"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.2.1 Party and counsel portal

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (counsel) route group: case list, filings, documents, payments, hearing join

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(counsel)` route group, URL prefix `/portal`, on every tenant host. It inherits all defaults from [[APP-route-groups-per-persona]]; this node records what is specific.

**Personas**: parties acting for themselves (claimants, respondents, SEBI ODR investors, MSME claimants) and their counsel or authorised representatives. Two very different audiences share the group: experienced counsel on laptops handling many cases at an arbitral institution tenant, and first-time unrepresented parties on mid-range phones at a SEBI ODR institution or CORD tenant. Plain-language rules in [[DOC-plain-language-guidance-for]] apply to every screen.

**Entry points**: email or SMS notice link (deep link to a case), invitation acceptance (from `(public)`), sign-in, public filing entry hand-off after account creation.

**Out of scope**: the in-browser hearing room ([[APP-hearing-room-in-browser]]), document rendering ([[APP-document-viewer-and-sandbox]]), sign-in and invitation screens ([[APP-public-and-sign-in-surfaces]]), payment gateway pages themselves ([[BIL-payment-gateway-integration]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(counsel)/portal/
  layout.tsx                       # shell; requirePersona('party' | 'counsel')
  page.tsx                         # redirect -> /portal/cases
  cases/
    page.tsx                       # my cases (streamed list, filters in URL)
    [caseRef]/
      layout.tsx                   # case header: ref, stage badge, parties, next deadline
      page.tsx                     # overview + case timeline
      error.tsx  not-found.tsx     # not-found also for no access
      filings/page.tsx
      filings/new/[filingType]/page.tsx       # stepper: Statement of Claim, Response, Reply, Application
      filings/[filingId]/page.tsx              # submitted filing, receipt
      documents/page.tsx
      documents/[docId]/page.tsx               # full-page viewer (deep link)
      @modal/(.)documents/[docId]/page.tsx     # viewer as modal from the list
      hearings/page.tsx
      hearings/[hearingId]/room/page.tsx       # -> APP-hearing-room-in-browser
      payments/page.tsx
      payments/[invoiceId]/pay/page.tsx        # hand-off to gateway
      payments/[invoiceId]/return/page.tsx     # verifies status server-side
      requests/new/[requestType]/page.tsx      # extension, accommodation, withdrawal
      representatives/page.tsx                 # add / remove counsel
  notifications/page.tsx
  profile/page.tsx                 # contact details, language, notification preferences
```

- The case layout reads the case header through `getCaseHeaderForParticipant(tenantId, userId, caseRef)`; if the user is not a participant it calls `notFound()`. Every child page repeats the participant check through the data access layer because the layout is not re-run on client navigation.
- `[caseRef]` is the tenant-visible case reference; the database UUID never appears in URLs.
- Pages under `payments/` and `hearings/[hearingId]/room` get route-specific CSP and Permissions-Policy additions (see Security).

<!-- section:rendering -->
## Rendering and caching strategy

| Route | Rendering | Cached data inside | Cache-Control |
|---|---|---|---|
| `/portal/cases` | dynamic, list streamed in `<Suspense>` | none (per user) | `private, no-store` |
| `/portal/cases/[caseRef]` | dynamic; header first, timeline streamed | rule-set summary for the case's procedure via `'use cache: remote'` keyed `(tenantId, ruleSetId, version, locale)` | `private, no-store` |
| `filings/new/[filingType]` | dynamic; form schema from tenant form definition cached `(tenantId, formId, version)` | form definition | `private, no-store` |
| `documents`, `hearings`, `payments` | dynamic, streamed | none | `private, no-store` |
| `payments/[invoiceId]/return` | dynamic, never cached; reads payment status from the server | none | `no-store` |

Nonce-based CSP for the whole group ([[APP-rendering-and-caching-strategy]]).

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Called from | Notes |
|---|---|---|---|
| `portal.cases.list` | tRPC query | cases list (client filters) | cursor pagination, 25 per page; filters: stage, role, has-deadline |
| `getCaseHeaderForParticipant` | server read | case layout | `React.cache` per request |
| `portal.case.timeline` | tRPC query | timeline component ([[PKG-case-timeline]]) | events visible to this participant only (no tribunal-only events) |
| `portal.documents.list` | tRPC query | documents page | includes scan status from [[PKG-encryption-at-rest-signed-urls]] |
| `portal.documents.getViewUrl` | tRPC mutation | viewer | issues a short-lived signed URL on the sandbox origin ([[APP-document-viewer-and-sandbox]]) |
| `portal.filings.saveDraft` | tRPC mutation | stepper autosave (every 15 s and on step change) | optimistic concurrency with `draftVersion` |
| `submitFiling` | Server Action | stepper final step | Idempotency key from the draft ID; consequential confirmation ([[PKG-modal-dialog-and-consequential]]); starts or signals the case workflow; returns receipt |
| `requestProcedural` | Server Action | requests pages | extension and accommodation requests; creates a human task for the tribunal secretary ([[WF-human-tasks]], [[APP-accessibility-feedback]]) |
| `inviteRepresentative`, `removeRepresentative` | Server Action | representatives page | step-up required |
| `startPayment` | Server Action | pay page | creates a payment intent with the gateway, returns redirect URL |
| `portal.payments.status` | tRPC query | return page | server-side verification with the gateway, never trusts query parameters |

After `submitFiling`, the action calls `updateTag('tenant:{tenantId}:case:{caseRef}')` and the client invalidates `[tenantId, 'portal', 'case', caseRef]`.

<!-- section:state -->
## Client state and URL state

- URL: case list filters and sort, document list folder and filter, active stepper step (`?step=parties`).
- Server: filing drafts (`filing_drafts` table, owned by [[DOM-cases]]), so a draft started on a phone can be finished on a laptop.
- IndexedDB: only the upload queue for files not yet uploaded (so a page reload can resume), keyed `{userId}:{tenantId}:upload:{draftId}`; cleared on submit and on sign-out.
- Nothing about a case is kept in `localStorage`.

<!-- section:forms -->
## Forms, validation and uploads

- Filing stepper uses [[PKG-stepper-and-multi-step-form]] with save-and-resume; each step validates with the step's Zod schema on the client and again on the server.
- Tenant-defined fields come from [[PKG-forms-and-form-builder]]; their schema version is stored with the draft and the submitted filing.
- Uploads: [[PKG-file-upload-dropzone]] with direct-to-storage signed PUT, 500 MB per file and 2 GB per filing (proposed; tenant-configurable lower), resumable multipart for files over 50 MB. A file cannot be attached to a submitted filing until malware scanning passes; the UI shows "Checking file" and announces the result.
- Declarations at submission (statement of truth, consent to electronic service) render from the legal text register with version IDs recorded ([[I18N-legal-declaration-and-consent]]).
- Before JavaScript loads, the short forms (reply to a request, accept terms) work as plain form posts to Server Actions; the stepper requires JavaScript and says so.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Case not found or not a participant | `notFound()` → case `not-found.tsx`, same text as unknown case |
| Filing outside allowed stage or after deadline | Action returns `{ ok: false, code: 'FILING_STAGE_CLOSED' }`; inline alert with the deadline and a link to request an extension |
| Draft edited in another tab | `DRAFT_VERSION_CONFLICT`; dialog offers "Load latest" or "Keep mine as a copy" |
| Upload failed or file infected | Per-file status in the dropzone with retry; infected files removed with the copy from [[APP-error-message-catalogue]] |
| Payment failed or cancelled | Return page shows status from the server and a retry button; never marks paid from query parameters |
| Session expired mid-filing | Draft already saved; redirect to sign-in and back to the same step |

Loading: skeleton for the case header, streamed timeline, progress bar for uploads with percentage text.

<!-- section:performance -->
## Performance budgets

Inherits the `(counsel)` budgets from [[APP-route-groups-per-persona]] (LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at p75 on mid-range Android over slow 4G; ≤ 180 KB gzip first-load JS). Additional: the case list must render its first 25 rows in the initial HTML (no client-only fetch); the document viewer and stepper are separate chunks loaded on their routes only.

<!-- section:security -->
## Security headers and browser session

Inherits nonce CSP, `frame-ancestors 'none'`, `private, no-store` and the persona session rules. Differences:
- `payments/[invoiceId]/pay`: `form-action` and `connect-src` extended with the tenant's configured gateway hosts only on this route; if the gateway uses an embedded widget, its script host is allowed only here.
- `hearings/[hearingId]/room`: Permissions-Policy enables `camera`, `microphone`, `display-capture` for self and the video provider only on this route ([[APP-hearing-room-in-browser]]).
- `/portal/*` HTML never carries other parties' contact details unless the procedure requires service between parties and the tenant setting allows it.
- Step-up before: adding or removing a representative, changing refund bank details, withdrawing a claim.
- "This is a shared device" option at sign-in shortens idle timeout to 15 minutes and disables draft storage in IndexedDB.

<!-- section:i18n -->
## Localisation hookup

Message namespace `portal`. SEBI ODR tenants may enable Indian languages; the case timeline shows legal documents in the language filed, with `lang` set on each document title. Deadlines show the seat time zone and the user's local time ([[PKG-date-and-time-picker-with]]). Money uses the invoice currency with locale formatting (for example `₹1,25,000.00` in `en-IN`).

<!-- section:theming -->
## Tenant theming hookup

Tenant theme from the root layout. Case-stage and deadline badges use semantic status tokens that tenants cannot recolour ([[PKG-status-and-deadline-badges]]).

<!-- section:observability -->
## Frontend observability

Business funnel events (no content): `filing_started`, `filing_step_completed`, `filing_submitted`, `payment_started`, `payment_returned` with tenant, filing type, step index and duration only ([[OBS-business-events]]). RUM per route template. Upload failures counted by error class.

<!-- section:testing -->
## Testing strategy

- Playwright journeys: file a Statement of Claim with two uploads; respond to a claim; request an extension; pay an invoice (gateway sandbox); join a hearing pre-check. Each on mobile viewport and desktop, with axe and keyboard-only runs.
- Negative access: party of case A opens `/portal/cases/{caseRef of B}` and gets the same not-found as an unknown reference.
- Contract tests for `submitFiling` and `portal.*` procedures.
- Version-skew test on the stepper.

<!-- section:questions -->
## Open questions

- [ ] Upload limits (500 MB per file, 2 GB per filing) and whether tenants can raise them (owner: product, [[DOM-documents]])
- [ ] Should party-to-party contact details ever be shown in the portal, or only through served documents? (owner: legal, per tenant rules)
- [ ] Payment gateway per billing entity and region, and whether any embeds a widget (owner: finance, [[BIL-payment-gateway-integration]])
- [ ] Is a "shared device" option enough for court-kiosk use, or do some tenants need a kiosk mode? (owner: CORD product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Tenant from host; case access checked through `getCaseHeaderForParticipant` and repeated in each page and action; all reads in tenant transactions with forced RLS. Cached data in this group is limited to rule-set summaries and form definitions keyed by `tenantId` and version. A counsel with cases at two tenants works on two hosts with separate query caches. The two-tenant diff test covers `/portal/cases` and one case page.

<!-- check:data-exposure -->
### Server boundary and data exposure

View objects for the portal exclude tribunal-only events, internal secretariat notes and other parties' contact details unless allowed. `submitFiling` ignores any party or case IDs in the payload that do not match the authorised case from the reference. Not-found and no-access are identical.

<!-- check:session -->
### Sessions in the browser

`(counsel)` timeouts: 30 min idle (15 min on a shared device), 12 h absolute; warning 2 minutes before. Drafts are on the server, so expiry loses nothing. Step-up for representative changes, bank details and withdrawal.

<!-- check:resilience -->
### Failure, deploys and version skew

Filing drafts autosave to the server every 15 seconds and on step change; uploads are resumable multipart and their queue is kept in IndexedDB; a forced reload after a deploy restores the step. `submitFiling` is idempotent on the draft ID, so a double tap or a retry after a timeout produces one filing and one receipt.

<!-- check:accessibility -->
### App-level accessibility mechanics

The stepper announces "Step 2 of 5: Parties" on step change and moves focus to the step heading; the error summary takes focus on failed submit and links to each field; upload progress is announced politely at 25% steps and on completion. Deadlines are written as absolute dates with time zone, never colour or countdown alone. Conformance mapping is in [[APP-party-and-counsel-portal-2]].

<!-- check:residency -->
### Region, residency and telemetry privacy

All requests go to the tenant's regional host; uploads go directly to the regional bucket via signed URLs; payment gateway calls are per billing entity and region. RUM events contain route templates only.

<!-- end -->
