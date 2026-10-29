# Template: Decision / rule set (`rules`)

Generated from `rules.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a business decision as data (inputs, outputs, decision table) so legal or operations teams can own and change it without code.

**Depth:** 1–4 pages. The table itself plus test cases are the spec. Every input must have a defined source; every row must have at least one test case. If a table exceeds ~30 rows, split it into chained decisions.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Decision question (level 1)

The decision phrased as a question, and who owns the answer.

Illustrative example (not a requirement):

> "How large must the tribunal be for this case?" Owned by the tenant's rules committee; platform default maintained by Nomology legal ops.

### `inputs` Inputs (facts) (level 1)

Each input, type, allowed values and where it comes from at evaluation time.

Illustrative example (not a requirement):

> | Input | Type | Source |
> |---|---|---|
> | tenant | enum | Case.tenant_id |
> | ruleSet | enum (HKIAC-2024, SEBI-ODR, CORD-STD) | Case.rules |
> | claimValueINR | number | Case claims, converted at filing date |
> | partiesAgreedSize | 1 / 3 / null | Arbitration agreement metadata |

### `outputs` Outputs (level 1)

Each output, type and meaning.

Illustrative example (not a requirement):

> | Output | Type | Meaning |
> |---|---|---|
> | tribunalSize | 1 or 3 | Number of arbitrators to appoint |
> | basis | string | Short reason shown to the secretariat |

### `table` Decision table (level 1)

The table with its hit policy. Order rows deliberately for FIRST; ensure no overlaps for UNIQUE.

Illustrative example (not a requirement):

> **Hit policy: FIRST**
> | # | ruleSet | partiesAgreedSize | claimValueINR | → tribunalSize | → basis |
> |---|---|---|---|---|---|
> | 1 | any | 1 or 3 | any | = agreed | Parties' agreement |
> | 2 | SEBI-ODR | null | > 30,00,000 | 3 | SEBI ODR circular threshold |
> | 3 | SEBI-ODR | null | ≤ 30,00,000 | 1 | SEBI ODR circular threshold |
> | 4 | any | null | any | 1 | Institution default |

### `hitpolicy` Hit policy rationale (level 2)

Why this hit policy fits (UNIQUE for complete segments, FIRST for ordered criteria, COLLECT for independent rules, SUM for scoring).

Illustrative example (not a requirement):

> FIRST, because parties' agreement must override every other criterion and is placed at the top; the final row is a catch-all.

### `overrides` Tenant overrides and versioning (level 2)

Which rows tenants may override, how a new version is published, and how running cases are pinned.

Illustrative example (not a requirement):

> Tenants may add rows above row 4. Publishing creates version n+1; cases record the version used at constitution and never re-evaluate.

### `tests` Test cases (level 1)

Table of input → expected output, covering every row and boundaries.

Illustrative example (not a requirement):

> | ruleSet | agreed | claim (INR) | Expected |
> |---|---|---|---|
> | SEBI-ODR | null | 30,00,000 | 1 |
> | SEBI-ODR | null | 30,00,001 | 3 |
> | HKIAC-2024 | 3 | 5,00,000 | 3 |

### `sources` Rule sources (level 2)

Regulation, institutional rules or contract clause behind each row.

Illustrative example (not a requirement):

> Rows 2–3: SEBI ODR circular of 31 July 2023 as amended in December 2023, or the current consolidated master circular (cite the paragraph; threshold to be confirmed by legal). Row 4: tenant default per onboarding agreement.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Currency conversion source and date for non-INR claims?

## Checks

### `inputs` Input facts and evaluation time

**Question:** Is every input fact defined with its type, allowed values, source and the moment at which it is read, including what happens when it is missing or wrong?

- For each input, which field or service supplies it at evaluation time, and is it read inside the same transaction and tenant context (RLS) as the case?
- At what moment is the decision evaluated (filing, constitution, each reminder tick in a Temporal workflow), and are inputs frozen at that moment or re-read later?
- What is the behaviour for a null, unknown or out-of-range input: a dedicated row, a default, or an error that stops the workflow and alerts a person?
- For money inputs, which currency, which conversion source and which date (for example claim value converted to INR at the filing date)? Is the rate stored with the result?
- For dates and deadlines, which time zone and calendar (calendar days, business days, which holiday list per tenant and seat of arbitration)?
- Can a user influence an input after the fact (editing claim value) to change the outcome, and is that change audited and does it trigger re-evaluation?

**Good answer:** The inputs table gives type, allowed values, source field, evaluation moment, and missing-value behaviour for every fact. Currency conversion and calendar rules are explicit and stored with the result, and the spec says whether later changes to inputs re-evaluate the decision and how that is audited.

**Red flags:**

- Inputs with no defined source, or 'from the case' without naming the field
- Nulls silently fall through to a catch-all row without being noticed
- Deadline rules with no time zone or holiday calendar

### `completeness` Hit policy and coverage

**Question:** Does the table return exactly one correct answer (or the intended set) for every possible combination of inputs, under the stated hit policy?

- Is the hit policy (UNIQUE, FIRST, PRIORITY, ANY, COLLECT with aggregation) stated and justified for this decision?
- For UNIQUE: has an automated check confirmed no two rows overlap? For FIRST: is the row order reviewed so that no row is unreachable?
- Is there a catch-all row, and if so, does matching it raise a warning so gaps in the table are noticed rather than hidden?
- Are numeric boundaries unambiguous (≤ versus <, inclusive ranges) and consistent with the source regulation's wording?
- Has the table been checked for gaps by enumerating each input's value set (a DMN tool's gap and overlap analysis, or a generated test grid)?
- If the table exceeds about 30 rows or mixes unrelated criteria, has it been split into chained decisions with a decision requirements diagram?

**Good answer:** States the hit policy with a reason, shows the result of an automated gap and overlap check, and confirms every row is reachable. Boundaries are written with explicit operators that match the source text, the catch-all row is monitored, and large tables are split into named chained decisions.

**Red flags:**

- Hit policy not stated
- FIRST used to hide overlapping rows nobody has reviewed
- Unreachable rows
- Catch-all row that silently applies to unexpected inputs

### `tenancy` Tenant overrides

**Question:** Which parts of the decision may a tenant change, which are locked because they encode law or platform policy, and how is a tenant's version kept isolated from other tenants?

- Which rows or outputs are tenant-overridable, which are locked (regulatory floors such as SEBI ODR thresholds), and how is the lock enforced in the editor and at publish time?
- Is an override a full copy of the table or a layer on top of the platform default? When Nomology updates the default, how does a tenant's override pick up or ignore the change?
- Are tenant decision tables stored with tenant_id under forced RLS, and can a tenant read the platform default but not another tenant's version?
- Can a tenant override make the outcome less protective than a regulation requires (for example a longer deadline than SEBI allows)? What validation stops it?
- Does the same tenant run several rule sets (HKIAC rules, SEBI ODR, CORD standard), and is the override scoped per rule set?
- Who at the tenant may propose and approve an override, and is that a separate permission from day-to-day case work?

**Good answer:** Marks each row or output as locked or overridable with the reason, describes the layering model and how platform default updates propagate, and confirms storage under forced RLS. Validation rejects overrides that breach regulatory bounds, overrides are scoped per rule set, and propose and approve permissions are named.

**Red flags:**

- Tenants can edit rows that encode regulation
- Overrides stored without tenant isolation
- No rule for what happens to overrides when the platform default changes

### `change` Versioning and change control

**Question:** How is a new version of the decision proposed, reviewed, tested, published and applied, and which version do already-running cases and workflows use?

- Is each published version immutable, numbered and effective-dated (effective from a date, not just 'when published')?
- Who approves publication: maker and checker, legal ops sign-off for regulatory rows, tenant rules committee for overrides?
- Does publication require the full test suite to pass automatically, and is a diff of changed rows shown to the approver?
- Are running cases pinned to the version used at their key event (for example constitution), or re-evaluated? Is that choice stated per decision and justified by the institutional rules' transition provisions?
- If the decision is called from a Temporal workflow, is the version passed in or recorded so that workflow replay stays deterministic when a new version is published?
- Can a bad version be rolled back, and what happens to cases decided under it (report, re-evaluate, notify)?
- Is there a way to preview the impact of a new version on current open cases before publishing?

**Good answer:** Describes immutable, effective-dated versions with maker-checker approval and mandatory passing tests, a row diff for reviewers, and an impact preview against open cases. States the pinning or re-evaluation rule per decision with its legal basis, how version IDs are recorded for deterministic Temporal replay, and the rollback procedure including handling of affected cases.

**Red flags:**

- Published tables can be edited in place
- One person can change and publish a regulatory decision
- Workflows read 'latest version' during replay
- No plan for cases decided under a faulty version

### `audit` Decision record

**Question:** For every case the decision affects, is there a stored record of which version ran, with which inputs, which row matched and what it returned, so the outcome can be reproduced years later?

- Is a decision record stored per evaluation with: decision ID, version, tenant, case, timestamp, input values, matched row(s), outputs, and caller (user, workflow, job)?
- Can the platform re-run a past evaluation against the stored version and inputs and get the same answer, and is that tested?
- How long are decision records kept, and does that match case retention and any institutional or regulatory record-keeping period?
- Are decision records append-only and protected from edits, including by Nomology staff?
- When a secretariat member overrides the decision's output manually, is the override, reason and approver recorded next to the original result?
- Can the decision record be exported for an institution's review, a court challenge to an award, or a regulator's inspection?

**Good answer:** Defines the decision record schema with version, inputs, matched rows and outputs, stored append-only with the case and kept for the case retention period. A replay test proves past outcomes can be reproduced, manual overrides are recorded alongside the computed result, and an export exists for institutional, judicial or regulatory review.

**Red flags:**

- Only the output is stored, not inputs or version
- Manual overrides replace the computed value with no trace
- Decision records deleted before the case record

### `compliance` Regulatory and rule sources

**Question:** Does every row that encodes a regulation, institutional rule or contract term cite its exact source, and is there a process to update the table when that source changes?

- For each regulatory row, which document, clause and version is cited (for example SEBI ODR master circular paragraph, HKIAC Administered Arbitration Rules article, MSME Act section)?
- Has a qualified person (legal ops or tenant counsel) confirmed that the row's logic matches the source, and is that sign-off recorded with a date?
- Who monitors for amendments (SEBI circulars, MII notices from NSE or BSE, institutional rule revisions), and how fast must the table be updated after one takes effect?
- When a rule change applies only to cases filed after a date, is that transition encoded as an input (filing date) rather than by editing old rows?
- Does any row make or materially inform a decision about a person using AI or scoring? If so, is it covered by the ISO 42001 and DPDP assessments?
- Where the decision affects deadlines or fees owed by parties, is the outcome explained to parties in the way the source rules require?

**Good answer:** Each regulatory row cites document, clause and version with a dated legal sign-off. A named owner monitors listed sources with a target time to update after an amendment, transition rules are encoded with effective-date inputs, and any automated decision about individuals is covered by the relevant AI and data protection assessments.

**Red flags:**

- Regulatory rows with no citation
- Citation to a superseded circular
- No owner for tracking amendments

### `testing` Test coverage

**Question:** Do automated tests cover every row, every boundary and every invalid input, and do they run on every change to the table, including tenant overrides?

- Is there at least one test per row, and is row coverage measured automatically (a row with no test fails the build)?
- Are boundary values tested on both sides of each threshold (for example INR 30,00,000 and 30,00,001) and at the edges of date ranges?
- Are null, unknown and invalid inputs tested, including the expected error or catch-all behaviour?
- Do tenant overrides run the platform's regulatory tests as well as their own, so an override cannot break a locked rule?
- Are the test cases written or reviewed by the decision owner (legal ops or tenant committee), not only by engineers?
- Is there a regression suite of real past cases (anonymised) whose expected outcomes must not change unexpectedly?

**Good answer:** Tests are stored with the table, run on every publish, and the build fails if any row lacks a test. Boundaries are tested on both sides, invalid inputs have explicit expectations, tenant overrides inherit locked regulatory tests, the owner signs off the expected results, and an anonymised regression set guards against unintended changes.

**Red flags:**

- Rows with no test
- Thresholds tested on one side only
- Tests maintained only by engineers with no owner review

### `explainability` Explanation and challenge

**Question:** Can secretariat users, parties and neutrals see why the decision produced its result, and is there a defined route to question or override it?

- Does each output include a plain-language basis (the 'basis' output) naming the rule and source, shown where the result appears?
- Is the explanation available in the case record for parties where the outcome affects them (fees, deadlines, tribunal size)?
- Who may override a computed result in a specific case, with what approval, and how is the case then flagged?
- Is the explanation text reviewed for accuracy and accessible language, and translated where the tenant serves non-English users?
- Are override rates monitored per decision and per tenant, so a decision that is often overridden is reviewed?

**Good answer:** Every output carries a reviewed, plain-language basis citing the rule, shown to the users it affects. The spec names who may override a result in a case, the approval needed and how it is recorded, and override rates are reported to the decision owner for periodic review.

**Red flags:**

- Results shown with no reason
- Anyone with case access can override silently
- No tracking of how often results are overridden

