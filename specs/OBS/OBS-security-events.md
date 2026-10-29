---
id: "OBS-security-events"
title: "Security events"
parent: "OBS"
order: 5
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Security event vocabulary (authentication, authorization, cross-tenant blocks, impersonation, exports, files, network), write-once regional storage, SIEM feed and detections"
links: []
rev: 2
syncHash: "b1b3a4198a35a4e3"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.5 Security events

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Security event vocabulary (authentication, authorization, cross-tenant blocks, impersonation, exports, files, network), write-once regional storage, SIEM feed and detections

<!-- section:purpose -->
## Purpose

Records security-relevant events from the application and infrastructure so the security team can detect attacks, investigate incidents and show auditors that monitoring works (ISO 27001:2022 Annex A logging and monitoring controls [R1]; SOC 2 monitoring criteria). Feeds detections, [[SEC-security-incident-response-and]] and [[RPT-platform-security]].

Distinct from the audit trail ([[PKG-audit-trail]]): the audit trail is the tenant-visible legal record of actions on cases; security events are the security team's record of attacks and control failures. Some actions (role change, impersonation) appear in both, emitted by the same code path, and the audit trail is the system of record for *what changed*, the security log for *detection and investigation*.

<!-- section:catalogue -->
## Event catalogue

Names follow the OWASP logging vocabulary where one exists [R2], prefixed `nomo.sec.`.

| Event | When | Emitter | Key attributes | PII |
|---|---|---|---|---|
| `nomo.sec.authn_login_success` / `_fail` | Sign-in attempt (password, magic link, OTP, SSO) ([[PKG-authentication]]) | Auth package | `auth.method`, `failure.reason` (enum), `nomo.user.id` (if known), `client.address`, `user_agent.original` | IP, user agent |
| `nomo.sec.authn_login_lock` | Account locked after repeated failures | Auth | `nomo.user.id`, `lock.duration_s` | Pseudonymous |
| `nomo.sec.authn_mfa_changed` | MFA enrolled, removed or reset | Auth | `mfa.type`, `change` (enum), `actor.user.id` | Pseudonymous |
| `nomo.sec.session_revoked` | Session or token revoked | Auth | `reason` (enum) | Pseudonymous |
| `nomo.sec.authz_fail` | Permission denied by policy engine ([[PKG-policy-engine-permission-matrix]]) | Authorization | `permission`, `resource.type`, `nomo.persona` | No |
| `nomo.sec.tenant_cross_access_blocked` | Tenant mismatch: request tenant ≠ session tenant, or Postgres `42501` from RLS `WITH CHECK` | Middleware / data-access | `requested.tenant.id`, `nomo.tenant.id`, `resource.type` | No |
| `nomo.sec.ethical_wall_block` | Access blocked by an ethical wall ([[PKG-ethical-walls-conflict-based]]) | Authorization | `case.id`, `wall.id` | No |
| `nomo.sec.privilege_changed` | Role or permission granted / removed | Admin | `role`, `change`, `target.user.id`, `actor.user.id` | Pseudonymous |
| `nomo.sec.impersonation_started` / `_ended` | Support access or "view as" ([[PKG-support-access-and-impersonation]]) | Support access | `support.grant.id`, `target.user.id`, `actor.user.id`, `approved_by` | Pseudonymous |
| `nomo.sec.break_glass_used` | Break-glass role assumed (cloud or app) | IAM / platform admin | `scope`, `ticket.id`, `actor` | Pseudonymous |
| `nomo.sec.bulk_export` | Export of > 500 records or > 100 documents | Reporting / documents | `export.type`, `record.count`, `nomo.tenant.id` | No |
| `nomo.sec.api_key_created` / `_revoked` / `_used_new_origin` | API key lifecycle or use from a new network | API platform ([[INT-api-platform-tables]]) | `api.client.id`, `client.address` | IP |
| `nomo.sec.upload_rejected` | Malware found or type blocked ([[PKG-encryption-at-rest-signed-urls]]) | Storage | `reason`, `document.kind`, `scanner.signature` | No |
| `nomo.sec.webhook_signature_invalid` | Inbound webhook fails signature check | Integrations | `provider` | No |
| `nomo.sec.rate_limited` | Request blocked by app rate limit | Rate limiter | `limit.key` (enum), `client.address` | IP |
| Infrastructure sources | CloudTrail, GuardDuty findings, WAF blocks, VPC flow logs, egress firewall drops, Postgres connection / auth logs, Temporal operator actions ([[INF-temporal#security]]) | Cloud services | Native fields | Varies |

Common attributes: `event.outcome` (`success`, `failure`), `nomo.tenant.id`, `cloud.region`, `trace_id`, timestamp in UTC from synchronised clocks.

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels |
|---|---|---|---|
| `nomo.sec.events` | Counter | `{event}` | `event.name`, `event.outcome` |
| `nomo.sec.login_failures` | Counter | `{attempt}` | `auth.method`, `failure.reason` |
| `nomo.sec.cross_tenant_blocks` | Counter | `{block}` | `resource.type` |

Per-tenant and per-user analysis happens in the SIEM, not in metric labels.

<!-- section:alerts -->
## Alerts

Detections (proposed starting set, tuned after a month in report-only mode):

| Detection | Severity | Route |
|---|---|---|
| Any `tenant_cross_access_blocked` from a signed-in user (not a test) | High → security on-call page | May indicate an isolation bug or an attack; also a possible breach trigger |
| > 20 login failures for one account in 10 min, or > 200 from one IP | Medium → ticket + automatic lock / block | |
| Successful login after many failures from a new country | Medium | |
| `bulk_export` volume > 5× tenant baseline in 24 h | High → page | Possible exfiltration |
| `break_glass_used` | Notify security lead immediately | Always reviewed |
| `impersonation_started` without a valid grant | Critical → page | Control failure |
| GuardDuty high-severity finding | High → page | |
| Console write by a human role in production | Medium → ticket | See [[INF-cloud-and-iac]] |
| Security log ingestion stopped for a region for 15 min | High → page | Monitoring blind spot |

Every High / Critical alert opens an incident record and starts the triage in [[SEC-security-incident-response-and]], where the clocks for CERT-In (6 hours [R3]), the DPDP Board, GDPR and PDPC and client contracts are owned.

<!-- section:dashboards -->
## Dashboards

- **Security overview** per region: authentication outcomes, authorization denials, cross-tenant blocks, exports, malware detections. Audience: security team.
- **Tenant security summary** (feeds [[RPT-platform-security]]): counts only, for client security reviews.

<!-- section:pipeline -->
## Collection pipeline

- Application security events are emitted through `@nomology/telemetry` `securityEvent()` and routed by the collector to a **separate security log store** per region; they are not subject to tail sampling or debug-level toggles.
- Store: S3 bucket in the regional log archive account with Object Lock (compliance mode), plus a searchable index in the SIEM in the same region. Engineers whose actions are recorded have no delete rights.
- Infrastructure sources (CloudTrail, GuardDuty, WAF, flow logs) go to the same regional log archive ([[INF-cloud-and-iac]]).
- Clocks: all hosts use the cloud provider's time sync service; events carry UTC timestamps. CERT-In asks for synchronisation to NIC / NPL NTP servers or traceable sources [R3]; whether the provider service satisfies this is an open question for India.

<!-- section:retention -->
## Retention and privacy

| Store | Retention (proposed) | Reason |
|---|---|---|
| Security log store (write-once) | 2 years | ISO 27001 / SOC 2 evidence and investigations |
| SIEM searchable index | 13 months | Detection and audit sampling |
| India region | At least 180 days within India, as a floor [R3] | CERT-In |

Security events contain IP addresses and user agents, which are personal data: access restricted to the security team, every query logged, quarterly access review ([[SEC-access-reviews]]). Retention to be confirmed against the retention schedule ([[PKG-retention-and-deletion-schedule]]).

<!-- section:questions -->
## Open questions

- [ ] SIEM choice per region (must store in-region).
- [ ] Is the cloud provider's time sync acceptable for CERT-In clock synchronisation in India, or do we configure NIC / NPL NTP sources?
- [ ] Two-year retention for security logs: confirm with legal and ISMS policy.
- [ ] Do client contracts require us to share security events or notify them of specific detections within set times?
- [ ] Who staffs security on-call outside India business hours?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Every event carries `nomo.tenant.id`; cross-tenant attempts carry both the requested and the session tenant so investigations can see which tenants were involved. Tenant-facing summaries in Reporting show counts for that tenant only.

<!-- check:naming -->
### Naming and schema

Event names follow the OWASP logging vocabulary [R2] with the `nomo.sec.` prefix and are registered like all other events.

<!-- check:privacy -->
### Personal and confidential data

IP addresses and user agents are allowed only in security events, which are stored separately with access limited to the security team and every query logged. No case content or document data; user IDs are pseudonymous.

<!-- check:actionability -->
### Alerts and response

High and Critical detections page security on-call and open an incident in [[SEC-security-incident-response-and]], which owns the CERT-In 6-hour and other regulatory clocks [R3]. Detections start in report-only mode for a month to tune noise. A loss of security log ingestion is itself a paging alert.

<!-- check:retention -->
### Retention and residency

Two years write-once, 13 months searchable, at least 180 days in India [R3], all in-region; to be confirmed against the retention schedule.

<!-- check:security -->
### Security and audit signals

The catalogue covers sign-in success / failure, MFA changes, role changes, cross-tenant blocks (including RLS `WITH CHECK` failures), ethical-wall blocks, impersonation, break-glass, bulk exports, API key use, malware and webhook signature failures, plus cloud sources. Events go to a write-once regional store that the recorded engineers cannot alter, feed SIEM detections, and use synchronised UTC clocks. They provide evidence for ISO 27001 Annex A logging, monitoring and clock synchronisation controls [R1].

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "excerpt": "Annex A includes controls on logging (8.15), monitoring activities (8.16), clock synchronisation (8.17), backup (8.13) and ICT readiness for business continuity (5.30).",
    "id": "R1",
    "ident": "ISO/IEC 27001",
    "kind": "standard",
    "title": "Information security management systems — Requirements",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "excerpt": "A standard vocabulary for security events, e.g. authn_login_fail, authz_fail, privilege_permissions_changed.",
    "id": "R2",
    "kind": "web",
    "publisher": "OWASP",
    "title": "OWASP Logging Vocabulary Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Vocabulary_Cheat_Sheet.html"
  },
  {
    "excerpt": "Reportable cyber incidents to be reported to CERT-In within 6 hours of noticing; logs of ICT systems to be maintained securely for a rolling period of 180 days within Indian jurisdiction; clocks to be synchronised to NTP servers of NIC/NPL or traceable sources.",
    "id": "R3",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and IT, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under sub-section (6) of section 70B of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  }
]
```

<!-- end -->
