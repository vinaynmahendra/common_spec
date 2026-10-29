---
id: "PLAN"
title: "Order of Implementation"
parent: null
order: 18
type: "area"
template: "plan"
childTemplate: "plan"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 4
syncHash: "f4652a283f306096"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 18 Order of Implementation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:objective -->
## Objective

Deliver the new multi-tenant platform in phases, each ending with something that works end to end and can be checked, until CORD and TERES tenants can run their full case lifecycle on it in their home region (India, Singapore or US), with AI assistance available to tenants that opt in, and with the evidence needed for ISO 27001, SOC 2 and client security reviews.

Dates are not yet set; each phase gets a target date at its entry review. The first externally visible goal is a **pilot tenant in production in one region at the end of Phase 3**.

**What changed from the earlier outline, and why**

| Earlier outline | Problem | Now |
|---|---|---|
| Security testing only in Phase 8 (Hardening) | Real tenant data would arrive in Phase 3 without a penetration test, and security defects found late are expensive to fix | Security testing runs from Phase 0 in the pipeline; threat modelling per phase; an external penetration test is an exit criterion of Phase 3 (before pilot data) and of every phase that opens new attack surface to production |
| Data residency not placed in any phase | Region pinning, the global tenant directory and per-region stacks shape the tenant model, routing, workers and storage; retrofitting them breaks Phase 1 to 3 work | Residency is built in Phase 1: tenant directory, home-region routing and two regional stacks (India and Singapore) in staging; US stack before the first US tenant |
| Observability in Phase 7 | Phases 3 to 6 would run in production without traces, alerts or security events | Observability foundations, security events and alerting move to Phase 1; Phase 7 keeps reporting and analytics |
| DR drills in Phase 8 | No tested restore before real data | Backups from the first deployment; a restore test per region before any pilot data (Phase 3 exit) |
| ISO 27001 / SOC 2 evidence in Phase 8 | Evidence cannot be produced after the fact; SOC 2 Type II needs an observation period | Evidence collection starts in Phase 0; Phase 8 is the external audit, not the start of evidence |
| AI governance not mentioned | AI features would be built before policy, impact assessment and provider terms exist | AI policy and provider review start in Phase 1; AI features in Phase 6 are gated on Approved impact assessments |

<!-- section:phases -->
## Phases

| Phase | Scope (linked nodes) | Outcome | Entry criteria | Exit criteria (pass / fail, with evidence) |
|---|---|---|---|---|
| **0. Foundations** | [[FND-monorepo]], [[FND-language-and-conventions]], [[FND-environment-management]], [[FND-environments]], [[FND-governance]], [[DEP-ci-cd-pipelines-build-test]], [[INF-cloud-and-iac]] (module skeleton for a regional stack), [[TST-security-testing]] (pipeline part) | Buildable, deployable skeleton; one dev environment; security scanning in CI | IaC tool and orchestration decisions Approved ([[ADR]]) | CI runs lint, type check, unit tests, SAST, dependency and secret scanning, container image scan and blocks on high findings (evidence: pipeline config and a failing-build demo); skeleton deployed by IaC to dev; evidence store for ISO 27001 / SOC 2 created and first artefacts filed |
| **1. Core platform and residency** | [[MT-tenant-model]], [[MT-tenant-resolution]], [[MT-isolation-strategy]] and children, [[MT-data-residency-2]], [[PKG-authentication]], [[PKG-authorization]], [[PKG-settings]], [[PKG-audit-trail]], [[PKG-data-access]], [[INF-database]], [[INF-pgbouncer]], [[INF-secrets-and-keys]], [[INF-networking]], [[INF-backup-and-disaster-recovery]] (backups on), [[OBS-foundations]], [[OBS-security-events]], [[OBS-alerting]], [[TST-multi-tenant-isolation-tests]]; **administration and access core**: [[PKG-authorization-data-model]], [[PKG-permission-catalogue]], [[PKG-roles-and-permission-sets]], [[PKG-separation-of-duties]], [[PKG-non-human-principals]], [[PKG-settings-data-model]], [[PKG-configuration-scope-hierarchy]], [[PKG-configuration-lifecycle]], [[PKG-settings-catalogue]], [[PKG-authentication-policies]], [[PKG-external-party-identity]], [[PKG-domain-verification]], [[PKG-settings-security-and-identity]], [[PKG-settings-access-control]], [[PKG-settings-platform-operations]], [[APP-administration-model]], [[APP-tenant-admin-console]] (shell), [[APP-platform-admin-and-support]], [[APP-tenant-onboarding-wizard]], [[APP-user-and-access-admin]], [[APP-admin-change-history]] | Secure multi-tenant shell running in **two regional staging stacks (India, Singapore)** with home-region routing | Phase 0 exit; ORM, tenant isolation, pooler and identity provider decisions Approved | Cross-tenant isolation suite green and blocking; a tenant pinned to India cannot be served, queued or processed in Singapore and vice versa (automated residency test in both regions); threat model for the core shell reviewed; DAST baseline scan of staging with no open high findings; backups running with retention set; traces, logs and security events flowing to regional collectors; AI policy draft approved by management ([[AI-ai-governance-and-impact]]); a tenant can be provisioned from the platform console, its owner can assign scoped roles, and every admin change is a change set visible in admin history with maker-checker where marked |
| **2. Shared services** | [[PKG-storage]], [[PKG-encryption-at-rest-signed-urls]], [[PKG-caching]], [[PKG-notifications]], [[PKG-feature-flags]], [[PKG-ui-design-system]], [[I18N-i18n]], [[PKG-data-retention-legal-hold-and]], [[WF-background-jobs-and-queues]], [[INF-redis]], [[APP-security-headers-csp-cors]], [[APP-accessibility-wcag-2-1-aa]] (component level); **settings and self-service**: [[PKG-settings-notifications]], [[PKG-notification-policies]], [[PKG-settings-branding-content]], [[PKG-settings-data-and-privacy]], [[PKG-personalisation]], [[PKG-settings-personal]], [[PKG-access-explainer]], [[PKG-jit-and-break-glass]], [[APP-bulk-admin-operations]], [[PKG-user-provisioning-scim]] (invitations first; SCIM by Phase 5) | Reusable building blocks | Phase 1 exit; Redis topology decision Approved | Malware scanning blocks unscanned files in a test; signed URLs expire as specified; retention and legal-hold engine deletes and holds correctly in tests; security headers and CSP score checked in CI; design-system components pass automated accessibility checks; threat model updated for file upload and notifications; settings pages for these catalogues resolve values across all scopes in tests |
| **3. First domain slice and pilot readiness** | [[DOM-cases]], [[DOM-documents]], parties within cases, [[WF-workflow-engine]], [[WF-entity-state-machines]], [[INF-temporal]], [[SEC-privacy-controls]] (notices, rights requests), [[SEC-security-incident-response-and]], [[OBS-uptime-synthetic-monitoring]], **US regional stack** in staging; **case-type blueprints**: [[WF-process-definition-model]], [[WF-workflow-versioning]], [[WF-sla-and-business-calendars]], [[PKG-settings-cases-and-workflows]], [[PKG-configuration-packages]] (tenant blueprint for the pilot tenant) | First usable vertical; **pilot tenant in production in one region** | Phase 2 exit; rules engine, visibility store and search decisions Approved | Cases, documents and parties end to end in staging in all three regions; **external penetration test** of the slice with no open critical or high findings (retest evidence); **restore test** of database, object storage and Temporal persistence in each region with measured RPO / RTO; incident response and breach-notification runbook exercised (tabletop covering CERT-In 6-hour, DPDP Board and PDPC clocks); privacy notice and rights-request flow live; production readiness review passed [R1]; pilot tenant's security questionnaire answered; pilot tenant created from a published tenant blueprint and its cases pinned to blueprint versions |
| **4. Extended domain** | [[DOM-neutrals]], [[DOM-transcribers]], [[DOM-hearings]], [[DOM-invoices-and-vendor-bills]], [[PKG-rules-and-decision-engine]], [[PKG-configuration-and-customisation]], [[PKG-calendars-and-deadline]], [[INT-video-conferencing-for-hearings]]; **workflow authoring**: [[WF-workflow-authoring-studio]], [[WF-automation-rules]], [[WF-workflow-simulation]], [[SEC-access-reviews]] | Full case lifecycle | Phase 3 exit | Full lifecycle scenario passes for an arbitral institution tenant, a SEBI ODR institution tenant and a CORD tenant in staging; penetration test of new surfaces (hearing room, neutral workspace); accessibility audit of party portal and hearing room against WCAG 2.2 AA with no open blockers; a tenant workflow designer publishes a changed case type through simulation and review, and running cases stay on their pinned version |
| **5. Commercial and integrations** | [[BIL-plans-entitlements-and-usage]], [[BIL-invoicing-taxes-gst-singapore]], [[BIL-payment-gateway-integration]], [[INT-integration-framework]], [[INT-common-integrations]], [[INT-public-api-and-webhooks]], [[INT-kyc-and-sanctions-screening]]; **integration and commercial administration**: [[INT-tenant-admin-api]], [[INT-connections-admin]], [[INT-connector-data-policies]], [[PKG-settings-integrations]], [[PKG-api-clients-and-keys]], [[PKG-settings-billing-and-plans]] | Sellable product | Phase 4 exit | Invoices correct per billing entity in tests; API security test (authentication, rate limits, idempotency, webhook signing) with no open high findings; payment provider and KYC provider sub-processor reviews done; tenant admin API and connector data policies pass the same security test |
| **6. Intelligence** | [[AI-ai-gateway]], [[AI-prompt-management]], [[AI-rag]], [[AI-guardrails]], [[AI-human-in-the-loop]], [[AI-cost-controls]], [[TST-evals-and-ai-testing]], first AI feature nodes; **AI administration**: [[AI-tenant-ai-policy]], [[PKG-settings-ai]], [[AI-agent-configuration]], [[WF-ai-steps-and-agents]], [[APP-admin-copilot]] | AI-assisted features for opted-in tenants | Phase 3 exit (document pipeline events); AI providers per region and vector store decisions Approved; AI policy Approved | AI residency test green in every region; zero cross-tenant or cross-case retrieval in the isolation suite; feature evals at threshold; AI red-team test against OWASP LLM risks with no open high findings; Approved impact assessment per feature; tenant opt-in recorded before enablement as the `ai.policy.enabled` setting; the admin copilot proposes changes only as draft change sets |
| **7. Insight and regulatory reporting** | [[RPT-report-infrastructure]], [[RPT-platform-stats]], [[RPT-compliance-reports]], [[RPT-aggregators]], [[OBS-business-events]], [[OBS-ai-usage]] | Operational and regulatory visibility | Phase 4 exit; aggregator formats obtained ([[ADR-aggregator-reporting]]) | Report templates for the first aggregator pass golden-dataset tests and are approved by the tenant; cross-tenant reporting only through the reporting role (test) |
| **8. Certification and scale** | [[SEC-isms-controls]], [[SEC-business-continuity]], [[TST-performance-and-load-testing]], [[INF-backup-and-disaster-recovery]] (full exercise) | Production and audit ready at scale | Evidence collected since Phase 0; observation period under way | External ISO 27001 certification audit and SOC 2 report (scope and type to be decided); regional loss exercise per region; load test at the proposed target volumes; open findings within agreed remediation windows |

**Rule for missed criteria:** a phase stays open until every exit criterion passes, or the ARB records an exception with owner, compensating measure and due date. Exceptions are never allowed for isolation tests, residency tests, critical or high penetration-test findings, or restore tests before real tenant data.

<!-- section:dependencies -->
## Dependencies

| Item | Depends on | Type | Owner | Needed by | Fallback |
|---|---|---|---|---|---|
| Phase 0 IaC | IaC tool decision (Terraform or Pulumi) | Decision ([[ADR]]) | Platform lead | Phase 0 start | Default to Terraform |
| Phase 1 residency | Cloud accounts / subscriptions in India and Singapore; Azure for clients that need it | External (cloud provider, finance) | CTO | Phase 1 start | Start with AWS only |
| Phase 1 pooling | Pooler decision per cloud, validated with Prisma and `set_config(..., true)` ([[INF-pgbouncer]]) | Spike | Data lead | Phase 1 week 2 | Self-managed PgBouncer |
| Phase 1 auth | Identity provider decision | Decision | Security lead | Phase 1 start | — |
| Phase 2 queues | Redis topology decision ([[ADR-queue-technology]]) | Decision | Platform lead | Phase 2 start | Separate instances |
| Phase 3 workflows | Rules engine and visibility store decisions ([[WF-separation-of-concerns-temporal]]) | Decision | ARB | Phase 3 start | In-house JSON evaluator; Postgres visibility |
| Phase 3 pen test | External testing firm booked (lead time often several weeks) | External | Security lead | 6 weeks before Phase 3 exit | Second approved firm |
| Phase 3 pilot | Pilot tenant identified and contract signed | External (client) | CEO / COO | Phase 3 start | Internal CORD tenant as pilot |
| Phase 3 US stack | US cloud account and US entity contracts | External | CTO, finance | Phase 3 mid-point | Delay US tenants |
| Phase 6 AI | Provider contracts with no-training and retention terms per region | External (providers, legal) | AI platform lead, legal | Phase 6 start | Feature unavailable in that region |
| Phase 7 reporting | Current NSE and MSME formats | External (aggregators, tenants) | Compliance | Phase 7 start | Defer that aggregator |
| Phase 8 audits | Certification body and auditor engaged; observation period started | External | Security and compliance lead | Observation start in Phase 3 or 4 | — |

**Critical path (proposed):** Phase 0 IaC decision, Phase 1 residency and isolation, Phase 2 storage and retention, Phase 3 pen test and restore test, pilot go-live.

<!-- section:milestones -->
## Milestones

| Milestone | Signed off by | Target date |
|---|---|---|
| M0 Skeleton deployed with security pipeline | Platform lead, security lead | TBD at Phase 0 entry |
| M1 Two-region staging with isolation and residency tests green | CTO, security lead | TBD |
| M2 Shared services ready | Platform lead | TBD |
| M3 Pilot go-live (pen test closed, restore tested, incident drill done, PRR passed) | CTO, security and compliance lead, pilot tenant | TBD |
| M4 Full case lifecycle for the three tenant types | Product lead, CTO | TBD |
| M5 Commercial launch readiness | CEO, COO, CTO | TBD |
| M6 First AI feature enabled for an opted-in tenant | AI platform and governance lead, CTO | TBD |
| M7 First aggregator report accepted | Compliance lead, tenant | TBD |
| M8 ISO 27001 certification / SOC 2 report | CEO, CTO | TBD |

<!-- section:crosscutting -->
## Cross-cutting from day one

Not deferred; each has an owner and is part of every phase's exit criteria:

| Concern | From | How it is checked each phase |
|---|---|---|
| Security testing: SAST, dependency, secret and image scanning | Phase 0 | Blocking CI ([[TST-security-testing]], [[SEC-vulnerability-management]]) |
| Threat modelling | Phase 1 | Updated threat model per phase, reviewed by security lead |
| DAST and external penetration tests | DAST from Phase 1; pen test before pilot (Phase 3) and for each new production surface | No open critical / high findings at phase exit |
| Tenant isolation tests | Phase 1 | Blocking suite ([[TST-multi-tenant-isolation-tests]]) |
| Data residency | Phase 1 | Residency tests per region; every new store, queue, workflow or AI call states its region |
| Audit logging | Phase 1 | Every new action emits audit events ([[PKG-audit-trail]]) |
| Structured logging, tracing, security events | Phase 1 | Regional collectors, tenant tags ([[OBS-foundations]]) |
| Security headers and CSP | Phase 2 | CI check ([[APP-security-headers-csp-cors]]) |
| Accessibility (WCAG 2.2 AA) | Phase 2 | Automated checks in CI, manual audits at Phase 4 ([[TST-accessibility-testing]]) |
| Backups and restore | Phase 1 (backups), Phase 3 (restore test) | Restore test per region at Phase 3 and then on the DR schedule |
| ISO 27001 / SOC 2 evidence | Phase 0 | Evidence store filled each phase; control owners named |
| AI governance | Phase 1 | Policy before any AI work; impact assessments before any AI feature |

<!-- section:risks -->
## Risks

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Support load from current CORD and TERES products slows the build | High | High | Fixed allocation per person; protected platform team | CTO |
| Residency rules for a client turn out stricter than the regional model (dedicated stack) | Medium | High | Same schema deployable single-tenant ([[ADR-tenant-isolation]]) | CTO |
| RLS plus PgBouncer plus Prisma behaves unexpectedly under load | Medium | High | Phase 1 spike and load test | Data lead |
| Pen test finds structural issues late | Medium | High | Threat modelling from Phase 1; DAST from Phase 1; pen test before pilot, not at the end | Security lead |
| In-region AI models unavailable in a region | Medium | Medium | Feature unavailable in that region; self-hosted option | AI platform lead |
| Aggregator formats change during build | Medium | Medium | Configuration-driven templates ([[ADR-aggregator-reporting]]) | Compliance |
| Migration of existing tenants underestimated | High | High | Separate migration plan with rehearsal (open question) | CTO |

<!-- section:questions -->
## Open questions

- [ ] Target dates per phase and the pilot tenant: who and when?
- [ ] Is migration of existing CORD and TERES tenants a separate plan node (proposed), and which phase must be complete before the first migration?
- [ ] Which certifications and reports are required, by which entity, and by when (ISO 27001 scope, SOC 2 Type I or Type II)? This sets when the observation period must start.
- [ ] Which region hosts the pilot tenant, and does it need Azure?
- [ ] Capacity: team size and allocation per phase after support load; not yet stated.
- [ ] Should Phase 6 (AI) start in parallel with Phase 4 or 5 once Phase 3 document events exist? Proposed: yes for gateway and governance work, features only after Phase 4.

<!-- checks -->
## Template checks

<!-- check:dependencies -->
### Dependencies

A dependency table lists item, depends-on, type, owner, needed-by point and fallback, including external parties (cloud accounts, pen-test firm, pilot tenant, AI providers, aggregators, auditors), and the critical path is stated. Needed-by dates become real dates once phase dates are set.

<!-- check:exit -->
### Exit criteria

Each phase has pass / fail exit criteria naming the evidence (pipeline configs, test suite results, pen test retest report, restore test record with measured RPO / RTO, incident drill record, PRR checklist). The rule for missed criteria is stated, with no exceptions allowed for isolation, residency, high pen-test findings or restore tests before real data.

<!-- check:risk -->
### Risk-first sequencing

Risk-first changes: residency, isolation and the RLS / PgBouncer / Prisma spike in Phase 1; threat modelling and DAST from Phase 1; pen test and restore test before pilot data; AI governance before AI features. A thin end-to-end slice with a pilot tenant is Phase 3.

<!-- check:migration -->
### Migration and cutover

Not yet covered: migration of existing CORD and TERES tenants needs its own plan node with mapping, verification by counts and checksums, in-flight case handling, rollback and a rehearsal on a production-sized copy in the tenant's region. Listed as an open question and a high risk.

<!-- check:compliance -->
### Compliance and assurance gates

Assurance activities are plan items inside exit criteria: security scanning from Phase 0, evidence store from Phase 0, pen tests at Phase 3 and for new surfaces, breach-notification drill covering CERT-In, DPDP and PDPC clocks at Phase 3 [R2] [R3], accessibility audit at Phase 4, AI impact assessments at Phase 6, external ISO 27001 audit [R4] and SOC 2 at Phase 8 with evidence gathered since Phase 0.

<!-- check:readiness -->
### Operational readiness

A production readiness review [R1] is an exit criterion of Phase 3 (before pilot) and of every phase that adds production surface: monitoring and alerts, runbooks, on-call, tested restore per region, rehearsed rollback, support readiness, and an exercised incident process. Dates of last restore and DR exercise are recorded per region in [[INF-backup-and-disaster-recovery]].

<!-- check:tracking -->
### Progress tracking and re-planning

Progress is measured by exit criteria and node approval status per phase, plus the four DORA delivery metrics [R5] reported monthly. Re-plan when a phase's exit slips by more than a proposed 25 percent of its planned duration or when a critical-path dependency misses its needed-by date.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Describes the Production Readiness Review as a gate before a service is supported in production.",
    "id": "R1",
    "kind": "web",
    "publisher": "Google",
    "title": "Site Reliability Engineering: The Evolving SRE Engagement Model (Production Readiness Review)",
    "url": "https://sre.google/sre-book/evolving-sre-engagement-model/"
  },
  {
    "excerpt": "Reportable cyber incidents to be reported to CERT-In within 6 hours of noticing; logs of ICT systems to be maintained securely for a rolling period of 180 days within Indian jurisdiction; clocks to be synchronised to NTP servers of NIC/NPL or traceable sources.",
    "id": "R2",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and IT, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under sub-section (6) of section 70B of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  },
  {
    "excerpt": "Rules under the DPDP Act 2023, including intimation of personal data breaches to the Board and affected Data Principals and reasonable security safeguards.",
    "id": "R3",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Digital Personal Data Protection Rules, 2025",
    "status": "notified, phased commencement",
    "title": "Digital Personal Data Protection Rules, 2025 (as notified, PIB)",
    "url": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf"
  },
  {
    "body": "ISO/IEC",
    "excerpt": "Annex A includes controls on logging (8.15), monitoring activities (8.16), clock synchronisation (8.17), backup (8.13) and ICT readiness for business continuity (5.30).",
    "id": "R4",
    "ident": "ISO/IEC 27001",
    "kind": "standard",
    "title": "Information security management systems — Requirements",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "excerpt": "Change lead time, deployment frequency, change fail rate and failed deployment recovery time.",
    "id": "R5",
    "kind": "web",
    "publisher": "DORA",
    "title": "DORA's software delivery metrics: the four keys",
    "url": "https://dora.dev/guides/dora-metrics-four-keys/"
  }
]
```

<!-- end -->
