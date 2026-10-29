---
id: "SEC-vendor-sub-processor-management"
title: "Vendor / sub-processor management"
parent: "SEC"
order: 6
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "5083e3c4a405a71c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.6 Vendor / sub-processor management

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:objective -->
## Control objective

Every third party that processes tenant or personal data, or that the platform depends on, is assessed before use, bound by a contract with the security and privacy terms our own obligations require, recorded with its processing locations, and monitored; tenants are told about sub-processors before they are used, and no personal data leaves a region without a recorded basis.

<!-- section:mapping -->
## Framework mapping

| Framework | Clause |
|---|---|
| ISO/IEC 27001:2022 | A.5.19 Information security in supplier relationships; A.5.20 Addressing information security within supplier agreements; A.5.21 Managing information security in the ICT supply chain; A.5.22 Monitoring, review and change management of supplier services; A.5.23 Information security for use of cloud services |
| SOC 2 TSC | CC9.2 (vendor and business partner risk), CC3.4 |
| GDPR | Art. 28(2) and (4) (sub-processor authorisation and flow-down), Art. 28(3) contract terms, Chapter V transfers [R1] |
| DPDP Act | s.8(2) data fiduciary may engage a processor only under a valid contract [R2] |
| PDPA | Transfer limitation obligation (comparable protection) [R3]; data intermediary obligations |

<!-- section:description -->
## Control description

**Vendor register.** One entry per vendor with: service, owner, data classes processed ([[SEC-data-classification]]), regions and countries of processing and support access, sub-processor of whom (which tenants / products), criticality (critical / high / low), contract and DPA status, certifications (ISO 27001, SOC 2), last assessment date, exit plan.

**Expected sub-processor categories** (actual vendors to be selected): cloud hosting (AWS, Azure where required), email delivery, SMS and WhatsApp messaging per region ([[INT-messaging-providers]]), video conferencing ([[INT-video-conferencing-for-hearings]]), e-signature ([[INT-e-signature]]), KYC and sanctions screening ([[INT-kyc-and-sanctions-screening]]), payment gateways ([[BIL-payment-gateway-integration]]), AI model providers ([[AI-ai-gateway]]), transcription services, error monitoring, support desk.

**Lifecycle**

1. **Request**: the business owner submits the vendor, purpose, data classes and regions.
2. **Assess** (before any data flows): security questionnaire or review of the vendor's ISO 27001 certificate / SOC 2 report; privacy review by the DPO including processing locations and onward sub-processors; transfer assessment where personal data would leave the tenant's region or the data's origin jurisdiction; for AI providers, data use and retention terms (no training on our data).
3. **Contract**: DPA with processor terms (instructions, confidentiality, security, sub-processor flow-down, assistance with rights and breaches, deletion or return at end, audit), breach notification to us within a set period (target 24–48 hours, proposed), and data location commitments. GDPR Standard Contractual Clauses where EU personal data is transferred.
4. **Notify tenants**: update the public sub-processor list per product and region; give tenants advance notice (30 days proposed, or the period in their contract) with the right to object as their DPA provides.
5. **Onboard technically**: credentials in the regional secrets manager; regional endpoints configured; data minimised to what the vendor needs.
6. **Monitor**: annual reassessment for critical and high vendors (biennial for low); track certificate expiry; watch for vendor incidents; review the vendor's sub-processor changes.
7. **Offboard**: revoke credentials, obtain deletion confirmation, update the list, notify tenants if relevant.

**Inbound obligations.** The same register records obligations clients impose on us (client DPAs, security schedules), so that a change of vendor is checked against them.

<!-- section:owner -->
## Owner and frequency

Owner: ISMS lead (process) with the DPO (privacy and transfer assessment). Backup: legal counsel. Business owners per vendor. Frequency: per new vendor; annual reassessment for critical / high; quarterly register review; sub-processor list updated on every change.

<!-- section:evidence -->
## Evidence

- Vendor register with history (3 years after vendor exit).
- Completed assessments, certificates and SOC 2 reports reviewed (with reviewer notes).
- Signed contracts and DPAs, SCCs where applicable.
- Transfer assessments.
- Tenant notification records (email logs and the published list's change history).
- Offboarding deletion confirmations.

<!-- section:test -->
## Test procedure

Auditor reconciles the vendor register against accounts payable and the IaC / configuration list of external endpoints (any vendor paid or called but not in the register is an exception); samples 10 vendors (all critical vendors) for assessment, contract and annual review; samples 2 sub-processor changes for timely tenant notice.

<!-- section:implementation -->
## Implementation in the platform

Per-region provider configuration in [[INT-integration-framework]]; regional endpoints and residency rules in [[MT-data-residency-2]]; AI provider routing and opt-outs in [[AI-ai-gateway]]; public sub-processor list published from the register (help centre, [[DOC-tenant-facing-help-centre]]).

<!-- section:exceptions -->
## Exceptions

Urgent use of a vendor before full assessment (for example during an incident) needs ISMS lead and DPO approval, no personal data beyond what is essential, and completion of the assessment within 30 days.

<!-- section:metrics -->
## Monitoring and KPIs

- Vendors in use but not in the register (target 0).
- Critical / high vendors with overdue reassessment (target 0).
- Sub-processor changes notified on time (target 100%).

<!-- section:questions -->
## Open questions

- [ ] Standard sub-processor change notice period (30 days proposed) versus what institutional client contracts require.
- [ ] Do any SEBI-regulated tenants or MIIs require prior approval (not just notice) for sub-processor changes? To be confirmed per client.
- [ ] Legal view on transfers of Indian personal data under DPDP s.16 (currently a negative-list approach; no list notified at the time of writing — assumption, to be confirmed by legal).

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

Every third party that stores, processes, transmits or can access tenant or personal data, plus critical operational dependencies, across NTPL, TAPL and the US entity. The population is reconciled quarterly against payments, IaC configuration and outbound network destinations.

<!-- check:evidence -->
### Evidence quality and retention

Register history, assessments, contracts, transfer assessments and tenant notifications are stored centrally and timestamped.

<!-- check:deficiency -->
### Failures and remediation

A vendor found in use without assessment is an incident-level nonconformity: data flow paused where possible, assessment within 10 working days, tenants notified if their contracts require it.

<!-- check:assurance -->
### Independent assurance

SOC 2 / ISO reports of critical vendors are reviewed annually, including their complementary user entity controls we must operate; our own process is tested by the SOC 2 auditor.

<!-- check:commitments -->
### Legal and client commitments

Client DPAs normally require advance notice of new sub-processors, flow-down of terms and location commitments; GDPR Art. 28 and DPDP s.8(2) require processor contracts. Changing a vendor can breach a client's residency or approval clause, so changes are checked against inbound obligations first.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Art. 12(3) one month to respond to requests (extendable by two months); Arts 13–14 information; Arts 15–22 rights; Art. 28 processors; Art. 30 records; Art. 32 security; Art. 33 notify the supervisory authority within 72 hours; Art. 34 communicate to data subjects; Chapter V transfers.",
    "id": "R1",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU / EEA",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  },
  {
    "excerpt": "Sections 5–6 (notice and consent), 8 (obligations of data fiduciary, including breach intimation), 11–14 (rights of data principal), 17 (exemptions).",
    "id": "R2",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "Personal data transferred outside Singapore must receive a standard of protection comparable to the PDPA.",
    "id": "R3",
    "issuer": "Personal Data Protection Commission, Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Advisory Guidelines on Key Concepts in the PDPA, Chapter 19",
    "title": "The Transfer Limitation Obligation",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/the-transfer-limitation-obligation---ch-19-(270717).pdf"
  }
]
```

<!-- end -->
