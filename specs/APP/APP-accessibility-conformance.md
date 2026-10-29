---
id: "APP-accessibility-conformance"
title: "Accessibility Conformance Reports and accessibility statements"
parent: "APP-accessibility-wcag-2-1-aa"
order: 2
type: "requirement"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "ACR (VPAT INT edition, plus machine-readable copy) per product release; per-tenant public accessibility statement; signatory and evaluator"
links: []
rev: 2
syncHash: "eab4ee52bbc716fe"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.1.2 Accessibility Conformance Reports and accessibility statements

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> ACR (VPAT INT edition, plus machine-readable copy) per product release; per-tenant public accessibility statement; signatory and evaluator

<!-- section:scope -->
## Scope and surfaces

The reports that state our conformance publicly and to clients: the Accessibility Conformance Report (ACR) per product release, in VPAT INT edition with a machine-readable copy, and the per-tenant public accessibility statement. Covers CORD, TERES and HKIAC CMP builds of the platform. Also defines signatory, evaluator and publication.

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

Reports serve the obligations in [[APP-accessibility-legal-obligations]]: ACRs for procurement (Section 508 edition for US government, EN 301 549 edition for EU-facing clients), evidence for SEBI-regulated tenants, and statements expected under tenant contracts.

<!-- section:target -->
## Conformance target and baseline

Reports describe conformance against WCAG 2.2 AA and the extra EN 301 549 clauses listed in [[APP-accessibility-wcag-2-1-aa#target]].

<!-- section:criteria -->
## Success criteria mapping

Each ACR row is generated from the surface criteria mappings ([[APP-party-and-counsel-portal-2]], [[APP-secretariat-console-and-neutral]]) and the test records attached to them; no row may be written by hand without a linked record.

<!-- section:at -->
## Assistive technology support matrix

Each ACR states the AT matrix tested ([[APP-accessibility-wcag-2-1-aa#at]]) and the dates.

<!-- section:testing -->
## Testing method

An ACR is issued only after the release's manual review and AT pass; the evaluator is named (internal accessibility lead or an independent IAAP-certified auditor for regulated tenants).

<!-- section:exceptions -->
## Known exceptions and remediation plan

Exceptions in the ACR come from the surface nodes' exception registers; nothing may be omitted because it is 'minor'.

<!-- section:reporting -->
## Conformance reporting

**ACR**
- Format: VPAT INT edition (WCAG 2.2, Revised Section 508, EN 301 549 tables) [R1], using the current VPAT template version, plus a machine-readable copy (OpenACR YAML proposed).
- Scope statement: product, release (semantic version and build SHA), surfaces and route groups, date, evaluation methods, AT matrix.
- Conformance levels: Supports, Partially Supports, Does Not Support, Not Applicable; every Partially Supports and Does Not Support entry states user impact, workaround and fix date.
- Cadence: per minor release with UI changes; at least every 6 months; immediately after a major redesign.
- Signatory: accessibility lead and CTO; legal reviews wording.
- Storage: `docs/accessibility/acr/{product}/{version}/` in the repo and published to the trust centre.

**Accessibility statement (per tenant)**
- Generated from a template plus tenant data: tenant name, scope (the tenant's host), conformance status, known limitations (from the ACR plus tenant-specific exceptions such as their own document templates), feedback channels (link to report-a-barrier, email, phone), nodal officer where required, response targets, enforcement or complaint route as advised by legal, date of last review.
- Published at `/accessibility` on the tenant host ([[APP-public-and-sign-in-surfaces]]), in all enabled tenant locales.
- Reviewed by the tenant admin at publish; updated automatically when a new ACR is issued, with the tenant notified.

<!-- section:questions -->
## Open questions

- [ ] Machine-readable format: OpenACR or another (owner: accessibility lead)
- [ ] Separate ACRs per product (CORD, TERES, HKIAC CMP) or one platform ACR with product scope notes? (owner: product)
- [ ] Independent auditor for the first ACR, and for SEBI-regulated tenants annually? (owner: CTO, budget)

<!-- checks -->
## Template checks

<!-- check:evidence -->
### Integrity of the conformance claim

ACR rows are generated from criteria mappings with linked test records (date, tester, method, AT, build SHA); the scope statement names release and surfaces; legal reviews wording; re-issue is mandatory after major UI changes.

<!-- check:tenancy -->
### Tenant customisation and content

Each tenant statement is generated from that tenant's configuration, exceptions and contacts, so it reflects their theme, templates and nodal officer rather than a generic platform claim.

<!-- check:regression -->
### Preventing regression

The ACR cadence is tied to releases with UI changes; a new ACR cannot be published if open blocker defects exist on the sample pages.

<!-- check:feedback -->
### People with disabilities in the loop

Every statement links to the report-a-barrier channel and states response targets taken from [[APP-accessibility-feedback]].

<!-- citations -->
## Citations

```json
[
  {
    "body": "Information Technology Industry Council (ITI)",
    "id": "R1",
    "ident": "VPAT",
    "kind": "standard",
    "title": "Voluntary Product Accessibility Template",
    "url": "https://www.itic.org/policy/accessibility/vpat"
  }
]
```

<!-- end -->
