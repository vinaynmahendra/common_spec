# Template: AI capability (`ai`)

Generated from `ai.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies an AI-powered feature or AI infrastructure with its intended use, limits, safeguards and evaluation, so it can be trusted in legal work and audited later.

**Depth:** 3–8 pages. Intended use, out-of-scope use, evaluation with pass thresholds and human oversight are mandatory for Approved. Write it so a client's compliance team could read it as a model card. Each user-facing AI feature is its own node.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Intended use (level 1)

What the feature does, for whom, and the decision it supports.

Illustrative example (not a requirement):

> Hearing summary: produces a structured summary (issues, arguments, rulings, action items) from a hearing transcript for the tribunal secretary to edit and circulate.

### `outofscope` Out-of-scope uses (level 1)

Uses the feature must not be put to, and how that is prevented.

Illustrative example (not a requirement):

> - Not for drafting or suggesting the outcome of an award
> - Not shown to parties unless a human has approved it
> Enforced by role checks and a "Draft — AI generated" watermark until approval.

### `models` Models and providers (level 1)

Models used, provider, region, version pinning, fallback.

Illustrative example (not a requirement):

> | Use | Model | Region |
> |---|---|---|
> | Summary | Large model via AI gateway | Same region as tenant |
> | Fallback | Second provider via gateway | Same region |
> Model version pinned per prompt version.

### `context` Inputs and context sources (level 1)

What data goes into prompts, retrieval sources, and minimisation.

Illustrative example (not a requirement):

> Transcript segments for one hearing; case metadata (type, rule set, issue list). No documents from other cases; RAG index is per tenant and per case.

### `prompts` Prompt design and versioning (level 2)

Prompt structure, where prompts are stored, how versions are released.

Illustrative example (not a requirement):

> Prompt stored in Prompt management as `hearing.summary@v3` with output JSON schema. New versions run against the eval set before release.

### `guardrails` Guardrails (level 1)

Input / output checks, redaction, refusal behaviour, grounding requirements.

Illustrative example (not a requirement):

> - Every summary bullet must cite transcript timestamps; uncited bullets are dropped
> - Output schema validation; failure → retry once, then return "Summary unavailable"
> - PII redaction not applied (secretary needs names) but outputs never leave the case

### `oversight` Human oversight (level 1)

Who reviews, when, and what they can change.

Illustrative example (not a requirement):

> Secretary must open, edit if needed, and approve before the summary is visible to the tribunal. Edits are stored for evaluation feedback.

### `evaluation` Evaluation (level 1)

Datasets, metrics, thresholds, cadence.

Illustrative example (not a requirement):

> | Metric | Method | Threshold |
> |---|---|---|
> | Faithfulness | % bullets supported by cited timestamps (LLM judge + human sample) | ≥ 98% |
> | Coverage | Issues captured vs human reference summary | ≥ 90% |
> | Edit distance | Secretary edits per summary | Track trend |
> Eval set: 40 anonymised transcripts across 3 tenants; run on every prompt or model change.

### `failure` Failure modes and fallback (level 2)

Known failure modes and how users are protected.

Illustrative example (not a requirement):

> Hallucinated ruling → caught by citation rule; long transcripts → chunked map-reduce with section headings; provider outage → gateway fallback, else manual.

### `cost` Cost and limits (level 2)

Expected tokens, budgets, throttles.

Illustrative example (not a requirement):

> ≈ 60k input tokens per 2-hour hearing. Tenant monthly budget from plan; 80% budget alert to tenant admin.

### `logging` Logging and audit (level 2)

What is recorded for audit and improvement, with retention.

Illustrative example (not a requirement):

> Prompt version, model version, input hash, output, reviewer and edits; retained with the case.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Client opt-out per tenant for any AI processing?

## Checks

### `risk` Risk classification and impact

**Question:** How risky is this AI feature for the people affected by the case, and has that risk been assessed and accepted by a named owner?

- Which risk tier does the feature fall into under our AI policy (for example: internal productivity, case-facing draft, influences a party's rights or the outcome), and why?
- Who could be harmed if the output is wrong, biased or leaked: parties, counsel, arbitrators, institution staff? What is the worst realistic harm?
- Does any client contract, institution rule (for example HKIAC or a SEBI-recognised ODR institution's rules) or regulator restrict AI use for this task, and does the tenant have to opt in or disclose it to parties?
- If a tenant serves EU-based parties, has someone checked whether the feature could be 'high-risk' under the EU AI Act (Annex III covers AI used to assist judicial authorities and alternative dispute resolution)?
- Is there an AI impact assessment record (ISO 42001 clause 6.1.4) and an entry in the AI risk register, with likelihood, severity, treatment and residual risk?
- Who is the accountable owner who signed off the residual risk, and when is the assessment reviewed again?
- Is the feature off by default, and can each tenant switch it on or off without a deployment?

**Good answer:** Names the risk tier with a reason, lists the affected groups and the worst credible harm for each, and links to a dated impact assessment and risk-register entry with a named owner and next review date. States the tenant-level control (feature flag, default state) and any disclosure owed to parties. For features that touch the merits of a dispute, explains why the human oversight design keeps the AI in an assistive role.

**Red flags:**

- No impact assessment, or 'low risk' asserted without saying who is affected
- The feature can influence an award, order or party-facing decision with no recorded risk acceptance
- Enabled for all tenants by default with no per-tenant switch or disclosure decision
- EU AI Act applicability not considered for a tenant that handles EU parties

### `privacy` Privacy and redaction

**Question:** Is personal and confidential case data limited to what the task needs, protected in transit to the model, and never reused beyond the case?

- List every field and document type that reaches the prompt or the retrieval index. Which contain personal data, special-category data (health, financial, children's data) or privileged material?
- What is removed, masked or pseudonymised before the call, and what is deliberately left in (with the reason)?
- What is the lawful basis or contractual permission for this processing under DPDP, GDPR and PDPA, and does the privacy notice or the institution's terms cover AI processing?
- Does the provider contract guarantee zero data retention and no training on our prompts or outputs? Is the provider listed as a sub-processor in the tenant's data processing agreement?
- Are embeddings, caches and vector indexes treated as personal data: tenant- and case-scoped, encrypted, and deleted when the case or tenant data is erased?
- How do we honour a data principal's erasure or correction request for data already in prompts, logs, eval sets or indexes?
- Are production case documents ever copied into eval or fine-tuning datasets, and if so with what consent and anonymisation?

**Good answer:** Gives a field-level inventory of what is sent, what is redacted and why, and the legal basis for each data category per region. Confirms provider zero-retention and no-training terms with a reference to the signed agreement and sub-processor list. Shows that vector indexes and caches are scoped by tenant_id and case, follow the case retention schedule, and are covered by erasure workflows.

**Red flags:**

- Whole case files are sent 'for context' with no minimisation
- Provider terms allow retention or training on our data, or the terms have not been checked
- Embeddings or caches are not covered by deletion and retention rules
- Production case data used in evals or tuning without consent or anonymisation

### `residency` Residency

**Question:** Where exactly do inference, retrieval, caching and logging happen, and can any prompt, output or embedding leave the tenant's home region?

- For each model call (primary and fallback), which provider endpoint and cloud region serves it? Is that region the tenant's pinned region (India, Singapore or US)?
- Does the provider route requests across regions for capacity (cross-region inference or global endpoints)? How is that switched off and proved?
- Where do the vector index, prompt cache, AI gateway logs and eval runs store data? Are they in the same regional account as the tenant's Postgres?
- What happens when the in-region model is unavailable: fail closed, queue, or fall back to another region? Who approved that behaviour per tenant?
- Is any transfer outside India permitted for India tenants under DPDP rules and client contracts, and is it recorded in the transfer register?
- For tenants on Azure, which Azure OpenAI or equivalent region and deployment type is used?
- How does the AI gateway enforce region routing: from tenant configuration, not from a caller-supplied value?

**Good answer:** Provides a table of every AI data flow (inference, embeddings, retrieval, caching, logs, evals) with provider, region and account for each residency region. States that the gateway picks the endpoint from the tenant's region record and refuses calls that would cross regions, with a test proving it. Fallback behaviour is fail-closed unless a tenant has agreed in writing to an alternative.

**Red flags:**

- Provider 'global' or cross-region inference left on
- Fallback model sits in a different region with no tenant agreement
- Logs or eval datasets centralised in one region for all tenants
- Region chosen by the calling service rather than enforced by the gateway

### `security` AI security and tenant isolation

**Question:** How is the feature protected against prompt injection, data leakage between tenants or cases, and misuse of any tools the model can call?

- Which inputs are untrusted (party uploads, emails, transcripts, web content) and how are they kept apart from system instructions?
- What stops an injected instruction in a document from exfiltrating other data or changing the output (for example, link stripping, no tool use, output allow-lists)?
- Is retrieval filtered by tenant_id and case at query time inside the vector store (not only in application code), and is that covered by the same RLS-style isolation tests as Postgres?
- If the model can call tools or functions, what is each tool's permission scope, and does it run with the end user's permissions rather than a service account's?
- How are outputs rendered safely (escaped HTML, no auto-executed links or scripts)?
- Has the feature been red-teamed against the OWASP Top 10 for LLM Applications, and where are the findings tracked?
- Are API keys for providers held only in the gateway, rotated, and scoped per region?

**Good answer:** Identifies untrusted inputs, the injection defences applied to each, and the tool permissions model. Shows that retrieval enforces tenant and case scope in the data layer with an automated cross-tenant test. References a red-team or security test run against the OWASP LLM risks, with open findings and owners.

**Red flags:**

- Retrieval relies on the prompt or application code alone to keep tenants apart
- The model can call tools with broader permissions than the user who triggered it
- No prompt-injection testing using hostile party documents
- Provider keys embedded in application services rather than the gateway

### `oversight` Human oversight

**Question:** Which named role reviews each output before it can affect a case or reach a party, and does the design make real review likely rather than rubber-stamping?

- Which role (tribunal secretary, case manager, arbitrator, mediator) approves the output, and is approval enforced by the state machine rather than by convention?
- What does the reviewer see to check the output quickly: citations, source excerpts, confidence or uncertainty markers?
- How is AI-generated content labelled to the reviewer and, after approval, to parties if disclosure is required?
- What prevents automation bias: required edit or confirm steps, sampling of approved outputs, or training for reviewers?
- Can the reviewer reject, edit or regenerate, and are edits captured as feedback?
- Can a party or tribunal member ask whether AI was used in preparing a document, and can we answer from records?
- Who can switch the feature off immediately for a tenant or a case if a problem appears?

**Good answer:** Names the approving role, the state transition that enforces approval, and what the reviewer sees. Describes labelling and disclosure rules, how rubber-stamping is detected (for example, approval-without-open rate and periodic sampled audits), and the kill switch with its owner.

**Red flags:**

- Outputs can reach parties or the record without an enforced approval step
- No labelling of AI-generated content
- No measure of whether reviewers actually review
- No per-tenant or per-case way to switch the feature off

### `evals` Evaluation

**Question:** Are there representative datasets, defined metrics with pass thresholds, and an automated gate that blocks any prompt, model or retrieval change that regresses?

- What is in the eval set: size, source, how it was anonymised, and does it cover each tenant type, language, rule set and document format we support?
- Which metrics are measured (faithfulness, coverage, citation accuracy, refusal correctness, format validity) and what threshold must each meet to release?
- How is each metric scored: human graders, an LLM judge, or code? How was the LLM judge calibrated against human scores, and how often is that re-checked?
- Are there adversarial and edge-case sets: injected instructions, poor-quality scans, mixed languages, very long transcripts?
- Is fairness tested, for example whether quality differs for parties' names, languages or regions?
- Does the eval run automatically in CI on every prompt, model-version or retrieval change, and does a failure block release?
- Who signs off a release, and where are eval results stored with the prompt and model version they relate to?

**Good answer:** Describes the eval set composition and refresh cadence, a metric table with numeric thresholds and scoring method, judge calibration results, and adversarial cases. Shows the CI gate that runs on every prompt or model change, blocks on failure, and stores results keyed to prompt@version and model version.

**Red flags:**

- Evaluation is 'we tried some examples'
- No numeric pass thresholds, or thresholds set after seeing results
- LLM judge used without calibration against human review
- A provider's silent model update could reach production without an eval run

### `monitoring` Production monitoring and AI incidents

**Question:** How will we notice, in production, that quality, safety or behaviour has drifted, and what happens when an AI incident occurs?

- Which live signals are tracked: reviewer edit rate, rejection rate, schema failures, refusals, guardrail triggers, latency, user reports?
- What thresholds raise an alert, to whom, and how quickly?
- How is a provider model change or deprecation detected and handled (pinned versions, deprecation calendar)?
- What counts as an AI incident (for example, cross-case leakage, a wrong citation reaching a party, biased output), and how is it triaged under the security incident process?
- If personal data is exposed, how does the incident feed breach reporting: DPDP intimation to the Data Protection Board without delay and a detailed report within 72 hours, GDPR notification within 72 hours, and PDPC notification within 3 calendar days of assessing the breach as notifiable?
- How are incidents and near-misses fed back into the eval set and the risk register?

**Good answer:** Lists live quality and safety metrics with alert thresholds and owners, a dashboard location, and how model deprecations are tracked. Defines AI incident categories, links them to the incident runbook and regulatory notification clocks, and shows the feedback loop into evals and risk review.

**Red flags:**

- Only uptime and latency are monitored, not output quality
- No definition of an AI incident or link to breach-notification timelines
- Model deprecations discovered when calls start failing

### `cost` Cost and limits

**Question:** Is spend predictable and capped per tenant, with alerts before limits are hit and a defined behaviour when they are?

- What is the expected tokens and cost per request and per case, at typical and worst-case input sizes (for example a 6-hour hearing transcript)?
- What budget applies per tenant per month, and per user or per case per day? Where is it configured?
- At what percentage of budget do alerts fire, to whom (internal and tenant admin)?
- What happens when a budget is reached: hard stop, degrade to a cheaper model, or queue? Is the user told clearly?
- Are calls rate-limited and are long jobs run through BullMQ or Temporal with retries that cannot multiply cost unboundedly?
- Is AI usage metered for billing, and does metering reconcile with provider invoices each month?
- Are caching and smaller models used where quality allows, and is that decision backed by eval results?

**Good answer:** Gives a cost model with per-request and per-case estimates, configured per-tenant budgets, alert thresholds (for example 50, 80 and 100 percent), and the behaviour at the limit. Shows retry caps, rate limits and monthly reconciliation of metered usage against provider invoices.

**Red flags:**

- No per-tenant budget or alerting
- Retries or loops can generate unbounded calls
- Cost estimate based on average inputs only, ignoring large cases

### `audit` Audit and traceability

**Question:** Can we reconstruct, for any AI output in a case, exactly what went in, which model and prompt version produced it, who approved it, and what changed afterwards?

- Which fields are logged per call: tenant, case, user, prompt@version, model and provider version, retrieval document IDs, parameters, output, guardrail results, approver and timestamp?
- Are full prompts and outputs stored, or only references and hashes? Where, in which region, and encrypted how?
- How long are AI logs kept, and does that match case retention and the tenant's contract? How are they deleted?
- Are audit records append-only and tamper-evident, and who can read them?
- Can a tenant's compliance team export the AI record for a case on request?
- Is there a model card or system record maintained for the feature that compliance teams and auditors can read (ISO 42001 Annex A documentation controls)?

**Good answer:** Lists logged fields, storage location by region, encryption, retention period tied to case retention, and access controls. Confirms records are append-only, exportable per case, and linked to a maintained model card covering intended use, limits and eval results.

**Red flags:**

- Only the final approved text is kept; inputs and versions are lost
- AI logs kept indefinitely or outside the tenant's region
- Logs editable by application users or engineers without trace

