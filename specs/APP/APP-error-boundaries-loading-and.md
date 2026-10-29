---
id: "APP-error-boundaries-loading-and"
title: "Error boundaries, loading and empty states"
parent: "APP-frontend-standards"
order: 3
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "cbc20fe61b370c87"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.3 Error boundaries, loading and empty states

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:scope -->
## Scope, audiences and surfaces

App-wide patterns for error boundaries, loading states and empty states across all route groups in `apps/web`. Every persona node inherits these and only lists exceptions. Copy for each state is in [[APP-error-message-catalogue]]; visual components are [[PKG-alerts-toasts-and-status]] and skeletons in [[PKG-ui-design-system]].

<!-- section:routing -->
## Routes, layouts and boundaries

Boundary placement (each group follows the same shape):

```text
app/
  global-error.tsx                 # catastrophic: root layout failed
  not-found.tsx                    # unknown route
  (group)/{prefix}/
    error.tsx                      # group-level: keeps header and nav
    loading.tsx                    # only for list landing pages
    {entity}/[ref]/
      error.tsx                    # entity-level: keeps group shell and entity tabs
      not-found.tsx                # unknown OR forbidden entity, same copy
      {section}/page.tsx           # sections use <Suspense> + <ErrorBoundary> islands
```

- Sections that fail independently (timeline, documents panel, AI panel) wrap their server component in `<Suspense fallback={<Skeleton/>}>` and a client `<SectionBoundary>` so one failure does not take down the page.
- `notFound()` is used for missing and forbidden entities. `unauthorized()` sends expired sessions to sign-in. `forbidden()` (persona missing) renders the "no access to this area" page; it is never used for case-level access, to avoid revealing existence.

<!-- section:rendering -->
## Rendering and caching strategy

Loading uses streaming: the shell and entity header render first, sections stream in. `loading.tsx` is used only where nothing useful can render before data (list landing pages). Skeletons match final layout dimensions to keep CLS ≤ 0.1.

<!-- section:data -->
## Data fetching and mutations

Errors from data calls are classified on the server: domain errors (returned as problems), not-found, session, and unexpected. Only unexpected errors throw to boundaries. tRPC client errors are mapped by `problem.type` in one `handleProblem()` helper.

<!-- section:errors -->
## Error, loading and empty handling

| Error type | Detected | Handled by | User sees | Focus / announcement |
|---|---|---|---|---|
| Field validation | Zod on client, re-validated on server | form | inline messages + error summary | focus to summary; summary is `role="alert"` once |
| Domain rule (`business-rule-violation`) | domain package | inline alert near action | specific message for `code` with next step | alert announced politely; focus stays |
| Not found / forbidden entity | data access layer | `not-found.tsx` at entity | "We cannot find this page" with links back | focus to `<h1>` |
| Missing persona | `requirePersona` | `forbidden()` page | "You do not have access to this area" | focus to `<h1>` |
| Session expired | session check | redirect to sign-in with `next` | sign-in page with notice "You were signed out to protect your account" | focus to notice |
| Unexpected server error | thrown | nearest `error.tsx` | "Something went wrong" + retry + support reference (`digest`, request ID) | focus to `<h1>`; retry calls `reset()` then `router.refresh()` |
| Section failure | thrown in island | `<SectionBoundary>` | compact error within the section, rest of page usable | not announced unless user triggered it |
| Network offline | `navigator.onLine` + fetch failures | global banner | "You are offline…" | banner announced politely once |
| Stale deployment | Next.js deployment mismatch | hard reload | nothing lost (drafts saved) | — |
| Long job running | operation status | progress component | step text and percentage, "You can leave this page" | updates announced at most every 10 s |

**Empty states** always say what would appear here, why it is empty, and the next step if one exists (for example "No documents yet. Documents filed in this case will appear here."). They never imply that other parties' hidden items exist.

<!-- section:performance -->
## Performance budgets

Skeletons render without client JavaScript. Error boundaries add ≤ 3 KB gzip to each group. Error pages must render within the TTFB budget even when the database is unavailable (no data reads in boundary components).

<!-- section:security -->
## Security headers and browser session

Boundary components never render `error.message` from the server (production only passes `digest`); support references contain no personal data. `not-found` responses are identical for unknown and forbidden entities including status code (404) and response size class.

<!-- section:i18n -->
## Localisation hookup

All states use catalogue copy with ICU variables; times in messages use the seat time zone and the user's time zone.

<!-- section:observability -->
## Frontend observability

Each boundary reports `boundary.hit` with route template, boundary level (global, group, entity, section), digest and problem type; RUM dashboard per group shows boundary hit rate; alert if entity-level boundary rate exceeds 0.5% of page views for 15 minutes in a region (proposed).

<!-- section:testing -->
## Testing strategy

Storybook stories for each state of each shared component; Playwright tests that force each error type per group (mock data layer failures in preview); a test that unknown and forbidden case references return byte-identical HTML apart from nonce and request ID; axe on every state.

<!-- section:questions -->
## Open questions

- [ ] Should offline mutation queuing exist anywhere beyond uploads and drafts? (owner: frontend lead)
- [ ] Alert threshold for boundary hits (0.5% proposed) (owner: observability)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Boundary and empty-state components read no data, so they cannot show another tenant's content; support references are request IDs; tenant branding on error pages comes from the root layout's tenant-keyed theme, and the global error page uses the neutral platform theme.

<!-- check:data-exposure -->
### Server boundary and data exposure

Production boundaries see only `digest`; server logs hold the detail with request ID. Not-found and forbidden entities render the same `not-found.tsx` with a 404, tested for identical output.

<!-- check:session -->
### Sessions in the browser

`unauthorized()` redirects expired sessions to sign-in with a relative `next` path; drafts are saved first; the notice explains why the user was signed out.

<!-- check:resilience -->
### Failure, deploys and version skew

Section boundaries keep pages usable when one panel fails; drafts are saved before forced reloads; error pages make no data reads so they render during database incidents.

<!-- check:accessibility -->
### App-level accessibility mechanics

Each state defines focus and announcement behaviour: error summary takes focus on submit, boundary pages focus `<h1>`, background updates are polite and rate-limited, loading skeletons are hidden from AT with a single 'Loading' status message.

<!-- check:residency -->
### Region, residency and telemetry privacy

Boundary hits are reported to the regional RUM collector with route template, digest and problem type only; no error messages, URLs with IDs or form values leave the server.

<!-- end -->
