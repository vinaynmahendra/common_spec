---
id: "AI-ai-audit-and-transparency"
title: "AI audit and transparency records"
parent: "AI"
order: 9
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "One joined, tamper-evident record of every AI use per tenant, case and output (policy, prompt, model, guardrails, cost, review, AI-proposed changes) with admin views, signed exports and a party-facing disclosure page"
links: []
rev: 1
syncHash: "5a1a5a724cdbcf1e"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.9 AI audit and transparency records

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> One joined, tamper-evident record of every AI use per tenant, case and output (policy, prompt, model, guardrails, cost, review, AI-proposed changes) with admin views, signed exports and a party-facing disclosure page

<!-- section:statement -->
## Statement

When an authorised person asks for the AI record of a tenant, unit, case or single AI output, the platform shall produce, from tenant-region data only, a complete and tamper-evident account of every AI use in that scope: which feature, agent, workflow step or copilot was used, by or for whom, under which tenant AI policy version, with which prompt, model and route versions, on which inputs (by reference), with what guardrail results, cost, and review outcome (approver, edits, acceptance path), and which configuration changes were AI-proposed.

<!-- section:rationale -->
## Rationale and source

- **Explaining an AI-assisted step in a dispute.** An institution, a tribunal or a party's counsel may ask how a summary, a classification or a draft came about. Without one joined view, the facts are spread over `ai_requests`, `ai_outputs`, HITL audit events, agent turns, workflow step records and change sets.
- **ISO/IEC 42001** expects records that let the organisation demonstrate AI system operation and traceability [R1]; the EU AI Act asks deployers of high-risk systems to keep automatically generated logs for at least six months where it applies [R2]; the Singapore framework for generative AI stresses accountability, incident reporting and content provenance [R3].
- **Tenant administrators** need this to answer their own clients and regulators, and to check that their AI policy works as intended.
- Pattern borrowed from: trust-layer audit trails and feedback stores kept alongside every generative call [R4].

<!-- section:acceptance -->
## Acceptance criteria

**Views and exports**

| Surface | Route / API | Who | Content |
|---|---|---|---|
| AI activity (tenant) | `/admin/ai/audit`; `GET /admin/v1/ai/audit/events` | `ai_admin`, `auditor`, `security_admin` (`ai.audit:read`) | Filterable by unit, case type, case, feature, agent, step, principal, outcome, deny code, policy version, date |
| AI record of a case | Case page → AI tab; `GET /admin/v1/ai/audit/cases/{caseId}` | Case manager (summary), `auditor` and `ai_admin` (full) | Timeline of AI uses in the case with review outcomes and acceptance paths |
| AI output detail | `/admin/ai/audit/outputs/{outputId}` | `ai.audit:read` | Request chain: policy decision, prompt and model versions, guardrail flags, citations, reviewer, diff, apply target |
| Export | `POST /admin/v1/audit-exports` with `domain = ai` | `ai.audit:export` (tenant owner, security admin, auditor) | Signed, hash-listed bundle (CSV and JSON) delivered through a short-lived signed URL; bodies included only when the requester also selects them and holds case access |
| Party-facing disclosure | Case portal → "Use of AI in this case" | Parties and counsel of the case, if `ai.disclosure.*` requires it | The tenant's transparency statement and the list of disclosed AI uses (feature and date, not prompts) |
| Platform view | `/platform/ai/audit` | Platform security, only with approved support access ([[PKG-support-access-and-impersonation]]) | Metadata only |

**Scenarios**

- **Given** a bundle summary approved with edits by a tribunal secretary, **when** an auditor opens the output detail, **then** they see the policy version that allowed it, prompt `bundle-summary.tribunal@v`, route and model version, guardrail flags, the reviewer, the edit diff and the tribunal workspace target, all linked by `request_id`.
- **Given** a document auto-classified by a workflow AI step under `accepted_by_policy`, **when** the case record is viewed, **then** the classification shows "AI-classified", the AI step definition version, the calibrated score and whether it was sampled and confirmed or corrected.
- **Given** a role change drafted by the admin copilot and published by a second admin, **when** the change history is filtered by `origin = copilot`, **then** the change shows the copilot conversation reference, the author (invoking admin) and the approver.
- **Given** an AI request denied because a party opted out, **when** the AI activity view is filtered by deny code, **then** the deny is listed with `AI_PARTY_OPTED_OUT` and the internal party reference, and the party's identity is not shown to users without case access.
- **Negative:** **Given** a user with `ai.audit:read` in tenant A, **when** they request an output ID that belongs to tenant B, **then** the API returns the same not-found response as for a non-existent ID and logs a cross-tenant attempt ([[OBS-security-events]]).
- **Negative:** **Given** an auditor without case access, **when** they export AI records with bodies selected, **then** bodies are excluded and the export manifest says why.

<!-- section:verification -->
## Verification method

- Integration test that builds one case with every AI path (feature, agent, workflow step auto-accepted and reviewed, copilot draft, deny) and asserts the case AI record contains each with complete links (`ai_requests` ↔ `ai_outputs` ↔ audit events ↔ change sets).
- Hash-chain verification of AI audit events using the audit trail's verifier ([[PKG-audit-log-schema]]).
- Cross-tenant negative tests in [[TST-multi-tenant-isolation-tests]].
- Inspection: retention of AI records meets the longer of the case retention, the tenant's contract and six months (EU AI Act deployer log minimum where applicable, assumption to be confirmed by legal).
- Demonstration to the first arbitral institution and SEBI ODR tenant before general availability.

<!-- section:priority -->
## Priority

Must, AI phase part 1 (with the first AI feature). Export and party-facing disclosure page: must before any tenant enables a T2 or T3 feature.

<!-- section:questions -->
## Open questions

- [ ] Should parties and counsel be able to request the AI record of their own case (beyond the disclosure page), and through whom? (owner: legal, product)
- [ ] Minimum retention of AI metadata when `ai.retention.prompt_output_bodies = metadata_only`. (owner: legal)
- [ ] Does the export format need to match any regulator or MII template? Assumption: no; collect from tenants. (owner: compliance)

<!-- section:notes -->
## Notes

This node joins records owned elsewhere; it adds no new store. Sources: `ai_requests` and bodies ([[AI-ai-gateway]]), `ai_outputs` and review events ([[AI-human-in-the-loop]]), agent turns ([[AI-agent-configuration]]), workflow step outputs ([[WF-ai-steps-and-agents]]), policy versions and decisions ([[AI-tenant-ai-policy]]), change sets with origin ([[APP-admin-copilot]], [[APP-admin-change-history]]), usage ledger ([[AI-cost-controls]]). Telemetry without content stays in [[OBS-ai-usage]]; analytics in [[RPT-platform-ai-usage-analytics]].

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without it, ISO/IEC 42001 traceability evidence, tenant answers to tribunals and parties, and EU AI Act deployer logging (where applicable) depend on ad hoc database queries by Nomology staff.

<!-- check:complete -->
### Complete and scoped

States scopes (tenant, unit, case, output), the record content, surfaces, permissions, exports, party-facing disclosure, cross-tenant behaviour and the body-access rule; retention is linked to the settings catalogue.

<!-- check:verifiable -->
### Verifiable

End-to-end integration test with every AI path, hash-chain verification, cross-tenant negative tests and a demonstration gate.

<!-- check:consistent -->
### Consistent

Uses the same permission keys (`ai.audit:read`, `ai.audit:export`), the audit export endpoint of the admin API, deny codes from [[AI-tenant-ai-policy]] and acceptance states from [[AI-human-in-the-loop]].

<!-- check:traced -->
### Traced

Sources: ISO/IEC 42001 [R1], EU AI Act Article 26 [R2], Singapore MGF for GenAI [R3]; forward to the source nodes listed in Notes and to tests in [[TST-evals-and-ai-testing]] and [[TST-multi-tenant-isolation-tests]].

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "excerpt": "Requirements for establishing, implementing, maintaining and continually improving an AI management system, including AI risk assessment, AI risk treatment and AI system impact assessment.",
    "id": "R1",
    "ident": "ISO/IEC 42001",
    "kind": "standard",
    "title": "Information technology - Artificial intelligence - Management system",
    "url": "https://www.iso.org/standard/42001",
    "version": "2023"
  },
  {
    "excerpt": "Annex III lists high-risk uses, including AI intended to assist a judicial authority in researching and interpreting facts and the law and applying the law to facts, or used in a similar way in alternative dispute resolution. Article 6(3) excludes Annex III systems that perform narrow procedural or preparatory tasks and do not materially influence the outcome of decision making; Article 26 sets deployer duties (human oversight, log keeping); Article 50 sets transparency duties.",
    "id": "R2",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689",
    "status": "in force, phased application",
    "title": "Artificial Intelligence Act",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
  },
  {
    "excerpt": "Nine dimensions for trusted generative AI: accountability, data, trusted development and deployment, incident reporting, testing and assurance, security, content provenance, safety and alignment R&D, and AI for public good. Released 30 May 2024.",
    "id": "R3",
    "issuer": "IMDA and AI Verify Foundation (Singapore)",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Model AI Governance Framework for Generative AI",
    "status": "voluntary framework",
    "title": "Model AI Governance Framework for Generative AI",
    "url": "https://aiverifyfoundation.sg/resources/mgf-gen-ai/"
  },
  {
    "excerpt": "Trust layer features: grounding in customer data, data masking, toxicity detection, audit trail and feedback, and zero data retention agreements with third-party model providers.",
    "id": "R4",
    "kind": "vendor",
    "title": "Agentforce Developer Guide: Trust Layer",
    "url": "https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html",
    "vendor": "Salesforce"
  }
]
```

<!-- end -->
