---
id: "SEC-isms-controls"
title: "ISMS controls"
parent: "SEC"
order: 1
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "mapped to ISO 27001 Annex A and SOC 2 criteria"
links: []
rev: 4
syncHash: "1a631766b78e5a1c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-29T00:00:00Z"
updatedBy: null
---

# 13.1 ISMS controls

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> mapped to ISO 27001 Annex A and SOC 2 criteria

<!-- section:objective -->
## Control objective

Information security risks to the platform and to tenants' data are identified, treated and monitored through a management system that meets ISO/IEC 27001:2022 [R1] and the SOC 2 Trust Services Criteria [R2], so that every applicable control is designed, operated and evidenced, and gaps are found by us before they are found by an auditor, a client or an attacker.

(This node absorbs the earlier item "ISO 27001, SOC 2".)

<!-- section:mapping -->
## Framework mapping

**ISMS clauses (ISO/IEC 27001:2022)**: 4.1–4.4 context and scope; 5.1–5.3 leadership, policy, roles; 6.1.2 risk assessment, 6.1.3 risk treatment and Statement of Applicability; 6.2 objectives; 6.3 planning of changes; 7.1–7.5 support (competence, awareness, documented information); 8.1–8.3 operation; 9.1 monitoring, 9.2 internal audit, 9.3 management review; 10.1–10.2 improvement and nonconformity.

**Control register (excerpt)** — the full register maps all 93 Annex A controls; this excerpt shows how controls in this area are mapped once and reused:

| Control (node) | ISO/IEC 27001:2022 Annex A | SOC 2 TSC | DPDP / GDPR / PDPA |
|---|---|---|---|
| Tenant isolation ([[MT-isolation-strategy]]) | A.8.3, A.5.15, A.8.31 | CC6.1, C1.1 | DPDP s.8(5); GDPR Art. 32 |
| Data classification ([[SEC-data-classification]]) | A.5.12, A.5.13, A.5.10 | C1.1 | GDPR Art. 32 |
| Access reviews ([[SEC-access-reviews]]) | A.5.15, A.5.16, A.5.18, A.8.2 | CC6.1, CC6.2, CC6.3 | GDPR Art. 32 |
| Vulnerability management ([[SEC-vulnerability-management]]) | A.8.8, A.8.29, A.5.7 | CC7.1 | GDPR Art. 32(1)(d) |
| Vendor management ([[SEC-vendor-sub-processor-management]]) | A.5.19–A.5.23 | CC9.2 | GDPR Art. 28; DPDP s.8(2); PDPA transfer limitation |
| Incident response ([[SEC-security-incident-response-and]]) | A.5.24–A.5.28, A.6.8 | CC7.3, CC7.4, CC7.5 | DPDP s.8(6) and Rule 7; GDPR Arts 33–34; PDPA Part 6A; CERT-In Directions |
| Business continuity ([[SEC-business-continuity]]) | A.5.29, A.5.30, A.8.13, A.8.14 | A1.2, A1.3, CC9.1 | — |
| Privacy controls ([[SEC-privacy-controls]]) | A.5.34, A.5.33, A.8.10, A.8.11 | P1–P8 (if Privacy in scope) | DPDP ss.5–6, 8, 11–14; GDPR Arts 5, 12–22, 30 |
| Logging and monitoring ([[OBS-foundations]], [[OBS-security-events]]) | A.8.15, A.8.16, A.8.17 | CC7.2 | CERT-In log retention; DPDP Rule 6 |
| Secure development ([[DEP-ci-cd-pipelines-build-test]], [[TST-security-testing]]) | A.8.25–A.8.29, A.8.32 | CC8.1 | — |
| Secrets and cryptography ([[INF-secrets-and-keys]], [[PKG-encryption-utilities-key]]) | A.8.24 | CC6.1, CC6.7 | DPDP Rule 6 (encryption, masking) |
| Authentication ([[PKG-authentication]]) | A.5.17, A.8.5 | CC6.1 | — |
| AI governance ([[AI-ai-governance-and-impact]]) | A.5.1 (policy), ISO/IEC 42001 separately | — | — |

<!-- section:description -->
## Control description

1. **Scope.** The ISMS scope statement names the entities (NTPL, TAPL, US entity), locations (Bangalore office, remote staff, cloud regions in India, Singapore, US, and Azure regions where used), products (TERES, CORD and the shared platform) and interfaces with tenants and sub-processors. Reviewed at each management review.
2. **Risk assessment.** Asset-based and scenario-based risk assessment using a 5 × 5 likelihood × impact matrix (proposed), run at least annually and on major change (new region, new product, new sub-processor category). Output: risk register with owner, treatment, residual risk and acceptance by the risk owner.
3. **Statement of Applicability.** For each Annex A control: applicable or not, justification, implementation status and the node(s) that implement it. Kept as a versioned document generated from the control register.
4. **Control register.** One row per control node with framework mappings (table above), owner, frequency, evidence location and last test result. The register is the source for the SoA and for SOC 2 control descriptions.
5. **Policies.** Information security policy plus topic policies (access control, cryptography, supplier security, incident management, secure development, acceptable use, classification, continuity), approved by the CTO, reviewed annually, acknowledged by all staff on joining and annually.
6. **Awareness.** Security and privacy training on joining and annually; phishing simulation quarterly (proposed).
7. **Internal audit.** Annual programme covering all clauses and a rotating third of Annex A each year, by an auditor independent of the area audited (external if the team is too small).
8. **Management review.** At least annually, covering the inputs required by clause 9.3; minutes and actions recorded.
9. **Nonconformity and corrective action.** Logged in the ISMS tracker with root cause, correction, corrective action, owner and due date; effectiveness checked.
10. **SOC 2.** System description and control matrix derived from the same register; complementary user entity controls (what tenants must do, for example manage their own users and SSO) and complementary subservice organisation controls (AWS, Azure) documented.

<!-- section:owner -->
## Owner and frequency

| Role | Responsibility |
|---|---|
| CTO | Top-management sponsor; approves policies, scope, risk acceptance above threshold |
| ISMS lead | Operates the ISMS: register, SoA, risk process, evidence, audits liaison |
| Backup | Platform engineering lead (technical controls), DPO (privacy) |
| Control owners | Named per control node |

Frequency: risk assessment annual and on change; SoA review annual; internal audit annual; management review annual; register review quarterly; evidence collection continuous.

<!-- section:evidence -->
## Evidence

| Evidence | Produced by | Stored in | Retention |
|---|---|---|---|
| Scope statement, policies, SoA (versioned) | ISMS lead | Document management system, read-only after approval | 3 years after superseded (proposed) |
| Risk register exports per quarter | ISMS tracker | Evidence repository | 3 years |
| Control test results (CI artefacts, nightly RLS checks, scanner exports, access reviews) | Systems | Evidence repository, organised by control id and period | 3 years |
| Training completion records | HR / LMS | Evidence repository | 3 years after leaving |
| Internal audit reports, management review minutes, corrective actions | ISMS lead | Evidence repository | 3 years |
| SOC 2 and ISO audit reports | Auditors | Evidence repository; shared with clients under NDA | 5 years |

Evidence repository: a dedicated, access-controlled store with write-once retention for closed periods, separate from the production platform.

<!-- section:test -->
## Test procedure

- Internal audit samples each control: for recurring controls, 2 samples for quarterly, 5 for monthly, 25 for daily or more frequent, and 1 for annual controls (proposed sampling, aligned with common SOC 2 practice; final sizes set by the external auditor).
- Design test: walk-through of the control description with the owner; confirm the evidence would show failure if the control did not operate.
- Operating test: inspect samples for the full period; re-perform where possible (for example re-run the RLS catalogue check for a sampled date's schema).
- Methods follow the examine / interview / test approach in [R3].

<!-- section:implementation -->
## Implementation in the platform

Platform features that produce evidence: RLS catalogue and isolation test results ([[MT-safeguards]]), audit trail exports ([[PKG-audit-trail]]), CI pipeline records and approvals ([[DEP-ci-cd-pipelines-build-test]], [[DEP-release-notes-and-change]]), security event dashboards ([[OBS-security-events]], [[RPT-platform-security]]), access review exports from the identity provider and platform admin console, backup and restore drill records ([[INF-backup-and-disaster-recovery]]).

<!-- section:exceptions -->
## Exceptions

Exceptions to a policy or control are raised in the ISMS tracker with: control, scope, reason, compensating control, risk rating, requested duration (maximum 6 months, renewable once), and approval by the control owner and ISMS lead (CTO for high risk). Open exceptions appear in the risk register and the management review.

<!-- section:metrics -->
## Monitoring and KPIs

- Percentage of Annex A controls with evidence for the last period (target 100%).
- Percentage of evidence collected automatically (target 70% or more).
- Open nonconformities by age (none over 90 days).
- Open risk treatments past due.
- Training completion (target 100% within 30 days of due date).

<!-- section:questions -->
## Open questions

- [ ] Confirm ISMS scope: does the first certificate include the US entity and Azure deployments?
- [ ] Is the Privacy category in the first SOC 2 report, or Security, Availability and Confidentiality only?
- [ ] GRC tooling: spreadsheet register for Phase 1, or a compliance automation platform? (Affects automation target.)
- [ ] Internal auditor: in-house with independence safeguards, or outsourced?
- [ ] Merged item "ISO 27001, SOC 2" (from the former Security node) is now covered by Objective and Mapping; remove after review.

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

Entities NTPL, TAPL and the US entity; all production and staging regional stacks (India, Singapore, US, Azure where used); global components (directory, CI/CD, code host, staff identity provider); all staff and contractors with access; all tenants as data owners. The population is identified from the IaC inventory (cloud accounts and subscriptions), the staff directory and the vendor register, reconciled quarterly.

<!-- check:owner -->
### Ownership and accountability

Design: ISMS lead, approved by the CTO. Operation: control owners per node. Cover: platform engineering lead and DPO as named backups. Accountability for ISMS failure: CTO as top-management sponsor.

<!-- check:evidence -->
### Evidence quality and retention

Evidence is generated by systems (CI, scanners, identity provider, ISMS tracker) into an evidence repository organised by control id and period, timestamped and write-once after the period closes, so an auditor can sample without the team recreating anything.

<!-- check:automation -->
### Automation and continuous monitoring

Automated: RLS and role checks, dependency and container scanning, CI change records, cloud configuration checks, access lists exports, backup job results. Manual: risk assessment, management review, access review decisions, supplier assessments, tabletop exercises. Automation is trusted because its own configuration is in code with reviews, and canary tests prove the checks fail when they should (for example the RLS canary in [[MT-safeguards]]).

<!-- check:deficiency -->
### Failures and remediation

A failed control is a nonconformity: logged, rated, corrected and root-caused with an owner and due date; high-rated deficiencies reported to the CTO within 1 working day; if the deficiency caused or could cause a personal data breach, it enters [[SEC-security-incident-response-and]]. Deficiencies that affect a SOC 2 commitment are disclosed to the auditor; client notification follows contract terms.

<!-- check:assurance -->
### Independent assurance

Internal audit annually; ISO certification body (Stage 1, Stage 2, annual surveillance, 3-yearly recertification); SOC 2 auditor annually. The ISMS relies on AWS (and Azure) for physical and infrastructure controls; their SOC 2 / ISO 27001 reports are reviewed annually and the complementary controls we must operate are listed in the system description.

<!-- check:commitments -->
### Legal and client commitments

Client contracts and security questionnaires reference ISO 27001 certification and SOC 2 reports; DPDP s.8(5), GDPR Art. 32 and the PDPA protection obligation require reasonable security safeguards that this ISMS evidences. Narrowing the ISMS scope or dropping a control can breach these commitments, so scope changes need CTO approval and a contract check by legal.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "excerpt": "Clauses 4–10 (ISMS requirements) and Annex A reference controls (93 controls in four themes).",
    "id": "R1",
    "ident": "ISO/IEC 27001",
    "kind": "standard",
    "title": "Information security, cybersecurity and privacy protection — Information security management systems — Requirements",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "excerpt": "Common criteria CC1–CC9 plus Availability (A), Confidentiality (C) and Privacy (P) criteria used in SOC 2 reports.",
    "id": "R2",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  },
  {
    "body": "NIST",
    "excerpt": "Examine, interview and test assessment methods for control effectiveness.",
    "id": "R3",
    "ident": "SP 800-53A",
    "kind": "standard",
    "title": "Assessing Security and Privacy Controls in Information Systems and Organizations",
    "url": "https://csrc.nist.gov/pubs/sp/800/53/a/r5/final",
    "version": "Rev. 5"
  }
]
```

<!-- end -->
