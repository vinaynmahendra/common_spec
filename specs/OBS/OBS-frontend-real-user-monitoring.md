---
id: "OBS-frontend-real-user-monitoring"
title: "Frontend real-user monitoring and error reporting"
parent: "OBS-performance"
order: 1
type: "feature"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Browser Web Vitals, client errors and CSP violation reports sent same-origin to the regional collector; route templates only, no case content, no third-party RUM scripts"
links: []
rev: 2
syncHash: "828122605c10db1d"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.3.1 Frontend real-user monitoring and error reporting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Browser Web Vitals, client errors and CSP violation reports sent same-origin to the regional collector; route templates only, no case content, no third-party RUM scripts

<!-- section:purpose -->
## Purpose

Measures what users actually experience in the browser: loading and interaction speed (Core Web Vitals), JavaScript errors, and Content Security Policy violations. Answers *is the party portal slow on mobile networks in India? did the last release break the secretariat console for Firefox users? is a CSP rule blocking the hearing room SDK?*

Feeds the budgets in [[APP-frontend-performance-budgets]], the CSP rollout in [[APP-security-headers-csp-cors]], error-boundary work in [[APP-error-boundaries-loading-and]], and [[RPT-platform-performance]].

<!-- section:catalogue -->
## Event catalogue

All events sent from the browser to the same-origin path `/_t/v1/` (routed by the ALB to the regional collector's OTLP/HTTP receiver, behind WAF).

| Event | When | Attributes (type) | PII |
|---|---|---|---|
| `nomo.rum.web_vital` | Each Core Web Vital is final (on page hide) | `vital.name` (`LCP`, `INP`, `CLS`, `FCP`, `TTFB`), `vital.value` (double), `vital.rating` (`good`, `needs-improvement`, `poor`), `url.template` (route template, e.g. `/(counsel)/cases/[caseId]`), `navigation.type`, `device.class` (`mobile`, `tablet`, `desktop`), `network.effective_type`, `app.build_id`, `nomo.persona`, `nomo.tenant.id` | No |
| `nomo.rum.client_error` | Uncaught error, unhandled rejection, or React error boundary catch | `exception.type`, `exception.message` (redacted, max 200 chars), `exception.stacktrace` (minified frames, mapped server-side), `error.boundary` (segment name), `error.digest` (Next.js digest), `url.template`, `app.build_id`, `browser.name`, `browser.major_version` | Message may contain data → redacted |
| `nomo.rum.csp_violation` | Browser Reporting API CSP report | `csp.effective_directive`, `csp.blocked_origin` (origin only, no path), `csp.disposition` (`enforce`, `report`), `url.template` | No |
| `nomo.rum.hearing_media` | Hearing room media quality sample every 60 s ([[APP-hearing-room-in-browser]]) | `media.rtt_ms`, `media.packet_loss_pct`, `media.mode` (`full`, `low_bandwidth`), `nomo.tenant.id` | No |

**Never sent**: full URLs or query strings, page titles, DOM text, form values, file names, user names or emails, cookies, local storage, screenshots or session replays.

<!-- section:metrics -->
## Metrics

Computed in the collector from RUM events (browsers do not send metrics directly):

| Metric | Instrument | Unit | Labels |
|---|---|---|---|
| `nomo.rum.web_vital` | Histogram | `ms` (LCP, INP, FCP, TTFB) / `1` (CLS) | `vital.name`, `url.template`, `device.class`, `nomo.persona` |
| `nomo.rum.client_errors` | Counter | `{error}` | `url.template`, `exception.type`, `app.build_id` |
| `nomo.rum.csp_violations` | Counter | `{report}` | `csp.effective_directive`, `csp.blocked_origin`, `csp.disposition` |

<!-- section:sli -->
## SLIs and SLOs

| SLI | SLO (proposed) | Window |
|---|---|---|
| Page views with LCP ≤ 2.5 s / all page views, per route group | 75th percentile ≤ 2.5 s, i.e. ≥ 75% good | 28 days per region |
| Interactions with INP ≤ 200 ms / all | ≥ 75% good | 28 days |
| Page views with no client error / all | 99.5% | 28 days |

Thresholds follow the Core Web Vitals "good" boundaries; budgets per route group are owned by [[APP-frontend-performance-budgets]]. Pages with fewer than 500 views in the window are reported but not alerted (too little data).

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route | Runbook |
|---|---|---|---|
| Client error rate for a route group > 3× 7-day baseline within 1 h of a deploy | Page (business hours) | Owning frontend team | `runbooks/frontend-regression.md` (roll back first) |
| CSP violations in `enforce` mode from a new blocked origin | Ticket | Security + frontend | `runbooks/csp-violation.md` |
| LCP or INP SLO burn 1× over 3 days | Ticket | Owning team | |
| No RUM events from a region for 30 min during business hours | Ticket | Platform on-call | collector runbook |

<!-- section:dashboards -->
## Dashboards

- **Web Vitals by route group and persona** (per region), split by device class and network type.
- **Release health**: client errors per build ID for the first 24 h after each deploy.
- **CSP report view**: violations by directive and blocked origin; used during report-only → enforce rollout.

<!-- section:pipeline -->
## Collection pipeline

- Collection: the small `web-vitals` library plus a ~2 KB reporter in `@nomology/telemetry/browser` batches events and sends them with `navigator.sendBeacon` to `/_t/v1/rum` (same origin, so `connect-src 'self'` suffices and no third-party script is loaded).
- CSP: `Reporting-Endpoints: csp="/_t/v1/csp"` and `report-to csp` in the policy ([[APP-security-headers-csp-cors]]).
- Route templates: the reporter maps the current path to its App Router route template using the build's route manifest; unknown paths become `unknown`.
- Collector: rate limit per client IP and per tenant, schema validation, redaction of `exception.message`, source-map resolution of stack frames (source maps stored privately in-region, never served publicly), then the normal pipeline ([[OBS-foundations#pipeline]]).
- Sampling: Web Vitals 100% (small), client errors 100% with de-duplication by digest per session, hearing media samples 100% while in a hearing.
- Tenant and persona come from the server-rendered page context, not from user input; the endpoint rejects events whose tenant does not match the session.

<!-- section:retention -->
## Retention and privacy

RUM events and derived metrics: 30 days raw, 13 months aggregated. No personal data by design; IP addresses are used only for rate limiting in the collector and are not stored. Assumption: operational performance telemetry without personal data does not require consent under DPDP / GDPR / PDPA; to be confirmed by the DPO, and if consent is needed the reporter is disabled until consent is given ([[SEC-consent-and-notice-management]]).

<!-- section:questions -->
## Open questions

- [ ] DPO to confirm whether RUM needs consent or notice in each region.
- [ ] Is the hearing media quality sampling acceptable to institutions, or should it be opt-in per tenant?
- [ ] Do we need a separate RUM path for the sandboxed document viewer origin ([[APP-document-viewer-and-sandbox]])?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Tenant and persona come from server-rendered context; the collector endpoint rejects events whose tenant does not match the authenticated session, so one tenant cannot inject data attributed to another. Region is implicit: the browser sends to its own region's origin.

<!-- check:privacy -->
### Personal and confidential data

Only route templates, never real URLs or query strings; no DOM text, form values, titles or file names; no session replay or third-party RUM scripts. Error messages are redacted and truncated in the collector, and stack frames are mapped server-side from private source maps. IP addresses are used only for rate limiting and not stored.

<!-- check:slo -->
### SLIs, SLOs and error budgets

LCP and INP at the 75th percentile per route group and a client-error-free page-view ratio, per region over 28 days; low-traffic pages are excluded from alerting.

<!-- check:security -->
### Security and audit signals

CSP violation reports are the main security signal here and go to security as well as frontend teams; a new blocked origin in enforce mode may indicate an injection attempt or a compromised dependency. The endpoint sits behind WAF with rate limits.

<!-- check:cost -->
### Volume and cost

Events are small and few per page view; the main cost is storage of raw events for 30 days. Rate limits per IP and per tenant cap abuse.

<!-- end -->
