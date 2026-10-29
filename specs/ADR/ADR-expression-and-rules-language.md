---
id: "ADR-expression-and-rules-language"
title: "Expression and rules language"
parent: "ADR"
order: 11
type: "decision"
template: "adr"
status: "draft"
owner: null
indicative: false
summary: "Which language do tenant-authored conditions and decision tables use? Proposed: CEL restricted to a Nomology profile (expr/1) in one pure TypeScript package used in browser, server and Temporal; decision tables stay in our own DMN-vocabulary model with cells compiled to CEL; in-house grammar as fallback"
links: []
rev: 1
syncHash: "614cc9a2ccaf847e"
createdAt: "2026-10-28T09:00:00Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 19.9 Expression and rules language

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Which language do tenant-authored conditions and decision tables use? Proposed: CEL restricted to a Nomology profile (expr/1) in one pure TypeScript package used in browser, server and Temporal; decision tables stay in our own DMN-vocabulary model with cells compiled to CEL; in-house grammar as fallback

<!-- section:context -->
## Context and problem

**Question:** which language do tenant-authored conditions and computed values use, and how are decision tables evaluated? This covers blueprint gateway guards and stage exit criteria, automation rule conditions, form logic (show or hide, required-when, calculated fields), SLA policy conditions, cross-setting validation rules and decision-table cells. The same evaluator must run in the browser (studio and form preview), on the Node.js server, in BullMQ workers and inside the deterministic Temporal workflow sandbox.

**Affected parts:** [[PKG-rules-and-decision-engine]], [[WF-process-definition-model]] (gateway `when`, stage `exit`, step `args`), [[PKG-workflow-templates]] (`Expr`, `DeadlineExpr`, the proposed `@nomology/expr`), [[WF-automation-rules]] (conditions), [[PKG-forms-and-form-builder]] (conditions and calculated fields), [[WF-workflow-simulation]] (pure core), [[WF-workflow-authoring-studio]] (condition builder and text mode), [[WF-sla-and-business-calendars]] (SLA policy conditions), [[PKG-settings-catalogue]] and [[PKG-settings-data-model]] (validation rules between settings).

**What the specs already require**

- A closed, side-effect-free grammar over typed facts (`string`, `number`, `money`, `date`, `datetime`, `boolean`, `enum`, references). The proposed limit is 200 characters, and only the reviewed functions are allowed: `min`, `max`, `round`, `percentOf`, `lookup`, `in`, `contains`, `daysSince`, `businessDaysSince(schedule)`, `isEmpty` ([[PKG-workflow-templates#config]], [[WF-automation-rules#adapters]]).
- Decision tables use DMN vocabulary (hit policies FIRST, UNIQUE, COLLECT, PRIORITY; typed input and output columns) in our own JSON. There is no DMN XML import at launch ([[PKG-rules-and-decision-engine]]).
- Determinism: the same version and facts give the same output and `inputHash` in every region. Evaluation p99 must be 1 ms or less for a 500-rule table, and 2 ms or less per automation rule.
- Workflow designers are not engineers. The studio's primary editor is a structured condition builder; a text mode shows the same expression ([[WF-workflow-authoring-studio]]).
- Temporal TypeScript workflows run in a deterministic sandbox. It replaces `Date.now()` and `Math.random()` and cannot use Node.js or DOM APIs [R19].

**Open questions this record closes:** "in-house JSON evaluator vs GoRules Zen vs FEEL / DMN" ([[WF-separation-of-concerns-temporal#questions]], [[PKG-rules-and-decision-engine#questions]], [[ADR-workflow-engine]] notes) and "expression grammar: in-house vs CEL or JSONata" ([[PKG-workflow-templates#questions]]).

**Out of scope:** authorisation policies ([[ADR-policy-engine]]), integration data mapping and transformation, and AI prompts.

<!-- section:drivers -->
## Decision drivers

| # | Driver | Measure |
|---|---|---|
| D1 | **Safety**: no I/O, no unbounded loops, no code execution, and guaranteed termination without relying on wall-clock timeouts | Language property, not configuration |
| D2 | **Determinism inside Temporal workflows** and across regions and runtimes | Same input gives the same output in browser, Node and workflow sandbox |
| D3 | **One evaluator in browser and server**, pure JavaScript, no native modules | Bundle runs in Chrome, Node and the Temporal sandbox |
| D4 | **Error messages and authoring for non-engineers** | Type errors caught at save, with plain-language messages in every tenant locale |
| D5 | **Typed checking against blueprint facts** at save and publish | Undeclared or wrongly typed facts rejected before simulation |
| D6 | **Versioning**: language semantics can be pinned per artefact version and changed safely | Semantic profile version stored with each artefact |
| D7 | **Performance** | Within the NFRs above; compile once, evaluate many times |
| D8 | **Decision-table support**: hit policies, gap and overlap analysis, explanations | `analyse` and `explain` in [[PKG-rules-and-decision-engine]] remain possible |
| D9 | **Fit with team and stack**: TypeScript, Next.js, Prisma, Temporal; no JVM or Rust toolchain to own | — |
| D10 | **Licence, maturity and lock-in** | Permissive licence; a published specification; an exit path |

<!-- section:decision -->
## Decision

**Status: Proposed — awaiting CTO decision.**

**Recommended: the Common Expression Language (CEL) as the single textual expression language, restricted to a Nomology profile `expr/1`, evaluated by one pure TypeScript package `@nomology/expr`. Decision tables stay in our own DMN-vocabulary model in `@nomology/rules`, with cells as structured tests compiled to CEL. No third-party decision engine is adopted.**

#### 1. What CEL gives us

- A published specification with conformance tests, under Apache 2.0 [R1].
- It is designed to be non-Turing complete, mutation free and linear in evaluation time [R1]. It is "non-Turing complete, and only accesses data provided by the host application" [R2]. This meets D1 without timeouts.
- Expressions are parsed and then **type-checked against a declared environment**, so undeclared identifiers are caught before evaluation [R3]. This meets D5.
- It is used in production for API validation rules, with documented runtime cost budgets and estimated cost limits (Kubernetes) [R4], and for IAM conditions (Google Cloud) [R3].
- Its syntax (`facts.claimValue.amountMinor > 1000000 && case.stage == 'scrutiny'`) is familiar to TypeScript engineers. Non-engineers mostly use the condition builder.

#### 2. The `expr/1` profile (owned by `@nomology/expr`)

| Rule | Content |
|---|---|
| Environment | Variables are declared per context from the artefact's schema: `facts.*`, `case.*`, `stage.*`, `event.*`, `document.*`, `form.*`, `setting.*`, plus decision outputs. Undeclared names are a save-time error |
| Types | `bool`, `int`, `string`, `timestamp`, `duration`, `list`, `map`. `money` is `{amountMinor: int, currency: string}` with helpers. `date` is a calendar date type with helpers. Enums are strings checked against the declared values. **`double` is excluded**, so arithmetic is exact and identical across implementations |
| Time | **No `now()` function.** The host supplies `clock.now`: workflow time inside Temporal (deterministic `Date.now()` [R19]), the event time for automation rules, and the submit time for forms (the server recomputes it at submit) |
| Functions | Closed list, as already specified: `min`, `max`, `round`, `percentOf`, `lookup`, `in`, `contains`, `isEmpty`, `daysSince`, `businessDaysSince(schedule)`. Calendar functions are pure functions over a **pinned calendar snapshot** that the host passes in ([[PKG-calendars-and-deadline]]). They never read data themselves |
| Macros | `has`, `all`, `exists`, `exists_one`, `filter` over lists of 200 items or fewer (repeating groups, parties). No user-defined functions |
| Limits | 200 characters for gateway and automation conditions, 500 for form calculations (proposed). Parse limits on AST nodes (100) and depth (12), using the evaluator's options [R5]. Static cost estimate checked at publish |
| Literals | The validator rejects email addresses, phone numbers and personal names in expressions ([[WF-process-definition-model#protection]]) |
| Version | Each artefact stores `exprProfile: "expr/1"`. Changing semantics creates `expr/2`, selected by data and listed in the interpreter contract ([[ADR-workflow-interpreter-versioning]]). The evaluator bundled in a worker build is interpreter code, so any change that can alter a result goes through the replay gate |

#### 3. One package, every runtime

| Consumer | Where it runs | Inputs |
|---|---|---|
| Blueprint gateways, stage exit, step arguments | The pure interpreter core inside the Temporal workflow sandbox, and the simulator | Facts from history; `clock.now` = workflow time |
| Decision tables | `evaluateDecision` activity and synchronous server calls (existing); the browser for table test previews | Pinned table version; facts |
| Automation conditions | `automation.evaluate` BullMQ worker | Event payload; event time |
| Form logic | Browser runner for instant feedback; the **server is the authority** at step submit (FRM-FR-2) | Answers; submit time |
| Setting validation rules | Server when a change set is validated; console preview | Proposed values |
| SLA policy conditions | Server | Case facts |

`@nomology/expr` exposes `parse`, `check(env)`, `compile`, `evaluate`, `explain` and `toBuilderModel` / `fromBuilderModel`. The last two convert between the structured condition builder and text; the round trip is lossless for builder-expressible expressions. Inside it wraps one open-source CEL implementation in pure JavaScript. The candidates are `@marcbachmann/cel-js` (MIT, with a type-check API and parse limits [R5]) and `@bufbuild/cel` (Apache 2.0, labelled beta [R6]). The spike picks one. It is pinned by exact version and may be forked if needed.

#### 4. Errors for non-engineers

- Parser and checker errors map to a message catalogue (`expr.error.*`) with the character span, the fact's display label and a suggested fix. For example: "Claim value is an amount of money. Compare it with an amount, such as INR 10,00,000." Messages are localised with the tenant's languages ([[APP-error-message-catalogue]]).
- The condition builder (AND / OR groups, depth 2) stays the primary editor. Text mode is for advanced users and shows the same errors inline.
- `explain` returns the evaluated sub-terms, for traces in [[WF-workflow-simulation]] and for `explain` in [[PKG-rules-and-decision-engine]].

#### 5. Decision tables

- They keep the model already specified in [[PKG-rules-and-decision-engine]]: typed columns, hit policies FIRST, UNIQUE, COLLECT and PRIORITY, gap and overlap analysis, and `explain`.
- Input cells stay **structured tests** (`eq`, `in`, `between`, `lt` and so on), which compile to CEL. That keeps gap and overlap analysis exact.
- An `expr` cell (a CEL boolean over the row's inputs) is allowed only when the table is marked `advanced`. Such cells are excluded from overlap analysis, with a warning.
- Output cells are literals or CEL expressions over the inputs, replacing the `{ fn, args }` form.
- DMN XML import and export stay out of scope at launch. If they are needed, a compiler from FEEL unary tests to our model is the path (see Revisit).

#### Why

- CEL is the only candidate that meets D1 (termination by design), D2 and D3 (pure JavaScript implementations, no wall-clock guardrails) and D5 (a type checker), and also has a published specification and conformance tests (D6, D10).
- The in-house grammar would meet D1 to D5, but we would have to write and maintain the specification, parser, checker, fuzzing and documentation ourselves.
- GoRules Zen and FEEL bring decision-table engines we do not need. Zen does so through a native or WASM runtime and an optional JavaScript function node; FEEL through a JVM reference implementation or a JavaScript one that is not fully compliant.

**Scope:** every tenant-authored condition, calculated value and decision-table cell, in all products and regions. Nomology code may call `@nomology/expr` but never accepts other languages from tenants. The guardrail "no tenant-supplied scripts, expressions outside the closed grammar" in [[WF-workflow-engine]] now means "outside `expr/1`".

<!-- section:consequences -->
## Consequences

**Easier**

- One language and one evaluator across studio, forms, automation, SLA policies, settings and decision tables. One error catalogue and one set of documentation for tenants.
- The type checker catches errors at save, before simulation, and the simulator and live runs evaluate identically.
- If a non-TypeScript service ever needs to evaluate expressions, other CEL implementations exist. Assumption: Google maintains Go, Java and C++ implementations; cel.dev links the CEL-Java repository [R3].

**Harder**

| Who | Cost or risk | Mitigation |
|---|---|---|
| Platform engineers | We depend on a community (MIT) or beta (Apache) JavaScript implementation [R5][R6] | Wrapper interface; exact version pin; conformance suite in CI; licence allows a fork |
| Platform engineers | We must still build the profile, the money and date types, calendar helpers, the error catalogue and the builder conversion | Estimate 4 to 6 engineer-weeks (assumption). The in-house option needs this plus parser and checker work (8 to 12 weeks, assumption) |
| Workflow designers | Text mode uses `&&`, `\|\|` and `==`, which are less natural than FEEL for business users | The builder is the default editor; plain-language rendering ("Claim value is more than INR 10,00,000") is shown next to text mode |
| Security | The evaluator runs in the browser too | It never uses `eval` or `Function`; the server re-evaluates every value that matters; CSP is unchanged |
| Product and legal | No DMN import for institutions that keep rules in DMN tools | Revisit trigger; compile FEEL unary tests to our model if demand appears |
| Studio team | [[WF-workflow-authoring-studio]] currently says expressions are "never evaluated in the browser" | Change it to "never evaluated with `eval` or `Function`; previews use `@nomology/expr` in the browser; the server is the authority" |

**Operations and cost per region:** none. It is a library, so there is no service to run in India, Singapore or the US, no sub-processor and no licence fee. The browser bundle grows by an assumed 30 to 60 KB gzipped, to be measured in the spike.

**Follow-up work** (tickets on acceptance; owner: workflow squad unless stated): create `packages/expr` with profile `expr/1`; update `Expr` typing in [[PKG-workflow-templates]]; replace `OutputExpr` in [[PKG-rules-and-decision-engine]]; amend [[WF-workflow-authoring-studio]] browser-security text (studio team); add the `expr.error.*` messages to [[APP-error-message-catalogue]] (content); add `exprProfile` to artefact schemas in [[PKG-configuration-lifecycle]].

<!-- section:confirmation -->
## Confirmation

#### Automated checks (block merge)

| Check | Where | Pass condition |
|---|---|---|
| **Three-runtime conformance:** at least 300 golden expressions (types, money, dates, macros, every function, every error code) run in Node, in a headless browser (Playwright) and inside the Temporal time-skipping test environment | `packages/expr/conformance`, CI | Identical results and errors in all three |
| **CEL spec subset:** the cel-spec conformance cases for features in `expr/1` [R1] | CI on every evaluator version bump | 100% of included cases pass; exclusions listed with reason |
| **Profile lint:** no `double`, no undeclared functions, no host clock access, AST and depth limits | `check()` on every save and publish; unit tests with deliberately failing fixtures | Rejected expressions never reach a published artefact |
| **Determinism property test:** random facts give the same output and `inputHash` across 1,000 runs and both CI regions | CI | 0 differences |
| **Fuzzing:** 1 million generated inputs to `parse` and `check` | Nightly | No crash, and no parse slower than 5 ms |
| **Performance:** compiled-expression evaluation p99 of 50 µs or less (assumption); 500-row table p99 of 1 ms or less; automation condition p99 of 2 ms or less | CI benchmark on a fixed runner | Within budget |
| **Error catalogue coverage:** every checker error code has a message in every enabled locale | CI | 100% |
| **Replay gate:** an evaluator version bump runs the interpreter replay gate in [[ADR-workflow-interpreter-versioning]] | CI | 0 determinism errors |

**Measured after launch:** share of expressions authored in the builder versus text mode; save-time error rate; and `failed_config` human tasks caused by runtime expression errors (target 0 per month, because the checker should catch them first).

**Exceptions:** a new function or macro needs a PR with security review and a profile minor version. It is recorded in `packages/expr/PROFILE.md`.

#### Spike (two weeks, before Phase 3)

1. Implement `expr/1` on both JavaScript candidates [R5][R6].
2. Port every expression example in the current spec nodes (gateways, automation, SLA policies, form conditions, the hearing-reminder table).
3. Run the three-runtime conformance suite and the benchmarks.
4. Run a usability test with 5 non-engineer designers on seeded errors.

**Exit criteria:** one candidate passes 100% of the included cel-spec cases and gives identical results in all three runtimes. All ported examples are expressible. Bundle of 60 KB gzipped or less. Performance within budget. At least 4 of 5 designers fix each seeded error within 2 minutes using the messages. If no candidate passes, fall back to the in-house grammar (Option F) behind the same `@nomology/expr` interface, so consumers do not change.

<!-- section:options -->
## Options considered

Scores: ✔ meets the driver, ◐ partly, ✘ fails. Every option except the in-house grammar is a library. None adds a service or sub-processor, so operating effort and residency are the same in India, Singapore and the US.

| Option | D1 safety and termination | D2 determinism in Temporal | D3 browser and server, pure JS | D4 / D5 errors and type checking | D8 decision tables | D6 / D10 spec, maturity, licence | D9 skills | Lock-in | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **A. CEL, profile `expr/1`, own decision-table model** | ✔ Non-Turing complete, linear time [R1][R2] | ✔ No clock unless the host supplies one; pure JavaScript | ✔ Two pure JavaScript implementations [R5][R6] | ◐ Type checker built in [R3]; plain-language messages are ours to write | ✔ Our model, with cells compiled to CEL | ✔ Published spec and conformance tests, Apache 2.0 [R1]; JavaScript libraries MIT [R5] or Apache 2.0 beta [R6] | ✔ JavaScript-like syntax | Low; standard language, swappable implementation | **Recommended** |
| B. JSONata | ✘ Recursive functions allow loops; guardrails rely on a stack limit and a **wall-clock timeout** [R8] | ✘ A timeout can fire on one replay and not on another; `$now()` reads the wall clock unless overridden [R9][R11] | ◐ JavaScript reference implementation; evaluation is awaited (asynchronous) [R10] | ✘ No static type checking (assumption: none documented) | ✘ None | ◐ MIT [R10]; no formal standard; several ports [R7] | ✔ | Medium | Rejected for conditions; may suit integration mapping later (separate decision) |
| C. FEEL with a DMN evaluator (feelin in JavaScript, or Camunda FEEL on the JVM) | ✔ (assumption: FEEL has no general loops) | ◐ Depends on the implementation's date handling | ◐ feelin is JavaScript but not fully DMN TCK compliant [R15]; the reference-grade engine is Scala on the JVM [R16] | ◐ Business-friendly syntax; three-valued null logic is hard to explain (assumption) | ✔ Native DMN decision tables [R14] | ◐ OMG standard [R14]; MIT [R15] or Apache 2.0 [R16] | ✘ JVM, or a small single-maintainer JavaScript project | Medium | Rejected; kept as the import path if DMN demand appears |
| D. GoRules Zen (engine + ZEN expressions) | ◐ Expressions are safe, but the **function node runs JavaScript with an `http` module** [R12], which must be disabled | ✘ The Node binding is a native module, which the Temporal workflow sandbox cannot load [R19]; whether the WASM build can run in the sandbox is untested (assumption) | ◐ Browser through WASM [R13]; native modules on the server [R11] | ◐ Good editor tooling (assumption); no typed fact schema of ours | ◐ Hit policies only `first` and `collect` [R12]; UNIQUE and PRIORITY are ours to add | ◐ MIT, Rust core, version 2.0 stable; no outside code contributions accepted [R11] | ✘ Rust toolchain for fixes | Medium to high (JDM format) | Rejected; strongest if we later want a ready-made decision-graph engine run as an activity |
| E. JSON Logic | ✔ No `eval`, no side effects [R17] | ✔ | ✔ Same rule on server and browser [R17] | ✘ No types, money or dates; JSON is unreadable as text mode | ✘ None | ◐ MIT [R18]; no formal specification or conformance suite found (assumption); 67 open issues on the JavaScript library [R18] | ✔ | Low | Rejected |
| F. In-house grammar (`@nomology/expr` from scratch) | ✔ By design | ✔ | ✔ | ✔ Best messages and exact types | ✔ | ◐ We own the specification, parser, checker and fuzzing; no external conformance tests | ✔ | None, but all maintenance is ours | **Fallback** if the spike fails |

**Cost (assumptions):** A is 4 to 6 engineer-weeks to build the profile and tooling. F is 8 to 12 engineer-weeks, plus ongoing language maintenance. B to E carry a similar wrapper cost, plus the gaps marked ✘. There are no licence fees for any option.

**Conflicts with approved ADRs:** none. [[ADR-workflow-engine]] left the rules engine open and expected decisions to run as activities; that stays true for decision tables. Gateway conditions run inside the pure interpreter core, as [[WF-separation-of-concerns-temporal]] already specifies.

<!-- section:revisit -->
## When to revisit

- **DMN demand:** two or more institutions require DMN import or export, or a regulator publishes rules in DMN. Then add a FEEL-unary-test compiler, or reopen Option C.
- **Library health:** the chosen JavaScript CEL implementation has no release for 12 months, or a security advisory stays unfixed for 30 days. Then fork it or switch to the other candidate.
- **Usability:** after launch, more than 20% of expressions are saved with errors more than three times, or designers ask for text mode less than 5% of the time while asking for constructs the builder lacks.
- **Performance:** any p99 budget is exceeded in production for two consecutive weeks.
- **Scope pressure:** tenants need data transformation or loops (for example mapping integration payloads). That is a separate ADR (JSONata is a candidate there) and must not widen `expr/1`.
- **Decision-graph needs:** tenants need chained decision graphs beyond single tables plus blueprint steps. Then reassess Option D as an activity-only engine.
- **Scheduled review:** 6 months after the first tenant-authored blueprints are live.

<!-- section:questions -->
## Open questions

- [ ] Accept CEL (Option A) over the in-house grammar (Option F), accepting a dependency on a community JavaScript implementation for a published specification? (CTO)
- [ ] Accept evaluation in the browser for previews and form feedback, with the server as the authority? This changes [[WF-workflow-authoring-studio]]. (CTO with security)
- [ ] Confirm that DMN XML import and export stay out of scope for launch. (Product)
- [ ] Ownership of the `expr/1` profile and its function list: workflow squad, with security review for each new function? (Platform engineering lead)
- [ ] Form calculations limit: 500 characters, or the same 200 as gateways? (Product)

<!-- section:notes -->
## More information

- The overhaul nodes already use CEL-compatible examples: `case.stage == 'scrutiny'`, `document.filedByRole in ['claimant_counsel','respondent_counsel']` ([[WF-automation-rules#usage]]) and `case.priority != 'urgent'` ([[WF-sla-and-business-calendars]]). Note that `elig.eligible` and `facts.claimValueMinor > 1000000` need the money type in `expr/1` to become `facts.claimValue.amountMinor > 1000000`.
- Related proposed records: [[ADR-workflow-interpreter-versioning]] (the evaluator is part of the interpreter core) and [[ADR-policy-engine]] (authorisation, which is not tenant-authored expressions).
- Nodes to update on acceptance, each with a "Decided by" link: [[PKG-rules-and-decision-engine]], [[PKG-workflow-templates]], [[WF-automation-rules]], [[PKG-forms-and-form-builder]], [[WF-workflow-authoring-studio]], [[WF-sla-and-business-calendars]], [[WF-process-definition-model]] and [[PKG-settings-catalogue]].

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant. Expressions are stored in tenant data: blueprints, tables, rules, forms and settings. Changing the language after 18 months means converting every published artefact into new drafts for each tenant's review (estimate: 6 to 10 engineer-weeks plus tenant re-approval), and a running case can never change the meaning of its pinned expressions. The decision affects both products, every region and the determinism of legal deadlines. It decides the language and the decision-table evaluation approach only. Authorisation policies ([[ADR-policy-engine]]) and integration mapping are excluded.

<!-- check:options -->
### Options and evidence

Six options (CEL, JSONata, FEEL/DMN, GoRules Zen, JSON Logic, in-house) were scored against the same ten drivers, using official documentation and licences [R1]–[R19]. Unverified claims are labelled assumptions: the WASM build of Zen in the Temporal sandbox, FEEL null semantics, the JSON Logic specification status, build-cost estimates and bundle size. They are tested in the spike. The decisive drivers were D1 and D2 against JSONata (wall-clock guardrails), D2 and D3 against Zen (native module), D9 against FEEL (JVM reference implementation) and D4 and D5 against JSON Logic. There is no conflict with approved ADRs.

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

- **Residency:** unchanged. The evaluator is a library that runs where the data already is: the regional server, workers, the Temporal sandbox and the user's browser, using data the page already holds. There is no new data store or network call.
- **Tenant isolation:** unchanged. Expressions only see the variables their host passes in, inside the tenant's transaction [R2].
- **Sub-processors:** none. Third-party open-source dependencies (MIT or Apache 2.0) are added to the software bill of materials and the licence register.
- **Privacy:** expressions must not contain personal data (the validator rejects literals); traces show fact keys and sample values only.
- **Audit:** the expression text and `exprProfile` are stored in immutable artefact versions; evaluations that drive deadlines, fees or eligibility keep `decisionVersionId` and `inputHash` ([[PKG-rules-and-decision-engine]]).
- **Controls:** ISO 27001:2022 A.8.28 secure coding (no `eval`), A.8.25 secure development life cycle, and A.5.19–A.5.21 supplier and ICT supply-chain security for the dependency.
- **Reviewer:** security review to be recorded with name and date before acceptance.

<!-- check:consequences -->
### Consequences and costs

The downsides are listed per stakeholder: dependence on a community or beta JavaScript library; profile and tooling work still needed; a less business-friendly text syntax; browser evaluation needing a studio spec change; and no DMN import. There is no per-region running cost. Follow-up items are listed with owners and become tickets on acceptance. Build effort is an estimated 4 to 6 engineer-weeks (assumption).

<!-- check:reversibility -->
### Reversibility and revisit triggers

- **Kept reversible:** consumers only call `@nomology/expr`, and artefacts store `exprProfile`. The CEL library can be replaced, or the in-house grammar substituted for future profiles, without changing consumers.
- **Exit cost:** migrating existing expressions needs an upgrader from `expr/1` to the new language, applied to drafts (estimate: 3 to 5 engineer-weeks plus tenant re-approval). Running cases keep `expr/1`, which must stay supported for the interpreter contract window.
- **Triggers:** see When to revisit.
- **Review:** 6 months after the first live tenant blueprints.

<!-- check:confirmation -->
### Confirmation

Blocking CI checks: the three-runtime conformance suite (Node, browser and Temporal sandbox), the cel-spec subset on every evaluator bump, profile lint with deliberately failing fixtures, a determinism property test, nightly fuzzing, a performance benchmark against the NFRs, error-catalogue coverage, and the interpreter replay gate on evaluator changes. Production metrics cover builder versus text use, save errors and runtime `failed_config` tasks. New functions are exceptions, approved by security review and recorded in `PROFILE.md`. A two-week spike has explicit exit criteria and falls back to Option F.

<!-- check:linked -->
### Linked and lifecycle

Governs [[PKG-rules-and-decision-engine]], [[PKG-workflow-templates]], [[WF-process-definition-model]], [[WF-automation-rules]], [[PKG-forms-and-form-builder]], [[WF-workflow-authoring-studio]], [[WF-workflow-simulation]], [[WF-sla-and-business-calendars]] and [[PKG-settings-catalogue]]. It closes the open rules-engine question carried in [[ADR-workflow-engine]] notes (a new record, not an edit) and in [[WF-separation-of-concerns-temporal]]. Related: [[ADR-workflow-interpreter-versioning]], [[ADR-policy-engine]]. Status: Proposed on 2026-10-28; decider: CTO; consulted: workflow squad, studio team, security; informed: product, legal and implementation team. The listed nodes need "Decided by" back-links on acceptance.

<!-- citations -->
## Citations

```json
[
  {
    "body": "Google (CEL project)",
    "excerpt": "CEL evaluates in linear time, is mutation free, and not Turing-complete. Released under the Apache License.",
    "id": "R1",
    "kind": "standard",
    "licence": "Apache-2.0",
    "title": "Common Expression Language specification (cel-spec)",
    "url": "https://github.com/google/cel-spec"
  },
  {
    "body": "Google (CEL project)",
    "excerpt": "Non-Turing complete, and only accesses data provided by the host application; designed to evaluate safely and quickly with predictable costs.",
    "id": "R2",
    "kind": "standard",
    "title": "cel.dev: Common Expression Language",
    "url": "https://cel.dev/"
  },
  {
    "body": "Google (CEL project)",
    "excerpt": "Expressions are parsed, then type-checked against the declared environment; used by Google Cloud IAM conditions; now declared as a host-provided timestamp variable; formal verification framework in CEL-Java.",
    "id": "R3",
    "kind": "standard",
    "title": "cel.dev: CEL overview",
    "url": "https://cel.dev/overview/cel-overview"
  },
  {
    "excerpt": "CEL is used in the Kubernetes API to declare validation rules, policy rules and other constraints; sections on runtime cost budget and estimated cost limits.",
    "id": "R4",
    "kind": "vendor",
    "title": "Kubernetes docs: Common Expression Language in Kubernetes",
    "url": "https://kubernetes.io/docs/reference/using-api/cel/",
    "vendor": "Kubernetes (CNCF)"
  },
  {
    "excerpt": "Type checking with env.check(); macros has/all/exists/exists_one/map/filter; parse limits maxAstNodes, maxDepth, maxListElements; MIT licence.",
    "id": "R5",
    "kind": "web",
    "licence": "MIT",
    "title": "@marcbachmann/cel-js (CEL for JavaScript)",
    "url": "https://github.com/marcbachmann/cel-js"
  },
  {
    "excerpt": "An implementation of Common Expression Language (CEL) for ECMAScript. This project is in beta. Apache 2 licence.",
    "id": "R6",
    "kind": "web",
    "licence": "Apache-2.0",
    "title": "bufbuild/cel-es (@bufbuild/cel)",
    "url": "https://github.com/bufbuild/cel-es"
  },
  {
    "excerpt": "Lightweight query and transformation language for JSON; primary implementation in JavaScript; ports in Go and Java.",
    "id": "R7",
    "kind": "vendor",
    "title": "JSONata documentation: Overview",
    "url": "https://docs.jsonata.org/overview",
    "vendor": "JSONata project"
  },
  {
    "excerpt": "Recursive functions allow looping; tail-recursive loops are only stopped by the timeout guardrail; stack, timeout, sequence and regex options.",
    "id": "R8",
    "kind": "vendor",
    "title": "JSONata documentation: Configuring guardrails",
    "url": "https://docs.jsonata.org/guardrails",
    "vendor": "JSONata project"
  },
  {
    "excerpt": "All invocations of $now() within an evaluation of an expression will all return the same timestamp value.",
    "id": "R9",
    "kind": "vendor",
    "title": "JSONata documentation: Date/Time functions",
    "url": "https://docs.jsonata.org/date-time-functions",
    "vendor": "JSONata project"
  },
  {
    "excerpt": "MIT licence; examples use await expression.evaluate(data).",
    "id": "R10",
    "kind": "web",
    "licence": "MIT",
    "title": "jsonata-js/jsonata repository",
    "url": "https://github.com/jsonata-js/jsonata"
  },
  {
    "excerpt": "Open-source business rules engine written in Rust with native bindings for Node.js, Python, Go, Java, Kotlin and .NET; 2.0 first stable release of the new engine line; code contributions not accepted at this moment.",
    "id": "R11",
    "kind": "vendor",
    "licence": "MIT",
    "title": "gorules/zen repository (ZEN Engine)",
    "url": "https://github.com/gorules/zen",
    "vendor": "GoRules"
  },
  {
    "excerpt": "decisionTableNode hitPolicy 'first' (default) or 'collect'; functionNode runs JavaScript with built-in modules dayjs, big.js, zod, http, zen.",
    "id": "R12",
    "kind": "vendor",
    "title": "GoRules docs: JDM node types",
    "url": "https://docs.gorules.io/developers/jdm/node-types",
    "vendor": "GoRules"
  },
  {
    "excerpt": "Through WebAssembly, expressions run across platforms, including in the browser (@gorules/zen-engine-wasm).",
    "id": "R13",
    "kind": "vendor",
    "title": "GoRules: Expression language",
    "url": "https://gorules.io/tools/expression-language",
    "vendor": "GoRules"
  },
  {
    "body": "Object Management Group",
    "excerpt": "OMG specification for decision models and decision tables; formal versions listed on the page.",
    "id": "R14",
    "kind": "standard",
    "title": "Decision Model and Notation (DMN)",
    "url": "https://www.omg.org/spec/DMN/"
  },
  {
    "excerpt": "A DMN FEEL parser and interpreter written in JavaScript; 'Full DMN TCK compliance' not yet checked.",
    "id": "R15",
    "kind": "web",
    "licence": "MIT",
    "title": "nikku/feelin (FEEL interpreter in JavaScript)",
    "url": "https://github.com/nikku/feelin"
  },
  {
    "excerpt": "A parser and interpreter for FEEL written in Scala, officially maintained by Camunda; used in Camunda 7 DMN and Camunda 8.",
    "id": "R16",
    "kind": "vendor",
    "licence": "Apache-2.0",
    "title": "camunda/feel-scala (FEEL engine)",
    "url": "https://github.com/camunda/feel-scala",
    "vendor": "Camunda"
  },
  {
    "excerpt": "A small, safe way to delegate one decision; no side effects and deterministic computation time; never uses eval(); same rule on server and browser.",
    "id": "R17",
    "kind": "web",
    "title": "JsonLogic",
    "url": "https://jsonlogic.com/"
  },
  {
    "excerpt": "MIT licence; 67 open issues and 17 open pull requests at time of check (2026-10-28).",
    "id": "R18",
    "kind": "web",
    "licence": "MIT",
    "title": "jwadhams/json-logic-js repository",
    "url": "https://github.com/jwadhams/json-logic-js"
  },
  {
    "excerpt": "Workflows run in a deterministic sandboxed environment; Date.now() and Math.random() are replaced by deterministic versions; workflow code may not reference Node.js or DOM APIs; bundled with Webpack.",
    "id": "R19",
    "kind": "vendor",
    "title": "Temporal docs: Workflow basics (TypeScript SDK)",
    "url": "https://docs.temporal.io/develop/typescript/workflows/basics",
    "vendor": "Temporal Technologies"
  }
]
```

<!-- end -->
