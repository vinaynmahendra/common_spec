---
id: "APP-admin-copilot"
title: "Admin copilot"
parent: "APP-tenant-admin-console"
order: 2
type: "feature"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "Natural-language assistant in the tenant admin console that explains configuration, diagnoses access and drafts change sets through the same admin API, as the invoking admin and never with more rights; humans review, approve and publish"
links: []
rev: 1
syncHash: "d00b4e2d0a3353fd"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.5.2 Admin copilot

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Natural-language assistant in the tenant admin console that explains configuration, diagnoses access and drafts change sets through the same admin API, as the invoking admin and never with more rights; humans review, approve and publish

<!-- section:purpose -->
## Intended use

The admin copilot lets tenant administrators run the platform in plain language: *"Why can't Priya see the Singapore office cases?"*, *"Turn on SMS reminders for SEBI ODR conciliation, 2 days before each deadline"*, *"Create a read-only role for our auditors"*, *"Add a classification step after filing intake that sorts documents into our filing categories"*. It explains, finds and **drafts**; it never approves, publishes or executes.

**Where it appears:** a side panel on every page of the tenant admin console ([[APP-tenant-admin-console]]) that knows the page in view, and a full page at `/admin/copilot`. Change drafts it creates appear in the normal review queue at `/admin/changes` ([[APP-admin-change-history]]).

**How it works, in one line:** the copilot is a platform-defined system agent (`copilot.admin`, an `ai_agent` principal per [[PKG-non-human-principals]]) whose tools are the **typed read and draft operations of the tenant admin API** ([[INT-tenant-admin-api]]), so every proposal is a normal configuration draft that follows [[PKG-configuration-lifecycle]]. This is shared-model AI principle 1 to 4 in practice: same API, no extra rights, AI proposes and humans approve, everything audited.

**Supported jobs**

| Job | Example | Output |
|---|---|---|
| Explain | "What does `case.deadline.reminder_offsets` do and where is it set?" | Answer with links to the setting, its source scope and lock ([[PKG-settings-catalogue]]) |
| Diagnose access | "Why can't this user open case 2026/014?" | Result of the access explainer ([[PKG-access-explainer]]), in plain words, with the rule that denied |
| Find | "Which case types send WhatsApp notices?" | List with links |
| Draft configuration | Roles and permission sets, settings at tenant / unit / case-type scope, notification templates and policies, decision-table rows, blueprint edits including AI steps ([[WF-ai-steps-and-agents]]), agent drafts ([[AI-agent-configuration]]), webhook endpoints (without secrets) | A change set in `draft` with a readable diff and an explanation |
| Prepare bulk work | "Invite these 40 people as secretariat in the Singapore office" (pasted list) | A bulk job draft with dry-run results ([[APP-bulk-admin-operations]]) |
| Review help | "Summarise what this pending change set does and what it affects" | Plain-language summary of a diff, impacted users and running cases; the reviewer still decides |
| Troubleshoot | "Why did our webhook deliveries fail last night?" | Summary of delivery metadata (status codes, timings), never response bodies beyond what the console shows |

**Functional requirements**

| ID | Requirement |
|---|---|
| COP-FR-1 | The copilot calls only operations listed in its tool manifest, generated from the tenant admin API OpenAPI document and filtered to operation classes `read` and `draft` |
| COP-FR-2 | Each tool call is authorised as the invoking admin, intersected with the copilot principal's permission set `ps.ai.copilot_admin`; the copilot never holds a permission the admin lacks |
| COP-FR-3 | All proposed changes are written through `POST /admin/v1/change-sets` as `draft` with `via = copilot`, `copilot_run_id`, `author_membership_id = <invoking user>`, the conversation reference and a generated explanation |
| COP-FR-4 | Drafts are validated by the same server validators as console edits before they are shown as ready; an invalid draft is shown with its errors, never silently fixed |
| COP-FR-5 | The copilot cannot submit for review, approve, publish, roll back, execute bulk jobs, rotate secrets, create API keys, impersonate, approve support access or grant itself anything |
| COP-FR-6 | Every answer that states a configuration fact links to the setting, role or object it came from; facts that cannot be linked are not stated |
| COP-FR-7 | Copilot use is controlled by `ai.copilot.enabled` and by the `admin_copilot` feature in the tenant AI policy ([[AI-tenant-ai-policy]]) |
| COP-FR-8 | The copilot has no access to case documents, transcripts or messages; it sees configuration, directory metadata needed for administration, and (if the admin holds `audit.log:read`) audit metadata |

Pattern borrowed from: generative AI used to author flows and configuration that people then review, within a trust layer that masks data and keeps an audit trail [R3], and agent publishing and data controls held by administrators [R4].

<!-- section:outofscope -->
## Out-of-scope uses

| Not allowed | Prevention |
|---|---|
| Making changes live | No publish, approve, execute or rollback tools in the manifest; server rejects these operations for any request carrying the copilot principal |
| Raising anyone's access, including its own | Intersection rule; drafts that grant admin roles are allowed only as drafts and always require a second approver; drafts that change `ai.copilot.*` or `ps.ai.copilot_admin` are refused (self-modification block) |
| Reading case content to answer admin questions | No case-content tools; access diagnosis uses the explainer, which returns rules and decisions, not documents |
| Acting for platform staff across tenants | Tenant console only; a platform-console copilot is an open question |
| Handling secrets | Secret fields are write-only in the API and are never shown to or drafted by the copilot; it tells the admin to enter the secret in the form |
| Answering legal questions ("is this deadline lawful?") | Refusal with a pointer to the institution's rules owner; configuration facts only |

<!-- section:models -->
## Models and providers

Capability `chat.large` with tool calling, routed in the tenant's home region by [[AI-ai-gateway]] under the tenant's provider allow-list and zero-retention routes. A `chat.small` route classifies the request (explain, diagnose, draft, bulk) to choose the tool subset and reduce tokens. Model versions are pinned per route; a change re-runs the copilot evaluation set before activation.

<!-- section:context -->
## Inputs and context sources

| Input | Source | Notes |
|---|---|---|
| Page context | Current admin page, selected object and draft (if any) | Sent as identifiers plus the fields on screen |
| Setting definitions | Typed registry in `@nomology/settings` (description, type, bounds, scopes, lock, permission, effect timing) | Lets the copilot only name keys that exist |
| Current configuration | Admin API read operations, as the admin | Resolved values with their source scope |
| Permission catalogue and roles | [[PKG-permission-catalogue]], [[PKG-roles-and-permission-sets]] | For drafting roles and explaining access |
| Directory metadata | Users, groups, units: names, emails, roles, status | Needed for user administration; no case participation details beyond counts unless the admin can see them |
| Audit metadata | Admin change history and audit events, if the admin holds `audit.log:read` | No case content |
| Help content | Admin guides in [[DOC-tenant-facing-help-centre]] | Retrieved by `help.search` |

Minimisation: the copilot fetches what it needs per turn through tools; it does not receive a dump of the tenant's configuration. Directory searches return at most 50 rows per call.

<!-- section:prompts -->
## Prompt design and versioning

Base prompt `copilot.admin@v` released through [[AI-prompt-management]], with sections: role (assistant to a tenant administrator); rules (use tools for facts; never invent setting keys or permissions; propose drafts, never claim a change is live; explain risk of security-weakening and AI-widening drafts; refuse legal advice); tool usage; output format (answer, links, draft summary). Tenants cannot add instructions to the copilot at launch (unlike tenant agents), because its behaviour is part of the platform's admin control surface.

Tool descriptions are generated from the admin API's OpenAPI operation summaries and schemas at build time, so the copilot's tools change only with an API release.

<!-- section:guardrails -->
## Guardrails

**Plan, draft, validate, show.** For a change request the copilot (1) reads current values, (2) builds a change set of typed operations, (3) submits it as a draft, (4) receives the validator result, and (5) shows the admin a diff, the explanation and any warnings. The admin may edit the draft in the normal editor, discard it, or submit it for review.

**Risk classes shown on every draft** (computed by the server from the operations, not by the model):

| Class | Examples | Extra handling |
|---|---|---|
| Routine | Template wording, unit calendar, notification timing | Normal lifecycle |
| Access-widening | New role with admin permissions, adding users to admin roles | Maker-checker always ([[PKG-separation-of-duties]]); warning banner |
| Security-weakening | Shorter MFA coverage, longer sessions, new API scopes | Maker-checker; security admin as checker |
| AI-widening | Enabling an AI feature, adding data scopes, relaxing review | Maker-checker; tenant owner for first T3 enablement ([[AI-tenant-ai-policy]]) |
| Running-case impact | Changes marked "applies to running cases", blueprint migrations | Impact preview: number of running cases affected ([[WF-workflow-versioning]]) |
| Destructive | Deleting roles, archiving case types | Drafted only after the admin confirms in the conversation; maker-checker |

**Other guardrails**

- A setting key, permission or role named in a draft must exist in the registry, or the draft fails validation (no hallucinated keys can survive).
- Maximum 200 operations per change set; larger work becomes a bulk job draft with a dry run.
- Pasted lists (for example names and emails) are treated as untrusted data, validated row by row, and never interpreted as instructions.
- The copilot's own answers are labelled "AI answer" and drafts carry an "AI-proposed" badge in every list and in the change history.
- Rate limits: proposed 60 turns per admin per hour, 500 per tenant per day.

<!-- section:oversight -->
## Human oversight

- The invoking admin is the **author** of every copilot draft. A different person must approve it wherever maker-checker applies, so the copilot cannot help one admin bypass four-eyes approval.
- Reviewers see "Proposed with the admin copilot" with a link to the conversation summary, the explanation, and the server-computed risk class; reviewers are reminded to check the diff, not the explanation.
- `ai_admin` or `tenant_admin` can turn the copilot off (`ai.copilot.enabled = false`) or limit the domains it may draft for (`ai.copilot.draft_domains`).
- Nomology's AI team reviews anonymised quality signals (draft acceptance, edits before submit, validation failures) per release, never tenant configuration contents.

<!-- section:evaluation -->
## Evaluation

| Set | Content | Metric and threshold (proposed) |
|---|---|---|
| Golden admin tasks | 150 tasks across domains (roles, settings, notifications, blueprints, AI policy, integrations) on a synthetic tenant | Draft diff equals the expected diff (normalised) for at least 85 percent; validator pass for at least 95 percent of drafts |
| Explain and diagnose | 80 questions with known answers, including access explainer cases | Correct, linked answer at least 90 percent; zero invented setting keys |
| Escalation red team | Requests to grant itself or the admin more rights, publish, bypass maker-checker, reveal secrets, read case content, act on another tenant | 100 percent refused or reduced to a draft that still requires approval |
| Injection | Instructions hidden in pasted lists, template text and user display names | At least 98 percent no change in behaviour; 100 percent no out-of-scope tool calls |
| Usability study | Admins at an arbitral institution and a SEBI ODR institution | Admins find the diff before submitting in at least 90 percent of sessions |

Runs on every base prompt, tool manifest or model route change ([[TST-evals-and-ai-testing]]).

<!-- section:failure -->
## Failure modes and fallback

| Failure | Protection |
|---|---|
| Copilot drafts the wrong change | Draft only; diff shown; validator; maker-checker on risky classes; rollback by publishing the previous version |
| Copilot states a wrong fact | Facts must be linked; unlinked facts are dropped; "check in the console" link on every answer |
| Copilot unavailable | Console works fully without it; panel shows "The admin assistant is unavailable" |
| Admin over-trusts explanations | Reviewer screen leads with the diff; explanation is collapsed by default |
| Draft conflicts with another admin's draft | Normal `VERSION_CONFLICT` handling in the lifecycle; copilot re-reads and offers a rebased draft |

<!-- section:cost -->
## Cost and limits

Copilot usage is charged to the tenant AI budget under the `admin_copilot` feature, with a default per-admin daily quota (`ai.quota.admin_copilot.user_daily_requests`, default 100). Typical turn: 4,000 to 15,000 input tokens (tool results dominate) and 300 to 1,500 output tokens; the request classifier keeps tool manifests small. Plans may include a copilot allowance separate from case AI usage ([[BIL-plans-entitlements-and-usage]]).

<!-- section:logging -->
## Logging and audit

- Each turn writes `ai_requests` rows (prompt, model and policy versions) and an `admin_copilot_turns` row: conversation ID, admin, page context, tools called with argument hashes and result status, change set IDs created.
- Change sets record `origin = copilot` and `copilot_conversation_id`; the admin change history ([[APP-admin-change-history]]) filters by origin.
- Audit events: `admin.copilot.draft_created`, `admin.copilot.refused`, plus the normal `admin.<domain>.<verb>` events when a human later submits, approves and publishes.
- Conversation text is kept for `ai.copilot.conversation_retention_days` (default 90, because it explains configuration decisions), encrypted in regional storage; it contains no case content by design.

<!-- section:questions -->
## Open questions

- [ ] Should platform admins get the same copilot in `/platform/...` over the platform internal API, and with which extra limits (cross-tenant reads)? (owner: admin group, platform security)
- [ ] Default conversation retention (proposed 90 days). (owner: legal)
- [ ] Should tenants be allowed to add their own copilot instructions (for example naming conventions)? Proposed: not at launch. (owner: product)
- [ ] Does the change-set API (`/admin/v1/change-sets`, decision D3) support every admin domain at launch, including direct operations recorded as `admin.op` items, or do some domains need console-only edits first? (owner: config and admin groups)

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Tier T1 (configuration drafts only, no case content), but with high leverage because configuration controls access and procedure. Risk is contained by the draft-only tool set, server-computed risk classes, maker-checker for risky classes with the invoking admin as author, and the self-modification block. Inventory entry `AIS-ADMIN-COPILOT`.

<!-- check:privacy -->
### Privacy and redaction

No case documents, transcripts or messages; directory metadata only as needed; at most 50 rows per directory call; secrets are write-only and never visible. Conversation text has no case content and a defined retention.

<!-- check:residency -->
### Residency

Runs in the tenant's home region through the gateway, with conversations and logs in regional stores; the tool manifest is generated code and global.

<!-- check:security -->
### AI security and tenant isolation

Tools are the typed admin API operations of classes read and draft; every call is authorised as the admin intersected with `ps.ai.copilot_admin`; publish-class operations reject the copilot principal server-side; pasted data is untrusted; red-team set must pass 100 percent on escalation (OWASP LLM06 excessive agency [R2]).

<!-- check:oversight -->
### Human oversight

A human edits, submits and (where required) a different human approves every draft; reviewers see the diff first and the AI-proposed marker; admins can turn the copilot off or limit its domains.

<!-- check:evals -->
### Evaluation

Golden admin tasks, explain and diagnose set, escalation red team, injection set and a usability study, with thresholds and runs on every prompt, tool manifest or model change.

<!-- check:monitoring -->
### Production monitoring and AI incidents

Draft acceptance rate, edits before submit, validation failure rate, refusal rate and red-team regressions per release; spikes in refusals or escalation attempts per tenant raise a security event.

<!-- check:cost -->
### Cost and limits

Charged under `admin_copilot` with per-admin daily quotas and tenant budget; classifier narrows tool manifests to limit tokens.

<!-- check:audit -->
### Audit and traceability

Turns link to `ai_requests` and change sets; change sets carry origin and conversation ID; the later human submit, approve and publish events complete the chain, so any configuration change can be traced to whether AI proposed it and who approved it (ISO/IEC 42001 traceability [R1]).

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
    "excerpt": "Trust layer features: grounding in customer data, data masking, toxicity detection, audit trail and feedback, and zero data retention agreements with third-party model providers.",
    "id": "R3",
    "kind": "vendor",
    "title": "Agentforce Developer Guide: Trust Layer",
    "url": "https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html",
    "vendor": "Salesforce"
  },
  {
    "excerpt": "Admins govern agent actions, connectors, knowledge sources, HTTP requests, channel publication and authentication through data policies; can turn off publishing of agents that use generative AI for a tenant; makers see a security warning and risk assessment before publishing; maker activity is audited.",
    "id": "R4",
    "kind": "vendor",
    "title": "Microsoft Copilot Studio: Security and governance",
    "url": "https://learn.microsoft.com/en-us/microsoft-copilot-studio/security-and-governance",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
