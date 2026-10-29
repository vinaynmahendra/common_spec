---
id: "WF-workflow-authoring-studio"
title: "Workflow authoring studio"
parent: "WF"
order: 12
type: "capability"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "No-code studio under /admin/workflows for designing, validating, simulating, reviewing, publishing and migrating case-type blueprints, plus automation rules, SLA policies, business schedules and work queues"
links: []
rev: 2
syncHash: "31c27b24b45449d5"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 7.11 Workflow authoring studio

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> No-code studio under /admin/workflows for designing, validating, simulating, reviewing, publishing and migrating case-type blueprints, plus automation rules, SLA policies, business schedules and work queues

<!-- section:scope -->
## Scope, audiences and surfaces

The **workflow authoring studio** is the no-code workspace inside the `(tenant-admin)` route group ([[APP-tenant-admin-console]]) where tenant staff design, test, publish and migrate case-type blueprints, and manage the surrounding workflow configuration: automation rules, SLA policies, business schedules and work queues. It saves only declarative configuration ([[WF-process-definition-model]]); it never produces code.

| Item | Value |
|---|---|
| Route prefix | `/admin/workflows` on tenant hosts (for example `acme.cord.example/admin/workflows`) |
| Platform counterpart | `/platform/blueprints` in [[APP-platform-admin-and-support]] for Nomology library blueprints and offering-locked components (same components, platform data source) |
| Personas | `workflow_designer` (builds and tests), reviewers and approvers (`tenant_admin`, institution legal lead with `workflow.definition:approve`), `unit_admin` (unit-scoped queues and schedules), `auditor` (read-only, history and evidence), Nomology implementation specialists under approved support access ([[PKG-support-access-and-impersonation]]) |
| Entry points | Admin navigation "Workflows"; deep links from a case ("view blueprint version"), from the admin copilot ("open draft"), from change history ([[APP-admin-change-history]]) |
| Backing API | tRPC `admin.workflows.*` routers ([[APP-internal-api-trpc-routers-per]]) calling the same typed operations as the REST tenant admin API `/admin/v1/workflows/...` ([[INT-tenant-admin-api]]) |

Requirements use the prefix `WFA-FR-`.

- **WFA-FR-1** Every authoring operation available on the visual canvas shall be available in the outline view, and the reverse, so the studio can be used fully with keyboard and screen reader.
- **WFA-FR-2** The studio shall validate continuously and show errors and warnings in a panel linked to the element, using the same validator that gates publishing.
- **WFA-FR-3** The studio shall show for every element its locked or inherited state and the lock source (platform, offering, tenant).
- **WFA-FR-4** The studio shall never publish directly from an edit; every change goes through draft, review, approval and publish ([[WF-workflow-versioning#design]]).
- **WFA-FR-5** AI assistance (generate a draft from a description, explain a version, propose scenarios) shall produce drafts with a readable diff and an explanation, attributed as AI-assisted, and follow the same lifecycle ([[APP-admin-copilot]]).
- **WFA-FR-6** The studio shall preview what each participant role sees at each stage (stage name, tasks, forms, notices) using sample data, never real case data.

**Out of scope:** decision table editor internals ([[PKG-rules-and-decision-engine]]), form builder internals ([[PKG-forms-and-form-builder]]), template editors ([[PKG-document-and-notification]]), AI step configuration internals ([[WF-ai-steps-and-agents]]). The studio embeds or links to those editors.

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(tenant-admin)/admin/workflows/
  layout.tsx                                   # sub-navigation; requirePermission('workflow.definition:read')
  page.tsx                                     # case types list: status, current version, running cases, drafts awaiting review
  loading.tsx  error.tsx
  case-types/new/page.tsx                      # wizard: start blank, from library blueprint, or from copilot description
  case-types/[caseTypeKey]/
    layout.tsx  not-found.tsx                  # loads case type header (name, lock state)
    page.tsx                                   # overview: versions, running cases per version, migrations, owners
    versions/[version]/
      layout.tsx                               # version header: status, change class, validation badge, actions
      page.tsx                                 # redirect to canvas
      canvas/page.tsx                          # stage-lane canvas (client island) + outline toggle (?view=outline)
      canvas/@inspector/(.)steps/[stepId]/page.tsx   # intercepting route: step inspector drawer
      steps/[stepId]/page.tsx                  # full-page step editor (deep link, no-JS fallback)
      stages/[stageKey]/page.tsx               # stage settings: status mapping, SLA, visibility, entry and exit
      facts/page.tsx                           # facts and their sources
      components/page.tsx                      # forms, decision tables, templates, SLA policies used (links to editors)
      settings/page.tsx                        # case_type-scope settings overrides
      preview/page.tsx                         # role preview (?role=respondent&stage=awaiting_response)
      validate/page.tsx                        # full validation report
      simulate/page.tsx  simulate/[runId]/page.tsx   # scenarios, runs, traces, coverage
      diff/[otherVersion]/page.tsx             # semantic diff
      review/page.tsx                          # approver view: diff, evidence, approve / reject
    migrations/page.tsx  migrations/new/page.tsx  migrations/[planId]/page.tsx
  automation/page.tsx  automation/new/page.tsx  automation/[ruleKey]/page.tsx  automation/[ruleKey]/executions/page.tsx
  sla-policies/page.tsx  sla-policies/[policyKey]/page.tsx
  calendars/page.tsx  calendars/[scheduleKey]/page.tsx       # business schedules and bindings
  queues/page.tsx  queues/[queueKey]/page.tsx                # work queues, members, assignment strategy
  rules/  forms/  fields/                                   # editors owned by PKG-rules-and-decision-engine, PKG-forms-and-form-builder, PKG-metadata-management-entity
  library/page.tsx                                           # library blueprints and fragments available to copy
```

- `proxy.ts` resolves the tenant host and region as for all groups; nothing workflow-specific happens there.
- The `layout.tsx` at each level fetches only headers (names, status, permissions for the action bar); heavy data (blueprint body, projections) is fetched by the page.
- Unit admins see `calendars`, `queues` and `automation` filtered to their units; the server enforces this through scope checks, not the navigation.
- `not-found.tsx` uses the shared identical not-found and no-access text ([[APP-error-message-catalogue]]).

<!-- section:rendering -->
## Rendering and caching strategy

| Route | Rendering | Cache |
|---|---|---|
| Lists (case types, automation, SLA policies, calendars, queues) | Server Components streamed at request time | Configuration reads use `'use cache: remote'` keyed by `tenant:{tenantId}:workflows:{publishedSeq}`; drafts are never cached |
| Version canvas and outline | Server Component shell + client island (`'use client'`) for the canvas; body fetched server-side and passed as initial data to TanStack Query | No cache for drafts; published versions cached by `blueprintVersionId` (immutable, `cacheLife('max')`) |
| Diff, validation report, simulation trace | Streamed at request time; long simulations show progress via polling | Trace JSON cached by `traceSha256` |
| Preview | Server-rendered with sample data in the persona route group's components | No cache |

All responses carry `Cache-Control: private, no-store` (inherited from [[APP-tenant-admin-console#rendering]]); no CDN storage. Publish calls `updateTag('tenant:{tenantId}:workflows')` so the secretariat console and portals see new case-type metadata on the next request.

<!-- section:data -->
## Data fetching and mutations

Reads: Server Components through the data access layer; interactive canvas state through tRPC with TanStack Query (query keys `['wf', tenantId, 'version', versionId]`, cleared on tenant switch).

Writes: tRPC mutations (not Server Actions) for all canvas edits, because they are frequent and need structured validation results; each mutation sends `expectedVersion` and an idempotency key ([[APP-server-actions-and-mutation]]).

| Operation | Procedure | Permission | Notes |
|---|---|---|---|
| Create case type | `admin.workflows.caseTypes.create` | `workflow.definition:create` | From blank, library copy or copilot draft |
| Save draft body (patch) | `admin.workflows.versions.patch` | `workflow.definition:update` | JSON Patch ops; returns validation issues; soft edit lock renewed |
| Create draft from published | `admin.workflows.versions.branch` | `workflow.definition:update` | |
| Validate | `admin.workflows.versions.validate` | `workflow.definition:read` | Same validator as publish |
| Run simulation | `admin.workflows.simulations.run` | `workflow.simulation:create` | Enqueues `workflow.simulate`; returns run ID |
| Submit for review | `admin.workflows.versions.submit` | `workflow.definition:update` | Gate from [[WF-workflow-simulation]] |
| Approve / reject | `admin.workflows.versions.approve` / `.reject` | `workflow.definition:approve` | Not the author; step-up |
| Publish / schedule | `admin.workflows.versions.publish` | `workflow.definition:publish` | Step-up; optional `effectiveFrom` |
| Roll back | `admin.workflows.versions.rollback` | `workflow.definition:publish` | Creates draft copy of earlier version, then normal approval |
| Migration plan CRUD, dry run, approve, execute | `admin.workflows.migrations.*` | `workflow.migration:create` / `:approve` / `:publish` | [[WF-workflow-versioning#design]] |
| Automation rule CRUD, dry run, publish, enable | `admin.workflows.automation.*` | `workflow.automation:update` / `:publish` | [[WF-automation-rules#api]] |
| SLA policy, business schedule, queue CRUD | `admin.workflows.sla.*`, `.calendars.*`, `.queues.*` | `workflow.sla_policy:update` / `:publish`, `workflow.calendar:update`, `workflow.queue:configure` | |

The REST equivalents live under `/admin/v1/workflows/case-types/{key}/versions/{v}` with custom methods `:submit`, `:approve`, `:publish`, `:rollback`.

<!-- section:state -->
## Client state and URL state

| State | Where |
|---|---|
| Draft body | Server (draft version), mirrored in TanStack Query; optimistic updates with rollback on conflict |
| Undo / redo stack | Client memory per session (last 100 operations); each undo is a new patch to the server |
| Selected element, zoom, pan, outline expansion | URL search params (`?sel=step:serve_notice&view=outline`) so links can be shared |
| Canvas layout positions | Stored in the draft body under `layout` (ignored by the interpreter) |
| Edit lock | Server lease (15 minutes, renewed every 60 s while the tab is active); a second editor sees read-only with "Ask to edit" |
| Unsent comments on review | Local storage per user and version (convenience only, wrapped in try/catch) |

Cleared on sign-out and tenant switch: TanStack Query cache, undo stack, local storage drafts for that tenant ([[APP-client-state-and-data-fetching]]).

<!-- section:forms -->
## Forms, validation and uploads

- Inspector panels are React Hook Form with Zod schemas generated from the blueprint JSON Schema, shared with the server validator ([[APP-framework-dependencies]]).
- Expressions (gateway conditions, automation conditions) use a structured condition builder ("When [fact] [operator] [value]", AND / OR groups, depth 2) with a text mode that shows the expression in the closed grammar; both edit the same expression and type-check against fact types as the user types.
- Duration inputs accept ISO 8601 or a guided picker ("30 calendar days from service, roll to next working day") that writes the deadline spec used by [[PKG-calendars-and-deadline]].
- Localised labels: one field per enabled locale with a "missing translation" warning; the default locale is required.
- Autosave every 2 seconds after the last change and on blur; status text "Saved 10:42" in a polite live region.
- Imports: configuration package upload for blueprints (`.ntpkg`, signed, max 10 MB) goes through [[PKG-configuration-packages]] and always lands as a draft.

<!-- section:errors -->
## Error, loading and empty handling

| Error | Handling |
|---|---|
| Validation issues | Not errors: shown in the validation panel with severity, element link and fix hint; errors block submit only |
| `version-conflict` (someone else saved) | Banner "This draft changed since you opened it" with compare and merge (element-level three-way merge where no element was changed by both, else choose per element) |
| Edit lock held | Read-only canvas with the holder's name and "Ask to edit" (sends an in-app notice) |
| Permission denied | Action buttons hidden from server-computed allowed actions; direct calls return 403 problem `permission-denied` with the shared text |
| Locked element edit | Inline lock badge "Locked by Nomology (SEBI ODR offering)"; inspector read-only |
| Simulation running long | Progress text and cancel; result arrives by polling every 2 s |
| Server or network failure on save | "Your changes are not saved yet. Retrying…" with exponential retry; local queue of patches kept in memory, warning on tab close |
| Route-level failure | `error.tsx` per version layout with retry and a link back to the case type |

Loading: skeleton lanes for the canvas, skeleton rows for lists, streamed diff sections.

<!-- section:performance -->
## Performance budgets

Inherits the desktop budgets of [[APP-tenant-admin-console#performance]] with these additions:

| Budget | Target | Enforced by |
|---|---|---|
| Canvas route client JS | ≤ 350 KB gzip (canvas library and inspector loaded only on this route) | Bundle size check in CI ([[APP-frontend-performance-budgets]]) |
| Interaction to next paint on canvas edits | ≤ 200 ms p75 for blueprints up to 200 steps | RUM ([[OBS-frontend-real-user-monitoring]]) |
| Save round trip (patch + validation) | ≤ 800 ms p95 | Server metric `wf_studio_patch_duration_seconds` |
| Validate full blueprint | ≤ 2 s for 200 steps (same as [[PKG-workflow-templates#nfr]]) | Server metric |
| Scenario simulation | ≤ 1 s per scenario, ≤ 30 s for 30 scenarios | Queue metric |

Measured on the platform's desktop profile (mid-range laptop, 4× CPU throttling off, cable network). The canvas virtualises nodes outside the viewport above 150 elements.

<!-- section:security -->
## Security headers and browser session

- Inherits headers and session rules from [[APP-tenant-admin-console#security]] (15 minutes idle, 8 hours absolute).
- Step-up MFA for approve, publish, rollback, migration approve and execute, and automation publish ([[PKG-mfa-session-management-device]]).
- No third-party scripts; the canvas library is bundled and pinned (candidate `@xyflow/react`, decision open), reviewed under [[APP-framework-dependencies]].
- Preview renders sample data only; it never loads a real case. Simulation traces show fact keys and sample values only.
- Tenant-entered rich text (help text, notice snippets) is sanitised server-side to the allow-list schema; expressions use the sandboxed `expr/1` evaluator, never `eval` or `Function`. The browser may evaluate them for preview only; the server re-evaluates on validate, publish and run and is always authoritative (proposed in [[ADR-expression-and-rules-language]]).
- Every procedure checks permission and scope on the server; the browser receives only versions and components the user may read. Support staff see the studio read-only unless the support-access grant includes `workflow.definition:update`.

<!-- section:i18n -->
## Localisation hookup

- Studio UI strings come from the admin message pack for the user's locale ([[I18N-i18n]]); blueprint labels are edited in every locale enabled for the tenant ([[PKG-settings-branding-content]]).
- Terminology overrides ([[PKG-tenant-terminology-and-copy]]) apply in previews so the designer sees the tenant's words ("Request for arbitration" instead of "Statement of claim").
- Durations and dates in the inspector show both the rule ("30 calendar days") and, in previews and traces, the resolved date in the case seat time zone and UTC.
- Right-to-left locales: outline view and inspector support `dir="rtl"`; the canvas lays out stages right to left when the admin UI locale is RTL.

<!-- section:theming -->
## Tenant theming hookup

The studio uses the tenant admin shell's theme (tenant brand slots in the header only, [[PKG-branding-and-theming]]). Canvas element colours come from semantic tokens (`--color-stage-*`, status tokens from [[PKG-colour-and-contrast]]) and every element type also has a shape and an icon, so meaning never depends on colour. The role preview renders with the target persona group's tenant theme so the designer sees what parties will see.

<!-- section:observability -->
## Frontend observability

- Server spans for every `admin.workflows.*` procedure with attributes `tenant.id`, `region`, `route.group = tenant-admin`, `wf.operation`, never blueprint contents.
- Product usage events (pseudonymous, [[OBS-usage]]): `studio.version_created`, `studio.validation_failed{issueCode}`, `studio.simulation_run{result}`, `studio.submitted`, `studio.published{changeClass}`, `studio.copilot_draft_accepted`; used to find confusing parts of the editor.
- Web Vitals and errors via same-origin RUM ([[OBS-frontend-real-user-monitoring]]).

<!-- section:testing -->
## Testing strategy

| Layer | Proves |
|---|---|
| Component tests (Storybook + Testing Library) | Inspector forms, condition builder, lock badges, validation panel |
| Accessibility (axe in Storybook and Playwright; manual NVDA, JAWS and VoiceOver passes per release) | Outline view parity, keyboard move of steps (no drag-only, WCAG 2.5.7), focus not obscured by the inspector (2.4.11), status messages (4.1.3) [R1]; authoring tool guidance from ATAG Part A (accessible authoring UI) and Part B (helping authors produce accessible forms and notices) [R2] |
| Contract tests | Every tRPC procedure against the shared Zod schemas and the REST `/admin/v1/workflows` OpenAPI |
| Playwright end-to-end | Create case type from library, edit, fail validation, add scenario, pass gate, submit, approve as a second user, publish, see the new case type in the secretariat console; two-tenant test on every publish path |
| Visual regression | Canvas at three zoom levels in light, dark and high-contrast modes |
| Performance | Canvas with 200 steps meets INP budget in CI lab run |

<!-- section:questions -->
## Open questions

- [ ] Canvas library: `@xyflow/react` (React Flow) with our own keyboard layer, or a list-first editor with a read-only diagram rendered by Mermaid? Decision depends on an accessibility spike. Owner: frontend lead.
- [ ] Real-time co-editing (multiple designers in one draft) vs soft lock (proposed for launch). Owner: product.
- [ ] Should approvers be able to comment on individual elements in review (threaded comments stored with the version)? Proposed: yes, Phase 5. Owner: product.
- [ ] Which ATAG Part B success criteria do we commit to for content produced in the studio (forms and notices)? Owner: accessibility lead with [[APP-accessibility-wcag-2-1-aa]].
- [ ] Does the platform console reuse this route tree with a different data source, or a separate tree under `/platform/blueprints`? Owner: admin group ([[APP-platform-admin-and-support]]).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

All responses are `private, no-store`; configuration caches are keyed by tenant and published sequence, drafts are never cached; TanStack Query keys include `tenantId` and are cleared on tenant switch; previews use sample data; two-tenant Playwright tests run on every publish path.

<!-- check:data-exposure -->
### Server boundary and data exposure

Every tRPC procedure checks permission and unit scope on the server; allowed actions are computed server-side; support staff are read-only by default; traces and previews never include real case data.

<!-- check:browser-security -->
### Browser security posture

No third-party scripts; bundled, pinned canvas library; expressions parsed on the server with a closed grammar, never evaluated in the browser; rich text sanitised server-side; CSP and framing inherited from the tenant admin group.

<!-- check:session -->
### Sessions in the browser

Inherits 15-minute idle and 8-hour absolute limits; step-up MFA for approve, publish, rollback and migration actions; edit locks are server leases that expire, so an abandoned session does not block others.

<!-- check:resilience -->
### Failure, deploys and version skew

Autosave every 2 seconds; patches queued in memory and retried; conflict detection with element-level merge; simulation results are durable runs, so a closed tab does not lose them.

<!-- check:capacity -->
### Rendering cost and capacity

Studio traffic is low (tens of designers per region); the expensive work (validation, simulation) runs on BullMQ workers with per-tenant fairness, so the Next.js containers only serve light pages.

<!-- check:accessibility -->
### App-level accessibility mechanics

The outline view is the primary, fully equivalent representation (WFA-FR-1); no drag-only operations; focus management on drawer open and close; status messages announced; ATAG Part A and Part B used as the authoring-tool checklist [R2]; WCAG 2.2 AA tested with axe and manual screen-reader passes [R1].

<!-- check:residency -->
### Region, residency and telemetry privacy

The studio is served from the tenant's home region; all data, traces and RUM stay in-region; library blueprints are loaded per region from reference data.

<!-- check:supply-chain -->
### Framework upgrades and supply chain

The canvas library is the main new client dependency; it is pinned, reviewed under the framework dependency policy and updated with the monthly dependency cycle; no runtime-loaded plugins.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WCAG",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C",
    "id": "R2",
    "ident": "ATAG",
    "kind": "standard",
    "title": "Authoring Tool Accessibility Guidelines (ATAG) 2.0",
    "url": "https://www.w3.org/TR/ATAG20/",
    "version": "2.0"
  }
]
```

<!-- end -->
