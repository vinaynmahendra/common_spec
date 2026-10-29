---
id: "SEC-access-reviews"
title: "Access reviews"
parent: "SEC"
order: 5
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "Periodic access reviews for Nomology and a tenant access review feature, least privilege with JIT instead of standing privilege, and reviewed break-glass"
links: []
rev: 4
syncHash: "806bd21e5a082a8e"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 13.5 Access reviews

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Periodic access reviews for Nomology and a tenant access review feature, least privilege with JIT instead of standing privilege, and reviewed break-glass

<!-- section:objective -->
## Control objective

Only the right people and software hold access to production systems, privileged roles and tenant data, for only as long as they need it; unused or inappropriate access is found and removed within a quarter at most; standing privilege is replaced by just-in-time elevation; and emergency access is used rarely, visibly and reviewed every time. The control covers Nomology's own access (operated by Nomology) and gives tenants a product feature to review their own users (operated by tenants as a complementary user entity control).

<!-- section:mapping -->
## Framework mapping

| Framework | Clause |
|---|---|
| ISO/IEC 27001:2022 | A.5.15 Access control; A.5.16 Identity management; A.5.18 Access rights; A.8.2 Privileged access rights; A.8.18 Use of privileged utility programs; A.5.3 Segregation of duties [R1] |
| SOC 2 TSC | CC6.1, CC6.2 (registration and authorisation, removal), CC6.3 (role-based access, least privilege, periodic review) [R2] |
| NIST SP 800-53 Rev. 5 (design reference) | AC-2 account management including reviews; AC-6(7) review of user privileges [R3] |
| DPDP Act / GDPR / PDPA | Reasonable security safeguards (DPDP s.8(5); access control measures in the DPDP Rules, 2025, rule 6 — assumption on rule number, to be confirmed by legal); GDPR Art. 32; PDPA protection obligation (s.24) |

<!-- section:description -->
## Control description

**Populations reviewed**

| Population | System of record | Reviewer | Frequency |
|---|---|---|---|
| Staff accounts in the workforce identity provider | Staff IdP | Line manager | Quarterly |
| Cloud console / IAM roles per region (AWS accounts, Azure subscriptions) | IaC + cloud IAM export | Platform engineering lead | Quarterly |
| Database roles with human access (`nomo_platform_ops` break-glass, read replicas for engineers) | IaC + database role export | ISMS lead | Quarterly |
| Temporal UI / Codec Server access, Redis, observability tools | Tool exports | Platform engineering lead | Quarterly |
| Code host: org owners, admins, repository write, CODEOWNERS | Code host export | Engineering lead | Quarterly |
| CI/CD deploy permissions and secrets access | CI export | Engineering lead | Quarterly |
| Platform staff roles and **eligibilities** (`platform_owner`, `platform_admin`, `platform_support`, `platform_security`, `platform_billing`, `regional_ops`) in each region's platform tenant | Platform access review campaign (product feature below) | CTO | Quarterly |
| Staff elevations and application break-glass in the platform tenant ([[PKG-jit-and-break-glass]]) | Elevation and break-glass registers | ISMS lead | Monthly |
| Active support-access grants to tenants ([[PKG-support-access-and-impersonation]]) | Platform | ISMS lead | Monthly (normally zero open) |
| Nomology-owned non-human principals (system purposes, platform service accounts) | Catalogue `system.yaml` + platform tenant | Security lead | Quarterly |
| Tenant users, roles, eligibilities, non-human principals | Tenant access review campaigns | **Tenant reviewers** (complementary user entity control) | Per `access.review.frequency` (default quarterly) |

**Joiner / mover / leaver (Nomology staff)**

1. Joiner: access requested by ticket with role template; approved by manager and system owner; provisioned through IdP groups (no direct grants). Platform roles above `platform_support` tier 1 are granted as eligibilities, not standing assignments.
2. Mover: role change triggers removal of old group memberships within 5 working days.
3. Leaver: HR offboarding triggers IdP deactivation on the last working day (same day for involuntary leavers); downstream access removed automatically through SSO; non-SSO accounts (break-glass, vendor consoles) checked within 1 working day.

**Tenant access review feature** (product; screens in [[APP-user-and-access-admin]], data in `authz_access_review_campaign` and `authz_access_review_item`, [[PKG-authorization-data-model]]). Pattern borrowed from: recurring access review campaigns with reviewer assignment, recommendations and auto-apply in Microsoft Entra ID Governance [R4].

1. A campaign is created automatically per `access.review.frequency`, or manually by a security_admin (`access.review:create`). Population per `access.review.population`: assignments of tenant roles (direct and via group), eligibilities, custom roles flagged "admin with case access", toxic-combination exceptions, non-human principals (owner attestation), and case roles of external users on open cases only where `all` is chosen.
2. Each item is snapshotted (principal, role, scope, source, granted by, last used date from audit, risk flags: privileged, unused for `access.review.inactive_days_flag` days, toxic combination, orphaned owner).
3. Reviewers are assigned by `access.review.reviewer_rule`; a reviewer never reviews their own access (falls to security_admin).
4. Reviewers decide keep / change / remove with a reason, within `access.review.duration_days`; reminders at 50% and 80% of the window; the platform recommends "remove" for unused items.
5. On close, removals are applied automatically through the normal assignment API (one change set, with maker-checker where privileged); no-response items are removed only if `access.review.auto_remove_on_no_response` (never for case roles).
6. The campaign report (decisions, applied removals, exceptions) is exported as evidence for the tenant's own audits.

**Nomology's periodic review steps**

1. ISMS lead generates exports for each population on the first working day of the quarter (platform populations come from the platform campaign).
2. Reviewers mark each entry keep / change / remove with a reason, within 10 working days.
3. Removals completed within 5 working days of the decision and verified against a fresh export.
4. Exceptions (shared accounts, service accounts with human use) recorded.

**Least privilege rules (Nomology)**: no standing production database access for engineers; production read access through just-in-time grants of up to 8 hours with ticket reference; production write and `nomo_platform_ops` only via break-glass; platform roles eligible-only except two named platform_owners; MFA (WebAuthn) for every staff account; privileged actions only from managed devices.

**Infrastructure break-glass (Nomology)** (application-level break-glass is in [[PKG-jit-and-break-glass]]):

1. Operator opens a break-glass request stating incident or ticket, scope (region, system) and expected duration.
2. Second person (CTO, platform lead or ISMS lead) approves; in a P1 incident approval can be given after the fact within 24 hours.
3. Short-lived credentials issued (maximum 4 hours), session recorded (commands and SQL statements logged).
4. Alert sent to the security channel when the credentials are issued (`nomo.sec.break_glass_used`, [[OBS-security-events]]).
5. Within 2 working days the ISMS lead reviews the session log and closes the record; any tenant data accessed is assessed for notification duties under the tenant contract.

<!-- section:owner -->
## Owner and frequency

Owner: ISMS lead. Backup: platform engineering lead. Accountable: CTO (also reviews the ISMS lead's own access). Reviewers as in the population table. Frequency: quarterly reviews; monthly support-grant, elevation and break-glass review; per-event break-glass review; leaver checks per event. Tenant campaigns: owned by each tenant's security_admin; Nomology owns the feature and its correctness.

<!-- section:evidence -->
## Evidence

| Evidence | Stored | Retention |
|---|---|---|
| Quarterly exports per population (raw) | Evidence repository (in region for regional systems) | 3 years |
| Review decisions with reviewer, timestamp, reason (Nomology) | ISMS tracker; platform campaign items | 3 years |
| Removal tickets and post-removal exports | ISMS tracker / evidence repository | 3 years |
| Joiner / leaver tickets linked to HR records | ITSM | 3 years after leaving |
| Elevation register (platform tenant) | `authz_elevation` + audit trail | 7 years |
| Break-glass requests, approvals, session logs, reviews | ISMS tracker + log archive (in region); application break-glass in `authz_break_glass_event` | 3 years (session logs 1 year minimum; India logs also kept in India for 180 days under CERT-In directions) |
| Tenant campaign reports | Tenant's region, downloadable by the tenant | 3 years after close |

<!-- section:test -->
## Test procedure

- Quarterly reviews: auditor samples 2 quarters, checks completeness against independent exports and that removals were done.
- Leavers: sample 25 leavers (or all if fewer) and check deactivation date against HR last day.
- Break-glass: inspect all events in the period (expected few) for approval, duration and review.
- Elevations: sample 25 staff elevations for justification, approver distinct from requester, and duration within maximum.
- Tenant feature (for SOC 2 description of the system): demonstrate a campaign end to end in a test tenant and show that removals were applied.

<!-- section:implementation -->
## Implementation in the platform

Staff IdP groups mapped to cloud roles via IaC ([[INF-cloud-and-iac]]); database roles and just-in-time grants ([[MT-separate-privileged-role-used]]); platform roles, eligibilities and break-glass ([[PKG-roles-and-permission-sets]], [[PKG-jit-and-break-glass]]); support access ([[PKG-support-access-and-impersonation]], [[APP-platform-admin-and-support]]); non-human principals ([[PKG-non-human-principals]]); tenant access review campaigns ([[APP-user-and-access-admin]], [[PKG-authorization-data-model]]); settings ([[PKG-settings-access-control]] `access.review.*`); security events for privilege use ([[OBS-security-events]]); reporting ([[RPT-platform-security]]).

<!-- section:exceptions -->
## Exceptions

Shared or non-SSO accounts that cannot be removed (for example a cloud root account) are held under break-glass with hardware MFA, credentials in a sealed vault and quarterly verification; each is listed in the exception register. Toxic-combination exceptions follow [[PKG-separation-of-duties]] (maximum 90 days) and appear in every review until they expire.

<!-- section:metrics -->
## Monitoring and KPIs

- Review completion within 10 working days (target 100%), Nomology and per tenant (tenant figure reported to the tenant).
- Leavers deactivated by end of last day (target 100%).
- Standing privileged assignments outside the named exceptions (target zero; JIT instead).
- Break-glass events per quarter and percentage reviewed within 2 working days (target 100%).
- Removals applied within 5 working days of decision (target 100%).
- Non-human principals without an active owner (target zero).

<!-- section:questions -->
## Open questions

- [x] Should tenant admins be prompted by the platform to run their own access review? Decided: yes, automatic campaigns per `access.review.frequency`.
- [ ] Choose the just-in-time tool for infrastructure access (cloud-native, or a dedicated access broker); application JIT is built in ([[PKG-jit-and-break-glass]]). (Platform lead)
- [ ] Confirm DPDP Rules 2025 rule number for reasonable security safeguards. (Legal)
- [ ] Should tenant campaigns include external parties and counsel on open cases by default for court programmes? (Product)

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

All Nomology staff and contractors, all service accounts with human use, Nomology-owned non-human principals, all production regions and tools in the population table, reconciled against the HR roster and the IaC inventory each quarter. For tenants: every assignment, eligibility and non-human principal in the tenant, per the configured population.

<!-- check:owner -->
### Ownership and accountability

ISMS lead owns design and runs the cycle; reviewers own decisions for their population; platform engineering lead covers; CTO accountable and reviews the ISMS lead's access. Tenant security_admins own tenant campaigns.

<!-- check:evidence -->
### Evidence quality and retention

Raw exports, campaign snapshots, decisions and removal verification are stored per quarter so an auditor can re-perform the comparison; tenant campaign reports are exportable.

<!-- check:automation -->
### Automation and continuous monitoring

Exports, campaign creation, snapshots, recommendations, reminders, removal application, leaver deactivation via HR-to-IdP sync, short-lived credentials, elevation expiry and break-glass alerts are automated; review decisions remain human by design.

<!-- check:deficiency -->
### Failures and remediation

Late reviews escalate to the CTO (Nomology) or tenant_owners (tenant); an inappropriate grant found in review is removed and logged as a finding with root cause; misuse found in break-glass review becomes a security incident ([[SEC-security-incident-response-and]]).

<!-- check:exceptions -->
### Exceptions and risk acceptance

Non-removable accounts are listed with compensating controls (hardware MFA, sealed credentials, quarterly verification) and approved by the ISMS lead for a maximum of 6 months at a time; SoD exceptions are capped at 90 days.

<!-- check:assurance -->
### Independent assurance

Tested by internal audit annually and by the ISO 27001 certification and SOC 2 Type II auditors; relies on the cloud providers' IAM for infrastructure populations.

<!-- check:commitments -->
### Legal and client commitments

Client security schedules typically require least privilege and prompt revocation; tenant contracts may require notification when Nomology staff access tenant data, which support-access and break-glass records support; SOC 2 reports describe tenant access reviews as a complementary user entity control.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "id": "R1",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R2",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  },
  {
    "body": "NIST",
    "id": "R3",
    "ident": "SP 800-53 Rev. 5",
    "kind": "standard",
    "title": "NIST SP 800-53 Rev. 5, Security and Privacy Controls for Information Systems and Organizations (AC-2, AC-5, AC-6)",
    "url": "https://csrc.nist.gov/pubs/sp/800/53/r5/final",
    "version": "Rev. 5"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "Microsoft Learn: What are access reviews? (Microsoft Entra ID Governance)",
    "url": "https://learn.microsoft.com/en-us/entra/id-governance/access-reviews-overview",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
