---
id: "PKG-tenant-terminology-and-copy"
title: "Tenant terminology and copy overrides"
parent: "PKG-settings"
order: 1
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Tenant (and optionally case-type) terminology and copy override sets: only `term` and `overridable` messages, plain text with matching ICU variables, complete for every enabled language, published as immutable versions through the configuration change lifecycle"
links: []
rev: 3
syncHash: "be6745985c14bf11"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.1 Tenant terminology and copy overrides

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tenant (and optionally case-type) terminology and copy override sets: only `term` and `overridable` messages, plain text with matching ICU variables, complete for every enabled language, published as immutable versions through the configuration change lifecycle

<!-- section:statement -->
## Statement

When a holder of `settings.branding:write` publishes a terminology or copy override set through a change set, the platform shall accept it only for message IDs marked `term` or `overridable` in the platform message catalogue, only as plain text with the same ICU variables as the source message, and only when a value exists for every language in the effective `locale.languages.enabled`; and shall store the set as a new immutable version, make it the value of `content.terminology.override_set` (tenant scope) or `content.terminology.case_type_override_set` (case-type scope), and record an audit event.

<!-- section:rationale -->
## Rationale and source

Institutions use their own terms ("matter" for "case", "Registrar" for "secretariat", "lodge" for "file"), and SEBI ODR institutions need investor-friendly wording, so the platform must reflect their language. But some text must not change: legal notices, consent and privacy text ([[I18N-legal-declaration-and-consent]]), security messages and platform terms. Overrides are untrusted tenant input, so they must not carry markup, and a missing translation must not leave a party with an English-only or empty label. Parent: [[PKG-settings]]; settings keys in [[PKG-settings-branding-content]]; terminology governance: [[I18N-platform-glossary-and]]; change process: [[PKG-configuration-lifecycle]].

Override classes in the message catalogue (`packages/i18n/catalogue.json`, field `override`):

| Class | Examples | Tenant may change |
|---|---|---|
| `term` | `term.case`, `term.secretariat`, `term.claimant` | Yes; change propagates to every message that uses the term via ICU `{term_case}` references |
| `overridable` | Button labels on filing steps, help hints, empty states | Yes |
| `locked` | Consent and privacy text, security warnings, error messages for authentication, AI-content label, danger action labels | No |

Scopes ([[PKG-configuration-scope-hierarchy]]): a tenant-scope set applies everywhere in the tenant; where `content.terminology.allow_case_type_terms = true`, a case-type set (for example "conciliator" instead of "neutral" for SEBI ODR conciliation) is layered on top for screens, notifications and documents of that case type. Nomology can mark individual overrides in a blueprint as `managed` (for example regulator-defined investor terms, pending legal), which the tenant cannot change. There are no unit, case or user overrides.

Override sets are artefacts of kind `terminology_overrides` stored in `tenant_copy_override_version` (tenant-owned, forced RLS) and resolved into the message bundle passed to `UiProvider`, notifications and PDFs. Caches are keyed by `tenantId` + override set version (+ case-type set version) + locale.

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a tenant with `locale.languages.enabled = [en-IN, hi-IN]`, **when** a `content_admin` publishes a change set setting `term.case = "matter"` with a Hindi value, **then** a new override set version is stored, `content.terminology.override_set` points to it, `admin.config.published` and `admin.settings.published` are audited, and within 60 seconds the case list, notification emails and generated PDFs use "matter" and the Hindi term.
- **Given** the same tenant, **when** the admin submits `term.case` with only an English value, **then** submit is refused with `COPY_LOCALE_INCOMPLETE` listing `hi-IN`.
- **Given** an override value containing `<a href=...>`, or `{amount}` where the source message has no `amount` variable, **then** submit is refused with `COPY_MARKUP_NOT_ALLOWED` or `COPY_VARIABLE_MISMATCH`.
- **Given** a request to override `consent.dpdp.notice` (class `locked`), **then** it is refused with `COPY_LOCKED` (HTTP 403 problem type) and nothing is stored.
- **Given** a blueprint-managed override, **when** a tenant admin tries to change it, **then** it is refused with `SettingLockedError` shown as "Managed by Nomology".
- **Given** `allow_case_type_terms = true` and a case-type set for "SEBI ODR conciliation" with `term.neutral = "conciliator"`, **when** a party views a case of that type, **then** "conciliator" is shown, and cases of other types still show the tenant term.
- **Given** `content.copy.review_overrides = true`, **when** the author tries to publish their own change set, **then** publish is not offered and a second admin with `settings.branding:approve` must approve.
- **Given** two tenants A and B, **when** A publishes an override, **then** B's pages, notifications and caches are unchanged (cross-tenant test).
- **Given** an override that makes a button label longer than its limit (for example 30 characters), **then** the admin sees a warning and a preview at 320 px before submitting.
- **Given** a published override set, **when** the admin reverts the change set, **then** the previous version becomes active within 60 seconds and the revert is audited as `admin.config.rolled_back`.

<!-- section:verification -->
## Verification method

Test: unit tests in `packages/i18n/test/copy-overrides.spec.ts` for each error code and for case-type layering; integration test against Postgres with forced RLS for cross-tenant isolation (per [[MT-automated-tests-that-prove-one]]); change-set lifecycle tests from the shared kind suite ([[PKG-configuration-and-customisation#testing]]); Playwright test of the tenant admin flow at `/admin/settings/content/terminology` including preview and revert; audit event assertions. Evidence: stored versions, change sets and audit events.

<!-- section:priority -->
## Priority

Must for launch tenants that use non-default terminology (assumption: at least one arbitral institution tenant and every SEBI ODR institution). Phase 4 (configuration and metadata) of [[PLAN]], with tenant-scope `term` support needed earlier for Phase 3 if the first domain slice ships to such a tenant; case-type sets are Should for Phase 4.

<!-- section:questions -->
## Open questions

- [ ] Confirm the initial list of `locked` message IDs with legal. (owner: legal, content design)
- [ ] Are tenant overrides machine-translated as drafts for missing languages (`content.copy.ai_translation_drafts`), or must the tenant supply every language? Proposed: tenant supplies; AI suggestions allowed but marked and reviewed. (owner: i18n lead)
- [ ] Should a SEBI ODR institution be allowed to rename regulator-defined terms, or are those managed by the blueprint? (owner: legal)

<!-- section:notes -->
## Notes

Overrides are text only; rich text is not supported. Rollback is reverting the change set or restoring an earlier version. Copy history is retained as long as cases that displayed it may be disputed (retention per [[PKG-retention-and-deletion-schedule]]); generated documents record the override set version used.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without it, either tenants cannot use their institutional terms (a contract need for institutions), or overrides could remove legally required text, inject markup or leave locales incomplete.

<!-- check:singular -->
### Singular

The statement bundles four acceptance conditions (allowed class, plain text with matching variables, locale completeness, versioned with audit) for one action (publishing an override set). They are tested separately; if reviewers prefer strict singularity, split into four child requirements with the same trigger.

<!-- check:complete -->
### Complete and scoped

Covers all tenants and products, both scopes (tenant and case type), the locked class, managed overrides, missing languages, markup, variable mismatch, length warnings, review policy, rollback and cache keys. Open: the exact list of locked message IDs, which is maintained in the catalogue.

<!-- check:verifiable -->
### Verifiable

Each refusal has an error code tested in unit tests; cross-tenant isolation is tested against real Postgres with forced RLS; propagation within 60 seconds is tested end to end.

<!-- check:consistent -->
### Consistent

Error format follows the problem types in [[APP-api-error-catalogue-problem]]; storage follows [[MT-every-tenant-owned-table-carries]]; locked legal text aligns with [[I18N-legal-declaration-and-consent]]; keys and permissions follow [[PKG-settings-catalogue]]; publish and rollback follow [[PKG-configuration-lifecycle]].

<!-- check:traced -->
### Traced

Source: institutional terminology needs (arbitral institutions, SEBI ODR investor-facing language) and legal-text protection. Forward trace: settings keys in [[PKG-settings-branding-content]], kind `terminology_overrides` in [[PKG-configuration-and-customisation]], tests listed under verification.

<!-- end -->
