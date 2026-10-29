# Template: Observability signal (`observability`)

Generated from `observability.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies the telemetry the platform emits for one concern (business events, performance, usage, security, AI) and the objectives and alerts built on it, so signals are named consistently and acted on.

**Depth:** 2–6 pages. The event / metric catalogue is the core: names, attributes, emitters. Follow OpenTelemetry naming conventions. SLOs need an error budget policy to be meaningful. Personal data in telemetry must be addressed explicitly.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose (level 1)

Which questions these signals answer and who uses them.

Illustrative example (not a requirement):

> Business events let operations and reporting see what is happening in cases in near real time (filings, appointments, awards) and feed the Reporting area without querying operational tables.

### `catalogue` Event catalogue (level 1)

Event name, when emitted, emitter, attributes (with types), PII flag.

Illustrative example (not a requirement):

> | Event | Emitted when | Emitter | Attributes |
> |---|---|---|---|
> | `case.filed` | Filing accepted | Cases | tenant.id, case.id, case.type, case.rule_set |
> | `case.stage_changed` | Any stage transition | Cases | tenant.id, case.id, stage.from, stage.to |
> | `hearing.scheduled` | Hearing created | Hearings | tenant.id, case.id, hearing.id, hearing.mode |
> No party names, emails or document content in any event.

### `metrics` Metrics (level 1)

Metric name, instrument type, unit, labels, source.

Illustrative example (not a requirement):

> | Metric | Type | Unit | Labels |
> |---|---|---|---|
> | `cases.open` | gauge | {case} | tenant.id, stage |
> | `case.stage.duration` | histogram | d | tenant.id, stage |
> | `notifications.sent` | counter | {message} | tenant.id, channel, status |

### `sli` SLIs and SLOs (level 2)

For user-facing journeys: SLI definition, SLO target, window, and error budget policy.

Illustrative example (not a requirement):

> | Journey | SLI | SLO |
> |---|---|---|
> | File a document | % of filing submissions completing in < 5 s and without error | 99.5% over 28 days |
> | Case page load | % of loads < 2 s | 99% over 28 days |
> Error budget policy: when a budget is exhausted, feature work on that journey pauses until reliability work restores it.

### `alerts` Alerts (level 1)

Condition, severity, routing, runbook link.

Illustrative example (not a requirement):

> | Alert | Condition | Severity | Route |
> |---|---|---|---|
> | Filing SLO burn | 2% budget in 1 h | Page | On-call engineer |
> | Event pipeline lag | > 10 min | Ticket | Platform team |

### `dashboards` Dashboards (level 2)

Dashboards, audiences and key panels.

Illustrative example (not a requirement):

> "Case operations" (ops): events per hour by type and tenant; "Journeys" (engineering): SLO status per journey.

### `pipeline` Collection pipeline (level 2)

How signals get from code to storage (SDKs, collectors, exporters), per region.

Illustrative example (not a requirement):

> OpenTelemetry SDK in apps and workers → OTel Collector per region → regional log / metric / trace stores. Business events also written to the outbox → reporting warehouse.

### `retention` Retention and privacy (level 2)

Retention per signal type, PII handling, access.

Illustrative example (not a requirement):

> Traces 7 days, logs 30 days, metrics 13 months, business events per case retention. Log scrubber drops email, phone and document text patterns.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Do tenants get their own operational dashboards?

## Checks

### `tenancy` Tenant and region tagging

**Question:** Does every signal carry tenant and region identifiers so problems can be traced to a tenant, while no tenant can ever see another tenant's telemetry?

- Is tenant.id set once as a resource or context attribute (for example via OpenTelemetry Baggage or a span processor) so every span, log and metric from a request or job inherits it, rather than each developer adding it by hand?
- How is tenant.id carried into background work: BullMQ job payloads, Temporal workflow and activity context, and outbox events?
- Does every signal also carry deployment region (for example cloud.region) and environment, so India, Singapore and US data are never mixed in one view by mistake?
- Is tenant.id a high-cardinality label on metrics? If so, which metrics carry it and what is the series budget per metric?
- If tenants are given their own dashboards or status pages, how is access restricted to their tenant (separate data source, enforced label filter, or a different tool)?
- What happens to signals emitted where tenant is unknown (login, webhooks before tenant lookup): tagged as 'unknown' or dropped?

**Good answer:** Describes the single mechanism that sets tenant.id and region for all signals, including how it crosses into BullMQ and Temporal, and shows a sample span and log line with the attributes. Lists which metrics are labelled by tenant and the series limit, and explains how any tenant-facing view is isolated by the backend, not only by a dashboard filter.

**Red flags:**

- Tenant tagging left to individual log statements
- Background jobs and workflows emit signals with no tenant
- Tenant-facing dashboards built on the shared backend with only a front-end filter

### `naming` Naming and schema

**Question:** Are event, metric and attribute names consistent with OpenTelemetry semantic conventions and recorded in a catalogue that code is checked against?

- Do names follow OpenTelemetry rules: lowercase, dot-separated namespaces, standard attributes reused (http.*, db.*, messaging.*) before inventing new ones?
- Does each metric state instrument type (counter, up-down counter, gauge, histogram) and a UCUM unit (s, By, {case})?
- Where does the catalogue live (for example a YAML registry in the monorepo), and does CI fail when code emits a name or attribute not in it?
- How is a breaking change handled (renaming an event, changing an attribute type): versioned name, dual emission for a period, or a deprecation notice to Reporting?
- For business events consumed by Reporting, who owns the schema and is it treated as a data contract with that team?
- Which attributes have bounded value sets (stage, channel, status), and which are unbounded and therefore not allowed as metric labels (case.id, user.id, URL with IDs)?

**Good answer:** Points to a machine-readable catalogue with type, unit, attributes and owner for every signal, and a CI check that enforces it. Shows that standard semantic conventions are reused and that unbounded attributes are confined to spans and logs. Gives the change policy for renaming or removing a signal, including notice to downstream consumers.

**Red flags:**

- Free-text log messages used as the only record of business events
- case.id or user.id used as a metric label
- No unit on histograms
- Event schema changes made without telling Reporting

### `privacy` Personal and confidential data

**Question:** How is it guaranteed that personal data and confidential case content never reach logs, traces, metrics or events, and what catches it when a developer gets it wrong?

- Which attributes are explicitly allowed (an allow-list), and is everything else dropped, rather than relying on a block-list?
- Is there redaction both in the SDK (before data leaves the process) and in the regional OTel Collector (for example an attribute or redaction processor), and what patterns does it catch (email, phone, Aadhaar, PAN, passport, card numbers)?
- Are database statements in traces captured with parameters stripped? Are HTTP request and response bodies, headers (Authorization, cookies) and query strings excluded?
- Can document content, hearing transcripts or AI prompts and completions ever enter telemetry? If AI token counts are recorded, is the prompt text excluded?
- Are user IDs pseudonymous (internal UUIDs, not emails), and is the mapping held only in the application database?
- Is there a periodic scan of stored logs for personal data patterns, and what is the procedure if some is found (purge, incident review, DPDP and GDPR assessment)?
- Do third-party observability vendors receive any data, and if so, under which data processing agreement and in which region?

**Good answer:** Gives the attribute allow-list, the two layers of redaction with their rules, and explicit exclusions for SQL parameters, bodies, auth headers and AI prompt text. Describes a scheduled scan of stored logs with a named owner and a purge-and-assess procedure, and confirms that any vendor processes data in the same region under a signed DPA.

**Red flags:**

- Request bodies or full SQL with parameters captured in traces
- Redaction only by regex at the end of the pipeline
- Emails or party names used as identifiers in logs
- Telemetry sent to a vendor outside the tenant's region

### `slo` SLIs, SLOs and error budgets

**Question:** Does each user-facing journey covered here have an SLI measured from the user's point of view, an SLO target with a window, and an error budget policy that someone has agreed to follow?

- Is each SLI written as good events divided by valid events, with the exact measurement point (load balancer, server span, browser real-user monitoring)?
- Which requests are excluded from 'valid' (health checks, bots, client errors caused by bad input), and is that justified?
- Are long-running journeys covered by a meaningful SLI, for example a Temporal workflow step completing within its deadline, or a notification delivered within N minutes, not only HTTP latency?
- Are SLOs set per region, and is any tenant-specific SLO (from a contract or HKIAC/SEBI requirement) tracked separately?
- How do contractual SLAs in client agreements relate to internal SLOs (the SLO should be stricter)?
- Who signed the error budget policy (engineering and product), and what concretely happens when the budget is exhausted?
- Is there enough traffic for the SLO to be statistically meaningful, especially for small tenants or low-volume journeys?

**Good answer:** A table per journey with SLI formula, measurement point, exclusions, SLO target and rolling window, and region. Contractual SLAs are mapped to stricter internal SLOs. The error budget policy names who approved it and the concrete actions at exhaustion (for example freeze on non-reliability releases for that journey), and low-traffic journeys use longer windows or synthetic checks.

**Red flags:**

- SLOs only on CPU, memory or uptime of a container
- No error budget policy, or one nobody agreed to
- Internal SLO equal to or looser than the contractual SLA
- Async workflows (filing processing, notifications) have no SLI at all

### `actionability` Alerts and response

**Question:** Does every alert indicate user impact or imminent impact, reach a named owner through the right channel, and link to a runbook that tells them what to do?

- Are paging alerts based on SLO burn rate (for example multi-window, multi-burn-rate) rather than raw thresholds such as CPU above 80%?
- For each alert: severity, owning team, route (page, ticket, chat), business hours or 24x7, and the runbook link?
- Does each runbook give first diagnostic steps, safe mitigations (roll back, pause a BullMQ queue, pause a Temporal task queue), and escalation contacts?
- Who is on call for each region given time zones (India, Singapore, US), and is there a backup?
- Which alerts could indicate a personal data breach, and do they start the incident process that supports DPDP Board and data-principal notification and GDPR 72-hour regulator notification?
- What is the target number of pages per on-call shift, and how often are noisy or never-firing alerts reviewed and removed?
- Is there an alert for the monitoring pipeline itself (collector down, no data received from a region)?

**Good answer:** An alert table where every row has condition, severity, owner, route and a working runbook link, with paging limited to SLO burn-rate and security conditions. Names the on-call rota per region, the escalation path into the security incident process with its regulatory clocks, an alert for missing telemetry, and a monthly review of alert noise.

**Red flags:**

- Alerts with no owner or runbook
- Paging on resource thresholds with no link to user impact
- No alert when telemetry stops arriving
- Security-relevant alerts routed only to a chat channel

### `propagation` End-to-end correlation

**Question:** Can one user action be followed from the browser through Next.js, the database, BullMQ jobs, Temporal workflows and outbound calls as a single connected trace?

- Is W3C Trace Context propagated across every hop: browser to Next.js server, server to BullMQ job payload, job to Temporal (via the OpenTelemetry interceptor), Temporal activity to external APIs?
- How are long-running Temporal workflows that run for days represented: one trace per activity linked to the workflow, rather than a single multi-day trace?
- Do logs include trace_id and span_id so a log line can be opened from the trace and vice versa?
- Are database spans visible through PgBouncer, and do they show which tenant context was set for the transaction?
- What sampling is used (head, tail, per route), and are errors and slow requests always kept?
- Are business events tagged with the trace ID of the action that produced them, so Reporting anomalies can be traced back?

**Good answer:** Shows an example trace for a key journey crossing all components, names the propagation mechanism at each boundary, and explains how multi-day workflows are linked rather than kept as one trace. States the sampling policy with guaranteed retention of errors and slow traces, and confirms trace IDs appear in logs and business events.

**Red flags:**

- Traces stop at the web server and miss jobs and workflows
- Logs without trace IDs
- Uniform low sampling that drops most error traces

### `retention` Retention and residency

**Question:** How long is each signal type kept, where is it stored, and does that satisfy both investigation needs and data minimisation in each region?

- What is the retention for traces, application logs, security and audit logs, metrics and business events, and what is the reason for each period?
- Are all signals stored in the same region as the tenant (India, Singapore, US), including any vendor backend, backups and cold archive?
- Is security and audit log retention long enough for ISO 27001 and SOC 2 evidence and for incident investigation (often 12 months or more), and is it held separately from short-lived debug logs?
- How do business events align with case retention: are they deleted or anonymised when the case retention period ends?
- When a tenant leaves, how is their telemetry deleted or anonymised, and is that evidenced?
- Who can read raw logs, is that access logged, and is it reviewed?

**Good answer:** A table of signal type against retention, storage location per region and reason, with security logs kept longer and separately from debug logs. Business-event deletion is tied to the case retention schedule, tenant offboarding includes telemetry, and raw-log access is restricted and reviewed.

**Red flags:**

- One retention period for everything, chosen by vendor default
- Logs from all regions in one central store
- No deletion of telemetry when a tenant leaves

### `security` Security and audit signals

**Question:** Which security-relevant events does this concern emit, are they tamper-resistant, and do they reach the security monitoring that ISO 27001 and SOC 2 require?

- Which events are emitted: sign-in success and failure, MFA changes, role and permission changes, cross-tenant access attempts blocked by RLS, admin impersonation, bulk exports, API key use?
- Are security events kept separate from application audit trails that users see, and is it clear which is the system of record for each?
- Are security logs write-once or otherwise protected from change by the engineers whose actions they record?
- Do they feed a SIEM or detection rules, and which detections exist (for example many failed logins, export volume spikes, access outside normal region)?
- Are clocks synchronised across services so event order can be trusted in an investigation?
- Which ISO 27001:2022 Annex A controls (logging, monitoring activities, clock synchronisation) does this signal provide evidence for?

**Good answer:** Lists the security events with attributes and severity, the protected store they go to, and the detection rules built on them, each with an owner. Explains how integrity is protected (write-once storage or a separate account with restricted access), confirms time synchronisation, and maps the signals to the specific controls they evidence.

**Red flags:**

- Security events mixed into debug logs with short retention
- Engineers can edit or delete security logs
- Failed RLS or authorisation checks are not logged

### `cost` Volume and cost

**Question:** What volume of telemetry will this concern produce, what will it cost per region, and what stops it growing out of control?

- What are the estimated events per second, log GB per day and active metric series at launch and at year 3?
- What is the series budget for each metric, and is there an alert when cardinality exceeds it?
- What are the sampling rates and log levels in production, and who may change them?
- Is debug logging time-limited when turned on for an investigation?
- What is the monthly cost estimate per region, and who owns the budget?

**Good answer:** Gives volume estimates, per-metric series budgets with a cardinality alert, production sampling and log levels with a change process, and a monthly cost estimate per region with a named budget owner.

**Red flags:**

- No volume estimate
- Debug logging left on in production
- No limit on metric label values

