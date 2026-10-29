# Template: Domain module (`domain`)

Generated from `domain.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a business domain (a bounded context) in the language of the people who work in it, so the model, rules and lifecycle are agreed before code.

**Depth:** 6–15 pages; the deepest template. The glossary and lifecycle must be agreed with legal/operations, not just engineering. Each business rule should be one line with an ID; rules with tables move to a Decision node. Each multi-step process moves to a Workflow child.

**Default child template:** `workflow`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and vision (level 1)

Domain vision statement: what this context is responsible for and why it matters to the business.

Illustrative example (not a requirement):

> The **Cases** context owns a dispute from filing to closure: who the parties are, what stage it is in, what is due next, and what has been decided. It is the system of record that every other context refers to by case ID.

### `classification` Strategic classification (level 2)

Core / supporting / generic; business model role (revenue, compliance, engagement); evolution stage.

Illustrative example (not a requirement):

> **Core domain** — it is where institutions differ and where our product differentiates. Business role: revenue and compliance. Evolution: custom-built.

### `language` Ubiquitous language (level 1)

Glossary of terms as the business uses them, with precise definitions and synonyms to avoid.

Illustrative example (not a requirement):

> | Term | Meaning | Avoid |
> |---|---|---|
> | Case | One dispute with one reference number | Matter, ticket |
> | Party | Claimant or respondent (a person or organisation) | User |
> | Counsel | A representative acting for a party | Lawyer (too narrow) |
> | Reference | Formal referral of a dispute to the institution | Submission |

### `entities` Entities and aggregates (level 1)

Main entities, key attributes, relationships, aggregate boundaries, tenant ownership.

Illustrative example (not a requirement):

> ```
> Case (aggregate root) ─ tenant_id, ref, type, stage, claimValue, seat, rules
>  ├─ Party[]            ─ role, representedBy Counsel[]
>  ├─ Claim[]            ─ amount, currency, reliefSought
>  └─ Deadline[]         ─ due, kind, status
> References (by ID only): Tribunal (Neutrals), Hearing[] (Hearings), Document[] (Documents)
> ```

### `lifecycle` Lifecycle (state machine) (level 1)

States, transitions, who/what triggers each, guards. Diagram plus table.

Illustrative example (not a requirement):

> ```mermaid
> stateDiagram-v2
>   [*] --> Filed
>   Filed --> Registered: fee paid & checks pass
>   Registered --> Constituted: tribunal appointed
>   Constituted --> InProceedings
>   InProceedings --> Awarded
>   InProceedings --> Settled
>   Awarded --> Closed
>   Settled --> Closed
> ```
> | Transition | Trigger | Guard |
> |---|---|---|
> | Filed → Registered | Secretariat action | Registration fee paid; filing complete |
> | Registered → Constituted | All appointments accepted | Conflict check clear for every appointed neutral |

### `rules` Business rules (level 1)

Numbered one-line rules. Anything needing a table becomes a Decision child.

Illustrative example (not a requirement):

> - CASE-R1 A case has at least one claimant party and at least one respondent party
> - CASE-R2 Claim value in a non-tenant currency is converted at filing date for fee purposes
> - CASE-R3 Tribunal size depends on claim value and tenant rules → see Decision "Tribunal size"

### `commands` Commands and events (level 2)

Inbound commands and queries; outbound domain events with payload summary.

Illustrative example (not a requirement):

> | Inbound | Outbound event |
> |---|---|
> | FileCase | `case.filed` {caseId, tenantId, type, claimValue} |
> | RegisterCase | `case.registered` |
> | RecordAward | `case.awarded` {awardDocId} |

### `integrations` Relationships to other contexts (level 2)

Upstream/downstream contexts and the relationship pattern (customer–supplier, conformist, anti-corruption layer).

Illustrative example (not a requirement):

> - Neutrals (upstream, customer–supplier): Cases asks for appointment; Neutrals owns availability and conflicts
> - Billing (downstream): consumes `case.registered` to raise fee invoices
> - SEBI ODR portal (external, anti-corruption layer): maps portal complaint IDs to case refs

### `variations` Tenant and jurisdiction variations (level 2)

What differs by institution, rule set or jurisdiction, and how it is configured.

Illustrative example (not a requirement):

> | Variation | HKIAC | SEBI ODR |
> |---|---|---|
> | Stages | Full arbitration lifecycle | Conciliation (21 days) then arbitration (30 days) |
> | Tribunal size | Per rules / agreement | Sole arbitrator unless claim > INR 30 lakh |
> | Hearing | In-person or virtual | Document-only for claims ≤ INR 1 lakh |
> 
> *Illustrative figures: confirm every SEBI ODR value against the current SEBI ODR master circular before use.*

### `retention` Data retention and confidentiality (level 2)

Retention periods, deletion triggers, confidentiality tiers, legal holds.

Illustrative example (not a requirement):

> Case records retained 7 years after closure unless the tenant contract says otherwise; legal hold suspends deletion. Award documents retained permanently by tenants that publish anonymised awards.

### `metrics` Verification metrics (level 3)

How we will know the domain model works (business KPIs fed to Reporting).

Illustrative example (not a requirement):

> Median days Filed → Constituted per tenant; % of SEBI ODR cases resolved within timelines.

### `questions` Open questions and assumptions (level 3)

Checklist; mark assumptions explicitly.

Illustrative example (not a requirement):

> - [ ] Assumption: a case never moves between tenants. Confirm for HKIAC referrals from CORD.

## Checks

### `tenancy` Tenancy and residency

**Question:** For every entity in this context, who owns the row (a tenant, the platform, or both), which region it lives in, and how that is enforced in the database rather than in application code?

- List each table or aggregate with its owner: tenant-owned (carries tenant_id under forced RLS), platform-owned reference data (for example currencies, country codes, holiday calendars), or tenant-overridable reference data (platform default plus tenant override). Which pattern does each use?
- Can any aggregate ever reference an entity in another tenant (for example a neutral who sits on panels at two institutions, or a counsel acting in cases at both HKIAC and a CORD tenant)? If yes, is that modelled as two tenant-scoped records linked by a platform identity, and who can see the link?
- Is tenant_id part of every unique constraint and foreign key that should be tenant-scoped (for example case reference unique per tenant, not globally), so that a cross-tenant reference fails at the database?
- Which region does each tenant's data for this context live in, and can any entity be read or copied across regions (for example a global neutral directory, platform-wide analytics)? If so, what is copied, in what form, and under which transfer basis?
- Do background jobs, Temporal activities and reporting queries for this context run with the tenant set for the transaction via the Prisma extension, and which (if any) need a privileged cross-tenant role? Who approves that role?
- How are case reference numbers, invoice numbers and other sequences generated per tenant without gaps or collisions under PgBouncer transaction pooling?
- What happens to this context's data when a tenant is suspended, offboarded or exported? Which entities are deleted, anonymised or kept under legal retention?

**Good answer:** A table listing every entity with owner type, tenant_id presence, RLS policy name and home region, plus the cross-tenant identity rule (if any) and who approved it. Shared reference data is named explicitly with its update owner. The answer links to the Isolation node and names the automated test that proves a query in tenant A cannot read tenant B's rows for this context.

**Red flags:**

- "All tables have tenant_id" with no list of reference data or cross-tenant identities.
- Isolation relies on WHERE clauses in application code or a repository layer instead of forced RLS.
- A global entity (for example a shared neutral profile) that holds tenant-specific data such as fees, conflicts or case history.
- No statement of what happens to the data on tenant offboarding.

### `security` Access and confidentiality

**Question:** Is every command, query and field in this context covered by the permission matrix in a Security node, including case-level relationships (party, counsel, tribunal member) and not just tenant-level roles?

- Which permissions depend on the user's relationship to a specific record (for example counsel for the claimant can see claimant filings but not the tribunal's private deliberation notes), and how is that relationship stored and checked?
- Which fields need field-level protection (for example a neutral's fee rate, conflict disclosures, sealed or without-prejudice documents, KYC data), and who can see each?
- How does access change across the lifecycle, for example when a case closes, a neutral is challenged and removed, or counsel withdraws? Is access revoked on that transition, and is revocation tested?
- Are secretariat or platform support staff able to view case content? If yes, under what break-glass process, with what approval and how is it logged?
- Are information barriers needed, for example between two cases of the same tenant with overlapping parties, or for a neutral who has declared a conflict?
- Where are authorisation decisions enforced: in the domain service on every command and query, not only in the UI or API gateway?

**Good answer:** A link to the Security node's permission matrix with every command and query in the Commands section mapped to a permission, a list of relationship-based rules (for example "tribunal member of this case") with their data source, and a list of confidential fields with who may read them. Lifecycle-driven revocation and break-glass access are described and each has a named test.

**Red flags:**

- Permissions defined only by role (admin, user) with no record-level relationship rules for case participants.
- Access checks only in the UI or route handlers, not in the domain service.
- Support staff have standing read access to case documents.
- No rule for what a removed or recused neutral can still see.

### `audit` Audit and legal record

**Question:** Which state changes and reads in this context are legally significant, and what exactly is recorded for each so the record would stand up if challenged before a court or the institution's board?

- List every lifecycle transition and command that must be audited, for example filing, service of notice, tribunal appointment, challenge, procedural order issued, deadline extended, award issued, fee paid or waived.
- For each, what is captured: actor, acting-on-behalf-of (counsel for a party), tenant, case ID, before and after values, reason text, the rule or Decision version applied, and a trusted timestamp?
- Which reads must be audited (for example viewing a sealed document, exporting a case file, a support user's break-glass view)?
- How is the audit record made tamper-evident (append-only table, hash chain, write-once storage), and is it written in the same transaction as the state change so it cannot be lost?
- How long is the audit record kept compared to the case data itself, and does it survive case deletion or anonymisation?
- Can the audit trail reconstruct the case as it stood on any past date (for example "what did the tribunal see on the day of the order")?
- Who can read the audit trail inside the tenant, and can parties obtain an extract?

**Good answer:** A table of audited events with fields captured, retention and who can read them, linked to the shared Audit capability rather than a per-context log. The audit write happens in the same database transaction as the change (or through a transactional outbox), is append-only and tamper-evident, and stores the rule or configuration version used so a decision can be explained later.

**Red flags:**

- "We log everything" without a list of legally significant events and their fields.
- Audit written asynchronously with no outbox, so a crash can lose it.
- Audit rows can be updated or deleted by the application role.
- No record of which rule version or tenant configuration produced a decision.

### `privacy` Personal data

**Question:** What personal data does this context hold, about whom, for what purpose and on what legal basis, and how are data-subject rights handled where they conflict with the duty to keep a legal record?

- List the categories of personal data per entity (identity, contact, financial, KYC documents, health or other sensitive data inside pleadings or evidence) and whose data it is: parties, counsel, neutrals, witnesses, staff.
- Is the tenant (institution) the data controller / data fiduciary and Nomology the processor, or does Nomology act as controller for any data (for example platform-level neutral profiles)? Is this per region?
- What is the purpose and legal basis for each category under DPDP, GDPR and PDPA (consent, legitimate use, legal obligation, performance of contract)? Where consent is the basis, how is it recorded and withdrawn?
- How does a request to access, correct or erase data work when the data is part of an arbitral record that must be retained? Which data can be erased or redacted, and which is refused with a stated legal reason?
- Does the context hold data of children or persons with disabilities that triggers verifiable parental or guardian consent under the DPDP Act?
- Which personal data must never leave the tenant's home region, and is any of it sent to sub-processors (e-sign, transcription, AI models, payment)?
- If this context is involved in a personal data breach, which fields are in scope and can the platform produce the list of affected people and tenants quickly enough to meet DPDP Rules reporting (detailed report to the Data Protection Board within 72 hours) and GDPR / PDPA timelines?

**Good answer:** A personal-data inventory per entity with category, data subject, purpose, legal basis, home region and sub-processors, linked to the platform's record of processing. It states the controller / processor split for each tenant type and gives a written rule for rights requests against retained legal records (for example "redact on request, never delete before the retention period ends, record the refusal reason").

**Red flags:**

- No list of personal data categories, or "only names and emails" for a context that stores pleadings and evidence.
- Erasure implemented as a hard delete that destroys the legal record, or no erasure path at all.
- Personal data sent to a sub-processor outside the tenant's region with no stated transfer basis.
- No way to find which data subjects are affected by a breach of this context.

### `compliance` Retention and regulatory rules

**Question:** Which regulatory, institutional and contractual rules govern this context (timelines, retention, reporting, confidentiality), and where is each encoded, configured and evidenced?

- List each applicable source with the specific rule: for example SEBI ODR circular timelines for conciliation and arbitration via MIIs, institution rules (HKIAC Administered Arbitration Rules), MSME reporting obligations, AML / KYC / sanctions screening of parties or payers, FEMA for cross-border fee payments.
- For each rule, is it a hard guard on a lifecycle transition, a deadline in a Workflow, a report from Reporting, or a manual control? Link the node that implements it.
- What are the retention periods per entity and per tenant type, what event starts the clock (case closure, award, last payment), and what happens at expiry (delete, anonymise, archive)?
- How are legal holds placed and lifted, who can do it, and does a hold block every deletion path including tenant offboarding and backups expiry?
- Which confidentiality tiers apply (public, tenant-internal, case-participants, tribunal-only), and which regulator or institution rule requires each?
- Which rules vary by jurisdiction or tenant, and are those values held in versioned configuration (a Decision node) rather than code?
- What evidence would we show an auditor (ISO 27001, SOC 2) or a regulator that each rule is applied?

**Good answer:** A rule table with source (regulation, clause or institutional rule), rule ID in this node, how it is enforced (guard, timer, report, manual control) and the evidence produced. Retention is stated per entity with trigger event, period, end action and legal-hold behaviour, and tenant- or jurisdiction-variable values point to a versioned Decision node.

**Red flags:**

- "Compliance is handled by the Regulatory node" with no mapping to this context's entities and transitions.
- Retention periods hard-coded or missing, or no trigger event for the retention clock.
- No legal-hold mechanism, or one that does not stop scheduled deletion jobs.
- Regulatory timelines encoded in code constants instead of versioned configuration.

### `consistency` Invariants and concurrency

**Question:** Which business rules must always hold inside one aggregate, which can be eventually consistent across aggregates or contexts, and how are concurrent changes and duplicate commands handled?

- For each aggregate, which rules (by rule ID) are invariants that must hold at commit time, for example "at least one claimant and one respondent" or "total of fee instalments equals the assessed fee"?
- Which rules span aggregates or contexts (for example Hearing cannot be scheduled before the tribunal is constituted), and how is the gap handled: a domain event, a Temporal workflow, or a check at read time?
- How are concurrent edits detected, for example two secretariat users updating the same case, or a party filing while the deadline closes? Optimistic locking with a version column, or something else?
- Are commands idempotent? What idempotency key does each carry so that a retried request from the UI, a webhook or a Temporal activity does not file twice or pay twice?
- Are domain events published with a transactional outbox, so an event is never sent for a change that rolled back and never lost for one that committed?
- What is the clock of record for deadlines and timestamps (server time in UTC, tenant time zone for display), and how are deadline boundaries (end of day in the seat's time zone) defined?

**Good answer:** Each aggregate lists its invariants by rule ID and its consistency boundary; cross-aggregate rules name the event or workflow that enforces them and the maximum acceptable delay. The answer states the concurrency control (version column and conflict response), the idempotency key for every command, and the outbox pattern for events.

**Red flags:**

- Cross-aggregate rules enforced by multi-table transactions spanning contexts.
- No concurrency control on aggregates that several people edit.
- Commands from webhooks or retries with no idempotency key.
- Events published directly after commit with no outbox.

### `i18n` Localisation and jurisdiction

**Question:** Which terms, formats, time zones, currencies and languages vary by jurisdiction or tenant in this context, and are they modelled as data rather than assumed?

- Which glossary terms differ by jurisdiction or institution (for example award vs decision, claimant vs applicant, conciliator vs mediator), and does the model use one internal term with tenant-configured labels?
- Which time zone governs each deadline: the seat of arbitration, the tenant, or the user? How is a deadline that falls on a local public holiday or weekend handled, and where do holiday calendars come from?
- How are money amounts stored (integer minor units plus ISO 4217 currency), which exchange rate source and date apply for fee conversion, and how are rounding rules defined per currency?
- Which languages must case content support (for example English, Hindi and other Indian languages, Chinese for HKIAC), and is the language of proceedings an attribute of the case?
- Are names, addresses and identifiers modelled to allow non-Latin scripts, multiple name parts and country-specific formats (PAN, UEN, EIN) without forcing a Western shape?
- Are translated documents linked to their original, with which one is authoritative recorded?

**Good answer:** A list of jurisdiction- or tenant-variable items with where each is configured (Decision node or tenant settings), a stated time-zone rule for every deadline type, money stored as minor units plus currency with a named rate source, and language of proceedings modelled on the case. Formats come from CLDR-backed libraries, not hand-written patterns.

**Red flags:**

- Deadlines computed in server local time or with no stated time zone.
- Money stored as floating point or without a currency code.
- Single-name or Latin-only fields for parties and neutrals.
- Institution-specific vocabulary hard-coded in the model.

### `ai` AI assistance

**Question:** Where does AI act on this context's data (summaries, drafting, extraction, classification, search), what can it change, and what human review, records and controls apply before any AI output affects a case?

- List each AI use with its input data, output, and whether the output is advisory (a suggestion shown to a person) or can change state. Can any AI output change state without a named person accepting it?
- Which roles may use each AI feature, and is it switchable per tenant? Some institutions may forbid AI on case content.
- Which model and provider is used, in which region does inference run, and is tenant data kept out of provider training and logs by contract?
- How is AI output labelled to users and recorded: model version, prompt template version, inputs referenced, the reviewer who accepted or edited it, and the final text?
- What prevents a prompt-injection attack from a filed document (for example hidden instructions in an uploaded exhibit) causing the AI to leak another case's data or take an action?
- How is quality measured (for example summary accuracy on a labelled sample, hallucinated citation rate), what threshold blocks release, and who reviews it?
- Does any use fall into a higher-risk category for ISO 42001 impact assessment (for example suggesting neutral appointments or drafting parts of an award), and is that assessment linked?

**Good answer:** A table of AI uses with input, output, advisory or state-changing, required reviewer role, tenant switch, model and inference region. Every state-changing use requires explicit human acceptance, and acceptance is audited with model and prompt version. The answer links an AI node with the evaluation set, release threshold and ISO 42001 impact assessment.

**Red flags:**

- AI output written directly into the case record or sent to parties without human acceptance.
- Inference outside the tenant's residency region, or no contract term on training use.
- No record of which model and prompt produced a given text.
- Retrieval for AI not filtered by tenant and case permissions.

### `testing` Testing

**Question:** How will we prove the lifecycle, business rules, permissions and tenant isolation of this context behave as specified, before release and on every change?

- Is there a test for every allowed lifecycle transition and a test that every disallowed transition is rejected (generated from the state machine definition so the two cannot drift)?
- Does every business rule ID have at least one test that names it, and is rule coverage reported in CI?
- Are rules driven by Decision tables tested from the table itself, including boundary values (for example claim value exactly at a tribunal-size threshold)?
- Is there an automated tenant-isolation test for this context's tables that runs as the application database role with forced RLS (not a superuser)?
- Are permission tests generated from the permission matrix, including relationship-based rules and lifecycle-driven revocation?
- Are deadline and time-zone rules tested across daylight-saving changes, public holidays and the seat's end-of-day boundary?
- Which acceptance scenarios have been written with and signed off by legal or operations, in the ubiquitous language of this node?

**Good answer:** Transition tests generated from the state machine, one or more tests per rule ID with coverage reported in CI, Decision-table tests including boundaries, and isolation and permission tests that run against Postgres with RLS using the application role. Acceptance scenarios in business language are listed with the person from legal or operations who agreed them.

**Red flags:**

- Only happy-path tests, no tests for rejected transitions.
- Isolation tests run as a superuser or with RLS disabled.
- Business rules with no traceable test.
- No acceptance scenarios reviewed by the business.

