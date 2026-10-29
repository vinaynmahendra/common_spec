---
id: "INT-connector-data-policies"
title: "Connector data policies"
parent: "INT-integration-framework"
order: 2
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Data-loss-prevention policies for connectors: data kinds and confidentiality tiers per connector and operation, connector groups (case data approved, metadata only, blocked), layered platform-to-unit rules, exemptions, residency and enforcement points"
links: []
rev: 1
syncHash: "8d50dc24554aa6d6"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.1.2 Connector data policies

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Data-loss-prevention policies for connectors: data kinds and confidentiality tiers per connector and operation, connector groups (case data approved, metadata only, blocked), layered platform-to-unit rules, exemptions, residency and enforcement points

<!-- section:purpose -->
## Purpose and scope

Connector data policies decide **which data may leave the platform through which connector, for which operation, to where**. They are the platform's data-loss-prevention layer for integrations: a misconfigured or over-broad connection must not be able to send tribunal-only documents to a messaging provider, identity documents to an accounting system, or any case data to a provider outside the tenant's region without a recorded basis.

Protected by this control:
- every outbound provider call made through `callProvider` in [[INT-integration-framework]];
- automation rule actions that call connectors or a generic HTTPS action ([[WF-automation-rules]]) and AI or workflow steps that hand data to connectors ([[WF-ai-steps-and-agents]]);
- notification channel templates, which are checked for content classes before publish ([[PKG-document-and-notification]], [[PKG-notification-policies]]);
- connection creation and enablement ([[INT-connections-admin]]).

Not covered here: our own outbound webhooks (always thin payloads, [[APP-webhooks-outbound]]), our public API (callers are authorised principals, [[INT-public-api-and-webhooks]]), and AI model providers, which are governed by [[AI-tenant-ai-policy]] using the same data kinds and tiers.

Pattern borrowed from: connector classification into Business, Non-business and Blocked groups that cannot be combined in one flow, with a default group for new connectors, in Power Platform data policies [R1]; and app access rules that block installed apps from tenant content with explicit exemptions, in Atlassian data security policies [R2]. We adapt both to legal data: our default for new connectors is `blocked`, not the permissive group.

<!-- section:assets -->
## Protected assets

Data is described on two axes: the **confidentiality tier** from [[SEC-data-classification]] and the **data kind**.

| Data kind | Examples | Typical tier | Sensitivity notes |
|---|---|---|---|
| `contact_pii` | Name, email, phone, postal address | case_participants | Personal data under DPDP, PDPA, GDPR |
| `identity_document` | PAN, passport data, KYC result, liveness evidence | tribunal_only | Highest harm if leaked |
| `case_metadata` | Case reference, stage, dates, case type | case_participants | Reveals that a dispute exists |
| `case_parties_other_side` | Names or details of the opposing party | case_participants | Never in SMS, WhatsApp or push |
| `document_content` | Pleadings, evidence, orders, awards | case_participants or tribunal_only | Confidential under rules and contracts |
| `recording_media` | Hearing audio, video, transcripts | tribunal_only | Biometric-adjacent; residency-critical |
| `financial` | Invoice amounts, bank details, payment status | tenant_internal | Bank details are high risk |
| `system_reference` | Opaque IDs, links to the platform | public | Safe by design |

Actions protected: send (outbound call), fetch by reference (provider pulls from a signed URL we issue), store at provider (retention), and combine (one automation passing data from one connector or case source into another connector).

Policy artefacts are themselves assets: a weakened policy is a high-impact configuration change and follows maker-checker ([[PKG-separation-of-duties]]).

<!-- section:actors -->
## Actors and roles

| Actor | Role key | How acquired | What they do here |
|---|---|---|---|
| Platform owner / platform admin | `platform_owner`, `platform_admin` | Nomology staff, JIT elevation ([[PKG-jit-and-break-glass]]) | Maintain the platform baseline policy and connector manifests |
| Platform security | `platform_security` | Nomology staff | Approve baseline changes (checker), review exemptions on regulated blueprints |
| Regional ops | `regional_ops` | Nomology staff per region | Maintain region overlays (for example India in-region rules) |
| Tenant owner | `tenant_owner` | Tenant contract | Approve tenant policy changes as checker; accountable |
| Security admin | `security_admin` | Assigned by tenant owner | Author tenant policy, approve exemptions |
| Integration admin | `integration_admin` | Assigned by tenant admin | Classify new connectors within allowed groups (draft), request exemptions, view violations |
| Unit admin | `unit_admin` | Assigned per unit | Tighten policy for their unit (draft), view unit violations |
| Workflow designer | `workflow_designer` | Assigned | Sees policy results when publishing blueprints and automation rules; cannot change policy |
| AI admin | `ai_admin` | Assigned | Reads data kinds and tiers for AI policy alignment |
| Auditor | `auditor` | Assigned | Read policies, versions, exemptions and violations |
| `integration_connection` principal | non-human | Created with a connection ([[PKG-non-human-principals]]) | Subject of evaluation on every call |
| Automation rule / `ai_agent` principal | non-human | Published rule or configured agent | Subject of evaluation when its actions call connectors |

<!-- section:matrix -->
## Permission matrix

Permission keys from [[PKG-permission-catalogue]]: `integration.data_policy:read`, `integration.data_policy:update` (draft), `integration.data_policy:approve`, `integration.data_policy:publish`, `integration.data_policy.exemption:create`, `integration.data_policy.exemption:approve`, `integration.data_policy.violation:read`, `platform.integration.data_policy:update`, `platform.integration.data_policy:approve`.

| Role | Read policies | Draft tenant / unit policy | Approve / publish tenant policy | Classify new connector | Request exemption | Approve exemption | View violations | Edit platform / region baseline |
|---|---|---|---|---|---|---|---|---|
| `platform_owner` | all | no | no | no | no | no | aggregated | approve only |
| `platform_admin` | all | no | no | no | no | no | aggregated, tenant names under break-glass | draft |
| `platform_security` | all | no | no | no | no | regulated blueprints only (second approval) | aggregated | approve |
| `regional_ops` | own region | no | no | no | no | no | own region aggregated | draft region overlay |
| `tenant_owner` | tenant | no | yes (not own draft) | no | no | yes (not own request) | tenant | no |
| `security_admin` | tenant | tenant and units | yes (not own draft) | yes | yes | yes (not own request) | tenant | no |
| `integration_admin` | tenant | no | no | draft only (stricter-or-equal to default) | yes | no | tenant | no |
| `tenant_admin` | tenant | no | no | no | no | no | tenant | no |
| `unit_admin` | own units | own units, tighten only | no | no | own units | no | own units | no |
| `workflow_designer` | effective result for their blueprints | no | no | no | no | no | own blueprints | no |
| `ai_admin`, `auditor` | tenant | no | no | no | no | no | tenant | no |
| `secretariat`, `neutral`, `party`, `counsel` | no | no | no | no | no | no | no | no |

Conditions: maker and checker must be different people; a checker cannot approve a change that loosens a rule they drafted; no tenant role can loosen a platform or region rule; exemptions expire (default 30 days, maximum 90).

<!-- section:policy -->
## Policy model

**Layers** (most restrictive wins, deny overrides allow):

| Order | Layer | Scope key | Can loosen? | Example |
|---|---|---|---|---|
| 1 | Platform baseline | `platform` | — | WhatsApp: max tier `public`, kinds `system_reference` and `contact_pii` (recipient number only) |
| 2 | Region overlay | `region` | No, tighten only | India: `recording_media` only to connectors with in-region processing |
| 3 | Offering overlay | `offering` | No | TERES: transcription vendors may receive `recording_media` |
| 4 | Tenant policy | `tenant` | Within bounds of layers 1–3 | Institution: e-sign provider may receive `document_content` up to `tribunal_only` for awards |
| 5 | Unit policy | `unit` | No, tighten only | SEBI ODR desk: no `tenant_byo` accounting connector |
| 6 | Case-type blueprint | `case_type` | No | Blueprint declares the data kinds its steps send; publish fails if any is denied |
| 7 | Exemption | tenant or unit | Yes, time-limited, within platform bounds | 14-day exemption to backfill accounting records |

**Rule shape** (stored as versioned configuration in `connector_data_policy` and `connector_data_policy_rule`, lifecycle per [[PKG-configuration-lifecycle]]):

```ts
type ConnectorGroup = 'case_data_approved' | 'metadata_only' | 'blocked';
interface ConnectorPolicyRule {
  connector: string | { category: ProviderCategory };   // a connector key or a whole category
  group: ConnectorGroup;
  allowedKinds?: DataKind[];             // default for metadata_only: ['system_reference','case_metadata']
  maxTier?: 'public'|'tenant_internal'|'case_participants'|'tribunal_only';
  operations?: { allow?: string[]; deny?: string[] };    // operation-level control, e.g. deny 'accounting.exportAttachments'
  hostAllowlist?: string[];             // only for the generic HTTPS automation action
  residency: 'in_region' | 'approved_transfer';           // approved_transfer needs a transfer record ID
  providerRetentionMaxDays?: number;    // what we accept the provider keeps
  requireNoTrainingAttestation: true;   // fixed true at platform layer
}
```

**Evaluation.** Each connector operation declares a data manifest in its catalogue entry (`sends: [{kind, tier}]`). Before the call, `evaluateConnectorPolicy(connection, operation, payloadTags)` checks: the connection's group; that every declared kind is in `allowedKinds`; that the highest tier in the payload (from field tags on the domain objects, not from the manifest alone) is ≤ `maxTier`; operation allow / deny lists; residency; and active exemptions. The decision and the policy version are cached per tenant in [[PKG-caching]] with the policy version as part of the key; a cache miss that cannot load the policy fails closed.

**Combination rule.** In an automation rule or AI step, data read from a source of tier T, or returned by connector A, may be passed to connector B only if B's rules allow that kind and tier; a rule that mixes a `case_data_approved` connector's output into a `metadata_only` connector's input is rejected at publish with the field path.

**New connectors.** When the platform publishes a connector, each tenant sees it in group `blocked` until an `integration_admin` drafts a classification and a `security_admin` approves it, unless the platform marks it **core** (the regional platform-managed email and SMS connectors needed for legal service and sign-in). Core connectors cannot be blocked by a tenant, only constrained to `metadata_only`, because blocking them would stop legal notices and OTPs; a tenant that wants a different provider uses a BYO connection instead.

**Template checks.** Channel templates declare their variables with data kind tags; SMS, WhatsApp and push templates may use only `system_reference`, `case_metadata` limited to the case reference, and the recipient's own `contact_pii`. Publish is blocked otherwise; this enforces the lock-screen rules in [[PKG-notification-copy]].

<!-- section:threats -->
## Threats and abuse cases

| # | Threat (STRIDE) | Scenario | Mitigation | Residual risk |
|---|---|---|---|---|
| T1 | Information disclosure | Admin enables a messaging connector and a workflow designer adds award text to a WhatsApp template | Template kind tags checked at publish; platform baseline caps WhatsApp at `public` | Low |
| T2 | Information disclosure | Automation passes a KYC result from the KYC connector to the accounting connector | Combination rule at publish and runtime evaluation of payload tags | Low |
| T3 | Elevation of privilege | One tenant admin loosens the tenant policy alone | Maker-checker with distinct people; loosening also notifies `tenant_owner` | Low |
| T4 | Tampering | Adapter under-declares its data manifest | Contract test compares fields actually serialised against the manifest; manifest review is part of connector certification | Medium (depends on review quality) |
| T5 | Information disclosure | BYO connection whose provider processes outside the region | Residency `approved_transfer` requires a transfer record linked to [[SEC-vendor-sub-processor-management]] [R4][R5][R6] | Medium (tenant's own contract) |
| T6 | Repudiation | Exemption granted without trace | Exemptions are versioned artefacts with reason, approver, expiry; audit event on create, approve, use and expiry | Low |
| T7 | Denial of service | Policy service unavailable blocks legal notices | Policies are cached with version; core connectors evaluate against the last good platform baseline embedded in the release when the cache and database are both unavailable | Low |
| T8 | Elevation of privilege | Nomology insider weakens the platform baseline | Baseline in code plus database overrides; changes need `platform_security` approval and are visible to tenants in the change log | Low |
| T9 | Information disclosure | Generic HTTPS automation action posts to an attacker host | Disabled by default; host allow-list per tenant; SSRF checks as for webhooks ([[APP-webhooks-outbound]]) | Low |
| T10 | Spoofing | Stale policy cache after tightening | Version bump on publish invalidates the cache key; maximum staleness 60 s, stated in the console | Low |

<!-- section:failure -->
## Denial behaviour

- **At configuration time** (create connection, publish blueprint, automation rule or template): problem type `integration-data-policy-blocked` listing each violation with the layer that denies it ("Platform baseline: WhatsApp may not receive document content"), the field path and a link to request an exemption if the layer allows exemptions. Nothing is saved as published; the draft remains.
- **At run time**: `callProvider` throws `ConnectorPolicyViolationError` (non-retryable). The calling Temporal activity fails to a human task for the case manager or connection owner, with the case reference but without the blocked payload. BullMQ jobs go to the dead-letter queue with reason `policy_violation` and are not replayed automatically.
- **Users** (for example a secretariat member whose action triggered the call) see a neutral message: "This step could not be completed because of your organisation's data policy. Your administrator has been notified." Case existence is not revealed beyond what the user already sees.
- **Logged**: security event `integration.policy.denied` ([[OBS-security-events]]) with tenant, connection, operation, kinds and tiers, policy version and denying layer; never the payload.

<!-- section:requirements -->
## Security requirements

Requirement IDs `CDP-SR-n`. ASVS mapping is to OWASP ASVS **version 5.0** chapters [R3]; item-level IDs to be added at security review.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| CDP-SR-1 | Every outbound connector operation shall be evaluated against the effective connector data policy before the provider call, using the operation's declared manifest and the actual payload's field tags. | V8 Authorization; V14 Data Protection |
| CDP-SR-2 | If the policy cannot be loaded, the evaluation shall deny, except for core connectors, which evaluate against the release-embedded platform baseline. | V8; V16 Logging and Error Handling |
| CDP-SR-3 | A lower layer shall never loosen a rule set at a higher layer; the publish API shall reject such drafts. | V8; V13 Configuration |
| CDP-SR-4 | New connectors shall start in group `blocked` for every tenant unless marked core by the platform. | V13 |
| CDP-SR-5 | Tenant and unit policy changes that loosen any rule, and all exemptions, shall require approval by a second person with the approving permission. | V8 |
| CDP-SR-6 | Exemptions shall expire automatically (default 30 days, maximum 90) and the expiry shall restore the stricter rule within 60 seconds. | V8; V13 |
| CDP-SR-7 | Automation rules, AI steps and blueprints shall be rejected at publish when any action would pass a data kind or tier to a connector that does not allow it. | V2 Validation and Business Logic |
| CDP-SR-8 | SMS, WhatsApp and push templates shall be rejected at publish if they reference variables outside the allowed kinds. | V2; V14 |
| CDP-SR-9 | Any connector with residency `approved_transfer` shall reference an approved transfer record; without it the connection shall not become `active`. | V14 |
| CDP-SR-10 | Every deny and every exemption use shall emit a security event and an audit event with the policy version. | V16 |
| CDP-SR-11 | The platform baseline shall forbid any connector whose vendor has not attested that our data is not used to train models. | V14 |
| CDP-SR-12 | The generic HTTPS automation action shall be disabled by default and, when enabled, limited to a tenant host allow-list with SSRF protections. | V12 Secure Communication; V13 |

Acceptance (sample):
- **Given** WhatsApp is `metadata_only` at the platform layer, **when** a security admin drafts a tenant rule allowing `document_content` for WhatsApp, **then** publish fails with `integration-data-policy-blocked` naming the platform baseline.
- **Given** an exemption allowing `financial` to a BYO accounting connector expires at 10:00, **when** a sync job runs at 10:02, **then** the call is denied and `integration.policy.denied` is logged.
- **Given** the policy store is unavailable, **when** a legal-service email is sent through the core email connector, **then** it is evaluated against the release baseline and sent.

<!-- section:verification -->
## Verification

- Table-driven unit tests over layer × group × kind × tier × operation × exemption state in `packages/integrations-core/test/policy.spec.ts`.
- Manifest conformance test per connector: serialise every operation with tagged fixtures and assert the emitted fields equal the manifest.
- Publish-time tests for automation rules, blueprints and templates with deliberate violations.
- Fail-closed test: policy table unreadable → deny for non-core, baseline for core.
- Maker-checker tests: same person cannot draft and approve; exemption cannot be approved by its requester.
- RLS tests: tenant B cannot read tenant A's policy, exemptions or violations.
- Pen-test scope: attempts to bypass via automation chaining, generic HTTPS action, template variables and BYO connectors.

<!-- section:questions -->
## Open questions

- [ ] Should tenants be allowed to define their own data kinds (for example "settlement amount"), or only map custom fields to platform kinds? Proposed: map only. (Product + security)
- [ ] Should the policy also govern **inbound** data (for example refusing KYC results that include images)? (Security)
- [ ] Monitor-only mode for tenants rolling out a stricter policy: allowed in sandbox only (proposed) or also in production for 7 days? (Security)
- [ ] Which data kinds may a transcription vendor receive for SEBI ODR matters? Assumption: none, as SEBI ODR conciliation is largely online without recorded hearings; to be confirmed by legal. (Legal)
- [ ] Align AI provider governance in [[AI-tenant-ai-policy]] to the same layers and evaluator, or keep a separate engine? Proposed: same evaluator, separate rule sets. (AI group)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Policies, exemptions and violations are tenant-owned rows under forced RLS; the platform and region layers are platform-level tables with no tenant data. The evaluator runs inside the caller's tenant context and caches by tenant and policy version, so one tenant's policy can never be applied to another's call. Aggregated violation views at platform level hide tenant names unless under break-glass.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Enforced at four points that every path passes: connection activation, publish of blueprints, automation rules and templates, and `callProvider` (the only way to reach a provider, guaranteed by the boundary rule that vendor SDKs are imported only in integration packages). Automation and AI steps call connectors through the same wrapper, so there is no side path.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Policies follow draft → in_review → approved → published → superseded ([[PKG-configuration-lifecycle]]); loosening changes and exemptions need a second approver; exemptions expire automatically; new connectors start blocked; platform baseline changes need `platform_security` approval.

<!-- check:resilience -->
### Failure modes and secrets

Fails closed for non-core connectors when the policy cannot be loaded; core email and SMS fall back to the release-embedded baseline so legal notices and OTPs continue. Cache staleness is at most 60 seconds after publish.

<!-- check:residency -->
### Data residency

Every rule carries a residency requirement; `approved_transfer` needs a recorded transfer basis per jurisdiction [R4][R5][R6]. Policies, decisions and violation logs are stored in the tenant's region.

<!-- check:audit -->
### Audit trail

Every draft, approval, publish, exemption create, approve, use and expiry is audited (`admin.integration.data_policy_published`, `admin.integration.exemption_approved`, ...) with policy version; every deny emits `integration.policy.denied` with the denying layer, so a later dispute can show which rule stopped or allowed a transfer.

<!-- check:observability -->
### Detection and alerting

Signals: denies per tenant, connector, layer and data kind; exemptions active and expiring; policy cache staleness; core-connector baseline fallbacks (should be zero). Alerts: any baseline fallback (page on-call), deny spike over 10 per hour for one connection (tenant security admin and integration admin), exemption expiring in 3 days (requester and approver). Denies are security events forwarded to the SIEM feed ([[OBS-security-events]]).

<!-- check:compliance -->
### Framework and legal mapping

Supports DPDP purpose limitation and security safeguards for personal data shared with processors [R4], PDPA transfer limitation [R5], GDPR Articles 28 and 44 for EU parties [R6], ISO 27001:2022 Annex A 5.14 (information transfer) and 5.19–5.22 (supplier relationships) and SOC 2 CC6.1 and CC6.7. Evidence: policy versions, exemption register, violation log, manifest conformance test reports.

<!-- check:testing -->
### Verification and testing

Table-driven evaluator tests, manifest conformance tests per connector, publish-time violation tests, fail-closed tests, maker-checker tests and RLS isolation tests run in CI; external pen tests target chaining, templates, generic HTTPS and BYO paths.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Connectors are grouped as Business, Non-business or Blocked; connectors in different groups cannot be used together in one app or flow; a default group classifies new connectors.",
    "id": "R1",
    "kind": "vendor",
    "publisher": "Microsoft",
    "retrieved": "2026-10-28",
    "title": "Power Platform: Connector classification (data policies)",
    "url": "https://learn.microsoft.com/en-us/power-platform/admin/dlp-connector-classification"
  },
  {
    "excerpt": "An app access rule blocks installed apps from reading, writing or deleting user-generated content in covered spaces, with exemptions for allowed apps.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Atlassian",
    "retrieved": "2026-10-28",
    "title": "Block app access (data security policies)",
    "url": "https://support.atlassian.com/security-and-access-policies/docs/block-app-access/"
  },
  {
    "body": "OWASP",
    "id": "R3",
    "ident": "ASVS 5.0",
    "kind": "standard",
    "title": "OWASP Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard/",
    "version": "5.0"
  },
  {
    "id": "R4",
    "issuer": "Ministry of Electronics and Information Technology, India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "An organisation transferring personal data outside Singapore must ensure the recipient is bound to provide a comparable standard of protection, for example by contract.",
    "id": "R5",
    "kind": "web",
    "publisher": "Personal Data Protection Commission Singapore",
    "retrieved": "2026-10-28",
    "title": "Advisory Guidelines: The Transfer Limitation Obligation (Chapter 19)",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/the-transfer-limitation-obligation---ch-19-(270717).pdf"
  },
  {
    "id": "R6",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation (official text)",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  }
]
```

<!-- end -->
