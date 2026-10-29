# Template: Integration (`integration`)

Generated from `integration.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a connection between the platform and an external system: who owns each side, what data crosses, how it is secured, and how failures are handled.

**Depth:** 2–6 pages. The data mapping and error handling sections must be complete. Link the provider's API reference rather than copying it. Each external party is its own node; shared mechanics live in the Integration framework node.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and use cases (level 1)

Why we integrate and the concrete use cases.

Illustrative example (not a requirement):

> E-signature (provider TBD) lets parties sign settlement agreements and tribunals sign awards without printing. Use cases: settlement agreement after successful conciliation; award signing by a three-member tribunal.

### `party` External party and ownership (level 1)

Provider, contract owner, support contacts, environments.

Illustrative example (not a requirement):

> | Item | Value |
> |---|---|
> | Provider | E-sign vendor (shortlist: two vendors with India Aadhaar e-sign and global e-sign) |
> | Contract owner | NTPL; per-tenant sub-accounts |
> | Environments | Sandbox, production per region |

### `flows` Data flows (level 1)

Each flow: direction, trigger, sync / async, sequence.

Illustrative example (not a requirement):

> 1. Platform → provider: create envelope (document, signers, order) — sync API call from a Temporal activity
> 2. Provider → platform: signer events — webhook
> 3. Platform → provider: fetch signed PDF and certificate — on `envelope.completed`

### `mapping` Data mapping (level 1)

Field-level mapping both ways, including identifiers and personal data.

Illustrative example (not a requirement):

> | Platform | Provider | Notes |
> |---|---|---|
> | document.id | envelope.externalRef | Used to match webhooks |
> | party.email / mobile | signer.email / phone | Personal data → DPA required |
> | signing order | routingOrder | Presiding arbitrator last |

### `auth` Authentication and secrets (level 1)

Auth method, where credentials live, rotation, webhook verification.

Illustrative example (not a requirement):

> OAuth client credentials per tenant sub-account, stored in secrets manager under `tenants/{id}/esign`. Webhooks verified with HMAC signature and timestamp (reject > 5 min old).

### `errors` Errors, retries and idempotency (level 1)

Error classes, retry policy, idempotency, duplicate and out-of-order webhooks.

Illustrative example (not a requirement):

> | Case | Handling |
> |---|---|
> | 5xx / timeout | Temporal activity retry, exp. backoff, max 10 |
> | 4xx validation | Fail activity, create secretary task |
> | Duplicate webhook | Dedupe on provider event ID |
> | Out-of-order events | Apply only forward status transitions |

### `limits` Rate limits and SLAs (level 2)

Provider limits, our expected volume, provider uptime commitments.

Illustrative example (not a requirement):

> Provider: 100 req/min per account; our peak ≈ 5/min per tenant. Provider SLA 99.9%.

### `residency` Data transfer and compliance (level 2)

Where data is processed, DPAs, cross-border considerations.

Illustrative example (not a requirement):

> Choose provider region matching tenant region. DPA and sub-processor listing required before go-live (Vendor management control).

### `testing` Sandbox and testing (level 2)

How we test without production effects.

Illustrative example (not a requirement):

> Sandbox account per environment; recorded webhook fixtures for contract tests; monthly synthetic end-to-end sign in staging.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Do awards require a specific e-sign assurance level in any seat jurisdiction?

## Checks

### `tenancy` Tenant separation at the provider

**Question:** Is each tenant's data held at the external provider in a way that keeps it separate from other tenants, and can every inbound event be mapped to exactly one tenant before it is processed?

- Does each tenant have its own account, sub-account, workspace or API key at the provider, or is one platform account shared? If shared, how is data tagged and kept apart, and what does the client contract allow?
- How is an incoming webhook or callback mapped to the right tenant (per-tenant endpoint path, per-tenant signing secret, external reference lookup), and what happens if the mapping fails?
- Is the tenant re-checked against the stored record before any write (so a forged or misrouted event for tenant A cannot change tenant B's case)?
- Can a tenant bring their own provider account (for example their own payment gateway or e-sign contract), and how is that configured and validated?
- When a tenant leaves, how are their credentials revoked and their data deleted or exported at the provider, and is there written confirmation?
- Are provider-side resources (templates, branding, sender IDs, webhook endpoints) created per tenant and region by automation rather than by hand?

**Good answer:** States the account model (dedicated sub-account per tenant, or shared with justification), how credentials are scoped per tenant, and the exact rule for mapping inbound events to a tenant with rejection when it fails. Describes onboarding and offboarding steps at the provider, including data deletion and evidence of it.

**Red flags:**

- One shared provider account with all tenants' data and no tagging or contractual basis
- Tenant chosen from a field in the webhook body without verifying it against our own records
- No offboarding step at the provider

### `security` Security

**Question:** Are credentials stored and rotated safely, are all calls and callbacks authenticated in both directions, and does the integration hold only the permissions it needs?

- Which authentication method is used outbound (OAuth client credentials, signed JWT, API key, mTLS), where is each credential stored (regional secrets manager path per tenant), and what is the rotation period and process?
- Are OAuth scopes or API key permissions the minimum needed for the listed use cases, and is that reviewed when use cases change?
- How are inbound webhooks verified (HMAC or asymmetric signature over the raw body, timestamp tolerance, replay protection by event ID), and are unverified requests rejected before parsing?
- Is the webhook endpoint protected against abuse (rate limiting, payload size limits, IP allow-list where the provider publishes ranges)?
- If we call URLs supplied by the provider (file download links), how is server-side request forgery prevented (allow-listed hosts, no internal network access)?
- Are files received from the provider scanned for malware and validated by type before storing or showing them to users?
- For our own public API and outbound webhooks to clients, are tenant API keys hashed at rest, scoped and revocable, and are our webhooks signed?

**Good answer:** Names the auth method, secret path and rotation interval, and lists scopes requested with the reason for each. Webhook verification is described precisely (algorithm, header, timestamp window such as 5 minutes, dedupe store) and happens before any processing. File and URL handling defend against malware and SSRF, mapped to the OWASP API Security Top 10.

**Red flags:**

- Credentials in environment variables shared by all tenants
- Webhooks accepted without signature check, or signature checked after JSON parsing changes the body
- Admin or full-access scopes requested 'to be safe'
- Provider-supplied URLs fetched without host restrictions

### `residency` Data transfer and residency

**Question:** Which personal or case data leaves the tenant's region or country through this integration, where exactly is it processed and stored, and what legal basis and contract cover that transfer?

- Which fields cross to the provider (from the data mapping), and which of them are personal data, sensitive personal data or confidential case material?
- In which countries does the provider process and store the data, including backups, support access and sub-processors? Is there a regional endpoint matching each tenant region (India, Singapore, US)?
- Which transfer mechanism applies: DPDP Act (transfers allowed unless to a country the Government restricts), Singapore PDPA Transfer Limitation Obligation (comparable protection via contract), GDPR (adequacy or Standard Contractual Clauses plus a transfer risk assessment) for EU parties?
- Can the amount of data sent be reduced (send a reference or pseudonym instead of name and email, send a redacted document)?
- Do any client contracts or institution rules (for example HKIAC, SEBI ODR via MIIs) restrict where case data may go?
- Is the provider listed in our sub-processor list shown to tenants, and are tenants notified before a new one is added?

**Good answer:** A table of fields sent, their sensitivity, destination country per tenant region, and transfer mechanism. Confirms a signed data processing agreement, the sub-processor listing, and any data minimisation applied. Notes client contract restrictions and how the integration is disabled for tenants who forbid the transfer.

**Red flags:**

- Provider processes data in an unknown country
- No data processing agreement before go-live
- EU parties' data transferred with no SCCs or transfer assessment
- Whole documents sent when only metadata is needed

### `vendor` Vendor risk and exit

**Question:** Has the provider been assessed as safe enough to hold this data and run this function, and can we leave them without losing data or service?

- What security assurance does the provider give (ISO 27001 certificate, SOC 2 Type II report, penetration test summary), and when was it last reviewed by us?
- What are the provider's breach notification commitments, and are they fast enough for us to meet CERT-In (6 hours), DPDP intimation to the Data Protection Board (without delay, detailed report within 72 hours), GDPR (72 hours) and client contract windows?
- What uptime and support commitments are in the contract, and are they compatible with our own commitments to tenants?
- Does the provider use our data for its own purposes, such as training AI models? Is that switched off contractually?
- What is the exit plan: data export format, deletion certificate, time to switch to an alternative, and is our code written against an adapter interface so a second provider can be added?
- For KYC and sanctions screening providers, which lists and jurisdictions are covered and how quickly are list updates applied?

**Good answer:** Links the vendor assessment record with certifications and review date, the contractual breach-notice period, uptime commitment and data-use restrictions. Describes the exit path, including export, deletion confirmation and the adapter boundary that allows switching.

**Red flags:**

- No security review of the vendor
- Vendor breach notice period longer than our regulatory deadlines
- Vendor allowed to use case data for its own model training
- Provider-specific logic spread through business code with no adapter

### `resilience` Failure handling and degradation

**Question:** When the provider is slow, down, rate-limiting us or sending bad data, what do users see, what happens to in-flight work, and how does it recover without manual clean-up?

- Which user journeys depend on this provider, and what does each one do during an outage (queue and retry, switch to a manual path, show a clear message)?
- Are all outbound calls made from Temporal activities or BullMQ jobs with explicit timeouts, retry limits and backoff, and are non-retryable errors (validation failures) separated so they stop retrying?
- Does every mutating outbound call carry an idempotency key so retries cannot create duplicate envelopes, payments or messages?
- Is there a circuit breaker or per-tenant rate limiter so one tenant's burst cannot exhaust the shared provider quota?
- If webhooks are missed during an outage, how do we catch up (provider event replay, scheduled status polling)?
- Which failures create a task for a human (for example the case secretary) and how quickly?

**Good answer:** For each journey, the degraded behaviour during a provider outage. Retry policy with timeouts and limits, idempotency keys on all mutating calls, rate limiting within provider quotas, and a catch-up mechanism for missed webhooks. Human tasks are created for unrecoverable errors with an owner.

**Red flags:**

- Synchronous provider calls inside a user's web request with no timeout
- Retries on mutating calls without idempotency
- No plan for missed webhooks
- Failures only visible in logs

### `consistency` Consistency and reconciliation

**Question:** Which system is the source of truth for each piece of shared data, and how do we detect and fix differences between our records and the provider's?

- For each mapped field or status, which side is authoritative (for example the provider for payment settlement status, the platform for case data)?
- How are duplicate and out-of-order events handled (dedupe on provider event ID, applying only valid forward transitions in the entity state machine)?
- Is there a scheduled reconciliation job (daily payment settlement, envelope status, message delivery) that compares both sides and reports mismatches?
- How are amounts, currencies, time zones and identifiers converted, and are rounding and FX rules defined (relevant for payments, MSME reporting and accounting sync with Odoo)?
- When a mismatch is found, who is alerted and what is the correction procedure?

**Good answer:** A source-of-truth table per field, dedupe and ordering rules tied to the state machine, and a reconciliation job with schedule, owner and alert. Conversion rules for money, time and identifiers are written down.

**Red flags:**

- No reconciliation for payments or financial data
- Status overwritten by whichever event arrives last
- Currency or time zone conversions left implicit

### `audit` Audit and evidence

**Question:** Can we later prove exactly what was sent to and received from the provider for a given case, in a form that would stand up in a dispute or regulatory review?

- Which exchanges are recorded in the audit trail (request summary, response, provider IDs, timestamps, actor), and is personal data minimised in that record?
- For evidential outputs (signed documents, signing certificates, payment receipts, KYC results, sanctions screening results), are the original artefacts stored in-region with a hash so they can be shown to be unaltered?
- How long are these records kept, and does that meet arbitration, SEBI ODR, AML/KYC record-keeping and tenant contract requirements?
- Are configuration changes to the integration (credentials, endpoints, scopes, tenant enablement) audited?
- Can a tenant administrator see the history of external actions on their cases?

**Good answer:** Lists the audit events and stored artefacts per flow, with hashing and in-region storage, the retention period with its legal source, and auditing of integration configuration changes.

**Red flags:**

- Signed documents or screening results stored only at the provider
- No record of what data was sent
- Retention period not tied to any requirement

### `observability` Observability

**Question:** Can we see, per provider, region and tenant, whether the integration is healthy right now, and are we alerted before users notice a problem?

- Which metrics are tracked: call success rate by error class, latency percentiles, rate-limit responses, webhook received versus processed, webhook signature failures, reconciliation mismatches?
- What are the alert thresholds, who is paged, and does each alert link to a runbook?
- Are traces propagated from the user action through Temporal or BullMQ to the provider call and back through the webhook, using one correlation ID stored with the provider reference?
- Is the provider's own status page or incident feed monitored?
- Is quota usage tracked against provider limits with an early warning (for example at 70%)?
- Do logs exclude credentials and personal data while keeping provider IDs for support cases?

**Good answer:** Names the dashboards and metrics per provider and region, alert thresholds with routing and runbooks, correlation from user action to webhook, quota warnings and redacted logging.

**Red flags:**

- No metric for webhook failures or signature rejections
- Learning about provider outages from users
- Access tokens or full payloads in logs

### `testing` Testing

**Question:** How do we test the integration end to end without touching real people, money or legal records, and how do we find out quickly when the provider changes its API?

- Is there a sandbox account per environment and region, and is it impossible for non-production environments to use production credentials?
- Are there contract tests built from recorded provider responses and webhooks (including error and edge cases), and are those fixtures refreshed when the provider releases a new API version?
- Are failure scenarios tested: timeouts, 429 rate limits, 5xx, malformed payloads, duplicate and out-of-order webhooks, invalid signatures?
- Is there a scheduled synthetic end-to-end test in staging and a safe production smoke test (for example a test tenant)?
- How do we learn about provider deprecations and API version changes, and who tracks them?
- Is test data synthetic, with no real party names, ID documents or bank details?

**Good answer:** Sandbox per environment with credential separation enforced, contract tests from recorded fixtures including negative cases, scheduled synthetic end-to-end runs, a named owner watching provider changelogs and deprecations, and synthetic test data only.

**Red flags:**

- Testing against production
- Only happy-path tests
- No owner for provider API version changes
- Real personal data in fixtures

