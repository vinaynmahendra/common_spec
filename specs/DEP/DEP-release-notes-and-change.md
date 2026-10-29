---
id: "DEP-release-notes-and-change"
title: "Release notes and change management"
parent: "DEP"
order: 5
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "b29572144b0ee5fe"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 15.5 Release notes and change management

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines how production changes are classified, approved, recorded and communicated: the change classes and who approves each, the change record created for every production deploy, the emergency path, and the internal and tenant-facing release notes. It is the release-level part of change management; pull-request-level rules are in [[FND-governance]].

<!-- section:rules -->
## Rules

**Change classes**

| Class | Examples | Approval before production | Lead time |
|---|---|---|---|
| Standard | Feature behind an off flag, bug fix, copy change, dependency patch | Normal PR review + release manager approves the release | Weekly release train |
| Normal | User-visible behaviour change, new integration, expand migration | As standard + product owner sign-off on release notes | Weekly train |
| High-risk | Contract migration, changes to authentication, authorisation, RLS, encryption, tenancy or residency routing, network or WAF rules, AI model change for a case-facing feature | CTO and information security owner, recorded on the change record | 2 working days notice |
| Emergency | Fix for an active incident or critical vulnerability | Release-rota engineer + incident lead; retrospective approval by CTO within 2 working days | Immediate |

- **CHG-1** Every production deploy creates a change record automatically (`change_records` in the release tooling store) with: release ID, image digests, regions and times, change class, list of PRs and tickets, approvers, CI and canary results, rollback events and the release notes link.
- **CHG-2** The release manager for the week classifies the release; the highest class of any included PR sets the class of the release.
- **CHG-3** Standard releases run on a weekly train (proposed: cut Tuesday, production waves Wednesday and Thursday), outside every tenant's protected windows ([[DEP-blue-green-canary-releases]] REL-12).
- **CHG-4** Emergency changes follow the same pipeline with shortened canary steps; the incident ticket is the change ticket.

**Release notes**
- **CHG-5** Internal release notes are generated from Conventional Commit PR titles, grouped by package and change type, with migration phases and new feature flags listed.
- **CHG-6** Tenant-facing release notes are written by product for each product (CORD, TERES), in plain language using glossary terms ([[I18N-platform-glossary-and]]), and published in the help centre ([[DOC-tenant-facing-help-centre]]) and the tenant admin console. Changes behind a flag are announced when enabled for that tenant, not when deployed.
- **CHG-7** Breaking changes to the public API or webhooks are announced in the API changelog ([[DOC-api-documentation-openapi]]) with a deprecation period of at least 90 days (proposed; subject to client contracts).
- **CHG-8** Planned maintenance that may affect availability is notified to tenant admins at least 5 working days ahead (proposed), and on the public status page ([[OBS-uptime-synthetic-monitoring]]).
- **CHG-9** Release notes never mention tenants by name, case details, or unfixed vulnerabilities.

<!-- section:rationale -->
## Rationale

- Classes keep approval effort proportional: most changes ship on the weekly train with review evidence alone, while changes that can break isolation or residency get senior sign-off.
- **CHG-1** Generated records mean an auditor sampling a production change sees the full trail without anyone assembling it by hand.
- **CHG-6** Tenants (and their parties) care about what changed for them; announcing at flag enablement avoids describing features they cannot see.

<!-- section:tooling -->
## Tooling and configuration

- `tooling/release`: cuts releases, tags `release/YYYY.MM.DD-N`, generates internal notes, writes change records.
- Change record store: append-only table in the platform-level release database (not tenant data), exported monthly to the ISMS evidence store.
- Help centre "What's new" pages and tenant admin console banner fed from the curated notes.
- Ticketing system link via ticket keys in PR titles or bodies.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| CHG-1 | Promotion workflow cannot reach production without writing the change record |
| CHG-2 | Release cannot start a production wave without a class and release manager approval (GitHub environment reviewers) |
| High-risk approvals | Production environment requires CTO and security reviewers when the release is labelled high-risk; labels set automatically when PRs touch paths owned by `security` or contract migrations |
| CHG-4 | Emergency label requires an incident ticket reference; daily report of emergency changes missing retrospective approval |
| CHG-7 | `openapi-diff` breaking change requires a changelog entry in the same PR |
| CHG-9 | Review by product and security before publishing tenant-facing notes |

<!-- section:examples -->
## Examples

Good tenant note (CORD): "You can now ask for more time to file a reply from the case page. Your institution decides whether to allow it."

Bad: "Fixed IDOR in /api/cases allowing access to other tenants' cases" (discloses a vulnerability) or "HKIAC asked for this feature" (names a tenant).

<!-- section:exceptions -->
## Exceptions

Out-of-train standard releases need release manager approval and a reason on the change record. Skipping the change record is not allowed.

<!-- section:questions -->
## Open questions

- [ ] Which client contracts require advance notice of changes or maintenance, and how long? (Legal to confirm per client.)
- [ ] Is a weekly train right for all regions, or should regulated tenants (SEBI ODR institutions) get a slower cadence?
- [ ] Retention period for change records as audit evidence.
- [ ] Do tenant-facing notes need translation into tenant languages at launch?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Change records and approvals are enforced by the promotion workflow and GitHub environment reviewers; high-risk labelling is automatic from CODEOWNERS paths; breaking API changes need a changelog entry by CI. Content of tenant-facing notes is review-only.

<!-- check:compliance -->
### Compliance evidence

Primary evidence source for ISO/IEC 27001:2022 Annex A change management and SOC 2 change-management criteria: every production change has a class, approvers, test and canary results and a deploy timeline. Emergency changes carry retrospective approval, which auditors usually sample.

<!-- check:measurement -->
### Adoption measurement

Tracked: releases per region per month, share of emergency changes (target under 10%), emergency changes without retrospective approval after 2 working days (target 0), and high-risk changes per release.

<!-- check:ownership -->
### Ownership and change

Owner: DevOps lead for the process and tooling; product leads for tenant-facing notes; CTO approves changes to the change classes.

<!-- end -->
