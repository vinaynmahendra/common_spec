---
id: "AI-ai-governance-and-impact"
title: "AI governance and impact assessment"
parent: "AI"
order: 7
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "AI policy, AI system inventory, ISO 42001 impact assessments, AI risk register and tenant opt-in / disclosure decisions"
links: []
rev: 3
syncHash: "b0110b875f074198"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.7 AI governance and impact assessment

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> AI policy, AI system inventory, ISO 42001 impact assessments, AI risk register and tenant opt-in / disclosure decisions

<!-- section:objective -->
## Control objective

Every AI system Nomology builds or uses on case data is known, assessed for its impact on parties, neutrals, institutions and Nomology before use, enabled for a tenant only by that tenant's recorded decision, and kept under review, so that AI cannot affect a dispute in ways nobody assessed or accepted.

Risks addressed: unassessed AI use on case data; AI drifting into decisions on the merits; tenants unaware that AI is used; providers using our data in ways we did not agree; inability to show an auditor or client how AI risk is managed.

<!-- section:mapping -->
## Framework mapping

| Framework | Clause / control | How this control meets it |
|---|---|---|
| ISO/IEC 42001:2023 [R1] | 5.2 AI policy | Approved AI policy |
| | 6.1.2 AI risk assessment, 6.1.3 AI risk treatment | AI risk register with treatment per risk |
| | 6.1.4 and 8.4 AI system impact assessment | Impact assessment per AI system before enablement and on material change; umbrella assessments for tenant-built agents and steps |
| | 9.2 internal audit, 9.3 management review | Annual internal audit of the AI management system; quarterly review |
| | Annex A.2 (policies), A.5 (assessing impacts), A.6 (life cycle), A.8 (information for interested parties), A.10 (third-party relationships) | Policy, impact assessment, lifecycle gates, tenant notices and transparency statements, provider review |
| NIST AI RMF [R2] | Govern, Map, Measure, Manage | Policy and roles (Govern), inventory and context (Map), evals and monitoring (Measure), risk treatment and incidents (Manage) |
| EU AI Act [R3] | Risk classification; Annex III high-risk categories; Article 6(3) | Classification step in each impact assessment (applicability to be confirmed by legal) |
| EU AI Act [R7] | Article 50 transparency | Labels on AI output and tenant transparency statements; assessment records whether human review exempts a given output |
| GDPR [R4] | Art. 22, Art. 35 | Check that no feature makes solely automated decisions with legal effect (workflow provenance rules); DPIA where required, linked to [[SEC-privacy-controls]] |
| Singapore Model AI Governance Framework for Generative AI [R5] | Accountability, data, trusted development and deployment, incident reporting, testing and assurance, security, content provenance | Owners and tenant decisions; minimisation; evals and gates; AI incident process; red teaming; labels and provenance of AI facts |
| India AI Governance Guidelines [R6] | Principles and organisational measures (voluntary) | Same controls, presented in the India client assurance pack |
| ISO/IEC 27001:2022 | A.5.19 to A.5.22 supplier relationships | AI provider review in [[SEC-vendor-sub-processor-management]] |

<!-- section:description -->
## Control description

**1. AI policy (Nomology's).** One policy covering acceptable uses (assistive only), prohibited uses (deciding or predicting outcomes, assessing credibility, use of consumer AI tools on case data, training on tenant data without agreement), roles, and the lifecycle gates below. Approved by the CTO and CEO; reviewed annually. This is Nomology's own management-system policy; each tenant's AI choices are a separate, tenant-owned **tenant AI policy** ([[AI-tenant-ai-policy]]).

**2. AI system inventory.** Register `ai_systems` (platform-level) with one entry per AI feature and per shared component (gateway, RAG, guardrails, agent runtime, admin copilot): ID (`AIS-...`), purpose, owner, risk tier, models and routes used, data categories, regions, tenants enabled, impact assessment ID and date, eval suite, status. Two **umbrella entries** cover tenant-built AI: `AIS-CUSTOM-AGENTS` (with one child entry per published tenant agent, created automatically on publish, see [[AI-agent-configuration]]) and `AIS-WF-AI-STEPS` (one child entry per published blueprint with AI steps, see [[WF-ai-steps-and-agents]]). Reconciled monthly against the feature catalogue, availability flags `ai.<feature>.available` and the kill switch `ai.killswitch` ([[PKG-feature-flags]] FLAG-R-7), tenant policies, published agents, published blueprints and the gateway route table: any enabled AI use without an inventory entry is a finding.

**3. Impact assessment (per AI system).** Completed by the feature owner with the AI governance lead, before first enablement and on material change (new model family, new data category, new persona, new output destination, new tool class for agents). Contents:

- Intended use and out-of-scope uses (from the feature node)
- Affected groups (parties, counsel, neutrals, secretariat, transcribers, institutions) and worst credible harm for each
- Risk tier: **T1** internal productivity, no effect on case record; **T2** output enters the case record or reaches parties after human approval; **T3** assists work on the merits (drafting orders or awards). Prohibited uses have no tier.
- Regulatory classification (EU AI Act Annex III and Article 6(3) check, Article 50 transparency check, GDPR Art. 22 check, DPDP purpose check)
- Human oversight design ([[AI-human-in-the-loop]]), evaluation thresholds ([[TST-evals-and-ai-testing]]), residency confirmation ([[AI-ai-gateway]])
- Residual risk and acceptance by the named risk owner

Tenant agents and blueprint AI steps do not each need a full assessment: they inherit the umbrella assessment for their computed tier, provided they stay inside the platform tool registry, step kinds and policy bounds. Anything outside those bounds is not configurable.

**4. AI risk register.** Entries linked to inventory items with likelihood, impact, treatment, owner and review date; T3 risks are reviewed quarterly.

**5. Tenant AI decisions.** A tenant enables AI only by accepting the current AI notice (versioned legal text, [[AI-ai-generated-text-labelling-and]]) and publishing a tenant AI policy in the admin console (`/admin/ai/policy`). Acceptances are recorded in `tenant_ai_decisions` (tenant-owned): notice version, accepting `tenant_owner`, step-up method, date and conditions. Policy versions (which features, scopes, review and disclosure rules) are recorded by the configuration lifecycle. Institution-specific disclosure requirements (for example statements in awards) are captured as settings `ai.disclosure.*` ([[PKG-settings-ai]]).

**6. Lifecycle gates.** An AI feature can be made available in a region (release flag) only if: inventory entry exists, impact assessment Approved, eval run passing, provider terms recorded for the routes used. A tenant can turn a feature on (policy publish) only if: the feature is available, the tenant's plan includes it, and the current notice is accepted. A tenant agent or blueprint with AI steps can be published only if: its evaluation passes, the policy allows it, and its inventory child entry is created. Enforced in the availability flag service ([[PKG-feature-flags]]), the policy publish validator and the agent and blueprint publish validators.

**7. AI-proposed configuration.** Configuration changes drafted by the admin copilot or agents are recorded with `origin = copilot` or `origin = agent` and are always approved and published by humans ([[APP-admin-copilot]]). The share of AI-proposed changes and their rollback rate are monitored as an AI system metric.

<!-- section:owner -->
## Owner and frequency

| Role | Who (to be named) | Responsibility |
|---|---|---|
| Control owner | AI platform and governance lead | Policy, inventory, assessment process, register |
| Operators | Feature owners | Complete assessments, keep inventory entries current |
| Reviewer | Security and compliance lead; legal for regulatory classification | Approve T2 and T3 assessments |
| Approver of policy | CTO and CEO | Annual approval |
| Backup | Engineering lead for the AI area | Operates the control when the owner is away |

Frequency: inventory reconciliation monthly; assessments before enablement and on change; T3 risks quarterly; policy annually; internal audit annually.

<!-- section:evidence -->
## Evidence

| Artefact | Source | Stored | Retention (proposed) |
|---|---|---|---|
| Approved AI policy with version and approvers | Document control | ISMS evidence store (append-only, per entity) | Life of the policy plus 6 years |
| Inventory export with reconciliation query and row counts (including agent and blueprint child entries) | `ai_systems`, flags, tenant policies, agents, blueprints, route table | Monthly export in evidence store | 6 years |
| Impact assessments with approvals | Workspace node per AI system | Evidence store snapshot at approval | Life of the system plus 6 years |
| Risk register snapshots | Register | Quarterly snapshot | 6 years |
| Tenant notice acceptances | `tenant_ai_decisions` in the tenant's region | Regional database and audit trail | Contract term plus 6 years |
| Tenant AI policy versions | Configuration history ([[PKG-configuration-lifecycle]]) | Regional database and audit trail | Contract term plus 6 years |
| Gate check logs (availability, policy publish, agent and blueprint publish, pass / fail) | Validators' audit events | [[PKG-audit-trail]] | As audit trail |
| AI-proposed change records | Change sets with origin | [[PKG-audit-trail]] | As audit trail |

Retention periods are assumptions to align with [[PKG-retention-and-deletion-schedule]] and legal advice.

<!-- section:test -->
## Test procedure

- **Design:** confirm the policy, assessment template and all gates (availability, policy publish, agent publish, blueprint publish) exist and cover the required clauses.
- **Operating effectiveness:** sample 25 percent of inventory entries (minimum 5) per audit period; for each, confirm an Approved assessment predates first availability (from flag audit events), eval run exists, provider terms are recorded, and a notice acceptance precedes the first policy publish enabling it for each sampled tenant.
- Sample 10 published tenant agents and 10 blueprints with AI steps (or all if fewer): confirm child inventory entries, passing evaluation before publish, and a different approver from the author.
- Re-perform one monthly reconciliation and compare with the stored export.
- In staging, attempt to: publish a tenant policy enabling a feature without notice acceptance; publish an agent with a failing evaluation; publish a blueprint whose AI step feeds a legal-effect decision table. Confirm each gate blocks.

<!-- section:implementation -->
## Implementation in the platform

- `ai_systems` register with umbrella and child entries; `tenant_ai_decisions` table; gates in [[PKG-feature-flags]] (availability), [[AI-tenant-ai-policy]] (policy publish and runtime decision), [[AI-agent-configuration]] and [[WF-ai-steps-and-agents]] (publish).
- Notice acceptance and policy screens in the tenant admin console (`/admin/ai/policy`, [[APP-tenant-admin-console]]).
- Provider review in [[SEC-vendor-sub-processor-management]]; route activation requires `terms_ref`, `zero_retention` and `no_training` ([[AI-ai-gateway]]).
- Evals in [[TST-evals-and-ai-testing]]; monitoring in [[OBS-ai-usage]]; AI incidents through [[SEC-security-incident-response-and]].
- Reconciliation job `ai-inventory-reconcile` (BullMQ, monthly, per region) writes its export and findings to the evidence store.

<!-- section:exceptions -->
## Exceptions

Exceptions (for example a pilot with one tenant before full assessment) require a written request, approval by the CTO and the security and compliance lead, a maximum of 60 days (proposed), a compensating control (internal-only output, extra sampling), and an entry in the risk register. Exceptions are never allowed for prohibited uses or for cross-region processing without the tenant's written agreement.

<!-- section:metrics -->
## Monitoring and KPIs

- Share of available AI features with a current Approved assessment (target 100 percent)
- Inventory reconciliation findings per month (target 0)
- Overdue T3 risk reviews (target 0)
- Tenants with AI enabled and a current notice acceptance (target 100 percent)
- Published tenant agents and blueprints with AI steps without a child inventory entry (target 0)
- AI-proposed configuration changes: share of all changes and rollback rate within 30 days
- AI incidents per quarter and time to close

<!-- section:questions -->
## Open questions

- [ ] Name the control owner, reviewer and backup.
- [ ] Is Nomology pursuing ISO/IEC 42001 certification, and for which entities (NTPL, TAPL, US entity) and by when?
- [ ] Legal view on EU AI Act applicability, given EU parties may appear in cases administered by our tenants, including current application dates for Annex III obligations.
- [ ] Do any institutions or regulators (for example via SEBI-recognised MIIs) have their own rules on AI use in ODR that tenants must follow? Do not assume; collect from tenants at onboarding into `ai.disclosure.*` settings.
- [ ] Are umbrella assessments for tenant agents and AI steps acceptable to auditors, or does each T2 agent need its own short assessment?
- [ ] Evidence retention periods (proposed 6 years) to be confirmed.

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

Covers every AI feature and shared AI component, every tenant-built agent and blueprint AI step, and the admin copilot, across NTPL, TAPL and the US entity, in India, Singapore and US regions and Azure deployments. The population is the `ai_systems` register with child entries, reconciled monthly against the feature catalogue, flags, tenant policies, published agents and blueprints, and the route table. Tenant responsibilities (deciding to enable AI, institution disclosure rules, their users' review of outputs, agents they build) are listed separately for publication to clients.

<!-- check:owner -->
### Ownership and accountability

Owner, operators, reviewer, policy approver and backup are defined by role; names to be filled in. Segregation: feature owners complete assessments; the security and compliance lead approves T2 and T3.

<!-- check:evidence -->
### Evidence quality and retention

Policy versions, monthly inventory exports with query and counts, approved assessments, register snapshots, notice acceptances, tenant policy versions, gate-check logs and AI-proposed change records, stored in append-only evidence stores per entity and region with proposed retention.

<!-- check:automation -->
### Automation and continuous monitoring

Automated: monthly reconciliation of the register against the feature catalogue, flags, tenant policies, published agents, blueprints and routes; availability, policy, agent and blueprint publish gates; notice acceptance recording; child inventory entries on publish. Manual: assessments, risk reviews, policy approval. A missing monthly reconciliation run raises a dead-man alert to the control owner.

<!-- check:exceptions -->
### Exceptions and risk acceptance

Written request, CTO plus security and compliance approval, 60-day maximum (proposed), compensating control and risk-register entry; never for prohibited uses or cross-region processing without written tenant agreement.

<!-- check:commitments -->
### Legal and client commitments

Depends on: client contract terms on AI use and disclosure (tenant-specific, now captured as tenant AI policy settings), provider data terms (zero retention, no training), ISO/IEC 42001 certification plans if pursued [R1], GDPR Art. 22 and 35 where EU personal data is processed [R4], and EU AI Act duties where applicable [R3]. Changes to the control need compliance and legal review.

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
    "body": "NIST",
    "excerpt": "Organises AI risk management into four functions: Govern, Map, Measure and Manage.",
    "id": "R2",
    "ident": "AI RMF 1.0",
    "kind": "standard",
    "title": "AI Risk Management Framework",
    "url": "https://www.nist.gov/itl/ai-risk-management-framework"
  },
  {
    "excerpt": "Annex III lists high-risk uses, including AI intended to assist a judicial authority in researching and interpreting facts and the law and applying the law to facts, or used in a similar way in alternative dispute resolution. Article 6(3) excludes Annex III systems that perform narrow procedural or preparatory tasks and do not materially influence the outcome of decision making; Article 26 sets deployer duties (human oversight, log keeping); Article 50 sets transparency duties.",
    "id": "R3",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689",
    "status": "in force, phased application",
    "title": "Artificial Intelligence Act",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
  },
  {
    "excerpt": "Article 22 restricts decisions based solely on automated processing that produce legal or similarly significant effects; Article 35 requires a data protection impact assessment for high-risk processing.",
    "id": "R4",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "status": "in force",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  },
  {
    "excerpt": "Nine dimensions for trusted generative AI: accountability, data, trusted development and deployment, incident reporting, testing and assurance, security, content provenance, safety and alignment R&D, and AI for public good. Released 30 May 2024.",
    "id": "R5",
    "issuer": "IMDA and AI Verify Foundation (Singapore)",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Model AI Governance Framework for Generative AI",
    "status": "voluntary framework",
    "title": "Model AI Governance Framework for Generative AI",
    "url": "https://aiverifyfoundation.sg/resources/mgf-gen-ai/"
  },
  {
    "excerpt": "Non-binding national guidance issued by MeitY under the IndiaAI Mission (November 2025) setting out principles for safe and trusted AI, including accountability, understandability by design and safety, and recommending institutional and organisational measures.",
    "id": "R6",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "India AI Governance Guidelines",
    "status": "guidance, non-binding",
    "title": "India AI Governance Guidelines: Enabling Safe and Trusted AI Innovation",
    "url": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc2025115685601.pdf"
  },
  {
    "excerpt": "Article 50 applies from 2 August 2026. Deployers must disclose AI-generated text published to inform the public on matters of public interest, unless the content has undergone human review or editorial control and a person holds editorial responsibility.",
    "id": "R7",
    "issuer": "European Commission",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689, Article 50 (Commission FAQ)",
    "status": "applies from 2 August 2026",
    "title": "Transparency obligations under Article 50 of the AI Act",
    "url": "https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act"
  }
]
```

<!-- end -->
