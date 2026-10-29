---
id: "OBS-alerting"
title: "Alerting"
parent: "OBS"
order: 7
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Alert rules as code, severities, burn-rate paging, on-call routing per region, error budget policy, incident and breach hand-off, and alert hygiene"
links: []
rev: 2
syncHash: "42e1698c97423892"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.7 Alerting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Alert rules as code, severities, burn-rate paging, on-call routing per region, error budget policy, incident and breach hand-off, and alert hygiene

<!-- section:purpose -->
## Purpose

Turns signals into action: decides what wakes someone up, who that is in each region and time zone, what they do first, and how an alert becomes an incident (including a possible personal data breach). Consumes SLOs and alert conditions defined in the other observability nodes and infrastructure nodes, and tenant-configurable thresholds from [[PKG-thresholds-and-alert]].

Two kinds of alert are kept apart:

| Kind | Example | Goes to |
|---|---|---|
| **Engineering alerts** | API SLO burn, Temporal backlog, Redis memory | On-call engineers |
| **Business notifications** | Filing deadline in 48 h, transcript turnaround breached | Tenant users through [[PKG-notifications]], configured in [[PKG-thresholds-and-alert]] — never pages

<!-- section:catalogue -->
## Event catalogue

| Event | When | Emitter | Attributes |
|---|---|---|---|
| `nomo.alert.fired` / `nomo.alert.resolved` | Alert state change | Alert manager | `alert.name`, `severity`, `cloud.region`, `owner.team`, `slo.name` (if any) |
| `nomo.incident.opened` | Alert escalated to an incident | Incident tool | `incident.severity`, `possible_breach` (bool) |
| `nomo.alert.acknowledged` | On-call acknowledges | On-call tool | `alert.name`, `ack.delay_s` |

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels |
|---|---|---|---|
| `nomo.alert.pages` | Counter | `{page}` | `cloud.region`, `owner.team`, `alert.name` |
| `nomo.alert.time_to_ack` | Histogram | `s` | `severity`, `cloud.region` |
| `nomo.slo.budget_remaining` | Gauge | `1` (ratio) | `slo.name`, `cloud.region` |

<!-- section:sli -->
## SLIs and SLOs

**Error budget policy (proposed, to be signed by the CTO and the product lead per product)** [R1]

1. Each SLO has a 28-day budget per region (for 99.9% availability: about 40 minutes).
2. If a region has spent > 50% of a budget in the first half of the window, the owning team prioritises reliability work in the next sprint.
3. If the budget is exhausted, releases to that region are limited to fixes and security patches until the 28-day SLI is back above target; exceptions need CTO approval.
4. Any single incident consuming > 20% of a budget gets a written post-incident review within 5 business days.
5. The policy is reviewed every quarter.

Meta-SLI for alerting itself: pages acknowledged within 5 minutes (24×7 Sev1/Sev2) for 95% of pages.

<!-- section:alerts -->
## Alerts

**Severities**

| Severity | Meaning | Response | Route |
|---|---|---|---|
| Sev1 | Region or product down, or suspected data breach / cross-tenant exposure | Page 24×7, ack 5 min, incident commander, client communication | Region primary on-call + security on-call |
| Sev2 | Major journey degraded (fast SLO burn), pipeline stopped | Page 24×7, ack 15 min | Region primary on-call |
| Sev3 | Slow burn, capacity warning, single-tenant issue | Ticket, next business day in region | Owning team queue |
| Sev4 | Information, hygiene | Chat / report | — |

**Paging rules (examples; full list in each node)**

- SLO fast burn: 14.4× over 1 h with 5-minute confirmation, and 6× over 6 h with 30-minute confirmation → Sev2; slow burn 1× over 3 days → Sev3 ticket [R2].
- Imminent impact without an SLO: Redis queue memory > 75% ([[INF-redis]]), Postgres free storage < 15% ([[INF-database]]), PgBouncer waits ([[INF-monitor-pool-usage-wait-times]]), certificate expiry < 3 days.
- Monitoring blind spots: no telemetry from a region 10 min ([[OBS-foundations#alerts]]); security log ingestion stopped ([[OBS-security-events#alerts]]).
- Possible breach signals: cross-tenant access blocked for a signed-in user, inference residency mismatch, bulk export spike, PII found in telemetry → Sev1 with `possible_breach = true`, which starts the assessment in [[SEC-security-incident-response-and]]. That process owns the regulatory clocks (CERT-In 6 hours in India [R3], DPDP Board, GDPR, PDPC) and client contractual notice periods.

**Rule format**: every rule in `observability/alerts/<area>/*.yaml` must declare `name`, `severity`, `owner.team`, `regions`, `runbook` URL, `query`, `for`, and `slo` (if burn-rate). CI lints rules and rejects any without owner or runbook; rules are deployed per region by Terraform.

<!-- section:dashboards -->
## Dashboards

- **On-call home** per region: firing alerts, SLO budgets, recent deploys, open incidents.
- **Alert hygiene** (monthly review): pages per shift, alerts never fired in 90 days, alerts auto-resolved within 5 minutes (noise), time to ack.

<!-- section:pipeline -->
## Collection pipeline

- Regional metrics / logs stores evaluate rules in-region; alert notifications contain **no personal data** (alert name, region, service, counts, links) so they may pass through a global on-call tool.
- Notification routes: on-call tool (paging, escalation, schedules) → phone / push; Sev3 → issue tracker; Sev4 → team chat.
- Incident tool opens a channel and timeline; incidents with `possible_breach` also notify the DPO and security lead.
- Status page updates for client-visible incidents ([[OBS-uptime-synthetic-monitoring]]).

**On-call model (proposed)**: follow-the-sun is not possible with a Bangalore-centred team at launch. Proposed: primary on-call from the Bangalore team 24×7 per week with a secondary; US region nights (India daytime) are covered naturally; Singapore overlaps India hours. Target ≤ 2 pages per shift; compensatory time off after night pages.

<!-- section:retention -->
## Retention and privacy

Alert and incident history 2 years (post-incident reviews, ISO 27001 evidence of incident management). Notifications contain no personal data.

<!-- section:questions -->
## Open questions

- [ ] On-call and incident tool choice; it receives only alert metadata — confirm that a global SaaS tool is acceptable to legal.
- [ ] On-call model: one 24×7 rotation from Bangalore, or regional rotations once US / Singapore staff exist?
- [ ] Who signs the error budget policy for CORD, TERES and HKIAC CMP?
- [ ] Do client contracts require incident notifications within set times (for example HKIAC or SEBI-regulated tenants)? To be confirmed by legal and account owners.
- [ ] Should tenant admins be able to subscribe to platform incident notifications for their region?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Alerts are per region; single-tenant problems are Sev3 tickets routed with the tenant ID; tenant-configurable thresholds are business notifications to the tenant, not engineering pages.

<!-- check:privacy -->
### Personal and confidential data

Alert notifications carry only metadata (alert name, region, service, counts, links), never tenant personal data or case content, so they can go through an on-call tool without moving personal data out of region.

<!-- check:slo -->
### SLIs, SLOs and error budgets

The error budget policy defines concrete consequences (sprint priority at 50% spend, release limits at exhaustion, post-incident review for > 20% budget incidents) based on the SRE workbook example [R1]; signatories are an open question.

<!-- check:actionability -->
### Alerts and response

Paging alerts are SLO burn rates (multiwindow, multi-burn-rate [R2]) or named imminent-impact conditions; each rule must declare severity, owning team, regions and a runbook, enforced by CI lint. Runbooks start with safe mitigations (roll back, pause a BullMQ queue, scale a Temporal worker to zero). Breach-indicating alerts open a Sev1 with `possible_breach` and hand over to [[SEC-security-incident-response-and]], which owns the CERT-In 6-hour clock [R3] and the other regulatory and contractual clocks. Monitoring blind spots page. Hygiene is reviewed monthly with a target of ≤ 2 pages per shift.

<!-- check:security -->
### Security and audit signals

Security detections share the same routing with a separate security on-call; breach indicators always reach the security lead and DPO.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "An example policy stating what happens when a service exceeds its error budget.",
    "id": "R1",
    "kind": "web",
    "publisher": "Google",
    "title": "SRE Workbook: Example error budget policy",
    "url": "https://sre.google/workbook/error-budget-policy/"
  },
  {
    "excerpt": "Recommends multiwindow, multi-burn-rate alerts, e.g. page at 14.4x burn over 1 hour (with a 5-minute short window) and 6x over 6 hours (30-minute short window); ticket at 1x over 3 days.",
    "id": "R2",
    "kind": "web",
    "publisher": "Google",
    "title": "SRE Workbook: Alerting on SLOs",
    "url": "https://sre.google/workbook/alerting-on-slos/"
  },
  {
    "excerpt": "Reportable cyber incidents to be reported to CERT-In within 6 hours of noticing; logs of ICT systems to be maintained securely for a rolling period of 180 days within Indian jurisdiction; clocks to be synchronised to NTP servers of NIC/NPL or traceable sources.",
    "id": "R3",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and IT, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under sub-section (6) of section 70B of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  }
]
```

<!-- end -->
