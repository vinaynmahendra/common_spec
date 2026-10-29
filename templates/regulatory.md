# Template: Regulatory / aggregator submission (`regulatory`)

Generated from `regulatory.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies an obligation to report to a regulator, ministry or aggregator: what the rule requires, which entity owes it, exactly which data goes where and when, and how its accuracy is proven.

**Depth:** 3–10 pages. The field mapping table must cover every field in the prescribed format; a missing field is a compliance defect. Cite the exact circular / rule and its version. Each new regulator or aggregator format is its own node. Apply the accuracy, completeness, timeliness and traceability principles used in BCBS 239 regulatory reporting.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `obligation` Obligation and source (level 1)

The regulation, circular or contract that creates the obligation, with exact reference, version and clause. Quote the key requirement.

Illustrative example (not a requirement):

> **Source:** SEBI circular on Online Resolution of Disputes in the Indian Securities Market dated 31 July 2023 (updated 4 August 2023) as amended in December 2023, or the consolidated master circular that replaces them (cite the version in force and the paragraph), plus the MII's operating guidelines for empanelled ODR institutions.
> **Requirement (summarised):** ODR institutions report case status and outcomes to the MII in the MII's prescribed format (illustrative: Annexure X) so the MII can monitor timelines and report onward to SEBI.

### `applicability` Applicability (level 1)

Which legal entity owes it, for which tenants / case types, from when.

Illustrative example (not a requirement):

> | Item | Value |
> |---|---|
> | Obliged entity | The ODR institution (tenant); platform prepares on its behalf |
> | Platform entity | NTPL (India) as technology provider |
> | In scope | All SEBI ODR cases allocated via the ODR portal |
> | Effective from | Tenant go-live on the SEBI ODR rule set |

### `recipient` Recipient and channel (level 1)

Who receives it and how (portal upload, API, email, SFTP), with credentials ownership.

Illustrative example (not a requirement):

> NSE (as MII) via its ODR portal upload; credentials held by the tenant's compliance officer, never stored by the platform in plain text.

### `frequency` Frequency and deadlines (level 1)

Periodic schedule and event-driven triggers; cut-off times and time zone.

Illustrative example (not a requirement):

> | Type | When | Cut-off |
> |---|---|---|
> | Periodic status | Monthly | 7th of following month, 18:00 IST (illustrative) |
> | Event | Award issued | Within the MII-prescribed window |

### `fields` Field mapping (level 1)

Every field in the prescribed format → platform source → transformation → validation. This is the core of the spec.

Illustrative example (not a requirement):

> | # | Format field | Source | Transform | Validation |
> |---|---|---|---|---|
> | 1 | Complaint ID | case.external_refs['sebi_odr'] | as is | Required, unique |
> | 2 | Date of reference | case.referred_at | DD-MM-YYYY, IST | ≤ report end date |
> | 3 | Conciliator appointed on | appointment(type=conciliator).accepted_at | DD-MM-YYYY | ≥ date of reference |
> | 4 | Outcome | case.stage | Settled→"Resolved in conciliation", Awarded→"Arbitral award" | Enum |
> | 5 | Claim amount (₹) | Σ claims in INR | 2 decimals | ≥ 0 |

### `format` Format and template (level 2)

File type, layout, naming convention, sample file attached or linked.

Illustrative example (not a requirement):

> XLSX with one sheet "Annexure X", header row as prescribed, filename `{ODRI-code}_{YYYYMM}_status.xlsx`. Template stored as a Report template in Configuration (versioned per aggregator).

### `validation` Validation and reconciliation (level 1)

Checks before submission: completeness counts, cross-field rules, reconciliation totals.

Illustrative example (not a requirement):

> - Count of cases in file = count of SEBI ODR cases active in period (completeness)
> - No case breaches 21-day conciliation or 30-day arbitration timeline without a recorded reason
> - Totals reconcile to the operational report for the same period

### `workflow` Preparation, approval and submission (level 2)

Who prepares, reviews, approves and submits; maker-checker; what is recorded.

Illustrative example (not a requirement):

> Generated automatically on the 1st → compliance officer reviews exceptions → approves (maker-checker) → downloads and uploads to portal → records acknowledgement number on the submission record.

### `evidence` Evidence and retention (level 2)

What is kept to prove the submission was made, accurate and on time.

Illustrative example (not a requirement):

> Retain: generated file, validation report, approver and timestamp, acknowledgement, any resubmission and its reason. Retention: 8 years (confirm with tenant policy).

### `changes` Change management (level 2)

How format changes from the regulator / aggregator are detected and rolled out.

Illustrative example (not a requirement):

> Format versions stored as template versions. Compliance monitors MII circulars; a change creates a new version node linked to this one, with parallel run for one cycle.

### `risk` Non-compliance risk (level 3)

Consequences of late or inaccurate submission, and escalation path.

Illustrative example (not a requirement):

> Late or incorrect reporting may lead to MII action against the ODR institution, including suspension from allocation. Escalation: tenant compliance officer → Nomology account lead.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Obtain the current MII format and field definitions from NSE for each tenant
> - [ ] Confirm whether nil returns are required for months with no cases

## Checks

### `completeness` Completeness

**Question:** Does the submission include every case, entity or transaction that the rule puts in scope for the period, and how is that proven before sending?

- What is the independent control total for the population (for example cases allocated by the MII ODR portal for the period, or cases tagged with the SEBI ODR rule set), and is it compared against the file row count?
- How are cases that changed status, were transferred, withdrawn, merged or reopened during the period handled?
- Are cases created late, back-dated or corrected after the period end picked up, and in which period?
- Are nil returns required when there are no cases, and is that handled automatically?
- Is any record excluded by a filter (test tenants, sandbox cases, deleted records), and is every exclusion listed with its reason?
- If one tenant operates in two regions or on Azure, are all deployments included?

**Good answer:** Defines the in-scope population with an independent count source, shows a reconciliation of that count to the file with every difference explained, and lists exclusion rules with reasons. The completeness check is automated and its result is stored with the submission.

**Red flags:**

- Population defined only by the same query that builds the report
- No reconciliation to an independent count
- Silent exclusions such as soft-deleted or reopened cases

### `accuracy` Accuracy and reconciliation

**Question:** Is every value in the submission checked against source records and against related reports before it is sent?

- Which totals are reconciled (count of cases by outcome, total claim amount, number of timeline breaches) and against which independent source (operational report, billing, the MII's own records)?
- What tolerance is allowed for each reconciliation, and who signs off differences?
- How are dates and times converted (UTC storage to IST or SGT reporting, cut-off at midnight local time), and is that tested around period boundaries?
- How are currency amounts, rounding and enum mappings (case stage to the prescribed outcome text) validated?
- Are cross-field rules enforced (appointment date not before reference date, award date within the prescribed timeline or a reason recorded)?
- Are reconciliation results stored with the submission so an auditor can see what was checked?

**Good answer:** Lists each reconciliation with its independent source and tolerance, describes automated cross-field and format validations run before the maker can submit, and keeps the validation report with the submission. Date, time zone and currency rules are stated explicitly and covered by tests at period boundaries.

**Red flags:**

- No reconciliation, or reconciliation only against the report's own query
- Time zone handling not defined
- Mapped values (outcomes, statuses) not validated against the prescribed list

### `lineage` Traceability

**Question:** Can every submitted figure be traced back to the source records, rule version and code version that produced it, and reproduced later?

- For each field, can you show the source table and column, the transformation and the record IDs that contributed to the value?
- Is the data used for the submission frozen (snapshot or point-in-time query) so it can be regenerated exactly, even after later case updates?
- Are the report template version, field mapping version and application release recorded with each submission?
- If an auditor or the MII queries one figure months later, how long would it take to show the supporting records?
- Are manual adjustments allowed, and if so, is each one recorded with who made it, why and the before and after values?

**Good answer:** Each submission stores a data snapshot or reproducible query with the template, mapping and code versions, and a drill-down from each reported figure to the contributing case records. Manual overrides are logged with reason, maker and checker.

**Red flags:**

- Report cannot be regenerated as it was on submission day
- Spreadsheet edits after export with no record
- Mapping or template version not recorded

### `segregation` Tenant and entity segregation

**Question:** Is each submission built only from the data of the tenant and legal entity that owes it, and kept within that tenant's region?

- Does report generation run under the tenant's own context so forced Row-Level Security applies, rather than with a reporting role that bypasses RLS?
- If a platform-level report aggregates several tenants (for example Nomology's own statutory reporting), who approves that and how is per-tenant data protected?
- Which legal entity is the reporter (the tenant institution, NTPL, TAPL or the US entity), and does the file identify the right one?
- Is the report generated and stored in the tenant's pinned region, and does it leave the region only to reach the recipient?
- Could a misconfigured rule set or tag pull another tenant's cases into this report, and what test would catch it?

**Good answer:** Report jobs run in Temporal or BullMQ with the tenant set per transaction so RLS applies, any cross-tenant report has its own approval and access rule, and the reporting entity is mapped explicitly per tenant. Generation and storage stay in the tenant's region, and a cross-tenant leak test is part of the report's test suite.

**Red flags:**

- Reports generated with a superuser or RLS-bypassing database role
- Reporting entity inferred rather than configured
- Report files stored in a single global bucket

### `timeliness` Timeliness

**Question:** Is every deadline tracked from its legal trigger, with alerts early enough to fix problems before the deadline is breached?

- For each periodic and event-driven submission, what starts the clock, what is the cut-off and in which time zone, and how are public holidays in India or Singapore handled?
- For event-driven obligations (award issued, breach detected, suspicious transaction identified), does the platform record the trigger time automatically?
- At what points before the deadline do alerts fire (for example T-5 days, T-2 days, T-4 hours), and to whom, including a backup?
- Is generation scheduled early enough to leave time for review, correction and portal problems?
- What happens if the recipient's portal is down at the deadline, and is evidence of the attempt kept?
- Is on-time performance reported to the tenant and to management (submissions on time, late, missed)?

**Good answer:** Gives a deadline calendar per obligation with trigger, cut-off and time zone, implemented as scheduled Temporal workflows with escalating alerts to a named owner and backup. Records the trigger time, submission time and acknowledgement time so on-time performance can be measured and shown.

**Red flags:**

- Deadlines tracked in someone's calendar only
- No alert before the deadline, only after a miss
- Event-driven trigger time not captured

### `security` Access, approval and transmission

**Question:** Who can prepare, approve and submit, how are their actions separated, and how are portal credentials and the file protected in transit and at rest?

- Is maker-checker enforced by the system so the preparer cannot approve their own submission?
- Who holds credentials for the regulator or aggregator portal (for example the tenant's compliance officer for the NSE ODR portal), and does the platform store them? If so, where (secrets manager per region) and who can use them?
- If submission is by API or SFTP, how are keys or certificates issued, rotated and revoked?
- Is the file encrypted at rest and in transit, and is personal data in it limited to what the format requires?
- Are prepare, approve, download and submit actions all recorded in the audit trail?
- For confidential reports (for example suspicious transaction reports to FIU-IND, where the obliged entity is a reporting entity under PMLA), is access restricted so the subject of the report cannot learn of it?

**Good answer:** Defines roles for preparer, approver and submitter, enforced in the platform with self-approval blocked, and explains credential custody, including that portal passwords are never stored in plain text. File handling uses encryption in transit and at rest and data minimisation, and every step is audited.

**Red flags:**

- One person can prepare, approve and submit
- Portal credentials shared by email or stored in plain text
- Report files downloadable by anyone with tenant admin access

### `resubmission` Corrections and resubmissions

**Question:** How are errors found after submission corrected, resubmitted and disclosed, and how is the history kept?

- Does the recipient accept corrections, replacements or only new submissions, and within what window?
- Who decides that a resubmission is needed, and must the recipient be told about the error separately?
- Is the original submission kept unchanged alongside the corrected one, with the reason and the differences recorded?
- If a source-data fix affects past periods, how are all affected submissions identified?
- How are rejections or queries from the recipient captured, tracked and closed?

**Good answer:** Describes a versioned submission record where each correction is a new version linked to the original, with reason, differences, approver and recipient acknowledgement. A source-data change triggers a check for affected past submissions, and rejections are tracked to closure.

**Red flags:**

- Original submission overwritten by the correction
- No process to find past submissions affected by a data fix
- Recipient rejections handled by email with no record

### `retention` Evidence retention

**Question:** Is everything needed to prove the submission was complete, accurate, approved and on time kept for the required period, in the right region, and protected from change?

- Is the full set kept: generated file, data snapshot, validation and reconciliation reports, approvals, submission time, acknowledgement, recipient queries and resubmissions?
- What retention period applies under each source (the regulation or circular, PMLA record-keeping for AML reports, tenant policy, client contract), and which one wins?
- Is the evidence stored in write-once or append-only storage in the tenant's region?
- How does retention interact with DPDP or GDPR erasure requests for personal data inside the reports?
- Who can retrieve the evidence, and how quickly, if a regulator or auditor asks?

**Good answer:** Lists the evidence pack per submission, states the retention period with its legal source, and stores it in tamper-evident storage in-region. Explains how a legal duty to keep records overrides an erasure request and how that is recorded.

**Red flags:**

- Acknowledgements kept only in someone's email
- No retention period or legal basis stated
- Evidence deleted by routine data-erasure jobs

