---
id: "OBS-uptime-synthetic-monitoring"
title: "Uptime / synthetic monitoring"
parent: "OBS"
order: 8
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Synthetic checks per region and per persona journey using synthetic tenants, uptime SLOs per region and product, and a public status page with no tenant data"
links: []
rev: 3
syncHash: "2df0f22ab5da1cf6"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.8 Uptime / synthetic monitoring

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Synthetic checks per region and per persona journey using synthetic tenants, uptime SLOs per region and product, and a public status page with no tenant data

<!-- section:purpose -->
## Purpose

Proves from the outside that each region works for each persona, including at night when real traffic is low, and publishes that status to clients. Answers *can a party sign in and open their cases in Singapore right now? can a filing reach the Temporal pipeline in India? is the public API up in the US?*

Users: on-call (early detection), account managers and clients (status page), [[RPT-platform-performance]] (monthly uptime per region and product).

<!-- section:catalogue -->
## Event catalogue

**Synthetic journeys** — run against a dedicated synthetic tenant per region (`synthetic-in`, `synthetic-sg`, `synthetic-us`) with synthetic users and documents only; all traffic tagged `nomo.synthetic=true` and excluded from business events, usage and SLO "valid" counts.

| Check ID | Journey | Persona | Frequency | Steps (summary) |
|---|---|---|---|---|
| `syn.public.home` | Public sign-in page loads | Public | 1 min | GET sign-in page, check status 200 and CSP header |
| `syn.auth.signin` | Sign in with password + TOTP | Party | 5 min | Sign in, land on case list ([[APP-public-and-sign-in-surfaces]]) |
| `syn.party.case_list` | Open case list and a case | Party / counsel | 5 min | List, open synthetic case, timeline renders |
| `syn.party.upload` | Upload a 1-page PDF, wait for malware scan clean | Party | 15 min | Upload via signed URL, poll status until `clean` < 2 min |
| `syn.secretariat.queue` | Load secretariat queue with filters | Secretariat | 5 min | Queue renders < 3 s |
| `syn.neutral.workspace` | Open case file in neutral workspace | Neutral | 15 min | |
| `syn.hearing.preflight` | Hearing room pre-join: token issued, provider reachable | Party | 15 min | No media session started ([[INT-video-conferencing-for-hearings]]) |
| `syn.api.health` / `syn.api.cases_read` | Public API health and authenticated read with a synthetic API key | API client | 1 min / 5 min | [[INT-public-api-cases-and-parties]] |
| `syn.webhook.delivery` | Trigger a test event and receive it at a synthetic endpoint | API client | 15 min | [[APP-webhooks-outbound]] |
| `syn.temporal.ping` | Start `synthetic-ping` workflow on each task queue and await completion | System | 5 min | Completes < 30 s |
| `syn.jobs.ping` | Enqueue a BullMQ ping job per queue | System | 5 min | Processed < 60 s |

Event per run: `nomo.synthetic.check_completed` with `check.id`, `outcome`, `duration_s`, `failed_step`, `probe.location`, `cloud.region`.

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels |
|---|---|---|---|
| `nomo.synthetic.check.duration` | Histogram | `s` | `check.id`, `probe.location`, `cloud.region` |
| `nomo.synthetic.check.result` | Counter | `{run}` | `check.id`, `outcome`, `probe.location`, `cloud.region` |

<!-- section:sli -->
## SLIs and SLOs

**Uptime SLO (proposed), per region and product, monthly**

- SLI: minutes in which the core checks (`syn.auth.signin`, `syn.party.case_list`, `syn.api.health`) pass from at least one of two probe locations / all minutes, excluding announced maintenance windows.
- SLO: **99.9%** per calendar month per region (about 43 minutes of allowed downtime), reported per product (CORD, TERES).
- Client SLAs (if any) must be looser than this SLO; to be checked by account owners.

For low-traffic tenants and night hours, these checks are the main availability evidence, since real-user SLIs have too little data.

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route |
|---|---|---|
| Core check failing from both probe locations for 3 consecutive runs | Sev1 page | Region on-call; draft status page incident |
| Core check failing from one location only for 15 min | Sev3 ticket | Probe or network path issue |
| Non-core journey failing 3 runs in a row | Sev2 page (upload, Temporal, jobs) / Sev3 (others) | Owning team |
| Check duration > 3× baseline for 30 min | Sev3 | Owning team |
| Synthetic runner itself not reporting | Sev2 | Platform on-call |

<!-- section:dashboards -->
## Dashboards

- **Synthetic status** per region: matrix of checks × locations, last 24 h.
- **Monthly uptime** per region and product for client reports.

<!-- section:pipeline -->
## Collection pipeline

- **In-region probes**: scheduled ECS tasks (Playwright for browser journeys, plain HTTP / SDK for API, Temporal and BullMQ checks) in each region's private network for system checks, and from a second availability zone through the public endpoint for user journeys.
- **External probes**: a probe location outside our cloud account but in the same country where possible (for example a monitoring vendor's node), to detect DNS, CDN and certificate issues. Synthetic data only, so external probes do not move tenant personal data.
- Synthetic credentials (passwords, TOTP seeds, API keys) stored in Secrets Manager; synthetic users have no access outside the synthetic tenant.
- **Status page**: hosted outside our infrastructure so it stays up when a region is down; components per product per region (for example "CORD — India", "TERES — Singapore"). An automatic "investigating" notice is posted after 10 minutes of Sev1 synthetic failure; humans write all further updates. No tenant names or data on the page.

<!-- section:retention -->
## Retention and privacy

Check results 13 months (uptime reporting); Playwright traces and screenshots of failed runs 14 days (synthetic data only). Status page history kept by the vendor for at least 12 months.

<!-- section:questions -->
## Open questions

- [ ] Status page provider and domain; per-tenant private status pages needed for any client?
- [ ] Should uptime be published per region and product, or per product only?
- [ ] Is the 99.9% monthly uptime SLO consistent with existing client contracts (CORD, TERES, HKIAC CMP)?
- [ ] External probe vendor with nodes in India, Singapore and the US.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Checks run only against a synthetic tenant per region with synthetic users and data; all synthetic traffic is tagged and excluded from business events, usage and SLO valid counts. The status page shows products and regions, never tenants.

<!-- check:privacy -->
### Personal and confidential data

No real tenant or personal data is ever used; external probes see only synthetic data. Failed-run screenshots contain synthetic data only and are kept 14 days.

<!-- check:slo -->
### SLIs, SLOs and error budgets

Uptime SLI is the share of minutes in which core checks pass from at least one of two probe locations, excluding announced maintenance; SLO 99.9% per month per region and product. It complements real-user SLIs for low-traffic periods and tenants.

<!-- check:actionability -->
### Alerts and response

Paging requires failure from both probe locations for three runs, which avoids pages from a single probe's network issues; each check maps to an owning team. The status page notice is automatic only for the first "investigating" post.

<!-- check:cost -->
### Volume and cost

About 11 checks per region at 1–15 minute intervals; Playwright runs dominate cost. Browser journeys at 5–15 minute intervals keep it small.

<!-- end -->
