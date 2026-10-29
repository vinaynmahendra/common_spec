---
id: "OBS-foundations"
title: "Foundations"
parent: "OBS"
order: 1
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "OpenTelemetry SDKs and the shared telemetry package: registry, resource and tenant attributes, W3C trace propagation through Next.js, Prisma, BullMQ and Temporal, structured logs, redaction, sampling and the regional collector pipeline"
links: []
rev: 2
syncHash: "b84acbb8e87ba516"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.1 Foundations

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> OpenTelemetry SDKs and the shared telemetry package: registry, resource and tenant attributes, W3C trace propagation through Next.js, Prisma, BullMQ and Temporal, structured logs, redaction, sampling and the regional collector pipeline

<!-- section:purpose -->
## Purpose

Defines the common machinery every other observability node relies on: how code emits traces, metrics, logs and events, how each signal is tagged with tenant and region, how context travels across processes, how personal data is kept out, and how signals reach regional storage. Used by every engineer writing code (through `@nomology/telemetry`) and by on-call engineers investigating incidents.

Questions these signals answer: *Which tenant and region is affected? Where in the request path is the time or error? Which deploy changed it? Can I follow this filing from the browser into the Temporal workflow that processes it?*

<!-- section:catalogue -->
## Event catalogue

**Resource attributes** (set once per process)

| Attribute | Type | Example | Notes |
|---|---|---|---|
| `service.name` | string | `web`, `worker-jobs`, `worker-temporal-documents` | |
| `service.version` | string | git SHA | Correlate with deploys |
| `deployment.environment.name` | string | `prod`, `staging` | |
| `cloud.provider`, `cloud.region` | string | `aws`, `ap-south-1` | |
| `nomo.residency_region` | enum | `in`, `sg`, `us` | Platform residency region, independent of cloud region names |

**Context attributes** (set by middleware / tenant extension, copied to every span, log and event by a processor)

| Attribute | Type | PII | Notes |
|---|---|---|---|
| `nomo.tenant.id` | UUID string, or `none` (platform-level) / `unknown` (before resolution) | No (pseudonymous ID) | From the same context as `set_config('app.tenant_id', …)` ([[MT-prisma-client-extension-wraps]]) |
| `nomo.product` | enum `cord`, `teres`, `hkiac-cmp` | No | |
| `nomo.persona` | enum `party`, `counsel`, `neutral`, `secretariat`, `transcriber`, `tenant-admin`, `platform-admin`, `system` | No | From route group ([[APP-route-groups-per-persona]]) |
| `nomo.user.id` | UUID | Pseudonymous | Never email or name; mapping only in the app database |
| `nomo.request.id` | string | No | Also returned as `X-Request-Id` to clients for support |

**Foundation events** (log records with `event.name` [R3])

| Event | When | Emitter | Key attributes |
|---|---|---|---|
| `nomo.telemetry.dropped_attribute` | An attribute not in the allow-list was dropped | SDK processor (sampled 1/100) | `attribute.key` (name only, never value) |
| `nomo.app.started` | Process start | All services | `service.version`, config hash |
| `nomo.deploy.completed` | Deploy finished | CI | `service.version`, region |

**The registry**: `packages/telemetry/registry/*.yaml` declares every event, metric and custom attribute: name, type, unit, allowed values, PII flag, `metricLabel` allowed or not, owner, stability. Generated TypeScript constants are the only way code refers to names. CI fails if code emits a name or attribute not in the registry; renames require a new name plus dual emission for one release and a note to Reporting. (OpenTelemetry Weaver can be used to validate and generate from the registry — to be evaluated.)

<!-- section:metrics -->
## Metrics

Foundation-level metrics only; domain metrics are in the child nodes.

| Metric | Instrument | Unit | Labels | Source |
|---|---|---|---|---|
| `http.server.request.duration` | Histogram | `s` | `http.route` (template), `http.request.method`, `http.response.status_code`, `nomo.persona` | OTel HTTP instrumentation in Next.js |
| `nomo.telemetry.untagged` | Counter | `{signal}` | `signal.type`, `service.name` | Collector processor counting signals with no tenant attribute |
| `nomo.telemetry.dropped_attributes` | Counter | `{attribute}` | `service.name` | SDK processor |
| `otelcol_exporter_send_failed_*`, `otelcol_receiver_refused_*` | Counter | | `exporter`, `receiver` | Collector self-telemetry |
| `nodejs.eventloop.delay` | Histogram | `s` | `service.name` | Runtime instrumentation |

Tenant ID is **not** a label on these metrics. The registry lists the few metrics allowed to carry `nomo.tenant.id` (for example per-tenant request counts in [[OBS-usage]]) with a series budget each.

<!-- section:sli -->
## SLIs and SLOs

Foundations has no user-facing journey of its own. It defines the shared SLI rules used by children:

- SLI = good events / valid events, measured at the server span of the `web` service (or the ALB for availability when the app is down).
- Valid excludes health checks, synthetic traffic tagged `nomo.synthetic=true`, and 4xx caused by client input (except 429 from our own rate limits, which count as bad).
- SLOs are per region; tenant-specific SLOs only where a contract demands it.
- Window: 28 days rolling. Error budget policy in [[OBS-alerting]].

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route | Runbook |
|---|---|---|---|
| No telemetry received from a region's collector for 10 min | Page | Platform on-call for that region | `runbooks/otel-collector.md` |
| Collector exporter failures > 5% for 15 min | Page | Platform on-call | same |
| `nomo.telemetry.untagged` > 0 for 1 h in production | Ticket | Owning team of `service.name` | `runbooks/telemetry-tagging.md` |
| Weekly PII scan finds a match | Ticket, plus privacy review | Observability lead + DPO | `runbooks/telemetry-pii-found.md` |
| Metric series count > 80% of budget | Ticket | Owner of the metric | |

<!-- section:dashboards -->
## Dashboards

- **Telemetry health** (per region): received / exported / dropped per signal, untagged counter, collector CPU and queue length. Audience: platform on-call.
- **Service overview** (per region and service): RED metrics (rate, errors, duration) per route, recent deploys as annotations. Audience: engineering teams.
- **Trace explorer** with tenant and persona filters. Audience: engineers investigating support tickets (`X-Request-Id` lookup).

<!-- section:pipeline -->
## Collection pipeline

```
Next.js (instrumentation.ts → NodeSDK)           Browser (see OBS-frontend-real-user-monitoring)
Workers (NodeSDK, BullMQ telemetry, Temporal         │
  OpenTelemetry interceptors)                         │ HTTPS via ALB path /_t/
       │ OTLP/gRPC 4317, mTLS                          ▼
       ▼
Regional collector — tier 1 (load-balancing exporter by trace ID)
       ▼
Regional collector — tier 2: memory_limiter → attributes/transform (allow-list) → redaction
       → resourcedetection (ECS / Azure) → tail_sampling → batch
       ▼
Regional stores (metrics, traces, logs) ── security events split to the write-once security store
```

**Propagation (W3C Trace Context [R2])**

| Hop | Mechanism |
|---|---|
| Browser → Next.js | `traceparent` header on fetch / tRPC calls to same origin only |
| Next.js → Postgres | `@prisma/instrumentation` spans; the tenant extension adds `nomo.tenant.id` to the transaction span (no SQL parameters) |
| Next.js → BullMQ job | BullMQ telemetry option (`bullmq-otel`) injects context into the job and links the worker span [R4]; tenant ID travels in job data, re-established by the worker before any database call |
| Next.js / worker → Temporal | `@temporalio/interceptors-opentelemetry` on client, workflow and activity; tenant ID carried in a Temporal header by our tenant interceptor ([[WF-separation-of-concerns-temporal]]) |
| Long-running workflows | One trace per workflow task / activity, **linked** to the starting trace; no multi-day traces |
| Outbound to third parties | `traceparent` sent only to providers that are documented as accepting it; **W3C Baggage is stripped on all outbound calls** to external hosts so tenant IDs never leak |

**Logs**: Pino JSON to stdout is not used for shipping; logs go through the OTel logs bridge with `trace_id`, `span_id`, severity and registered attributes. Message strings are templates (`"Filing {filingId} rejected: {reason}"`) with values as attributes so redaction applies.

**Sampling**: SDK parent-based always-on (so tail sampling sees whole traces); collector tail sampling keeps 100% of traces with errors, 100% slower than 2 s, 100% with `nomo.synthetic=true` for 1 day, and 10% of the rest (proposed). Logs are not sampled at `INFO` and above; `DEBUG` is off in production and can be enabled per service for at most 2 hours through a feature flag ([[PKG-feature-flags]]).

**Redaction (defence in depth)**: (1) SDK span / log processor applies the registry allow-list and drops HTTP bodies, headers except a safe list, query strings and `db.query.text` parameters; (2) collector `redaction` / `transform` processors drop non-allow-listed keys and mask patterns for email, phone, Aadhaar, PAN, passport and card numbers in any remaining string values; following OpenTelemetry guidance on sensitive data [R5].

<!-- section:retention -->
## Retention and privacy

| Signal | Hot retention (proposed) | Archive | Reason |
|---|---|---|---|
| Traces | 14 days | None | Investigation of recent issues |
| Application logs | 30 days searchable | 180 days in-region archive (India: required in India [R6]; same rule applied to all regions for simplicity) | CERT-In log retention; incident investigation |
| Metrics | 13 months (downsampled after 30 days) | None | Year-on-year capacity and SLO trends |
| Security events | See [[OBS-security-events#retention]] | | |
| Business events | See [[OBS-business-events#retention]] | | |

- All stores are in the tenant's region; no cross-region export.
- Access: engineers through SSO with read-only roles; raw log access is logged and reviewed quarterly ([[SEC-access-reviews]]).
- Tenant offboarding: telemetry is not deleted per tenant because it holds no personal data and ages out within 180 days; this must be stated in the offboarding record ([[MT-tenant-lifecycle]]). Assumption to be confirmed by the DPO.

<!-- section:questions -->
## Open questions

- [ ] Confirm the `nomo.*` prefix for custom attributes and whether `nomo.user.id` is acceptable as a pseudonymous identifier under DPDP and GDPR (it is still personal data in law if linkable).
- [ ] Tail-sampling rate (10% proposed) and whether two-tier collectors are needed at launch volume.
- [ ] Does any third-party provider (SMS, WhatsApp, video, AI) accept `traceparent`, and should we send it?
- [ ] Telemetry backend per region (shared open question with [[OBS]]).
- [ ] Is 180-day archive needed outside India, or should Singapore and US keep 30 days to minimise data?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

`nomo.tenant.id` is set once from the request's tenant context (the same source used for RLS) by a span / log processor, so developers never add it by hand. BullMQ jobs carry it in job data and Temporal carries it in a header via our interceptor, and workers re-establish context before any work. Every signal also carries `cloud.region`, `nomo.residency_region` and `deployment.environment.name`. Signals before tenant resolution carry `unknown`; platform-level work carries `none`. Tenant ID is a metric label only on registry-approved metrics with a series budget. Tenants never get direct access to telemetry tools.

<!-- check:naming -->
### Naming and schema

Names follow OTel rules (lowercase, dot-separated, standard `http.*`, `db.*`, `messaging.*` reused first [R1]); custom names use the `nomo.` prefix. The YAML registry in `packages/telemetry/registry/` declares type, unit (UCUM), allowed values and whether an attribute may be a metric label; CI fails on unregistered names; renames use dual emission for one release.

<!-- check:privacy -->
### Personal and confidential data

Allow-list, not block-list: only registry attributes survive, in the SDK and again in the collector. HTTP bodies, most headers, query strings and SQL parameters are never captured. Pattern masking (email, phone, Aadhaar, PAN, passport, card) runs in the collector as a second line [R5]. User IDs are pseudonymous UUIDs. Log messages are templates with values as attributes so redaction applies. A weekly scan of stored logs and spans looks for personal data patterns and triggers a privacy review if anything is found.

<!-- check:actionability -->
### Alerts and response

The foundation alerts cover the monitoring pipeline itself (no data from a region, exporter failures), which is a gap many platforms miss; each has a runbook and routes to the region's platform on-call.

<!-- check:propagation -->
### End-to-end correlation

W3C Trace Context [R2] across browser → Next.js → Prisma → BullMQ (via BullMQ telemetry [R4]) → Temporal (OTel interceptors) → outbound calls. Long workflows use one trace per task / activity linked to the starting trace. Logs carry `trace_id` / `span_id`. Baggage is stripped on outbound calls to external hosts. Errors and slow traces are always kept by tail sampling.

<!-- check:retention -->
### Retention and residency

Traces 14 days, logs 30 days hot plus 180 days in-region archive (meets CERT-In for India [R6]), metrics 13 months, all in-region. Access through read-only SSO roles, logged and reviewed quarterly.

<!-- check:cost -->
### Volume and cost

Main levers are tail sampling (10% of normal traces), no `DEBUG` in production except time-limited, series budgets per metric in the registry, and short trace retention. Volumes and cost per region will be estimated after the Phase 3 load test.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenTelemetry (CNCF)",
    "excerpt": "Names are lowercase, dot-separated namespaces; custom attributes should use a company-specific prefix to avoid clashes with future semantic conventions.",
    "id": "R1",
    "ident": "Semantic conventions",
    "kind": "standard",
    "title": "Attribute naming",
    "url": "https://opentelemetry.io/docs/specs/semconv/general/attribute-naming/"
  },
  {
    "body": "W3C",
    "excerpt": "Defines the traceparent and tracestate headers for propagating trace context.",
    "id": "R2",
    "ident": "Trace Context",
    "kind": "standard",
    "title": "W3C Trace Context",
    "url": "https://www.w3.org/TR/trace-context/"
  },
  {
    "body": "OpenTelemetry (CNCF)",
    "excerpt": "Events are log records with a required event name identifying the event class.",
    "id": "R3",
    "ident": "Semantic conventions",
    "kind": "standard",
    "title": "Semantic conventions for events",
    "url": "https://opentelemetry.io/docs/specs/semconv/general/events/"
  },
  {
    "excerpt": "BullMQ supports OpenTelemetry tracing through its telemetry option (bullmq-otel), propagating context from producer to worker.",
    "id": "R4",
    "kind": "vendor",
    "title": "BullMQ telemetry: traces",
    "url": "https://docs.bullmq.io/guide/telemetry/traces",
    "vendor": "Taskforce.sh (BullMQ)"
  },
  {
    "body": "OpenTelemetry (CNCF)",
    "excerpt": "Guidance on minimising, filtering and redacting sensitive data in SDKs and in the Collector.",
    "id": "R5",
    "ident": "OpenTelemetry documentation",
    "kind": "standard",
    "title": "Handling sensitive data",
    "url": "https://opentelemetry.io/docs/security/handling-sensitive-data/"
  },
  {
    "excerpt": "Reportable cyber incidents to be reported to CERT-In within 6 hours of noticing; logs of ICT systems to be maintained securely for a rolling period of 180 days within Indian jurisdiction; clocks to be synchronised to NTP servers of NIC/NPL or traceable sources.",
    "id": "R6",
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
