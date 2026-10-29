---
id: "TST-evals-and-ai-testing"
title: "Evals and AI testing"
parent: "TST"
order: 6
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "golden datasets, regression evals, hallucination and grounding checks, red-teaming"
links: []
rev: 2
syncHash: "2fe4812655dae275"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16.6 Evals and AI testing

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> golden datasets, regression evals, hallucination and grounding checks, red-teaming

<!-- section:purpose -->
## Intended use

Specifies the evaluation system that every AI feature on the platform must pass before release and keep passing afterwards: golden datasets, metrics and pass thresholds, LLM-as-judge calibration, adversarial and red-team suites, and the CI gate that blocks a prompt, model or retrieval change that regresses. It serves engineering, the AI governance owner ([[AI-ai-governance-and-impact]]) and tenants' compliance teams who need to see how AI features were tested. It does not itself make decisions about cases; it decides whether an AI feature version may be released.

Features covered: case and document summaries, drafting assistance in the neutral workspace ([[APP-neutral-workspace]]), transcription and transcript clean-up ([[APP-transcriber-workspace]]), retrieval over case documents ([[AI-rag]]), and guardrail behaviour ([[AI-guardrails]]).

<!-- section:outofscope -->
## Out-of-scope uses

- Evals are not a certification that an AI output is correct for a given case; human review under [[AI-human-in-the-loop]] remains mandatory for anything that reaches parties or the record.
- Eval sets must not be built from production case documents, transcripts or recordings unless the process in the Inputs section (anonymisation, tenant consent, approval) has been followed; ad-hoc copying of production data is forbidden.
- No evaluation of a feature that predicts case outcomes or recommends a decision to a neutral; such features are out of scope for the platform under the AI policy (to be confirmed in [[AI-ai-governance-and-impact]]).
- Eval tooling is not used to rank or score neutrals, counsel or parties.

<!-- section:models -->
## Models and providers

- **Systems under test**: whatever model and provider the AI gateway routes a feature to in each region ([[AI-ai-gateway]]), pinned by model version; every eval run records feature, prompt version, model ID and version, retrieval configuration and region.
- **Judge models**: a separate pinned model used as LLM judge, never the same model version as the system under test for the same metric. Judges are themselves versioned and re-calibrated when changed.
- **Region**: evals run in the region whose model endpoints they test, so each region's routing is evaluated; eval data sets classified as containing anonymised case-derived text stay in the region they came from.
- **Fallback**: when the gateway has a fallback model for a feature, the fallback is evaluated with the same thresholds; a fallback that fails is removed from routing.

<!-- section:context -->
## Inputs and context sources

**Dataset types**

| Set | Source | Use |
|---|---|---|
| Golden synthetic | Synthetic cases, pleadings, orders and transcripts written by legal staff and generated documents reviewed by them, in English and each launch locale | Main regression set |
| Public material | Published awards and judgments where licence and publication terms allow reuse | Long-document and legal-language coverage |
| Consented anonymised | Case material from a tenant who has agreed in writing, anonymised (names, IDs, contact data, unique facts) and reviewed by two people | Realism checks; optional |
| Adversarial | Documents with injected instructions, hidden text, poor scans, mixed scripts, very long transcripts | Guardrail and robustness checks |
| Fairness slices | Same synthetic case with party names, languages and regions varied | Quality parity |

- **EVAL-1** Each feature has a golden set of at least 200 items (proposed) covering each tenant type (`arb-inst`, `odr-inst`, `cord`), launch language and document format.
- **EVAL-2** Eval items are stored in the AI eval store in each region, versioned, with source type, licence or consent reference and anonymisation reviewer recorded per item.
- **EVAL-3** Production prompts and outputs are not copied into eval sets automatically. Reviewer feedback from [[AI-human-in-the-loop]] may nominate an item; it enters the set only through the consented anonymised route.

<!-- section:prompts -->
## Prompt design and versioning

Eval configurations live next to prompts in `packages/ai/prompts/<feature>/` ([[AI-prompt-management]]): `prompt.vN.md`, `eval.yaml` (datasets, metrics, thresholds, judge version). A prompt version cannot be marked `released` until an eval run for that exact version, model and retrieval configuration has passed and been signed off.

<!-- section:guardrails -->
## Guardrails

Evals test guardrails as features in their own right:
- **EVAL-4** Prompt injection set: documents containing instructions ("ignore previous instructions", hidden white text, instructions in metadata). Pass = zero cases where output follows the injected instruction or reveals system prompt or other-case content.
- **EVAL-5** Cross-case and cross-tenant leakage: retrieval for case X must return no chunks from case Y or another tenant, measured on a seeded index with near-duplicate texts across tenants (complements [[TST-multi-tenant-isolation-tests]] ISO-12).
- **EVAL-6** PII redaction: where [[AI-guardrails]] redacts before a call, recall of redaction on a labelled set at least 0.98 (proposed).
- **EVAL-7** Refusal correctness: requests out of scope (predict the outcome, advise a party) are refused at least 95% of the time, and in-scope requests are not refused more than 3% of the time (proposed).
- The suites follow the risk categories of the OWASP Top 10 for LLM Applications [R1].

<!-- section:oversight -->
## Human oversight

- Release sign-off for each AI feature version: AI platform lead plus the product owner; for case-facing features (drafting assistance, summaries shown to neutrals or secretariat), also the AI governance owner.
- A legal reviewer grades a sample of at least 10% of judge-scored items per release (proposed) and all items where the judge and the code-based metrics disagree.
- Red-team exercises (EVAL-11) are run by people outside the feature team.
- Any failure on EVAL-4 or EVAL-5 blocks release regardless of other scores and is reported to the information security owner.

<!-- section:evaluation -->
## Evaluation

**Metrics and proposed thresholds**

| Feature | Metric | How scored | Release threshold |
|---|---|---|---|
| Summaries | Faithfulness (no unsupported statements) | LLM judge with claim-level check, sampled human grading | ≥ 0.95 of claims supported |
| Summaries | Coverage of key facts | Human-written key-fact lists per item | ≥ 0.85 |
| Summaries, drafting | Citation accuracy (cited page or paragraph supports the statement) | Code check of citation targets + judge | ≥ 0.97 |
| Drafting | Format and template validity | Code (schema) | 100% |
| Drafting | Neutral wording (no favouring a party, no outcome prediction) | Judge with rubric + human sample | ≥ 0.98 |
| Transcription | Word error rate per language | Code against reference transcripts | Per language, set at baseline and may not regress more than 1 point |
| Transcription | Speaker attribution accuracy | Code | ≥ 0.95 |
| RAG | Recall@10 of relevant passages | Labelled queries | ≥ 0.9 |
| All | Guardrail suites EVAL-4 to EVAL-7 | As above | As above |
| All | Fairness: metric gap between slices | Code | ≤ 0.03 absolute |

- **EVAL-8** Judge calibration: each judge prompt is validated against at least 100 human-graded items; agreement (for example Cohen's kappa) of at least 0.7 is required before use, re-checked when the judge model or rubric changes and every quarter.
- **EVAL-9** CI gate: any change to a prompt, model routing, retrieval configuration, chunking or guardrail config triggers the affected features' eval suites; a metric below threshold or a regression of more than 2 points versus the last released version fails the check.
- **EVAL-10** Scheduled runs: full suites weekly per region and whenever a provider announces a model update, to detect drift in pinned or aliased models.
- **EVAL-11** Red-teaming before first release of each case-facing feature and at least twice a year, covering injection, data exfiltration, harmful or biased wording and misuse by a party.
- Approach to risk categories and pre-deployment testing follows NIST AI 600-1 [R2] and ISO/IEC 42001 impact assessment practice [R3].

<!-- section:failure -->
## Failure modes and fallback

| Failure | Protection |
|---|---|
| Judge model drifts and passes bad outputs | Quarterly calibration (EVAL-8); human sample grading every release |
| Eval set no longer represents real use (new tenant type, new language) | Coverage check: every tenant type and launch locale must have items; new locale cannot launch an AI feature without them |
| Provider silently updates a model | Weekly scheduled runs; pin versions in the gateway; alert on metric shift |
| Overfitting prompts to the eval set | Hold-out split (20%) never shown to prompt authors; release decision uses hold-out scores |
| Eval data contains residual personal data | Two-person anonymisation review; automated PII scan of eval items; immediate removal process |

<!-- section:cost -->
## Cost and limits

Proposed budget: eval runs are metered as an internal tenant in [[AI-cost-controls]], with a monthly cap per region. CI runs use a 50-item stratified subset per feature for fast feedback and the full set before release. Judge calls are cached by (item, output hash, judge version).

<!-- section:logging -->
## Logging and audit

Each eval run stores: run ID, trigger (PR, schedule, provider change), feature, prompt version, model and judge versions, retrieval config hash, region, dataset version, per-item outputs and scores, aggregate metrics, pass/fail and approvers. Stored in the regional eval store for 3 years (proposed), linked from the release's change record and from the feature's model card for compliance teams. OpenTelemetry generative AI attributes are used for model call telemetry [R4].

<!-- section:questions -->
## Open questions

- [ ] Which tenants, if any, will consent to anonymised case material for eval sets, and under what contract terms?
- [ ] Confirm the proposed thresholds with legal reviewers after the first baseline runs.
- [ ] Eval harness: build in-house, or adopt an open-source runner (for example promptfoo) wrapped in our CI?
- [ ] Is the EU AI Act relevant for any tenant serving EU-based parties? Annex III lists AI used in alternative dispute resolution among high-risk uses [R5]; legal to assess per feature.
- [ ] Retention period for eval outputs that include anonymised case-derived text.

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Evals are the main control for the accuracy and neutrality risks of case-facing AI features. Release of drafting assistance and summaries needs AI governance owner sign-off, and EVAL-4/EVAL-5 failures are blocking. Possible EU AI Act high-risk classification for tenants with EU parties is an open question for legal.

<!-- check:privacy -->
### Privacy and redaction

Eval sets are synthetic or public by default; consented anonymised material needs written tenant consent, two-person anonymisation review and an automated PII scan (EVAL-2, EVAL-3). Production prompts and outputs never flow into eval sets automatically.

<!-- check:residency -->
### Residency

Evals run in the region of the endpoints under test and eval data derived from a tenant's material stays in that tenant's region (Models section).

<!-- check:security -->
### AI security and tenant isolation

Injection, exfiltration and cross-case leakage suites (EVAL-4, EVAL-5) and red-teaming twice a year (EVAL-11), aligned to the OWASP Top 10 for LLM Applications.

<!-- check:evals -->
### Evaluation

Datasets of at least 200 items per feature with tenant-type, language and format coverage; metrics and thresholds per feature (Evaluation table); calibrated judges (kappa ≥ 0.7); hold-out split; CI gate on every prompt, model or retrieval change; weekly scheduled runs; results stored with versions and approvers.

<!-- check:monitoring -->
### Production monitoring and AI incidents

Weekly scheduled runs per region and runs on provider model announcements detect drift. Production signals (reviewer edit and rejection rates) are owned by [[OBS-ai-usage]] and feed candidate items into the eval process.

<!-- check:audit -->
### Audit and traceability

Every eval run is stored with prompt, model, judge, retrieval and dataset versions, scores and approvers, linked to the change record and model card, so a compliance team can see which tested version produced an output in a case (combined with gateway logs in [[AI-ai-gateway]]).

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Top risks for LLM applications, including prompt injection, sensitive information disclosure and excessive agency.",
    "id": "R1",
    "kind": "web",
    "publisher": "OWASP GenAI Security Project",
    "title": "OWASP Top 10 for LLM Applications",
    "url": "https://genai.owasp.org/llm-top-10/"
  },
  {
    "body": "NIST",
    "excerpt": "Identifies generative AI risks such as confabulation and information integrity, with suggested actions including pre-deployment testing and red-teaming.",
    "id": "R2",
    "ident": "NIST AI 600-1",
    "kind": "standard",
    "title": "Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile",
    "url": "https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence"
  },
  {
    "body": "ISO/IEC",
    "excerpt": "Requirements for establishing an AI management system, including AI system impact assessment and lifecycle controls.",
    "id": "R3",
    "ident": "ISO/IEC 42001",
    "kind": "standard",
    "title": "Artificial intelligence — Management system",
    "url": "https://www.iso.org/standard/42001",
    "version": "2023"
  },
  {
    "body": "OpenTelemetry",
    "excerpt": "Defines span and metric attributes for model calls such as model name, token usage and operation name.",
    "id": "R4",
    "ident": "Semantic conventions for generative AI",
    "kind": "standard",
    "title": "Semantic conventions for generative AI systems",
    "url": "https://opentelemetry.io/docs/specs/semconv/gen-ai/"
  },
  {
    "clause": "Annex III point 8(a)",
    "excerpt": "Lists as high-risk AI systems intended to be used by a judicial authority, or in a similar way in alternative dispute resolution, to research and interpret facts and law and apply the law.",
    "id": "R5",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689",
    "title": "Artificial Intelligence Act",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
  }
]
```

<!-- end -->
