---
id: "RPT-platform-security"
title: "Platform security"
parent: "RPT"
order: 5
type: "capability"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Security posture and incident reporting: denied and anomalous access, incidents by severity and status, vulnerability SLAs and access reviews, for management, auditors and tenants"
links: []
rev: 2
syncHash: "d0d904537238e91a"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.5 Platform security

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Security posture and incident reporting: denied and anomalous access, incidents by severity and status, vulnerability SLAs and access reviews, for management, auditors and tenants

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Security lead / ISMS manager | weekly | Q1 How many unauthorised-access attempts and anomalies occurred, where, and were they handled? Q2 Which incidents are open and are we inside their response and notification clocks? |
| Management / ISMS review | monthly, quarterly | Q3 Are vulnerability remediation SLAs met? Q4 Are access reviews done on time? |
| Auditors (ISO 27001, SOC 2) | per audit | Evidence for monitoring, incident and vulnerability controls |
| Tenant security contact | monthly or on request | Q5 What security events and support access affected our tenant? |

<!-- section:metrics -->
## Metric definitions

Sources: [[OBS-security-events]], [[SEC-security-incident-response-and]], [[SEC-vulnerability-management]], [[SEC-access-reviews]], [[PKG-support-access-and-impersonation]].

| ID | Metric | Formula | Grain |
|---|---|---|---|
| SECR-M1 | Denied access events | count of `security.access_denied` (authorisation failures) | region × tenant × day |
| SECR-M2 | Cross-tenant access attempts | count of requests where resolved tenant ≠ resource tenant (blocked) | region × day; any non-zero is reviewed |
| SECR-M3 | Failed sign-ins / lockouts | count by method (password, OTP, SSO) | tenant × day |
| SECR-M4 | Incidents | count by severity and status; time to contain | region × month |
| SECR-M5 | Notification clocks | per incident: required notifications, deadline, sent time (from incident record) | incident |
| SECR-M6 | Vulnerability SLA | open findings by severity past SLA | month |
| SECR-M7 | Access review completion | reviews done on time ÷ due | quarter |
| SECR-M8 | Support access sessions | count and duration of tenant-approved support access and impersonation | tenant × month |

<!-- section:dimensions -->
## Dimensions and filters

Region, tenant, event type, severity, source (WAF, app, auth), period.

<!-- section:freshness -->
## Freshness and delivery

Security operations works in the SIEM in real time; this report is daily with weekly and monthly packs.

<!-- section:lineage -->
## Data sources and lineage

Security events from regional log pipelines → daily aggregates; incident records from the incident register; findings from scanners. India-region security logs stay in India for the CERT-In retention period [R2].

<!-- section:quality -->
## Data quality and reconciliation

Aggregates reconcile to SIEM counts per day; every incident in the register appears in SECR-M4.

<!-- section:access -->
## Access and privacy

Security lead and ISMS manager: all. Management: aggregated packs. Tenant security contact: SECR-M1, M3, M8 and incidents affecting their tenant, through the tenant view; IP addresses shown truncated.

<!-- section:questions -->
## Open questions

- [ ] Which incident details tenants see, and how this aligns with contractual incident notices
- [ ] Is the SIEM per region or central (affects residency of security logs)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant users query `rpt.*` as `rpt_tenant_reader` with `app.tenant_id` set per transaction through the same Prisma extension as the app ([[MT-prisma-client-extension-wraps]]); every table behind this report carries `tenant_id` with forced RLS [R1], so isolation does not depend on a WHERE clause. With no tenant set the query returns zero rows (tested). Nomology staff use the separate platform view under `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]). Export and email jobs carry `tenantId` in the BullMQ job payload and re-set the tenant before querying; cache keys are prefixed `rpt:{tenantId}:` ([[PKG-caching]]). The cross-tenant suite in [[TST-multi-tenant-isolation-tests]] logs in as tenant A and asserts no tenant B row in any metric, drill-down or export.

<!-- check:residency -->
### Residency and cross-region figures

Security events are aggregated in each region; India-region raw logs remain in India for 180 days as required by CERT-In directions [R2]. Cross-region views use counts only.

<!-- check:security -->
### Access, privacy and export

This report itself is sensitive: access limited to security roles; tenant view only shows that tenant's events; IPs truncated; exports audited.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security; ALTER TABLE ... FORCE ROW LEVEL SECURITY makes policies apply to the owner as well.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  },
  {
    "excerpt": "Cyber incidents of the listed types must be reported to CERT-In within 6 hours of noticing; logs of ICT systems must be maintained for a rolling period of 180 days within Indian jurisdiction.",
    "id": "R2",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and Information Technology",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under section 70B(6) of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  }
]
```

<!-- end -->
