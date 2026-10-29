---
id: "DOC-developer-facing-api-copy"
title: "Developer-facing API copy"
parent: "DOC-api-documentation-openapi"
order: 1
type: "feature"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "API error messages, OpenAPI descriptions and webhook docs using the platform glossary"
links: []
rev: 2
syncHash: "bae7454b7970dadd"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17.2.1 Developer-facing API copy

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> API error messages, OpenAPI descriptions and webhook docs using the platform glossary

<!-- section:scope -->
## Scope and audiences

Governs the words integrators read: RFC 9457 problem `title` and `detail` text for the public REST API, OpenAPI summaries and descriptions, AsyncAPI webhook event descriptions, field descriptions, and developer portal guides ([[DOC-api-documentation-openapi]]). Readers are developers at institutions, aggregators (for example NSE as an MII routing SEBI ODR matters) and system integrators; they know HTTP and JSON, may not know arbitration or ODR procedure, often read English as a second language, and usually read error text while debugging under time pressure. UI error copy is governed by [[APP-error-message-catalogue]]; this node keeps API copy consistent with it.

<!-- section:voice -->
## Voice and tone

- **Precise and literal.** Say exactly what the API did and what the client must change. No idioms, jokes or exclamation marks.
- **Neutral.** The platform is a neutral forum: descriptions never imply that one party's action is preferred, never predict outcomes and never give legal advice ("Use this to withdraw a case" is fine; "Withdraw weak claims early" is not).
- **Short first, detail after.** The first sentence of every description says what it is or does; detail follows.
- **Tone by situation**: reference text is plain and factual; error `detail` is direct and actionable; deprecation notices state dates and the replacement.

<!-- section:terminology -->
## Terminology and glossary alignment

Canonical terms come from [[I18N-platform-glossary-and]]; API names use the same concept names in `camelCase`.

| Concept | API term | Banned in API copy |
|---|---|---|
| Dispute record | `case` | matter (except where the glossary lists it as a tenant display variant), lawsuit, ticket |
| Person or entity in a case | `party` | client, user (when meaning a party), litigant |
| Lawyer or authorised representative | `representative` (role `counsel`) | attorney, advocate (as API term) |
| Arbitrator, mediator, conciliator | `neutral` (with `neutralRole`) | judge, adjudicator |
| Submitted document set | `filing` | submission (as a noun for filings), upload |
| Single stored document version | `document`, `documentVersion` | file (except for the binary itself) |
| Hearing bundle | `bundle` | binder, pack |
| Institution or organisation using the platform | `tenant` in admin APIs only | organisation, account, customer (in public case APIs, the tenant is implicit and not named) |

Tenant display variants (for example a tenant that shows "matter" in its UI) never change API field names.

<!-- section:patterns -->
## Microcopy patterns

| Element | Rule | Good | Bad |
|---|---|---|---|
| Operation summary | Imperative verb + object, under 8 words | "Create a case" | "This endpoint can be used for case creation" |
| Operation description | What it does, preconditions, side effects, idempotency | "Creates a case in the tenant's home region and returns its ID. Send an `Idempotency-Key`; repeating the same key with the same body returns the original response." | "Creates stuff" |
| Field description | What the value means, unit, format, constraints | "`claimValueMinor`: claim value in the minor unit of `currency` (for example paise for INR). Integer, 0 or more." | "Claim amount" |
| Enum value description | One line per value | "`WITHDRAWN`: the claimant withdrew the case; no further filings are accepted." | none |
| Dates | Always ISO 8601 with offset; say which time zone governs deadlines | "`dueAt`: deadline as an ISO 8601 timestamp. Deadlines are computed in the seat time zone (`seatTimeZone`)." | "due date" |
| Deprecation | Date, replacement, link | "Deprecated. Removed on 2027-03-01. Use `GET /v2/cases/{caseId}/filings`." | "Will be removed soon" |

<!-- section:errors -->
## Error messages

Every problem response has `type` (stable URI), `title` (constant per type), `status`, `detail` (instance-specific, actionable), `instance` (request ID), and, for validation, `errors[]` with JSON Pointer and message. `detail` never includes another party's data, internal hostnames, SQL, stack traces or whether a resource exists in another tenant.

| Code | Status | Title | Detail (final copy) | Retry |
|---|---|---|---|---|
| `validation-failed` | 422 | Request validation failed | "{count} fields are invalid. See `errors` for each field." | No |
| `not-found` | 404 | Resource not found | "No {resourceType} with this ID exists, or you do not have access to it." | No |
| `forbidden-action` | 403 | Action not allowed | "Your API client is not allowed to {action} on this {resourceType}." | No |
| `case-state-conflict` | 409 | Case is not in a state that allows this action | "This case is {status}. {action} is allowed only when the case is {allowedStatuses}." | No |
| `idempotency-key-reused` | 409 | Idempotency key reused with a different request | "This `Idempotency-Key` was used with a different request body in the last 24 hours. Use a new key for a new request." | No |
| `deadline-passed` | 422 | Deadline has passed | "The deadline for this filing was {dueAt} ({seatTimeZone}). Late filings need permission from the tribunal or secretariat." | No |
| `upload-not-scanned` | 409 | File is still being checked | "The file is being scanned for malware. Try again after `Retry-After` seconds." | Yes |
| `rate-limited` | 429 | Too many requests | "This API client has exceeded {limit} requests per {window}. Retry after `Retry-After` seconds." | Yes |
| `wrong-region` | 421 | Request sent to the wrong region | "This tenant's data is served from {regionBaseUrl}. Send requests there." | No |
| `internal-error` | 500 | Unexpected error | "Something went wrong on our side. Quote request ID {instance} if you contact support." | Yes, with backoff |

`not-found` text is identical whether the resource does not exist or belongs to someone else, matching [[APP-error-message-catalogue]]. Status codes and types are defined in [[APP-api-error-catalogue-problem]]; this table defines their wording.

<!-- section:legal -->
## Legal and declaration text

API copy has limited legal effect, but these texts do and must be approved:

| Text | Owner | Approver | Versioning |
|---|---|---|---|
| API terms of use shown in the developer portal | Nomology legal | Nomology legal | Versioned; acceptance recorded per API client in [[INT-api-platform-tables]] |
| Webhook signature and delivery guarantee statements | API platform | Information security owner | With the AsyncAPI version |
| Descriptions of legally significant operations (service of notices, filing timestamps, deemed receipt) | API platform | Nomology legal plus the tenant where its rules define the effect | With the OpenAPI version |

Descriptions of legal effect point to the tenant's rules ("Filing time is the server timestamp `filedAt`; how it counts for deadlines is set by the tenant's rules") rather than stating a rule the platform does not own. Full register: [[I18N-legal-declaration-and-consent]].

<!-- section:localisation -->
## Localisation readiness

API copy is English only at launch (assumption, to confirm with aggregators). Problem `title` and `detail` templates are still externalised with stable IDs and ICU placeholders so a translated `Accept-Language` response can be added later without changing codes.

<!-- section:governance -->
## Content governance and workflow

Copy lives with the schemas in `packages/api-contracts` (descriptions) and `packages/api-contracts/problems/en.json` (problem text). Engineers write first drafts; content design reviews every new problem type and description of a legally significant operation; legal approves the items in the Legal table. Changes ship with the code and appear in the API changelog.

<!-- section:questions -->
## Open questions

- [ ] Do any aggregators or institutions need API error text in a language other than English?
- [ ] Should the `wrong-region` problem reveal the correct region URL, or is that itself information about the tenant? (Proposal: yes, because the client is already authenticated to that tenant.)
- [ ] Legal to confirm wording for filing timestamp and deemed receipt descriptions per tenant type.

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Descriptions of legal effect defer to the tenant's rules and are approved by Nomology legal (Legal table); numbers such as deadlines are inserted from data (`dueAt`, `seatTimeZone`), never typed into copy.

<!-- check:terminology -->
### Terminology consistency

API terms map one-to-one to glossary entries (Terminology table), with banned synonyms checked by a lint on OpenAPI descriptions and problem templates. Tenant display variants never change API field names.

<!-- check:disclosure -->
### Confidentiality and privacy in copy

Problem `detail` text never includes other parties' data, internals or cross-tenant existence; `not-found` is identical for absent and inaccessible resources, aligned with ISO-14 in [[TST-multi-tenant-isolation-tests]].

<!-- check:provenance -->
### Version and proof of what was shown

API terms acceptance is recorded per API client with the terms version; OpenAPI and AsyncAPI documents are versioned with each release so the description in force at any time can be reproduced.

<!-- end -->
