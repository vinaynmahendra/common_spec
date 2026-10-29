---
id: "APP-accessibility-legal-obligations"
title: "Accessibility legal obligations register"
parent: "APP-accessibility-wcag-2-1-aa"
order: 1
type: "requirement"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "Per region and tenant type: RPwD Act / Rules and draft amendments, SEBI digital accessibility circular, GIGW, ADA Title II, Section 508, EAA applicability; obligated party and contract clause"
links: []
rev: 2
syncHash: "22b4a06660f05d24"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.1.1 Accessibility legal obligations register

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Per region and tenant type: RPwD Act / Rules and draft amendments, SEBI digital accessibility circular, GIGW, ADA Title II, Section 508, EAA applicability; obligated party and contract clause

<!-- section:scope -->
## Scope and surfaces

Register of accessibility legal and contractual obligations per region and tenant type, stating for each: the instrument, its status, who carries the duty (tenant, Nomology, or both), the standard it points to, and the contract clause that passes it to Nomology. Covers the whole platform. Everything in this node is a **draft for legal review**; nothing here is legal advice until signed off.

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

| # | Jurisdiction | Instrument | Status | Applies to which tenants | Obligated party | Standard referenced | Our contract clause |
|---|---|---|---|---|---|---|---|
| L1 | India | Rights of Persons with Disabilities Act 2016, s.46 (service providers, public or private, to provide services per accessibility rules) and s.42 (access to ICT) [R1] | in force | all India tenants providing services to the public | tenant (service provider); Nomology as supplier by contract | RPwD Rules 2017 Rule 15; assumption: GIGW for websites and IS 17802 by later amendment — to be confirmed by legal | MSA accessibility clause (to draft) |
| L2 | India | RPwD Rules: draft amendments on ICT accessibility (including supplier due diligence) | draft, to be tracked | as L1 | tenant; suppliers must give evidence | to be confirmed | evidence pack obligation |
| L3 | India | SEBI circular on digital accessibility for regulated entities, 31 July 2025 [R2] | in force | SEBI-regulated entities and MIIs; ODR institutions only if covered directly or by MII contract — **to be confirmed** | regulated entity; passed down by contract | as stated in the circular — to be extracted by legal (assumption: periodic audit by certified professionals and a nodal officer) | SEBI addendum to MSA |
| L4 | India | Supreme Court, Pragya Prasun v. Union of India (30 April 2025): accessible digital KYC | binding directions to regulators | tenants performing KYC (for example payee onboarding) | regulators and regulated entities; affects our KYC flows | not a technical standard | KYC alternatives in [[PKG-accessible-authentication-and]] |
| L5 | India | GIGW 3.0 [R3] | in force for government | government bodies, courts, commissions | tenant | GIGW 3.0 | government addendum |
| L6 | US | ADA Title II, DOJ web accessibility rule (2024) | in force with phased compliance dates — to confirm current dates | state and local government tenants | tenant | WCAG 2.1 AA | US government addendum |
| L7 | US | Section 508 of the Rehabilitation Act (Revised 508 Standards) | in force | federal agencies buying the platform | agency; vendor provides ACR (508 edition) | WCAG 2.0 AA via 508 | ACR delivery |
| L8 | US | ADA Title III (public accommodations) | case-law driven; no web regulation | private US tenants, if any | tenant | courts commonly reference WCAG 2.x AA | counsel to advise |
| L9 | Singapore | Assumption: no general statutory web accessibility duty on private arbitral institutions | to confirm | Singapore tenants | contract only | WCAG 2.2 AA by our standard | MSA |
| L10 | EU | European Accessibility Act (Directive (EU) 2019/882), applying from 28 June 2025 | in force | not assumed to apply to ODR or arbitration services; counsel to confirm for any EU-facing tenant | — | EN 301 549 | — |
| L11 | Hong Kong (for HKIAC CMP) | Disability Discrimination Ordinance (Cap. 487) and any client security / accessibility schedule | to assess | HKIAC CMP | client; Nomology by contract | per client contract | per the CMP contract |
| L12 | All | Client contracts (institution MSAs, MII agreements) | per contract | per tenant | Nomology | usually WCAG 2.1 or 2.2 AA | per contract |

<!-- section:target -->
## Conformance target and baseline

This node does not set a target; the platform target is WCAG 2.2 AA ([[APP-accessibility-wcag-2-1-aa]]), which meets or exceeds every standard referenced above as far as is known today. Where an instrument points to a standard we do not yet test against (for example IS 17802 clauses for documents), the gap is listed in questions.

<!-- section:criteria -->
## Success criteria mapping

Not applicable to this node: it maps obligations, not success criteria. Criteria mappings live in [[APP-party-and-counsel-portal-2]] and [[APP-secretariat-console-and-neutral]].

<!-- section:at -->
## Assistive technology support matrix

Not applicable; see [[APP-accessibility-wcag-2-1-aa#at]].

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Each tenant record holds `accessibilityProfile`: tenant type (government, SEBI-regulated, serving SEBI matters, private), jurisdictions served, applicable rows of this register, nodal officer contact (where required) and contract clause reference. Set during onboarding ([[MT-tenant-lifecycle]]) and shown in the tenant's accessibility statement.

<!-- section:testing -->
## Testing method

Not applicable for success criteria. The register itself is reviewed quarterly and on any regulatory change by legal and the accessibility lead; each row records last review date and reviewer.

<!-- section:reporting -->
## Conformance reporting

Rows L3 and L5 to L7 require evidence: ACRs in the right edition ([[APP-accessibility-conformance]]) and the audit evidence pack ([[RPT-accessibility-audit-evidence-for]]).

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm every row, especially L1 standard by reference, L3 reach to ODR institutions empanelled with MIIs, and L6 compliance dates (owner: legal)
- [ ] Does any tenant contract set a stricter target or shorter remediation times than our standard? (owner: legal, account managers)
- [ ] Who watches for final versions of draft instruments (L2) and EN 301 549 updates? (owner: accessibility lead)
- [ ] Does HKIAC CMP's contract contain accessibility obligations? (owner: TERES account lead)
- [ ] Do we need a Singapore-specific review (owner: TAPL legal)

<!-- checks -->
## Template checks

<!-- check:applicability -->
### Legal applicability and allocation

Responsibility is set per row: the tenant as service provider or regulated entity carries the statutory duty, and contracts pass a WCAG 2.2 AA obligation, remediation times and evidence duties to Nomology. The tenant's `accessibilityProfile` records which rows apply. Draft instruments (L2) and unconfirmed reach (L3, L6, L10) are flagged for legal.

<!-- check:evidence -->
### Integrity of the conformance claim

For regulated tenants the register links to the evidence each row needs (ACR edition, auditor report, remediation tracker); legal sign-off and review date are recorded per row.

<!-- check:identity -->
### Authentication and identity verification

Row L4 (Pragya Prasun) drives alternatives to liveness and video KYC for blind users and users with facial differences; implemented in [[PKG-accessible-authentication-and]] and the KYC integration ([[INT-kyc-and-sanctions-screening]]).

<!-- check:feedback -->
### People with disabilities in the loop

Where a tenant must name a nodal officer or grievance route (assumption for SEBI-regulated tenants), it is captured in the tenant profile and used by [[APP-accessibility-feedback]] for routing.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 49 of 2016",
    "title": "Rights of Persons with Disabilities Act, 2016",
    "url": "https://indiacode.nic.in/bitstream/123456789/15939/1/the_rights_of_persons_with_disabilities_act%2C_2016.pdf"
  },
  {
    "id": "R2",
    "issuer": "SEBI",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "body": "Government of India",
    "id": "R3",
    "ident": "GIGW 3.0",
    "kind": "standard",
    "title": "Guidelines for Indian Government Websites and Apps: scope and objective",
    "url": "https://guidelines.india.gov.in/scope-and-objective/"
  }
]
```

<!-- end -->
