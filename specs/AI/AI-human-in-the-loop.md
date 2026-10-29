---
id: "AI-human-in-the-loop"
title: "Human-in-the-loop"
parent: "AI"
order: 5
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "Review and approval of AI output: lifecycle, approver roles from the tenant policy, workflow review tasks, a narrow calibrated acceptance path for internal classification, rubber-stamp detection"
links: []
rev: 3
syncHash: "8e22a397705bf2f2"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.5 Human-in-the-loop

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Review and approval of AI output: lifecycle, approver roles from the tenant policy, workflow review tasks, a narrow calibrated acceptance path for internal classification, rubber-stamp detection

<!-- section:purpose -->
## Intended use

Human-in-the-loop (HITL) makes sure a named person reviews AI output before it can affect a case. It defines the lifecycle of every AI output, who may approve it, what the reviewer sees, and how we detect rubber-stamping. The review obligation for each call (mode, approver role, second reviewer) comes from the tenant AI policy decision ([[AI-tenant-ai-policy]]), within the platform rules below.

Rule: **AI assists, people decide.** No AI output is sent to a party, placed on the case record, or used to change case state without an approval by the role named for that feature.

**Lifecycle** (code-defined state machine in [[WF-entity-state-machines]], entity `ai_output`)

```
generated --open--> in_review --approve--------------> approved --apply--> applied
    |                   |---edit+approve-------------> approved_with_edits --apply--> applied
    |                   |---reject-------------------> rejected
    |
    +--policy_accept (calibrated, internal only)-----> accepted_by_policy --apply--> applied
    |                                                        |--sample_review--> confirmed | corrected
    +--expire (unreviewed, ai.retention.unreviewed_output_expiry_days)--> expired
```

- `apply` is performed by the feature (for example inserting approved text into a procedural order draft) and is only allowed from `approved`, `approved_with_edits` or `accepted_by_policy`.
- Only users holding the feature's approver role in that case may approve; the approver cannot be a service account or AI agent.
- **`accepted_by_policy`** is a new, narrow state for workflow AI steps of kind `classify` or `extract` whose calibrated confidence meets the tenant's threshold, whose destination is internal (routing, internal metadata) and whose output has no legal effect ([[WF-ai-steps-and-agents]]). The transition is made by the interpreter with the AI step definition version as its authority, is labelled "AI-classified" wherever shown, and a sample is reviewed after the fact (`confirmed` or `corrected`). It is never allowed for outputs that go to parties, the case record as substantive content, deadlines, fees, status changes or neutrals' work. Tenants must turn it on (`ai.workflow_steps.allow_auto_accept`, default off in every blueprint, [[PKG-settings-ai]]). This exception is decision D8 and is flagged for CTO decision.

**Reviewer roles by feature type (platform defaults; tenants may narrow, not widen, through `ai.review.approver_roles.<feature>`)**

| Feature type | Who may approve | Where it can go after approval |
|---|---|---|
| Case summary for internal use | Secretariat case manager | Internal case notes only |
| Bundle or document summary shared with tribunal | Tribunal secretary or presiding neutral | Tribunal workspace |
| Drafting assistance for procedural orders and awards | The neutral who is drafting | Into the neutral's own draft; the order or award is then issued through the normal process |
| Transcript corrections suggested by AI | Transcriber, then transcript quality reviewer ([[DOM-transcribers]]) | Approved transcript |
| Notification or message text suggestions (including agent `message.draft`) | Secretariat user sending it | Sent message |
| Workflow AI step outputs (review mode `always` or below threshold) | Reviewer role named in the AI step definition | The case fact or draft named by the step |
| Agent proposals (tasks, tags, private notes) | The invoking user | As proposed |
| Admin copilot configuration drafts | The invoking admin (as author) and a different checker where maker-checker applies | Published configuration ([[APP-admin-copilot]]) |

<!-- section:outofscope -->
## Out-of-scope uses

- **Unreviewed AI output to parties** (for example auto-replies to a party's question). Not supported; the state machine has no path from `generated` or `accepted_by_policy` to anything party-facing.
- **AI decisions on the merits, credibility or outcome.** Features, agents and AI steps may not produce recommendations on who should win, damages amounts or credibility of witnesses. Enforced by feature review in [[AI-ai-governance-and-impact]], label-set purpose rules ([[WF-ai-steps-and-agents]]) and neutrality guardrails ([[AI-guardrails]]).
- **Bulk approval** of AI outputs that go to parties or the record. Bulk actions are disabled for those features; allowed only for internal-only outputs.
- **Policy acceptance for drafts, summaries or agent output.** Only calibrated classification and extraction with internal destinations.

<!-- section:models -->
## Models and providers

Not applicable directly: HITL works on outputs from any route. The model and prompt version that produced an output are shown to reviewers on request (details panel).

<!-- section:context -->
## Inputs and context sources

The reviewer sees: the output with AI label ([[AI-ai-generated-text-labelling-and]]), the cited passages with links to source pages, guardrail flags (for example "2 sentences without citations"), the instruction that was given, and what will happen on approval ("This text will be inserted into your draft order").

<!-- section:guardrails -->
## Guardrails

- Approval needs an explicit action; there is no default "approve" button focus, and keyboard shortcuts for approve are disabled on party-facing outputs.
- For drafting assistance, a reviewer must open the full output before the approve control is enabled (scroll-to-end or explicit "I have read this" is a proposed design, to be tested with neutrals).
- Outputs with guardrail flags show them prominently; approving an output with uncited sentences requires a second confirmation.

<!-- section:oversight -->
## Human oversight

| Control | Mechanism | Owner |
|---|---|---|
| Approval required | State machine; `apply` only from approved states or the narrow policy-accepted state | Feature owner |
| Approver is a named, authorised human | Role check in [[PKG-policy-engine-permission-matrix]] with permission `ai.output:approve`; service accounts and AI agents excluded | Authorization package |
| Workflow review tasks | AI step outputs needing review create `ai_review` human tasks with due dates and escalation ([[WF-human-tasks]]); overdue tasks escalate and never auto-approve | Workflow designer, case manager |
| Second reviewer | Optional per feature and case type (`ai.review.second_reviewer.<feature>`) | Tenant AI admin |
| Policy acceptance oversight | After-the-fact sample (`samplePercent`, floor 2 percent), automatic downgrade to always-review when measured precision drops below threshold | Workflow designer, AI governance lead |
| Rubber-stamp detection | Metrics per feature and reviewer: approval without opening, median time in review relative to output length, edit rate, rejection rate | AI governance lead |
| Sampled audits | Monthly sample (`ai.review.sample_audit_percent`, default 2 percent, or 50 outputs per feature, whichever is larger) checked by a second reviewer for grounding and neutrality | AI governance lead with tenant QA where agreed |
| Kill switch | Tenant: `ai.policy.enabled` and `ai.features.<key>.enabled` (tenant admin); case: `ai.case.restriction` (case manager, presiding neutral); region: `ai.killswitch` (platform) | Tenant admin / case roles / AI platform lead |

Signals that trigger review: approval-without-open rate above 5 percent, median review time below 10 seconds per 500 words, or edit rate near zero over 100 outputs (all proposed thresholds). Whether tenants see these metrics for their own users is a tenant setting (`ai.review.share_reviewer_metrics_with_tenant`, default off).

<!-- section:evaluation -->
## Evaluation

| Test | Threshold |
|---|---|
| No path from `generated` to `applied` without approval (state machine property test) | 100 percent, blocking |
| Approver role enforcement across personas (counsel cannot approve tribunal outputs) | 100 percent, blocking |
| Usability study with neutrals and secretariat users on the review screen | Reviewers detect at least 80 percent of planted errors in a study session (proposed) |
| Rubber-stamp metrics computed correctly on synthetic event streams | Pass |

<!-- section:failure -->
## Failure modes and fallback

| Failure | Protection |
|---|---|
| Reviewer approves wrong content | Applied text is still editable in the draft; sampled audits; AI incident process if it reached a party |
| Output never reviewed | Expires after `ai.retention.unreviewed_output_expiry_days` (default 30); nothing applied; workflow steps take their fallback |
| Feature misconfigured to auto-apply | Impossible by state machine; only AI step definitions of the allowed kinds can request `policy_accept`; property test in CI |
| Auto-accepted classification wrong | Sample review corrects it; correction re-evaluates open routing; precision drop downgrades the step |
| Overloaded reviewers | Feature-level throttle on generation per user per day; secretariat dashboards show pending reviews and `ai_review` tasks |

<!-- section:logging -->
## Logging and audit

Every transition writes an audit event (`ai.output.generated`, `ai.output.opened`, `ai.output.approved`, `ai.output.approved_with_edits`, `ai.output.rejected`, `ai.output.applied`) with user, role, case, timestamps and, for edits, the stored diff. `ai_outputs` rows keep `status, reviewed_by, reviewed_at, opened_at, edit_distance, label_version`. Retained with the case ([[PKG-audit-trail]]).

<!-- section:questions -->
## Open questions

- [ ] Do institutions require disclosure to parties when AI assisted a procedural order or award, and in what form? Tenant decision, captured as `ai.disclosure.neutral_use` in [[PKG-settings-ai]].
- [ ] Is a "must open full output" control acceptable to neutrals, or too intrusive? (Setting `ai.review.require_open_before_approve`, locked on for T3.)
- [ ] Expiry period for unreviewed outputs (default 30 days, now a setting).
- [ ] CTO decision (D8): confirm the `accepted_by_policy` state, the only path where a person does not approve each item. The review pass aligned [[WF-process-definition-model]], [[WF-ai-steps-and-agents]] and [[PKG-settings-ai]] to it: off by default, calibrated internal `classify` and `extract` steps only, no effect on the merits or on parties' rights. (owner: CTO, legal)
- [ ] Do tenants want access to rubber-stamp metrics for their own users, given they may be used for performance management? (Default off.)

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Highest-risk use is drafting assistance for orders and awards, which touches the merits. The design keeps AI assistive: output goes only into the neutral's own draft, the neutral alone approves, and the order or award is issued through the normal process. Features producing outcome or credibility assessments are out of scope. Policy acceptance is confined to internal routing data with no legal effect. Feature-level risk tiers are recorded in [[AI-ai-governance-and-impact]], which considers EU AI Act Annex III for alternative dispute resolution uses [R1].

<!-- check:oversight -->
### Human oversight

Named approver role per feature type, narrowed by the tenant policy and enforced by the `ai_output` state machine; reviewers see label, citations, flags and the effect of approval; workflow outputs create `ai_review` tasks that escalate and never auto-approve; the only non-individual path, `accepted_by_policy`, is limited to calibrated internal classification and extraction with sampling and automatic downgrade; rubber-stamping is detected with approval-without-open rate, review time and edit rate, plus monthly sampled audits; kill switches per tenant, feature, case and region.

<!-- check:evals -->
### Evaluation

Blocking property tests prove no unapproved path to `applied` and correct approver roles; a usability study measures planted-error detection on the review screen.

<!-- check:monitoring -->
### Production monitoring and AI incidents

Dashboards per feature and tenant for pending reviews, approval-without-open rate, review time and edit rate, with the proposed thresholds above alerting the AI governance lead.

<!-- check:audit -->
### Audit and traceability

Every state transition is an audit event with user (or, for `accepted_by_policy`, the AI step definition version and calibration run), role, timestamps and stored diffs, linked to `request_id`, so any applied text or fact can be traced to the AI request, prompt, model and policy version.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Annex III lists high-risk uses, including AI intended to assist a judicial authority in researching and interpreting facts and the law and applying the law to facts, or used in a similar way in alternative dispute resolution. Article 6(3) excludes Annex III systems that perform narrow procedural or preparatory tasks and do not materially influence the outcome of decision making; Article 26 sets deployer duties (human oversight, log keeping); Article 50 sets transparency duties.",
    "id": "R1",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689",
    "status": "in force, phased application",
    "title": "Artificial Intelligence Act",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
  }
]
```

<!-- end -->
