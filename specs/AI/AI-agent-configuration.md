---
id: "AI-agent-configuration"
title: "Tenant-configured assistants and agents"
parent: "AI"
order: 8
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "No-code, versioned tenant assistants built from platform base prompts, tenant instructions, scoped knowledge and permission-bound read and propose tools; tested, approved and published through the configuration lifecycle"
links: []
rev: 1
syncHash: "65e6efa59741c498"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.8 Tenant-configured assistants and agents

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> No-code, versioned tenant assistants built from platform base prompts, tenant instructions, scoped knowledge and permission-bound read and propose tools; tested, approved and published through the configuration lifecycle

<!-- section:purpose -->
## Intended use

Tenant-configured assistants and agents let an institution build its own AI helpers on the platform's AI layer, without code and without new risk: a **"Rules and practice assistant"** for secretariat staff that answers from the institution's rules and practice notes, a **"Case navigator"** for tribunal secretaries that finds where facts appear in the record, or a **"Correspondence helper"** that drafts routine letters for a case manager to check and send.

An **agent** is a versioned configuration object (kind `ai_agent`, lifecycle from [[PKG-configuration-lifecycle]]) made of:

| Part | What the tenant sets | Bounded by |
|---|---|---|
| Identity | Name, description, owner, icon, conversation starters | Naming rules; labelled as AI everywhere |
| Surface | Where it appears: secretariat console panel, neutral workspace panel, transcriber workspace panel, tenant admin console, or `workflow_only` | Surfaces allowed by `ai.agents.allowed_surfaces` |
| Audience | Which roles (and optionally units) may use it | Roles that hold `ai.generation:create` for `custom_agents` |
| Instructions | Up to 4,000 characters of plain-language guidance | Inserted into a platform base prompt; validated ([[AI-prompt-management]]) |
| Knowledge | Tenant knowledge collections, the current case's documents and metadata, glossary | Data scopes allowed by the policy ([[AI-tenant-ai-policy]]) |
| Tools | Chosen from the platform tool registry (read and propose tools) | Each tool needs a permission; intersection rule |
| Output | Where results may go (shown to the user only, saved as a private note, proposed as a draft or task) | Review rules ([[AI-human-in-the-loop]]) |
| Limits | Monthly budget, per-user daily quota, max steps per turn | [[AI-cost-controls]], [[PKG-settings-ai]] |

**Who uses it:** `ai_admin` and delegated agent builders (`ps.ai.agent_builder`) create and test agents in `/admin/ai/agents`; a second admin approves; users in the audience use the published agent in their workspace; workflow designers bind published agents to `agentTask` steps ([[WF-ai-steps-and-agents]]).

**Decision supported:** finding and organising information faster, and preparing drafts that a person then checks. An agent never decides anything about a case.

**Functional requirements**

| ID | Requirement |
|---|---|
| AGT-FR-1 | Agents are stored as `ai_agents` (identity) and immutable `ai_agent_versions` (configuration snapshot); only one version per agent is `published` at a time |
| AGT-FR-2 | Building, testing, approving and publishing use the same admin API operations (`/admin/v1/ai/agents/*`) from the console, bulk import and [[APP-admin-copilot]] |
| AGT-FR-3 | Publishing requires: a passing evaluation run for that version, an `allow` from the AI policy for the agent's surface, data scopes and tools, a second approver (maker-checker), and an inventory entry ([[AI-ai-governance-and-impact]]) created automatically |
| AGT-FR-4 | On publish, the platform creates or updates the agent's `ai_agent` principal ([[PKG-non-human-principals]]) and proposes a permission set `ps.ai.agent.<agentKey>` holding exactly the permissions its tools need; the grant is made with `ai_agent.principal:assign` and a `security_admin` checker, as part of the same change set |
| AGT-FR-5 | Every tool call is authorised against the intersection of the invoking user's permissions, the agent principal's permission set, the bound tools and the AI policy, at call time |
| AGT-FR-6 | Tools are platform-defined; tenants select and configure them but cannot define new tools that execute code or call external URLs at launch |
| AGT-FR-7 | Agents cannot use tools that send anything to a party, file, issue, change case status, change deadlines, move money, or change users, roles or settings |
| AGT-FR-8 | Conversations pin the agent version they started on; a newly published version applies to new conversations |
| AGT-FR-9 | Tenant admins can suspend an agent at once (`ai.agent:update` → `suspended`), which ends active conversations at the next turn |
| AGT-FR-10 | Agents are labelled as AI in every surface, and their outputs follow the labelling rules in [[AI-ai-generated-text-labelling-and]] |

Pattern borrowed from: agents defined by instructions, topics and actions with a trust layer around them [R4]; agents that act only with the invoking person's access, with admin control over who may create agents [R5]; admin data policies over agent connectors and knowledge, and controls over publishing [R6]; tool-call policies checked before and after each call that can only restrict, never expand [R7].

<!-- section:outofscope -->
## Out-of-scope uses

| Use not allowed | How it is prevented |
|---|---|
| Agents that predict outcomes, assess the merits or the credibility of a witness, or recommend how to decide | Base prompt constraints; instruction validator flags such instructions; mandatory red-team pack with merits-prediction prompts must pass before publish; neutrality output filter ([[AI-guardrails]]) |
| Drafting procedural orders or awards | Reserved for the platform-built `drafting_assist` feature (risk tier T3) with its own impact assessment; agent tools cannot write into order or award drafts |
| Party-facing agents (for example a chatbot answering investors in SEBI ODR matters) | Surface not offered at launch; would mean AI output reaching a party without review, which [[AI-human-in-the-loop]] forbids. Open question below |
| Cross-case questions ("show me similar cases") | Retrieval requires one `caseId`; tenant knowledge collections hold no case documents (validator blocks uploads tagged as case material) |
| Autonomous actions with legal or financial effect | No such tools exist in the registry; write-like tools only create drafts or proposals |
| Calling external websites or tenant systems | No web or HTTP tools at launch; integrations go through [[INT-connections-admin]] in a later phase, each as a reviewed platform tool with a connector data policy ([[INT-connector-data-policies]]) |
| Tenant-authored full system prompts | Instructions are a bounded slot inside the platform base prompt |
| Training or fine-tuning a model on tenant data | Not offered ([[AI-tenant-ai-policy]] platform bound) |

<!-- section:models -->
## Models and providers

Agents request a capability, not a model: `chat.large` for agents with case-document knowledge, `chat.small` for short lookups. The route is chosen by [[AI-ai-gateway]] from the tenant's region, limited to providers the tenant allows (`ai.models.allowed_providers`) and to zero-retention routes. Tenants cannot pick a model version; this keeps eval results valid and avoids silent drift.

Tool calling uses the provider's native function-calling where the route supports it, wrapped by our own schema validation; where a route lacks native tool calling, the agent runtime uses a structured-output plan step (JSON schema) instead. Both are tested in the agent eval pack.

When the platform changes a route's model version, every published agent on that capability re-runs its evaluation set; an agent that fails is marked `needs_attention` and stays on the previous route version until the tenant fixes it or a 14-day (proposed) window ends, after which it is suspended with notice.

<!-- section:context -->
## Inputs and context sources

**Knowledge source kinds**

| Kind | Content | Scope at retrieval | Who manages it |
|---|---|---|---|
| `tenant_library` | Institution rules, practice notes, guidance notes, model clauses, FAQs, fee schedules as text, internal procedures | Tenant; collection-level visibility by role and unit | `content_admin` or `ai_admin` in `/admin/ai/knowledge` |
| `case_documents` | Documents of the case in context, as visible to the invoking user | One case; document permissions and ethical walls ([[PKG-ethical-walls-conflict-based]]) | Nobody configures content; scope only |
| `case_metadata` | Case timeline, stage, deadlines, roles of participants | One case | Scope only |
| `glossary` | Tenant terminology ([[I18N-platform-glossary-and]], [[PKG-tenant-terminology-and-copy]]) | Tenant | `content_admin` |
| `help_centre` | Published help articles ([[DOC-tenant-facing-help-centre]]) | Platform and tenant | Content team |

**Tenant library rules.** Uploads go through malware scanning and OCR like case documents, are chunked and embedded by the `rag-ingest` workflow on the `ai-pipelines` task queue into a separate collection type `tenant_knowledge` ([[AI-rag]]). Each collection has an owner, a review date (proposed 12 months) and a status (`active`, `stale`, `archived`); stale collections show a warning in the builder. A personal-data detector runs on upload; collections with personal data above a threshold are blocked unless the uploader confirms a lawful reason, which is recorded.

**Minimisation.** The agent runtime sends only: the base prompt, the tenant instructions, the user's message, retrieved passages relevant to the turn (token budget per agent, default 16,000), and tool results trimmed to declared output fields. Party identifiers are pseudonymised by default according to the agent's redaction policy (stricter of the tenant setting and the knowledge kinds used). Deliberation notes are never available to tenant agents.

**Party opt-outs and case restrictions** apply automatically: passages from an opted-out party's submissions are filtered out, and a restricted case disables agents that use `case_documents` on that case ([[AI-tenant-ai-policy#policy]]).

<!-- section:prompts -->
## Prompt design and versioning

Each surface has a platform base prompt, released through [[AI-prompt-management]] like any other prompt (`agent.base.secretariat@v`, `agent.base.neutral@v`, `agent.base.transcriber@v`, `agent.base.admin@v`, `agent.base.workflow@v`). Structure:

1. Platform constraints (fixed): neutral tone; no outcome prediction, legal advice to a side or credibility assessment; answer only from supplied passages and tool results; cite passages; say when the answer is not in the sources; never claim to have taken an action that was only proposed.
2. Tool usage rules (fixed): which tools exist, when to confirm with the user.
3. **Tenant instructions slot** `{tenantInstructions}`, wrapped in delimiters and introduced as lower priority than (1) and (2).
4. Untrusted content block: passages and tool results, delimited ([[AI-guardrails]]).
5. Output format.

**Instruction validator** (runs on save and before publish): maximum 4,000 characters; plain text and simple lists only; flags phrases that try to override platform rules ("ignore previous", "you are now", "do not cite"), requests for prohibited uses, personal data, links and hidden characters. Flags block publish unless removed; there is no override.

**Versioning.** Each agent version snapshots: base prompt key and version, instructions text and hash, knowledge source IDs and their index versions, tool keys and tool configuration, audience, limits. Snapshots are immutable; rollback is publishing an earlier version again (audited).

<!-- section:guardrails -->
## Guardrails

**Tool registry (launch set).** Each tool declares a class, the permission it needs, input and output schemas, and whether the user must confirm.

| Tool key | Class | Needs permission | Confirmation | Effect |
|---|---|---|---|---|
| `case.search_documents` | read | `case.document:read` | No | Hybrid search in the current case ([[AI-rag]]) |
| `case.get_timeline` | read | `case:read` | No | Case events and stage |
| `case.list_deadlines` | read | `case.deadline:read` | No | Current deadlines and their sources |
| `case.get_participants` | read | `case:read` | No | Roles and names (pseudonymised unless policy allows names) |
| `tenant.search_knowledge` | read | `ai.knowledge:read` | No | Search allowed tenant collections |
| `calendar.compute_deadline` | read | none (pure) | No | Business-day arithmetic ([[PKG-calendars-and-deadline]]) |
| `case.note.draft_private` | propose | `case.note.internal:create` | Yes | Saves a private note for the invoking user, labelled AI-assisted |
| `message.draft` | propose | `case.message:create` | Yes | Creates a draft in the case outbox; a person must open, edit and send it ([[PKG-notifications]]) |
| `task.propose` | propose | `case.task:create` | Yes | Creates a proposed human task for the invoking user or their queue ([[WF-human-tasks]]) |
| `document.tags.propose` | propose | `case.document:update` | Yes | Proposes tags; applied only when the user accepts |

**Guardrails on tool use** (agent runtime, region-local service `ai-agents` next to `ai-gateway`):

1. Before each call: policy decision, permission intersection (AGT-FR-5), argument schema validation, `caseId` must equal the conversation's case, rate and step limits.
2. After each call: output schema validation, field trimming, redaction per policy, injection markers on any document text in results.
3. A tenant-level **tool policy** (`ai.agents.tool_policies`) can block or require confirmation for a tool for some roles or units, and can only restrict (pattern from [R7]).
4. Loop limits: maximum 8 model steps and 15 tool calls per user turn (platform bounds; tenants can lower).
5. Output: same output guardrails as every AI call (schema, output handling, neutrality filter, grounding for answers that cite case documents).

**Refusal behaviour.** When the agent is asked for a prohibited use it replies with a fixed, localised refusal ("I can't assess the merits or predict outcomes. I can help you find the relevant documents.") and records a `prohibited_request` flag.

<!-- section:oversight -->
## Human oversight

| Control | Who | Mechanism |
|---|---|---|
| Build and test | Agent builder (`ps.ai.agent_builder`) | Builder in `/admin/ai/agents/[agentId]` with tabs Overview, Instructions, Knowledge, Tools, Access, Test, Evaluate, Versions, Usage |
| Approve and publish | A second `ai_admin` or `tenant_admin` who is not the author ([[PKG-separation-of-duties]]) | Review screen shows the diff from the published version, eval results, risk tier and policy decision |
| Use | Users in the audience | Every agent answer is labelled; proposals need explicit confirmation; drafts are edited and sent by the person |
| Monitor | `ai_admin`, AI governance lead (Nomology) for tier T2 agents | Usage tab: conversations, tool calls by class, refusals, flags, thumbs-down feedback, cost |
| Suspend | `ai_admin`, `tenant_admin`, platform (for safety incidents) | Immediate; audited; users see "This assistant is paused by your administrator" |
| Periodic review | Agent owner | Review date per agent (proposed every 6 months); overdue agents flagged on the AI overview page |

**Risk tier of an agent** is computed, not chosen: T1 if it uses only `tenant_library`, `glossary` and `help_centre` and returns results only to the user; T2 if it reads case documents or uses any propose tool. Tenant agents cannot be T3. T2 agents need the tenant owner or a tenant admin as approver, and their inventory entry is visible to Nomology's AI governance lead.

<!-- section:evaluation -->
## Evaluation

**Two evaluation sets must pass before publish:**

| Set | Owner | Content | Threshold |
|---|---|---|---|
| Tenant test cases | Agent builder | At least 10 (proposed) questions or tasks with expected behaviour: answer should cite source X, should refuse, should call tool Y, should say "not in the sources" | 90 percent pass (proposed); every "should refuse" case must pass |
| Platform agent safety pack | Nomology AI team ([[TST-evals-and-ai-testing]]) | Prompt injection in documents and knowledge, requests for merits predictions or advice, cross-case requests, attempts to use tools outside scope, attempts to extract the base prompt | 100 percent of tool-scope and cross-case tests; at least 98 percent of injection tests (aligned with [[AI-guardrails]]) |

Tests run in the tenant's sandbox on synthetic or masked cases ([[PKG-configuration-lifecycle]] sandbox), never on live case data by default. A builder holding access to a live case may run an unsaved "try as me" test on it; outputs are not stored and the run is audited.

**Automatic re-evaluation** on: new agent version, base prompt release, model route change, knowledge index rebuild. Results are kept with the agent version and shown on the review screen.

**Production signals:** refusal rate, thumbs-down rate, proposal acceptance rate, "not in the sources" rate, grounding score, tool error rate per agent. Thresholds that open a review: thumbs-down above 15 percent over 50 conversations, or grounding score below the feature threshold for 3 days (proposed).

<!-- section:failure -->
## Failure modes and fallback

| Failure | Protection |
|---|---|
| Instructions push the agent beyond its purpose | Platform constraints take precedence; validator blocks override phrases; safety pack must pass |
| Knowledge collection out of date (old rules version) | Collections carry a review date and rules version; answers cite the collection and version; stale warning |
| Injected instructions inside a case document | Untrusted-content delimiters; tool scope fixed by the version, not by the conversation; injection flag raised |
| Agent proposes a wrong task or message | Proposals are drafts; the user confirms; drafts can be discarded |
| Model route change degrades the agent | Automatic re-evaluation; `needs_attention` state; previous route kept for the window |
| Agent runtime down | Panel shows "This assistant is unavailable"; no case process depends on agents |
| Runaway loop | Step and tool-call limits; per-turn token cap; budget reservation |

<!-- section:cost -->
## Cost and limits

Agents spend from the tenant's AI budget and, if set, the agent's own monthly cap (the `monthly_cap` field of the agent definition) and the user's daily quota (`ai.quota.custom_agents.user_daily_requests`, default 50). Each turn reserves an estimate (base prompt plus retrieval budget plus expected tool steps). Testing and evaluation runs are charged to the tenant at a separate `evaluation` usage category so that admins can see build cost apart from use cost; the platform safety pack is free to tenants. Typical turn: 8,000 to 20,000 input tokens and 500 to 1,500 output tokens (planning figure, to be replaced with measurements in [[OBS-ai-usage]]).

<!-- section:logging -->
## Logging and audit

| Record | Content | Retention |
|---|---|---|
| `ai_agent_versions` | Full configuration snapshot, author, approver, eval run IDs | Life of the tenant contract plus 6 years (proposed) |
| `ai_agent_conversations` | Agent version, user, case, started and ended times, turn count, flags | `ai.retention.conversation_days` (default 30) for message bodies; metadata with the case |
| `ai_agent_turns` | Request IDs into `ai_requests`, tool calls with arguments hash and result status, proposal IDs | As `ai_requests` |
| Message bodies | Encrypted in regional object storage, like other AI bodies | As above; deleted when the conversation retention ends unless a proposal was accepted (then kept with the case) |
| Audit events | `admin.ai.agent_created`, `admin.ai.agent_submitted`, `admin.ai.agent_approved`, `admin.ai.agent_published`, `admin.ai.agent_suspended`, `ai.agent.tool_called`, `ai.agent.proposal_accepted` | [[PKG-audit-trail]] |

Admins see usage metrics and flags, not conversation text. Reading a conversation's text needs `ai.audit:read` plus a recorded reason, and is itself audited (similar in spirit to retention and history controls offered to legal teams [R8]).

<!-- section:questions -->
## Open questions

- [ ] Do tenants want party-facing procedural help agents (answering only from published rules and FAQs, never about a specific case)? Needs a policy decision on unreviewed AI output to parties and an impact assessment. (owner: CTO, legal)
- [ ] Minimum number of tenant test cases before publish (proposed 10). (owner: AI platform lead)
- [ ] Should tenants be able to connect external knowledge (SharePoint, document management) through connectors in phase 2? (owner: integrations group)
- [ ] Default conversation retention (proposed 30 days) and whether neutrals' conversations need a shorter default. (owner: legal)
- [ ] Should Nomology review every T2 agent before publish, or only monitor? Proposed: monitor, with right to suspend. (owner: AI governance lead)

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Agents are tier T1 or T2 by computed rule; T3 is not available to tenant agents. T2 agents need a tenant owner or tenant admin approver and appear in the AI system inventory as children of `AIS-CUSTOM-AGENTS`, so they fall under the ISO/IEC 42001 inventory and impact assessment process [R1]. The worst credible harm is a misleading answer about a case or rules that a staff member relies on; mitigated by citations, refusal rules, labels and proposal-only tools.

<!-- check:privacy -->
### Privacy and redaction

Only the current case and allowed tenant collections are retrievable; tool results are trimmed to declared fields; party identifiers are pseudonymised by default; opted-out parties' submissions are filtered; conversation bodies are deleted after the configured retention; knowledge uploads are scanned for personal data. Supports PDPC guidance on minimisation in AI systems [R3].

<!-- check:residency -->
### Residency

The agent runtime, retrieval, model calls, conversation storage and logs run in the tenant's home region; routes are chosen by the gateway from in-region zero-retention routes only; the platform tool registry and base prompts are global code without tenant data.

<!-- check:security -->
### AI security and tenant isolation

Tools are platform-defined with fixed schemas and permissions; every call is authorised against the intersection of user, agent principal, bound tools and policy; no tools with external effect exist; injection defences on documents and knowledge; loop limits; instruction validator; mapped to OWASP LLM01 prompt injection and LLM06 excessive agency [R2].

<!-- check:oversight -->
### Human oversight

Maker-checker publishing; proposals and drafts always need a person to confirm or send; admins monitor flags and feedback; suspension is immediate; periodic owner review dates.

<!-- check:evals -->
### Evaluation

Tenant test cases plus the platform safety pack must pass before publish, with re-runs on any version, base prompt, model or index change; failing agents move to `needs_attention`.

<!-- check:monitoring -->
### Production monitoring and AI incidents

Per-agent refusal, thumbs-down, acceptance, grounding and tool-error rates with review thresholds; injection and prohibited-request flags feed [[OBS-security-events]] when repeated.

<!-- check:cost -->
### Cost and limits

Tenant budget, optional per-agent cap and per-user daily quota; per-turn reservation; step and tool-call limits; evaluation usage reported separately.

<!-- check:audit -->
### Audit and traceability

Every version is an immutable snapshot linked to author, approver and eval runs; every turn links to `ai_requests` rows with prompt, model and policy versions; tool calls and accepted proposals are audit events.

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
    "body": "OWASP Foundation",
    "excerpt": "Risk list including prompt injection, sensitive information disclosure, improper output handling, excessive agency, system prompt leakage, vector and embedding weaknesses, misinformation and unbounded consumption.",
    "id": "R2",
    "ident": "OWASP Top 10 for LLM Applications",
    "kind": "standard",
    "title": "OWASP Top 10 for Large Language Model Applications",
    "url": "https://genai.owasp.org/llm-top-10/",
    "version": "2025"
  },
  {
    "excerpt": "Guidance on consent, notification, data minimisation and accountability when personal data is used to develop or deploy AI systems.",
    "id": "R3",
    "issuer": "Personal Data Protection Commission Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Advisory Guidelines on Use of Personal Data in AI Recommendation and Decision Systems",
    "status": "advisory",
    "title": "Advisory Guidelines on Use of Personal Data in AI Recommendation and Decision Systems",
    "url": "https://pdpc.gov.sg/guidelines-and-consultation/2024/02/advisory-guidelines-on-use-of-personal-data-in-ai-recommendation-and-decision-systems"
  },
  {
    "excerpt": "Trust layer features: grounding in customer data, data masking, toxicity detection, audit trail and feedback, and zero data retention agreements with third-party model providers.",
    "id": "R4",
    "kind": "vendor",
    "title": "Agentforce Developer Guide: Trust Layer",
    "url": "https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html",
    "vendor": "Salesforce"
  },
  {
    "excerpt": "An agent acts for the person using it and can only access what that person can access; instructions and tools can further limit it. Admins choose who may create agents (all users, selected groups or no users); owners restrict who can use and edit an agent.",
    "id": "R5",
    "kind": "vendor",
    "title": "Rovo agent permissions and governance",
    "url": "https://support.atlassian.com/rovo/docs/rovo-agent-permissions-and-governance/",
    "vendor": "Atlassian"
  },
  {
    "excerpt": "Admins govern agent actions, connectors, knowledge sources, HTTP requests, channel publication and authentication through data policies; can turn off publishing of agents that use generative AI for a tenant; makers see a security warning and risk assessment before publishing; maker activity is audited.",
    "id": "R6",
    "kind": "vendor",
    "title": "Microsoft Copilot Studio: Security and governance",
    "url": "https://learn.microsoft.com/en-us/microsoft-copilot-studio/security-and-governance",
    "vendor": "Microsoft"
  },
  {
    "excerpt": "Agent access policies are evaluated before a tool runs and after it returns, can block, filter or flag for review, apply to users, groups, agents and tools, and can only further restrict what an agent can do, never expand it.",
    "id": "R7",
    "kind": "vendor",
    "title": "About agent access policies",
    "url": "https://docs.glean.com/administration/protect/ai-security/agent-access-policies",
    "vendor": "Glean"
  },
  {
    "excerpt": "Customers set a workspace retention period for data such as assistant queries, from hours after processing up to 30 days after the agreement ends; some stores have their own retention setting.",
    "id": "R8",
    "kind": "vendor",
    "title": "Understanding Retention Policies",
    "url": "https://help.harvey.ai/articles/understanding-retention-policies",
    "vendor": "Harvey"
  }
]
```

<!-- end -->
