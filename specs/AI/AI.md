---
id: "AI"
title: "Native AI"
parent: null
order: 8
type: "area"
template: "area"
childTemplate: "ai"
status: "draft"
owner: null
indicative: false
summary: "Shared AI layer: gateway, prompts, retrieval, guardrails, human review, cost controls, tenant AI policy and settings, tenant agents and workflow AI steps, admin copilot, and ISO/IEC 42001 governance"
links: []
rev: 4
syncHash: "21e51307e4c95b20"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8 Native AI

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared AI layer: gateway, prompts, retrieval, guardrails, human review, cost controls, tenant AI policy and settings, tenant agents and workflow AI steps, admin copilot, and ISO/IEC 42001 governance

<!-- section:purpose -->
## Purpose and scope

Native AI is the shared AI layer of the platform: one controlled route for every model call, shared retrieval over case documents, shared guardrails, human review of AI output, cost limits, the **tenant controls** that decide where AI may be used, the **no-code building blocks** tenants use to configure assistants, agents and AI workflow steps, and the AI management system that governs it all under ISO/IEC 42001 [R1]. User-facing AI features (case summaries, bundle summaries, drafting assistance in the neutral workspace, transcription support, the admin copilot) are built on this layer and each has its own node.

**In scope**

| Layer | Nodes |
|---|---|
| Runtime | [[AI-ai-gateway]] (provider abstraction, regional routing, fallbacks), [[AI-prompt-management]] (versioned prompts, tenant slots), [[AI-rag]] (ingestion, embeddings, case- and tenant-scoped retrieval), [[AI-guardrails]] (redaction, injection defences, filtering, grounding) |
| Oversight | [[AI-human-in-the-loop]] and [[AI-ai-generated-text-labelling-and]] (review, approval, labelling), [[AI-ai-audit-and-transparency]] (joined AI record, exports, party-facing disclosure) |
| Tenant administration | [[AI-tenant-ai-policy]] (features on per scope, permitted providers, data use and retention, review, labelling, disclosure, party opt-outs; the decision function), [[PKG-settings-ai]] (the `ai.*` settings catalogue), [[AI-cost-controls]] (budgets and quotas per tenant, unit, user, agent and step) |
| Tenant building blocks | [[AI-agent-configuration]] (tenant assistants and agents), [[WF-ai-steps-and-agents]] (AI steps in case-type blueprints) |
| AI for administrators | [[APP-admin-copilot]] (natural-language administration that drafts reviewed changes) |
| Governance | [[AI-ai-governance-and-impact]] (AI policy, inventory, impact assessments, risk register, tenant decisions) |

**Out of scope**

- Evals and red-team suites: [[TST-evals-and-ai-testing]] (this area defines what must pass; the test node defines how)
- AI usage telemetry and dashboards: [[OBS-ai-usage]], [[RPT-platform-ai-usage-analytics]]
- Billing of AI usage: [[BIL-plans-entitlements-and-usage]] (this area produces the metered events)
- Long-running pipeline mechanics: [[WF-long-running-pipelines]] (AI pipelines run on the `ai-pipelines` task queue)
- UI panels that show AI output: persona frontend nodes such as [[APP-neutral-workspace]]
- The generic configuration lifecycle, scopes and packages that AI settings, agents and steps reuse: [[PKG-configuration-lifecycle]], [[PKG-configuration-scope-hierarchy]], [[PKG-configuration-packages]]
- Agent identities as principals: [[PKG-non-human-principals]]

<!-- section:goals -->
## Goals and non-goals

**Goals**

1. 100 percent of model calls go through the gateway; zero direct provider SDK imports outside it (CI-enforced).
2. 100 percent of model calls, agent tool calls and workflow AI steps pass the tenant AI policy decision first; zero allows when the policy cannot be loaded (fail-closed tests).
3. Zero cross-region inference, embedding or AI logging calls; proven by an automated residency test per region.
4. Zero cross-tenant or cross-case retrieval results in the isolation test suite, on every release.
5. Every AI output that reaches a party, the case record or changes case state has a recorded human approval by a named role; auto-acceptance exists only for calibrated, internal classification and extraction.
6. Every AI feature, tenant agent and blueprint with AI steps has an inventory entry, an Approved impact assessment (or inherits one for its tier) and passing evals before it is enabled.
7. Tenants can switch AI off for the whole tenant, a unit, a case type or a case and see the effect within 5 seconds.
8. Every configuration change proposed by AI (copilot or agent) is a draft reviewed and published by a human, and is traceable as AI-proposed.
9. Per-tenant AI spend stays within its configured budget, with alerts at 50, 80 and 100 percent.

**Non-goals**

- Training or fine-tuning models on tenant data. Not done without a separate decision and explicit tenant agreement.
- Autonomous agents that take actions with legal or financial effect on a case (filing, sending to parties, issuing, changing deadlines or status, payments).
- AI that decides, recommends or predicts the outcome of a dispute, damages or the credibility of a person.
- Tenant-authored code, tools that call arbitrary URLs, or full tenant-written system prompts.

<!-- section:principles -->
## Principles

| # | Principle | Enforced by |
|---|---|---|
| P1 | All model and embedding calls go through the AI gateway | ESLint `no-restricted-imports` on provider SDKs outside `packages/ai-gateway`; egress firewall allows provider endpoints only from gateway tasks |
| P2 | Inference stays in the tenant's home region; if no in-region model is available the call fails closed | Gateway route table keyed by region; residency test in CI and synthetic check per region |
| P3 | AI is off by default; tenants decide where it is on, through a versioned AI policy, not feature flags | Settings `ai.policy.enabled` and `ai.features.<key>.enabled` default false ([[PKG-settings-ai]]); flags only express platform availability and the kill switch ([[PKG-feature-flags]]); notice acceptance recorded ([[AI-tenant-ai-policy]]) |
| P4 | Retrieval is scoped by tenant, case and the caller's document permissions in the data layer | RLS on vector tables plus case and permission filters; cross-tenant and cross-case tests |
| P5 | AI assists, people decide: no AI output reaches a party or the record without approval | AI output state machine ([[AI-human-in-the-loop]]); provenance rules for workflow facts ([[WF-ai-steps-and-agents]]) |
| P6 | Every output is traceable to inputs, prompt version, model version, policy version and approver | `ai_requests` and `ai_outputs` records; audit events ([[PKG-audit-trail]]) |
| P7 | No feature, agent or AI step ships without passing evals and an Approved impact assessment for its tier | CI eval gate ([[TST-evals-and-ai-testing]]); publish gates in agent and blueprint lifecycles; feature-availability gate |
| P8 | Provider terms must exclude training on our data and provide zero retention for case content | Sub-processor review ([[SEC-vendor-sub-processor-management]]); route activation requires `terms_ref` and `zero_retention = true` |
| P9 | AI never holds more rights than the narrower of the human who invoked it and its own principal | Intersection rule in [[AI-tenant-ai-policy#policy]] and [[PKG-non-human-principals]]; matrix tests |
| P10 | AI proposes configuration; humans approve and publish through the same admin API | Copilot and agents have only read and draft tools ([[APP-admin-copilot]]); publish operations reject AI principals server-side |
| P11 | Lower scopes can only narrow AI use | Narrow-only rule in the settings resolver; property tests |

<!-- section:context -->
## Context and boundaries

```
 persona apps (neutral, secretariat, counsel, transcriber)      tenant admin console (/admin/ai/*)
        | tRPC / server actions                                     |  admin API /admin/v1/ai/*, settings ai.*
        |                                       admin copilot ------+  (drafts only)
        v                                                           v
 +---------------- regional AI layer (one per region) -------------------------------------+
 |  ai-policy.decide()  <-- published tenant AI policy, case restrictions, party opt-outs   |
 |        |                                                                                |
 |  prompt registry -> AI gateway -> guardrails -> provider endpoint (in-region, zero retention)
 |                      |   ^                                                            |
 |      budgets/quotas -+   +- RAG retrieval (pgvector, RLS, case scope, tenant knowledge) |
 |                      |                                                                |
 |  agent runtime (tools = permission-checked platform operations)                         |
 |  Temporal `ai-pipelines` workers (pipelines, workflow AI steps, agent tasks)            |
 |                      v                                                                |
 |       ai_requests / ai_outputs -> human review -> case record                          |
 +----------------------------------------------------------------------------------------+
        | OTel spans, usage events                    | audit events
        v                                             v
   OBS-ai-usage / RPT-platform-ai-usage-analytics    PKG-audit-trail
```

| Neighbour | What crosses |
|---|---|
| [[DOM-documents]], [[DOM-ebundling]] | Document versions (after malware scan and OCR) feed RAG ingestion |
| [[DOM-hearings]], [[DOM-transcribers]] | Recordings and transcripts for transcription support and summaries |
| [[PKG-authorization]], [[PKG-non-human-principals]] | Document visibility at retrieval; agent principals and permission sets |
| [[PKG-settings]], [[PKG-configuration-lifecycle]] | AI policy values, agent definitions and change sets follow the shared configuration model |
| [[WF-process-definition-model]], [[WF-human-tasks]] | AI steps in blueprints; `ai_review` tasks |
| [[INT-tenant-admin-api]] | The operations the admin copilot and the console both call |
| [[WF-long-running-pipelines]] | Long AI jobs run as Temporal activities with heartbeats |
| [[BIL-plans-entitlements-and-usage]] | AI entitlements and metered usage |
| [[SEC-privacy-controls]], [[PKG-data-retention-legal-hold-and]] | Erasure and retention apply to prompts, outputs, conversations and embeddings |
| [[TST-evals-and-ai-testing]] | Eval datasets, thresholds and the CI gate |
| [[MT-data-residency-2]] | Tenant home region drives model routing |

<!-- section:decisions -->
## Key decisions

- [[ADR-tenant-isolation]]: vector rows, AI logs, AI policy rows, agent definitions and conversations carry `tenant_id` under forced RLS.
- [[ADR-workflow-engine]] and [[ADR-temporal]]: long AI pipelines and workflow AI steps are Temporal activities on the regional cluster; payloads are encrypted by the codec.
- [[ADR-queue-technology]]: small AI follow-up jobs (re-indexing a single document) may use BullMQ.
- Taken in this overhaul (to be recorded as decision nodes): tenant AI enablement moves from feature flags to settings; tenant agents use platform-defined tools only; AI-proposed configuration is always a draft.
- Still to be recorded: AI model providers per region and gateway form; vector store choice; whether agent runtime is part of the gateway service or a sibling service (see [[ADR]] Key decisions).

<!-- section:map -->
## Capability map

| Child | Owns |
|---|---|
| [[AI-ai-gateway]] | The only route to models: provider adapters, regional routing, fallbacks, timeouts, usage events; calls the policy first |
| [[AI-prompt-management]] | Prompt templates, versions, release and pinning, tenant slots, agent base prompts and workflow step prompts |
| [[AI-rag]] | Ingestion pipeline, chunking, embeddings, vector tables, scoped retrieval (case and tenant knowledge), deletion propagation |
| [[AI-guardrails]] | Input and output checks, redaction, injection defences, grounding validator, tool-call checks |
| [[AI-human-in-the-loop]] | AI output lifecycle, reviewer roles, approval, policy acceptance for calibrated steps, kill switch |
| [[AI-ai-generated-text-labelling-and]] | Labels, disclosure wording, glossary and neutrality checks for AI text |
| [[AI-tenant-ai-policy]] | Tenant AI policy model, permission matrix and the decision function |
| [[AI-agent-configuration]] | Tenant assistants and agents: instructions, knowledge, tools, testing, publishing |
| [[AI-ai-audit-and-transparency]] | Joined AI record per tenant, case and output; admin views, signed exports, party-facing disclosure page |
| [[AI-cost-controls]] | Budgets, quotas, rate limits, allocation to units, users, agents and steps, reconciliation |
| [[AI-ai-governance-and-impact]] | AI policy (Nomology's), inventory, impact assessments, risk register, tenant decisions |
| Outside this area | [[APP-admin-copilot]] (under the tenant admin console), [[WF-ai-steps-and-agents]] (under Tasks and Workflows), [[PKG-settings-ai]] (under the settings catalogue) |

<!-- section:phasing -->
## Phasing

AI work is split so that the governance, policy and residency foundations come before any feature (see [[PLAN]]):

| When | What | Gate to pass |
|---|---|---|
| Phase 1 (core platform) | AI policy draft, AI system inventory skeleton, provider sub-processor review started; `ai.*` keys registered in the settings registry with defaults off | Policy approved by management |
| Phase 3 (first domain slice) | Document pipeline emits the events RAG will consume; OCR text stored with page references | Event contract approved |
| AI phase, part 1 | Gateway, tenant AI policy and decision function, prompt management, RAG, guardrails, HITL, cost controls, evals; first features (case summary, classification) | Residency test, fail-closed policy tests, cross-tenant retrieval test, eval thresholds and Approved impact assessment per feature |
| AI phase, part 2 | Workflow AI steps (always-review mode first, auto-accept after calibration), admin copilot (explain and diagnose first, drafting second) | Copilot escalation red team at 100 percent; provenance validator in blueprint publish |
| AI phase, part 3 | Tenant agents with read tools, then propose tools | Agent safety pack; tool intersection tests |
| After first AI feature | Production monitoring, AI incident runbook, internal ISO/IEC 42001 audit | Monitoring live; incident drill done |

<!-- section:risks -->
## Risks and open questions

- [ ] Choose providers per region and confirm in-region availability and zero-retention terms for suitable chat and embedding models in India, Singapore and the US (and on Azure). Owner: AI platform lead.
- [ ] Confirm with legal whether any feature is high-risk under the EU AI Act for tenants or parties in the EU (Annex III covers AI used to assist judicial authorities or used similarly in alternative dispute resolution; Article 6(3) may exclude narrow procedural or preparatory tasks) [R2]. Assumption: Annex III obligations apply from 2 August 2026 unless the proposed EU "digital omnibus" changes postpone them; legal to confirm current dates. Article 50 transparency duties apply from 2 August 2026 [R3].
- [ ] Decide which institutions allow AI drafting assistance for neutrals at all, and what disclosure they require (tenant decision, recorded in the tenant AI policy).
- [ ] Confirm provider contract terms: no training on our data, zero retention, abuse-monitoring exemptions. Owner: legal and security.
- [ ] Risk: tenant agents or copilot drafts used to widen access or AI use. Mitigated by intersection rule, draft-only tools and maker-checker.
- [ ] Risk: auto-accepted classifications misroute filings. Mitigated by calibration, sampling and automatic downgrade ([[WF-ai-steps-and-agents]]).
- [ ] Risk: cost overrun from long documents (eBundles of thousands of pages). Mitigated by [[AI-cost-controls]].
- [ ] Risk: hallucinated content in summaries entering the record. Mitigated by grounding checks and mandatory review.
- [ ] Align with the Singapore Model AI Governance Framework for Generative AI [R4] and India AI Governance Guidelines [R5] for client assurance packs (both voluntary).

<!-- checks -->
## Template checks

<!-- check:ownership -->
### Ownership and governance

Accountable owner: the AI platform and governance lead (to be named), reporting to the CTO. Specialist reviewers: security lead (guardrails, policy, agents), legal (labelling, disclosure, EU AI Act, opt-outs), product (tenant controls), workflow lead (AI steps). Changes to this area's principles are proposed as decision nodes and approved by the CTO.

<!-- check:boundaries -->
### Scope and boundaries

The context table lists each neighbouring area and what crosses the boundary. Tenant administration of AI has one home ([[AI-tenant-ai-policy]] for behaviour, [[PKG-settings-ai]] for keys); the generic configuration lifecycle, scopes and packages stay in Platform Packages; agent principals stay in Authorization; AI steps live under Tasks and Workflows but use this layer. Out-of-scope items each name their owning node. Each user-facing AI feature has its own node that consumes this layer.

<!-- check:principles -->
### Principles and enforcement

Each of the eleven principles names its enforcement: lint and egress firewall (P1), route table and residency test (P2), default-off settings and notice records (P3), RLS and isolation tests (P4), the output state machine and provenance validator (P5), logged records (P6), CI eval and publish gates (P7), sub-processor review and route activation checks (P8), the intersection rule with matrix tests (P9), draft-only tools and server-side rejection of AI principals on publish (P10), and the narrow-only resolver with property tests (P11).

<!-- check:decisions -->
### Decisions linked

Recorded: tenant isolation, workflow engine, Temporal, queue technology. Taken in this overhaul and to be recorded: settings instead of flags for tenant AI enablement; platform-defined tools only for tenant agents; AI-proposed configuration is always a draft. Open and blocking: providers per region (blocks gateway activation), gateway form, vector store, agent runtime placement.

<!-- check:compliance -->
### Regulatory and control mapping

| Obligation / control | Implemented in | Evidence |
|---|---|---|
| ISO/IEC 42001 AI policy, impact assessment, risk treatment [R1] | [[AI-ai-governance-and-impact]] | Approved policy, assessments per AI system, risk register |
| Human oversight of AI affecting cases (EU AI Act Art. 14 and 26 where applicable [R2]) | [[AI-human-in-the-loop]], [[WF-ai-steps-and-agents]] | Approval records per output, sampling records |
| Transparency about AI use (EU AI Act Art. 50 where applicable [R3]; institution rules) | [[AI-tenant-ai-policy]], [[AI-ai-generated-text-labelling-and]] | Transparency statements, labels, disclosure records |
| DPDP / GDPR / PDPA purpose limitation and minimisation | [[AI-guardrails]], [[AI-rag]], [[AI-tenant-ai-policy]] | Field-level inventory per feature, redaction logs, opt-out records |
| Residency per tenant region | [[AI-ai-gateway]] | Route table, residency test results |
| ISO 27001 supplier relationships (AI providers) | [[SEC-vendor-sub-processor-management]] | Signed terms, sub-processor list |
| Erasure and retention | [[PKG-data-retention-legal-hold-and]] | Deletion job logs covering embeddings, conversations and AI logs |
| Voluntary frameworks: Singapore MGF for GenAI [R4], India AI Governance Guidelines [R5] | [[AI-ai-governance-and-impact]] | Mapping table in the client assurance pack |

EU AI Act applicability is an open question for legal.

<!-- check:regions -->
### Tenancy and residency

Every runtime part of the AI layer is per region: gateway and agent runtime tasks, policy snapshots, route table entries, vector tables, conversations, AI logs and eval runs on production-like data. Global parts are limited to prompt templates, the tool registry, the feature catalogue (code, no personal data) and the AI system inventory (no case data). If a region lacks a suitable model, features are unavailable there rather than routed elsewhere, unless a tenant agrees in writing to a named alternative, approved by platform security and legal and recorded as `ai.models.out_of_region_exception`.

<!-- check:quality -->
### Quality targets

Inherited targets: gateway overhead p95 under 50 ms; policy decision p99 under 2 ms after load; policy change enforced within 5 seconds; residency and fail-closed tests at 100 percent; per-feature eval thresholds; AI availability does not affect case-process availability because every AI path has a non-AI fallback.

<!-- check:phase -->
### Phasing

The phasing table puts AI governance and the `ai.*` settings registry in Phase 1 and the document event contract in Phase 3. Within the AI phase the tenant AI policy ships with the gateway, before any feature; workflow AI steps, the copilot and tenant agents follow in that order, each with its own gate. Nothing that lets AI propose configuration ships before maker-checker and the change-set API exist.

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
    "excerpt": "Article 50 applies from 2 August 2026. Deployers must disclose AI-generated text published to inform the public on matters of public interest, unless the content has undergone human review or editorial control and a person holds editorial responsibility.",
    "id": "R3",
    "issuer": "European Commission",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689, Article 50 (Commission FAQ)",
    "status": "applies from 2 August 2026",
    "title": "Transparency obligations under Article 50 of the AI Act",
    "url": "https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act"
  },
  {
    "excerpt": "Nine dimensions for trusted generative AI: accountability, data, trusted development and deployment, incident reporting, testing and assurance, security, content provenance, safety and alignment R&D, and AI for public good. Released 30 May 2024.",
    "id": "R4",
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
    "id": "R5",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "India AI Governance Guidelines",
    "status": "guidance, non-binding",
    "title": "India AI Governance Guidelines: Enabling Safe and Trusted AI Innovation",
    "url": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc2025115685601.pdf"
  }
]
```

<!-- end -->
