# Template: Operational report / analytics (`report`)

Generated from `report.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a report or dashboard by the questions it answers and the exact definition of every metric, so numbers mean the same thing to everyone who reads them.

**Depth:** 2–6 pages. Every metric needs a formula, grain, source and owner; that table is the core of the spec. Visual layout can be a rough sketch. Treat the metric definitions as a data contract with the teams that produce the source data.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `audience` Audience and questions (level 1)

Who uses it, how often, and the 3–7 questions it must answer. Each question should map to a metric or view.

Illustrative example (not a requirement):

> **Audience:** tenant secretariat heads (weekly), Nomology ops (daily).
> 1. Which cases are ageing beyond target at each stage?
> 2. Which clients have overdue invoices, and how much?
> 3. Is ageing getting better or worse month on month?

### `metrics` Metric definitions (level 1)

Name, formula, grain, filters, source, owner. Be exact about inclusions and exclusions.

Illustrative example (not a requirement):

> | Metric | Formula | Grain | Source |
> |---|---|---|---|
> | Case age (days) | today − stage_entered_at (calendar days) | case × stage | cases, case_stage_history |
> | Ageing breach | case age > target for stage (Decision "Stage targets") | case | as above + rules |
> | Unpaid invoice amount | Σ invoice.total − Σ payments where status ≠ void | client × currency | invoices, payments |

### `dimensions` Dimensions and filters (level 1)

How users slice the data, and default filters.

Illustrative example (not a requirement):

> Tenant (fixed for tenant users), client, case type, stage, rule set, neutral, date range (default: open cases).

### `layout` Layout and views (level 2)

Sketch of views, charts and tables; drill-downs.

Illustrative example (not a requirement):

> - KPI row: open cases, cases in breach, unpaid amount
> - Bar: cases by stage, stacked by ageing band (0–30, 31–60, 61–90, 90+)
> - Table: breaching cases with case ref, stage, days, assigned secretary → drill into case

### `freshness` Freshness and delivery (level 1)

Refresh frequency, latency, delivery channels (dashboard, scheduled email, export).

Illustrative example (not a requirement):

> Refreshed hourly from the reporting replica. Weekly PDF email to secretariat heads every Monday 08:00 tenant local time. CSV export for users with "reports.export".

### `lineage` Data sources and lineage (level 2)

Source tables / events per metric, transformations, and the producing team.

Illustrative example (not a requirement):

> `case_stage_history` (produced by Cases context via `case.stage_changed` events) → dbt model `fct_case_ageing` → dashboard. Invoices from Billing via nightly snapshot.

### `quality` Data quality and reconciliation (level 2)

Checks that run before figures are trusted.

Illustrative example (not a requirement):

> - Every open case has exactly one current stage
> - Unpaid totals reconcile to Billing ledger within 0.1%
> - Freshness alert if the source is more than 2 h stale

### `access` Access and privacy (level 2)

Who sees what; masking of personal data; export controls.

Illustrative example (not a requirement):

> Tenant users see only their tenant (enforced by reporting role + RLS). Party names masked for users without case access. Exports logged in the audit trail.

### `performance` Performance and cost (level 3)

Volumes, query budget, caching.

Illustrative example (not a requirement):

> Expected 50k cases per tenant at year 3; dashboard queries < 2 s p95 from pre-aggregated tables.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Business days or calendar days for ageing? (SEBI ODR timelines use calendar days)

## Checks

### `tenancy` Tenant isolation

**Question:** How is it guaranteed, in the data layer and not only in the UI, that a tenant user can only ever see figures built from their own tenant's rows?

- Is the report scoped to one tenant, to Nomology staff across tenants, or both? If both, are they separate reports or one report with a role switch?
- Do the reporting tables, materialised views and pre-aggregates carry tenant_id, and is forced Row-Level Security enabled on them, or does isolation rely on a WHERE clause in the query?
- Which database role does the reporting service connect as, and is it barred from BYPASSRLS and from owning the tables (owners skip RLS unless FORCE is set)?
- How is the tenant set for each query through PgBouncer transaction pooling, and what happens if it is not set (must return zero rows, not all rows)?
- Are caches, scheduled-email jobs and CSV exports keyed by tenant, so a cached or emailed result cannot be served to another tenant?
- For cross-tenant benchmarks (for example 'your ageing versus platform median'), what is the minimum number of tenants in the comparison group, so one tenant's figures cannot be inferred?
- Is there an automated test that logs in as tenant A and asserts that no tenant B row appears in any metric, drill-down or export?

**Good answer:** Names the scope (tenant, platform, or both as separate artefacts), the reporting DB role, and the RLS policies on every reporting table, including pre-aggregated ones. States the fail-closed behaviour when no tenant is set, cache and export keys that include tenant_id, and a minimum group size (for example at least 5 tenants) for any cross-tenant comparison. Points to a cross-tenant leakage test that runs in CI.

**Red flags:**

- Tenant filtering is done only in the dashboard filter or front-end query parameters
- Pre-aggregated or materialised tables have no tenant_id or no RLS
- Reporting connects as the table owner or a role with BYPASSRLS
- Cross-tenant benchmarks with no minimum group size

### `residency` Residency and cross-region figures

**Question:** Where is the report's data computed and stored, and does any platform-wide view move tenant data out of its home region (India, Singapore, US)?

- Is there one reporting store per region, and does each report run inside the region of the tenants it covers?
- For platform-wide views (for example Nomology MIS across all regions), is only aggregated, non-personal data moved to a central location, and at what grain?
- Could an aggregated row still identify a person or a case (for example a count of 1 at case × neutral grain)? What suppression rule applies to small counts?
- Which tenant contracts or regulators (for example SEBI-recognised ODR institutions, HKIAC) restrict even aggregated data leaving the region, and how is that recorded?
- Do scheduled emails and exports get generated and sent from the tenant's region, including the email provider's region?
- Where the client requires Azure, is the reporting store on Azure in the same region, and does any pipeline cross clouds?

**Good answer:** States the region of computation and storage for every dataset in the report, and lists exactly what (if anything) leaves a region: which columns, at what grain, with what small-count suppression (for example counts below 5 shown as '<5'). Cites the residency commitment in the tenant agreement and confirms that email and export delivery stay in region.

**Red flags:**

- A single global warehouse fed with row-level data from all regions
- Platform-wide MIS built by querying each region's operational tables directly from one region
- No small-count suppression on aggregated data that leaves a region

### `definitions` Metric semantics

**Question:** Is every metric defined precisely enough that two analysts computing it independently from the same data would get the same number?

- For each metric: what is counted, at what grain, and which records are explicitly excluded (test cases, withdrawn cases, void invoices, soft-deleted rows)?
- Calendar days or business days, and whose holiday calendar? Which time zone defines a day or a month (tenant local, UTC, or the region's)?
- How are multi-currency amounts shown: per currency, or converted? If converted, which rate source and on which date?
- Is the metric a snapshot (as at a time) or a flow (during a period)? For snapshots, at what time of day is the snapshot taken?
- How are late-arriving or corrected source records handled: are past periods restated, and is a restatement visible to the reader?
- Where a metric uses a business rule (for example stage targets from a Decision table), which version of the rule applies to historic periods?
- Is every metric's definition stored in one place (a metric layer or dbt model) and reused, rather than re-written in each chart?

**Good answer:** Each metric row gives formula, grain, inclusions, exclusions, time zone, calendar, currency treatment, snapshot or flow, and restatement policy, plus a worked numeric example. Definitions live in a single governed layer and the dashboard references them by name. Rule-dependent metrics name the decision and the version policy.

**Red flags:**

- 'Case age' or 'active case' used without saying what starts and stops the clock
- Amounts in different currencies summed without conversion rules
- Time zone or month boundary not stated for a multi-region tenant base
- The same metric computed differently in two charts

### `lineage` Lineage and data contracts

**Question:** Can every metric be traced to the exact source tables or events that produce it, under a data contract that the producing team has agreed to?

- For each metric, which source tables or business events (for example case.stage_changed) feed it, and which transformation (dbt model or SQL view) produces it?
- Which team owns each source, and is there a written data contract covering schema, meaning of fields, freshness and who to contact?
- How are breaking source changes (a renamed column, a new case status) caught before they silently change a number: schema tests in CI, contract checks, or a change notice period?
- Does lineage cover data from other systems (accounting system, payment gateway, Temporal workflow history), and how are those extracts versioned?
- If a new state is added to a case state machine, how does the report learn whether to count it?
- Can an auditor or tenant ask 'where did this number come from' and get the list of contributing records for a given cell?

**Good answer:** Gives a lineage diagram or table per metric from source to dashboard, names the owner of each source, and links a data contract (for example in Open Data Contract Standard format) with schema, semantics, freshness SLA and change policy. Describes the automated check that fails the build or blocks publication when a contracted source changes shape or adds an unmapped enum value.

**Red flags:**

- Metrics read directly from operational tables with no owner or contract
- Enum or status changes in source systems are not detected and fall into 'other' or vanish
- No way to drill from a figure to the underlying records

### `quality` Data quality and reconciliation

**Question:** What automated checks must pass before the figures are shown or sent, and what does the reader see when a check fails?

- Which freshness limit applies to each source, and is it monitored with an alert (for example source older than 2 hours)?
- Which completeness and validity tests run: not-null keys, unique IDs, exactly one current stage per open case, referential integrity to tenant and client?
- Which totals are reconciled against a system of record (for example unpaid totals against the Billing ledger, case counts against the operational DB), and with what tolerance?
- When a test fails, is the dashboard marked stale or blocked, and are scheduled emails held back rather than sent with wrong numbers?
- Is the 'data as of' timestamp shown on every view and export?
- Who is alerted on failure, and how quickly must they respond?

**Good answer:** Lists each test with its threshold, schedule and owner, including at least one reconciliation to a system of record with a numeric tolerance (for example within 0.1% or exact for money). States the user-visible behaviour on failure (stale banner, held email) and shows a 'data as of' timestamp everywhere. Tests run in the pipeline (for example dbt tests and source freshness) and alerts route to a named team.

**Red flags:**

- No reconciliation for any money figure
- Scheduled reports are sent even when the pipeline failed
- No visible freshness timestamp

### `security` Access, privacy and export

**Question:** Who may view, drill into, export and schedule this report, and how is personal data minimised and protected in every one of those paths?

- Which permissions (for example reports.view, reports.export, reports.schedule) gate each action, and which roles hold them by default?
- Does the report need personal data at all (party names, emails, neutral names)? If yes, why, and is it masked for users without case-level access?
- Can drill-down reach records the user could not open in the case screen? Is report access checked against the same case access rules?
- Are exports and scheduled emails logged in the audit trail with who, what filter, how many rows and when?
- Are scheduled email recipients limited to users in the tenant, and is access re-checked at send time (a user who left last week should not still receive it)?
- How does the report honour data-principal rights under DPDP and GDPR: if a person's data is erased or the case retention period ends, does it disappear from reporting tables and caches?
- For neutral or transcriber performance reports, has the impact on those individuals been assessed, and who may see individual-level scores?

**Good answer:** A table of actions against permissions and roles, a field-level list of personal data with the reason and masking rule for each, and confirmation that drill-down reuses case access checks. Exports and schedules are audit-logged with row counts, recipients are re-validated at send time, and reporting tables follow the same erasure and retention jobs as source data.

**Red flags:**

- Export available to every viewer by default
- Personal data included 'in case it is useful'
- Scheduled emails to external or personal addresses with no re-check
- Reporting copies kept after source records are erased

### `performance` Performance and cost

**Question:** Will the report stay fast and affordable at the expected year-3 volume without loading the operational database?

- What are the expected row counts at launch and year 3 (cases, stage history rows, events, invoices) per tenant and in total per region?
- What latency target applies (for example dashboard p95 under 2 seconds) and is it measured?
- Do queries run against a read replica or reporting store rather than the primary database used by case workflows?
- Which pre-aggregations or materialised views exist, how long does a refresh take, and does a refresh lock or slow anything?
- Is there a limit on export size and date range, and are large exports run as background jobs (BullMQ) rather than in the web request?
- What is the monthly compute and storage cost estimate, and who gets told if it doubles?

**Good answer:** Gives volume estimates, a measured or benchmarked p95 latency at year-3 volume, and the query path (replica or reporting store, pre-aggregates and their refresh time). Large exports are asynchronous with size limits, and there is a cost estimate with an owner and a budget alert.

**Red flags:**

- Dashboard queries hit the primary operational database
- No volume estimate or load test
- Unbounded exports run inside a web request

### `accessibility` Accessible presentation

**Question:** Can every figure in the report be read and understood by users with disabilities, meeting WCAG 2.2 AA in the dashboard, emails and exports?

- Is every chart backed by an accessible data table or text summary that a screen reader can read?
- Does meaning ever depend on colour alone (for example red for breach)? Is there a second cue such as a label, pattern or icon?
- Do chart colours and text meet contrast ratios (4.5:1 for text, 3:1 for graphical objects)?
- Can filters, drill-downs and tooltips be operated by keyboard alone, with visible focus?
- Are PDF and email versions tagged and readable, and is CSV the accessible alternative for large tables?
- Are numbers, dates and currencies formatted for the tenant's locale, including Indian digit grouping where expected?

**Good answer:** Confirms each chart has a data-table or text alternative, no colour-only encoding, measured contrast values, and keyboard-operable filters and drill-downs. States how emailed and exported versions are made accessible and how locale formatting is chosen.

**Red flags:**

- Charts rendered as images with no alternative
- Status shown by colour only
- Tooltips that only appear on mouse hover

