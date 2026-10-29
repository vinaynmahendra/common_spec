---
id: "APP-server-actions-and-mutation"
title: "Server Actions and mutation conventions"
parent: "APP-api-layer"
order: 3
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Rules for Server Actions vs tRPC mutations: auth inside every action, Zod validation, idempotency keys, cache invalidation tags"
links: []
rev: 3
syncHash: "1db92e2f3ebee82c"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.3.3 Server Actions and mutation conventions

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Rules for Server Actions vs tRPC mutations: auth inside every action, Zod validation, idempotency keys, cache invalidation tags

<!-- section:purpose -->
## Purpose and scope

Rules for writing Server Actions and tRPC mutations in `apps/web`: where they live, how they authenticate and authorise, validate input, stay idempotent, refresh caches and report errors. Server Actions are reachable as public HTTP POST endpoints even when not imported by any page, so each one must defend itself [R1].

<!-- section:rules -->
## Rules

1. **SA-1** Define Server Actions only in files with a top-level `'use server'` under `app/**/_actions/` or `packages/*/src/actions/`. No inline `'use server'` functions inside components (closures can capture values that are then sent encrypted to the client and back).
2. **SA-2** Every action is created with `defineAction({ input, persona, authorize, effect, handler })` from `@nomology/actions`. The wrapper: reads the session, confirms tenant membership, runs the persona check, parses input with the Zod schema (`.strict()`), runs `authorize(ctx, input)` against [[PKG-authorization]], applies rate limiting, applies idempotency when `effect` is `legal`, `financial` or `create`, and opens the tenant transaction.
3. **SA-3** Actions return `ActionResult<T>`: `{ ok: true, data }` or `{ ok: false, problem }` with a problem type from [[APP-api-error-catalogue-problem]]. Expected domain errors are returned, not thrown; unexpected errors are thrown and reach the error boundary with only a digest.
4. **SA-4** Actions never return Prisma records; they return view objects or IDs.
5. **SA-5** Actions that change data call `updateTag()` for every affected tenant-scoped tag (read-your-own-writes) before returning; client code then invalidates TanStack Query keys for the same entity ([[APP-client-state-and-data-fetching]]).
6. **SA-6** Forms that submit consequential actions include a hidden `idempotencyKey` generated when the form is rendered; the wrapper stores it ([[APP-api-versioning-rate-limiting]] IDEM-2).
7. **SA-7** Choose Server Action vs tRPC mutation by [[APP-route-handlers-trpc-for-internal]] STYLE-1: forms and single-entity commands use actions; interactive, high-frequency or bulk mutations use tRPC.
8. **SA-8** Actions that start long-running work start a Temporal workflow (ID `{tenantId}-{process}-{entityId}`) and return immediately with an operation reference; they never wait for the workflow to finish.
9. **SA-9** Actions with legal or financial effect write an audit event inside the same transaction ([[PKG-audit-trail]]).
10. **SA-10** Body size limit 1 MB; files never go through actions (signed upload URLs instead).

<!-- section:rationale -->
## Rationale

- Authorisation in layouts or pages does not protect actions, which can be invoked directly by their ID; SA-2 puts the check in the action itself [R2].
- Returning domain errors (SA-3) keeps form state and lets the UI show the right message, while thrown errors would reset the form through the error boundary.
- Ban on inline actions (SA-1) avoids accidental capture of server-only values in closures.

<!-- section:tooling -->
## Tooling and configuration

`@nomology/actions` (`defineAction`, `useActionForm` hook that binds React Hook Form to an action and maps `problem.errors` to fields); ESLint rules `platform/no-inline-server-action`, `platform/action-must-use-define`; generator `pnpm gen action`.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| SA-1, SA-2 | ESLint rules; CI fails |
| SA-3, SA-4 | TypeScript: `defineAction` handler return type excludes Prisma model types (branded types) |
| SA-5 | Unit test helper asserts `updateTag` called for declared tags; review checklist |
| SA-6, SA-9 | Wrapper enforces when `effect` set; reviewers check `effect` is declared correctly (CODEOWNERS for domain packages) |
| SA-8 | Lint: no `await handle.result()` in actions |
| SA-10 | `serverActions.bodySizeLimit` in `next.config.ts` |

<!-- section:examples -->
## Examples

```ts
// app/(counsel)/portal/cases/[caseRef]/filings/_actions/submit-filing.ts
'use server';
export const submitFiling = defineAction({
  input: SubmitFilingInput,                 // Zod, .strict()
  persona: ['party', 'counsel'],
  effect: 'legal',                          // idempotency + audit mandatory
  authorize: (ctx, i) => ctx.can('filing.submit', { caseRef: i.caseRef }),
  handler: async (ctx, i) => {
    const r = await ctx.domain.cases.submitFiling(i);     // inside tenant transaction
    if (!r.ok) return fail(r.problem);                    // e.g. FILING_STAGE_CLOSED
    updateTag(`tenant:${ctx.tenantId}:case:${i.caseRef}`);
    return ok({ filingRef: r.filingRef, receivedAt: r.receivedAt });
  },
});
```
Bad: `async function submit(formData) { 'use server'; await prisma.filing.create(...) }` inside a page component: no authorisation, no validation, direct Prisma, no idempotency.

<!-- section:exceptions -->
## Exceptions

Through the repo-wide process ([[FND-governance]]). SA-2 authorisation and SA-6 idempotency for legal and financial effects are non-waivable.

<!-- section:questions -->
## Open questions

- [ ] Should `defineAction` support optimistic UI helpers (`useOptimistic`) as standard, or leave per screen? (owner: frontend lead)
- [ ] How long to keep idempotency records for Server Actions (24 hours proposed, same as API) (owner: platform architecture)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

SA-1 and SA-2 are lint-enforced; SA-3 and SA-4 by types; SA-5 by test helpers and review; SA-6 and SA-9 by the wrapper when `effect` is declared; SA-10 by framework config.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

The wrapper opens the tenant transaction and performs authorisation for every action, so a page cannot ship an action without those steps; audit for legal effects is written in the same transaction.

<!-- check:onboarding -->
### Onboarding and usability

The generator produces an action with schema, persona, authorisation stub and test; the example in this node is the canonical pattern; lint messages link back to rule numbers here.

<!-- check:ownership -->
### Ownership and change

Owner: frontend lead with platform architecture; security reviews changes to `defineAction`.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Next.js: Server Actions guide",
    "url": "https://nextjs.org/docs/app/guides/server-actions",
    "vendor": "Vercel (Next.js)"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Next.js: How to think about data security",
    "url": "https://nextjs.org/docs/app/guides/data-security",
    "vendor": "Vercel (Next.js)"
  }
]
```

<!-- end -->
