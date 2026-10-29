---
id: "APP-client-state-and-data-fetching"
title: "Client state and data-fetching conventions"
parent: "APP-frontend-standards"
order: 6
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Where state lives (server, URL, TanStack Query, forms), query key conventions including tenantId, clearing on sign-out and tenant switch"
links: []
rev: 3
syncHash: "f5e65abd6e7785a4"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.4.6 Client state and data-fetching conventions

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Where state lives (server, URL, TanStack Query, forms), query key conventions including tenantId, clearing on sign-out and tenant switch

<!-- section:purpose -->
## Purpose and scope

Where each kind of state lives in `apps/web`, the TanStack Query conventions (query keys including `tenantId`, stale times, invalidation), how server data is passed from Server Components to the client, and what is cleared on sign-out and on tenant switch. The aim is that no client-side cache or storage can ever show one tenant's or one user's data to another, and that work in progress survives reloads.

<!-- section:rules -->
## Rules

1. **STATE-1** State placement:

   | State | Lives in |
   |---|---|
   | Data shown on first render | Server Components via `@nomology/data-access` |
   | Shareable view state (filters, sort, page cursor, tab, step) | URL search params (typed with a parser such as `nuqs`) |
   | Interactive server data on the client | TanStack Query through tRPC |
   | Form state | React Hook Form |
   | Drafts of legal filings and orders | Server (draft tables), with IndexedDB shadow only until saved |
   | Pending uploads | IndexedDB queue |
   | Purely local UI state | `useState` / `useReducer` |
   | User preferences (density, hearing devices) | server user settings, or `localStorage` for device-specific, non-case data |
2. **STATE-2** One `QueryClient` per tenant session: the `QueryProvider` is keyed by `tenantId` and `userId`, so a tenant or user change creates a fresh cache.
3. **STATE-3** Every query key starts with `[tenantId, persona, entity, ...]` (the tRPC integration's keys are wrapped by our `queryKey()` helper).
4. **STATE-4** Default `staleTime` 30 s, `gcTime` 5 min, `retry` up to 3 for queries with exponential backoff, no automatic retry for mutations (they retry only with the same idempotency key on user action).
5. **STATE-5** Server Components may prefetch into TanStack Query using `HydrationBoundary` only for data the user is allowed to see, shaped as view objects [R1].
6. **STATE-6** No case data, personal data or tokens in `localStorage` or `sessionStorage`. IndexedDB databases are named `{userId}:{tenantId}` and are encrypted at rest only by the OS; they hold drafts and upload queues only.
7. **STATE-7** On sign-out (any tab): broadcast on `BroadcastChannel('session')`; every tab clears its `QueryClient`, deletes IndexedDB databases for that user after flushing or discarding unsynced drafts with user consent, and navigates to `/sign-in`. Authenticated pages are `no-store` so the back button and back/forward cache do not show them.
8. **STATE-8** On tenant switch: navigate to the other tenant's host (new document); nothing is carried over.
9. **STATE-9** After a mutation, invalidate the precise keys for the entity (`[tenantId, persona, 'case', caseRef]`) and call `router.refresh()` only when Server Component data on screen depends on it.

<!-- section:rationale -->
## Rationale

Keying the provider by tenant (STATE-2) is a structural guarantee rather than relying on every key being correct; key prefixes (STATE-3) are a second layer that also makes targeted invalidation easy.

<!-- section:tooling -->
## Tooling and configuration

`@nomology/query` (`QueryProvider`, `queryKey()` helper, default options), `nuqs` (or equivalent) for typed URL state, `idb-keyval` or Dexie for IndexedDB, ESLint rules: no `localStorage` in `apps/web` except the allow-listed preference module, `@tanstack/eslint-plugin-query`.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| STATE-2, 3 | Unit test of `QueryProvider`; lint rule forbids `useQuery` with a literal key not built by `queryKey()` |
| STATE-6 | ESLint `no-restricted-globals` for `localStorage`/`sessionStorage` outside `packages/prefs` |
| STATE-7 | Playwright: sign out in tab A, assert tab B shows sign-in and IndexedDB is empty |
| STATE-8 | Two-tenant Playwright test |
| STATE-4, 5, 9 | Code review checklist |

<!-- section:examples -->
## Examples

```ts
const key = queryKey(tenantId, 'secretariat', 'queue', queueId, { stage, sort, cursor });
// ['7f3c…', 'secretariat', 'queue', 'q-awaiting', {stage:'awaiting-response', sort:'-nextDeadline', cursor:null}]
```
Bad: `useQuery({ queryKey: ['cases'] })` — no tenant, no persona, invalidates everything named 'cases'.

<!-- section:exceptions -->
## Exceptions

Through [[FND-governance]]; STATE-6 and STATE-7 are non-waivable.

<!-- section:questions -->
## Open questions

- [ ] Do we need encryption of IndexedDB drafts with a per-session key (WebCrypto), for shared devices? (owner: security)
- [ ] URL state library choice (owner: frontend lead)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Key and storage rules are lint-enforced; sign-out and tenant-switch clearing are Playwright-tested; stale times and invalidation are review items.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Tenant-keyed providers, tenant-prefixed keys and no case data in web storage keep client caches tenant- and user-isolated; drafts stay server-side where possible.

<!-- check:onboarding -->
### Onboarding and usability

`queryKey()` and `useActionForm()` make the right pattern the easy one; the STATE-1 table is the decision aid.

<!-- check:ownership -->
### Ownership and change

Owner: frontend lead; security reviews changes to STATE-6 and STATE-7.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "TanStack Query: Advanced server rendering",
    "url": "https://tanstack.com/query/latest/docs/framework/react/guides/advanced-ssr",
    "vendor": "TanStack"
  }
]
```

<!-- end -->
