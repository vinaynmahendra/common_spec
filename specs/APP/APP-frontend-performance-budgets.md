---
id: "APP-frontend-performance-budgets"
title: "Frontend performance budgets"
parent: "APP-frontend-standards"
order: 5
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Repo-wide Core Web Vitals, JavaScript size and TTFB budgets per route group, enforced in CI and RUM"
links: []
rev: 2
syncHash: "7d98f98919d1e0b8"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.5 Frontend performance budgets

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Repo-wide Core Web Vitals, JavaScript size and TTFB budgets per route group, enforced in CI and RUM

<!-- section:purpose -->
## Purpose and scope

Sets repo-wide performance budgets for `apps/web` per route group and how they are enforced in CI and watched in production. Budgets are measured in the tenant's region at the 75th percentile, consistent with the Core Web Vitals method [R1].

<!-- section:rules -->
## Rules

1. **PERF-1** Field budgets (RUM, p75, per route group and region, 28-day window): LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 for every group; `(public)` LCP ≤ 2.0 s.
2. **PERF-2** Server budgets (p75 in region): TTFB ≤ 200 ms for `(public)` static shells; ≤ 600 ms for `(counsel)`, `(neutral)`, `(transcriber)`; ≤ 800 ms for `(secretariat)` and admin groups.
3. **PERF-3** First-load JavaScript per route (gzip): `(public)` ≤ 130 KB; `(counsel)` ≤ 180 KB; `(neutral)` ≤ 250 KB plus editor chunk ≤ 200 KB on edit routes; `(secretariat)` ≤ 260 KB; `(transcriber)` ≤ 300 KB; admin groups ≤ 250 KB. Third-party SDKs (video, payments) are loaded on their routes only and measured separately.
4. **PERF-4** RSC payload for a page ≤ 200 KB (uncompressed) for the first render.
5. **PERF-5** Lab profiles: `(public)` and `(counsel)` on an emulated mid-range Android phone with "Slow 4G" throttling; others on desktop with "Fast 4G" / cable throttling.
6. **PERF-6** Images use `next/image` with explicit dimensions; fonts are self-hosted WOFF2 with `font-display: swap` and size-adjusted fallbacks.
7. **PERF-7** A budget may only be raised through a pull request to this node with a reason and a review date.

<!-- section:rationale -->
## Rationale

Budgets per group reflect different devices: parties on phones over mobile data need small bundles, while secretariat staff on managed desktops trade bundle size for dense tooling. RUM is the source of truth; lab checks catch regressions before release.

<!-- section:tooling -->
## Tooling and configuration

- `size-limit` on `.next` build output per route (CI)
- Lighthouse CI against preview deployments for one representative route per group, with the PERF-5 profiles
- RUM via `web-vitals` library reported to the regional collector ([[OBS-frontend-real-user-monitoring]])
- `@next/bundle-analyzer` report attached to PRs that change dependencies
- Load tests for TTFB at expected peak ([[TST-performance-and-load-testing]])

<!-- section:enforcement -->
## Enforcement

| Rule | Where | Fails when |
|---|---|---|
| PERF-3, PERF-4 | PR CI (required) | any route over budget by more than 2% |
| PERF-1, PERF-2 (lab proxy) | Lighthouse CI on preview | LCP or TBT over lab thresholds for the profile; warning, not blocking, until baselines are stable |
| PERF-1, PERF-2 (field) | RUM dashboards and alerts | p75 over budget for 3 consecutive days in any region opens a ticket for the owning team |
| PERF-6 | ESLint `@next/next/no-img-element` and font lint | build |

<!-- section:exceptions -->
## Exceptions

Over-budget routes may be allow-listed for up to 60 days in `perf-budgets.json` with owner and ticket; the CI job lists expired allow-list entries as failures.

<!-- section:questions -->
## Open questions

- [ ] Confirm device profiles with RUM data after the first pilot tenant (owner: frontend lead)
- [ ] Should budgets differ for Azure deployments? Proposed: no (owner: DevOps)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Bundle and RSC budgets block merges; lab Web Vitals warn on previews; field budgets raise tickets from RUM alerts; image and font rules are lint-enforced.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

RUM collection follows [[OBS-frontend-real-user-monitoring]]: route templates only, no URLs with IDs, no case content, regional collectors.

<!-- check:measurement -->
### Adoption measurement

RUM dashboards per group and region show p75 against budget; a weekly report lists routes over budget and allow-list entries nearing expiry.

<!-- check:ownership -->
### Ownership and change

Owner: frontend lead; each route group's owning team is accountable for its budgets.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "web",
    "publisher": "Google (web.dev)",
    "title": "Web Vitals",
    "url": "https://web.dev/articles/vitals"
  }
]
```

<!-- end -->
