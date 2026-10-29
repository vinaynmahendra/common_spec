---
id: "TST-security-testing"
title: "Security testing"
parent: "TST"
order: 4
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "044b2c9568dd4c28"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16.4 Security testing

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines the security testing that runs on code, dependencies, images, infrastructure and the running application, and the periodic manual testing by specialists, so that security weaknesses are found before attackers or auditors find them. Finding triage, SLAs and risk acceptance are owned by [[SEC-vulnerability-management]]; isolation testing has its own node, [[TST-multi-tenant-isolation-tests]].

<!-- section:rules -->
## Rules

| ID | Test | Tool (proposed) | When | Blocks |
|---|---|---|---|---|
| **SECT-1** | Static analysis | CodeQL; Semgrep with custom rules (raw SQL, `withTenant` missing, `dangerouslySetInnerHTML`, unsafe redirects, SSRF-prone `fetch` of user URLs) | Every PR | High and critical findings |
| **SECT-2** | Dependency (software composition) analysis | GitHub dependency review; OSV-Scanner on lockfile | Every PR; daily on `main` | New high/critical advisory with fix |
| **SECT-3** | Secret scanning | gitleaks; GitHub push protection | Pre-commit, PR, push | Any finding |
| **SECT-4** | Image scanning | Trivy | Every image build | Critical/high with fix; embedded secrets |
| **SECT-5** | Infrastructure as code scanning | Trivy config / Checkov on Terraform | Every infra PR | High findings (public buckets, open security groups, unencrypted stores) |
| **SECT-6** | Dynamic scanning (unauthenticated) | OWASP ZAP baseline | Every preview of `(public)` routes | High findings |
| **SECT-7** | Dynamic scanning (authenticated) | ZAP full scan with persona sessions per fixture tenant | Weekly in staging per region | Opens tickets per SLA |
| **SECT-8** | Authorisation matrix tests | Generated from the permission matrix ([[PKG-policy-engine-permission-matrix]]): every persona × action × relationship, expecting allow or deny | Every PR touching `authz` or routes | Any mismatch |
| **SECT-9** | Security headers and CSP | Header assertions in e2e ([[APP-security-headers-csp-cors]]) | Every preview | Missing or weakened header |
| **SECT-10** | File handling | Upload tests with malicious samples (EICAR, polyglot PDFs, zip bombs, oversized files) against [[PKG-encryption-at-rest-signed-urls]] | Every PR touching storage; nightly | Any file viewable before scan |
| **SECT-11** | Fuzzing | Property-based fuzzing of parsers (document metadata, CSV imports, aggregator payloads) | Nightly | Crash or hang |
| **SECT-12** | Penetration test | External tester, scope covering all persona apps, public API, webhooks, tenant isolation and the document viewer origin | Before first production tenant, yearly, and after major architecture changes | Critical/high must be fixed before go-live |
| **SECT-13** | Threat modelling | STRIDE-style session per new capability node with an Integration, AI or security template | Before Approved status | Node approval |

**Rules**
- **SECT-14** Verification target: OWASP ASVS Level 2 for all persona apps and public APIs (proposed) [R1]. Test cases map to ASVS requirement IDs in the security test catalogue.
- **SECT-15** DAST and pen tests use synthetic fixture tenants in staging; no testing against production except agreed, scoped checks in the pen test with written authorisation.
- **SECT-16** All findings go to the vulnerability register in [[SEC-vulnerability-management]] with severity, SLA and owner; suppressions in tools require a ticket and expiry.

<!-- section:rationale -->
## Rationale

- SECT-8 is the highest-value test for this platform after isolation: the permission matrix is large (six personas, case and party relationships, ethical walls), and a single wrong entry can expose sealed material.
- SECT-10 matters because parties upload arbitrary documents, and the viewer must never render active content before scanning.

<!-- section:tooling -->
## Tooling and configuration

CodeQL and Semgrep configs in `.github/codeql/` and `tooling/semgrep/`; ZAP automation framework plans in `tests/security/zap/`; authorisation matrix generator in `@nomology/testing/authz`; malicious sample corpus in a restricted test bucket (not in the repo).

<!-- section:enforcement -->
## Enforcement

SECT-1 to SECT-6, SECT-8 to SECT-10 are required checks or image-promotion gates ([[DEP-ci-cd-pipelines-build-test]]). SECT-7 and SECT-11 open tickets automatically. SECT-12 and SECT-13 are gates on go-live and on node approval respectively, recorded by the information security owner.

<!-- section:examples -->
## Examples

Good: a new tRPC procedure `secretariat.reassignCase` is added; the authz generator produces tests showing a neutral on the case is denied and a secretariat user of another tenant gets not-found; the PR fails until the permission entry is added.

Bad: a Semgrep finding on raw SQL suppressed with `// nosemgrep` and no ticket.

<!-- section:exceptions -->
## Exceptions

Risk acceptances for unfixable findings are approved under [[SEC-vulnerability-management]] with an expiry. SECT-3 (secrets) and SECT-8 (authorisation matrix) cannot be waived.

<!-- section:questions -->
## Open questions

- [ ] Assumption: SEBI-regulated tenants (through their MII) may require security audits by a CERT-In empanelled auditor; legal and the tenant to confirm, and whether our pen test can serve as that evidence.
- [ ] Do arbitral institution clients (for example under security schedules in their contracts) require sharing pen test summaries? Legal to confirm per contract.
- [ ] ASVS Level 2 for all surfaces, or Level 3 for platform admin and authentication?
- [ ] Bug bounty or responsible disclosure programme: when?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Automated scanners and the authorisation matrix are required checks; DAST weekly and fuzzing nightly open tickets; pen test and threat modelling are recorded gates. Tool suppressions need tickets and expiries.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Covers supply chain (SCA, image and secret scanning), tenant data (authorisation matrix, isolation in pen test scope), file safety (malicious uploads) and frontend protections (CSP and headers). Uses synthetic tenants only.

<!-- check:compliance -->
### Compliance evidence

Evidence for ISO/IEC 27001:2022 controls on security testing in development and acceptance and on technical vulnerability management, SOC 2 system-operations criteria, and client security questionnaires: scan histories, pen test reports and remediation records.

<!-- check:measurement -->
### Adoption measurement

Open findings by severity and age versus SLA, share of capability nodes with a recorded threat model, and pen test findings per test round.

<!-- check:ownership -->
### Ownership and change

Owner: information security owner; application security champion in each team.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OWASP",
    "excerpt": "A basis for testing web application technical security controls, organised in three verification levels.",
    "id": "R1",
    "ident": "ASVS",
    "kind": "standard",
    "title": "Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard"
  }
]
```

<!-- end -->
