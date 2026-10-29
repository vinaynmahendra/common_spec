---
id: "SEC-security-incident-response-and"
title: "Security incident response and breach notification"
parent: "SEC"
order: 7
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "Incident classification, response roles, evidence handling, and the regulatory clocks (CERT-In, DPDP Board, GDPR, PDPC, client contracts) owned in one place"
links: []
rev: 2
syncHash: "5bc41b5c6db74827"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.7 Security incident response and breach notification

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Incident classification, response roles, evidence handling, and the regulatory clocks (CERT-In, DPDP Board, GDPR, PDPC, client contracts) owned in one place

<!-- section:objective -->
## Control objective

Security incidents and personal data breaches are detected, contained and recovered from quickly, evidence is preserved, and every regulatory and contractual notification is made correctly and on time, by people who know their role before the incident starts.

<!-- section:mapping -->
## Framework mapping

| Framework | Clause |
|---|---|
| ISO/IEC 27001:2022 | A.5.24 Incident management planning and preparation; A.5.25 Assessment and decision on events; A.5.26 Response to incidents; A.5.27 Learning from incidents; A.5.28 Collection of evidence; A.6.8 Information security event reporting; A.5.5 Contact with authorities |
| SOC 2 TSC | CC7.3 (evaluate events), CC7.4 (respond), CC7.5 (recover), CC2.3 (external communication) |
| CERT-In Directions (2022) | Report specified incidents within 6 hours of noticing; point of contact; logs kept 180 days in India; NTP clock sync [R1] |
| DPDP Act s.8(6) and Rules 2025 Rule 7 | Intimate the Data Protection Board and each affected data principal; detailed report to the Board within 72 hours of becoming aware (or longer if the Board allows) [R2] |
| GDPR Arts 33–34 | Controller notifies the supervisory authority within 72 hours where feasible; processor notifies the controller without undue delay; communicate to data subjects where high risk [R3] |
| Singapore PDPA Part 6A | Assess within 30 days; notify PDPC no later than 3 calendar days after determining notifiable; data intermediary notifies the organisation without undue delay [R4] |
| US state breach laws | Vary by state (deadlines, thresholds, regulator notice); assessed per incident by legal |
| Framework guidance | NIST SP 800-61 Rev. 3 [R5] |

<!-- section:description -->
## Control description

**Severity**

| Severity | Definition | Examples | Response |
|---|---|---|---|
| SEV1 | Confirmed or likely exposure of tenant or personal data across tenants or to outsiders; platform-wide outage; active attacker | Cross-tenant data leak, ransomware, leaked database credentials in use | Incident commander within 15 min, 24×7; CTO and legal paged; clocks start |
| SEV2 | Contained exposure affecting one tenant or a small number of people; serious control failure | Misdirected notice to the wrong party, one tenant's documents publicly linked, table found without forced RLS | Commander within 1 hour; legal and DPO within 4 hours |
| SEV3 | Security event with no confirmed data impact | Blocked brute force, malware caught by upload scanning, vulnerability report | Next working day |

**Roles**: Incident commander (on-call platform lead rotation); Technical lead; Communications lead (client and public messaging); Legal and DPO / Grievance Officer (notification decisions and regulator contact); CERT-In point of contact (designated person for NTPL); Scribe (timeline). For a breach of tenant data where Nomology is a processor, the tenant's designated contact is a stakeholder from the start.

**Phases**

1. **Detect and report**: alerts ([[OBS-alerting]], [[OBS-security-events]]), staff reports (anyone can raise via the incident channel or the security@ address), tenant reports, vendor notices. Time of awareness recorded immediately; this starts the clocks.
2. **Triage** (within 30 minutes for SEV1): severity, data classes and tenants affected, regions, whether personal data is involved, initial notification assessment.
3. **Contain**: revoke credentials, disable features via flags, block at WAF, suspend affected integrations, isolate hosts; for a tenant-specific incident, consider suspending the tenant with reason `security` ([[MT-tenant-lifecycle]]).
4. **Preserve evidence**: snapshot affected volumes, export relevant logs and audit trail ranges to the evidence store in the same region, record hashes, maintain chain of custody; do not destroy evidence when eradicating.
5. **Notify** (in parallel with containment; see clock table).
6. **Eradicate and recover**: fix root cause, restore from clean backups where needed ([[INF-backup-and-disaster-recovery]]), monitor for recurrence.
7. **Post-incident review** within 10 working days: blameless write-up, timeline, root cause, actions tracked to closure; lessons fed into the risk register.

**Notification clock table** (owned here, single source; filings mechanics in [[RPT-privacy-and-confidentiality]])

| Who | When | Trigger | Our role | Owner |
|---|---|---|---|---|
| CERT-In | Within 6 hours of noticing | Incident type listed in the Directions (for example data breach, data leak, unauthorised access to systems, attacks on applications) affecting systems in India | Service provider / body corporate | CERT-In point of contact |
| Affected tenant (institution) | Contract deadline; target within 24 hours of awareness (proposed) | Any incident affecting the tenant's data | Processor / data processor | Communications lead + legal |
| DPDP Data Protection Board | Intimation without delay; detailed report within 72 hours | Personal data breach where NTPL is the data fiduciary (for example CORD tenant, own customers) | Data fiduciary | DPO |
| Affected data principals (India) | Without delay | Same, where NTPL is fiduciary | Data fiduciary | DPO + communications |
| Tenant as data fiduciary | Immediately enough for the tenant to meet its 72-hour duty | Breach of tenant's personal data | Data processor | Legal |
| EU supervisory authority | Within 72 hours of awareness where feasible | Breach of EU personal data where Nomology is controller | Controller | DPO |
| Controller (tenant) for EU data | Without undue delay | Nomology is processor | Processor | Legal |
| PDPC Singapore | No later than 3 calendar days after determining notifiable (assessment within 30 days) | Notifiable breach where TAPL (or the tenant) is the organisation | Organisation / data intermediary | DPO |
| US regulators / individuals | Per state law | US residents' data | Varies | Legal |
| SEBI-regulated tenants / MIIs | Per their contracts and circulars (to be confirmed) | Incident affecting their matters | Technology provider | Legal |
| Cyber insurer | Per policy | Any SEV1 / SEV2 | Policyholder | CTO |

Assumption: which entity (NTPL, TAPL, US entity) is the contracting party per tenant determines the notifying entity; to be confirmed by legal per contract.

<!-- section:owner -->
## Owner and frequency

Owner: ISMS lead (process). Incident commander rotation: platform engineering leads (24×7 on-call). Notification decisions: DPO with legal counsel; CTO approves external statements. Backup for DPO: legal counsel. Frequency: per event; runbook review every 6 months; tabletop exercise every 6 months; full simulation annually.

<!-- section:evidence -->
## Evidence

| Evidence | Stored | Retention |
|---|---|---|
| Incident record (timeline, severity, decisions, awareness time, clocks met) | Incident tracker | 5 years (proposed) |
| Breach register (all personal data breaches, including those not notified, with reasoning) | DPO register | 5 years; GDPR Art. 33(5) requires documenting all breaches |
| Copies of notifications sent and acknowledgements | Incident record | 5 years |
| Forensic evidence and chain of custody | Regional evidence store | Per legal advice; minimum 1 year |
| Post-incident reviews and action tracking | Incident tracker | 5 years |
| Tabletop and simulation reports | Evidence repository | 3 years |

<!-- section:test -->
## Test procedure

Auditor inspects all SEV1 / SEV2 incidents in the period and a sample of 10 SEV3 events: severity justified, clocks met, notifications sent with evidence, review done, actions closed. Inspects tabletop records (2 per year) and the on-call rota.

<!-- section:implementation -->
## Implementation in the platform

Detection: [[OBS-security-events]], [[OBS-alerting]]; investigation data: [[PKG-audit-trail]], regional logs per [[OBS-foundations]]; containment levers: [[PKG-feature-flags]], tenant suspension in [[MT-tenant-lifecycle]], session revocation in [[PKG-mfa-session-management-device]], WAF in [[INF-networking]]; filings: [[RPT-privacy-and-confidentiality]]; reporting dashboards: [[RPT-platform-security]].

<!-- section:exceptions -->
## Exceptions

No exceptions to notification duties. Deviations from internal targets (for example tenant notice later than 24 hours) are recorded with reasons in the incident record.

<!-- section:metrics -->
## Monitoring and KPIs

- Time from awareness to triage, containment and each notification (per incident).
- Percentage of statutory clocks met (target 100%).
- Post-incident actions overdue (target 0 older than 30 days).
- Tabletop exercises held (target 2 per year).

<!-- section:questions -->
## Open questions

- [ ] Confirm fiduciary / processor role per product (TERES for institutions, CORD, enterprise) — determines who notifies the DPDP Board and data principals.
- [ ] Contractual tenant notification deadline: 24 hours proposed; check against institutional client contracts.
- [ ] SEBI-related reporting duties for incidents affecting SEBI ODR matters (through MIIs) — legal to confirm.
- [ ] Which person is designated CERT-In point of contact for NTPL?
- [ ] Do we need a retained forensic firm on contract per region?

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

All incidents affecting any Nomology entity, any region, any tenant, staff devices and vendors processing our data. Detection sources and the reporting channel are open to all staff and tenants.

<!-- check:owner -->
### Ownership and accountability

ISMS lead owns the process; the on-call incident commander runs each incident; DPO and legal own notification decisions; CTO is accountable and approves external statements.

<!-- check:evidence -->
### Evidence quality and retention

The incident tracker captures awareness time, decisions and notifications as they happen, so the record is contemporaneous; the breach register includes non-notified breaches with reasoning.

<!-- check:deficiency -->
### Failures and remediation

A missed clock is itself reported (for example a late notice with reasons where the law allows) and treated as a nonconformity with root-cause analysis.

<!-- check:commitments -->
### Legal and client commitments

CERT-In 6 hours; DPDP Board detailed report within 72 hours; GDPR 72 hours; PDPC 3 calendar days after assessment; client contract notice periods. Changing roles, tools or on-call coverage can break these, so changes are tabletop-tested first.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Report specified cyber incidents to CERT-In within 6 hours of noticing them; keep logs of ICT systems for 180 days within Indian jurisdiction; synchronise clocks to NTP servers of NIC or NPL; designate a point of contact.",
    "id": "R1",
    "issuer": "CERT-In, Ministry of Electronics and IT",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under section 70B(6) of the IT Act, 2000 (28 April 2022)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/Directions70B.jsp"
  },
  {
    "excerpt": "Rule 1: Rules 3 and 5–16 come into force eighteen months after publication, Rule 4 after one year. Rule 3 notice; Rule 6 security safeguards including keeping logs for one year; Rule 7 breach intimation to the Board with a detailed report within seventy-two hours; Rule 14(3) grievances answered within a period not exceeding ninety days.",
    "id": "R2",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Digital Personal Data Protection Rules, 2025",
    "title": "Digital Personal Data Protection Rules, 2025 (Gazette notification)",
    "url": "https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf"
  },
  {
    "excerpt": "Art. 12(3) one month to respond to requests (extendable by two months); Arts 13–14 information; Arts 15–22 rights; Art. 28 processors; Art. 30 records; Art. 32 security; Art. 33 notify the supervisory authority within 72 hours; Art. 34 communicate to data subjects; Chapter V transfers.",
    "id": "R3",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU / EEA",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  },
  {
    "excerpt": "Assess a suspected breach within 30 days; notify the PDPC no later than 3 calendar days after determining a breach is notifiable; a data intermediary must notify the organisation without undue delay.",
    "id": "R4",
    "issuer": "Personal Data Protection Commission, Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Guide on Managing and Notifying Data Breaches under the PDPA (15 March 2021)",
    "title": "Guide on Managing and Notifying Data Breaches under the PDPA",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/other-guides/guide-on-managing-and-notifying-data-breaches-under-the-pdpa-15-mar-2021.pdf"
  },
  {
    "body": "NIST",
    "excerpt": "Aligns incident response with the CSF 2.0 functions (Govern, Identify, Protect, Detect, Respond, Recover).",
    "id": "R5",
    "ident": "SP 800-61",
    "kind": "standard",
    "title": "Incident Response Recommendations and Considerations for Cybersecurity Risk Management",
    "url": "https://csrc.nist.gov/pubs/sp/800/61/r3/final",
    "version": "Rev. 3 (2025)"
  }
]
```

<!-- end -->
