---
id: "PKG-forms-and-form-builder"
title: "Forms and form builder"
parent: "PKG-configuration-and-customisation"
order: 2
type: "feature"
template: "ui"
status: "draft"
owner: null
indicative: false
summary: "Tenant form builder and form runner: intake, filing, task-outcome and declaration forms with conditions, repeating groups, role-based field visibility, accessibility checks, maker-checker publishing and version pinning through blueprints"
links: []
rev: 3
syncHash: "00e88ae0e44ac4fc"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.2 Forms and form builder

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tenant form builder and form runner: intake, filing, task-outcome and declaration forms with conditions, repeating groups, role-based field visibility, accessibility checks, maker-checker publishing and version pinning through blueprints

<!-- section:persona -->
## Persona and goal

**Primary persona: tenant admin (or implementation specialist) at an institution.** Example: the tenant admin of a SEBI ODR institution needs an investor complaint intake form that collects the market participant, complaint category, amount and supporting documents, shows different questions for individual and corporate complainants, and is easy for an unrepresented investor to complete on a phone. Goal: build, test and publish that form without engineering help, and attach it to the intake step of the case type's workflow template.

**Secondary persona: the person filling the form** (party, counsel, neutral completing a declaration). Their journey is the runtime rendering of the published form, covered in the Screens and States sections as the "form runner".

**Tertiary persona: the approver** (a second tenant admin or the institution's legal lead) who reviews the diff of fields, conditions, visibility and legal text before publication.

<!-- section:journey -->
## Journey steps

1. Tenant admin or workflow designer opens **Forms** in the tenant admin console (`/admin/workflows/forms`, [[APP-tenant-admin-console]]), or opens a form directly from a blueprint step in the studio ([[WF-workflow-authoring-studio]]).
2. Creates a new form or duplicates a library template (for example "Statement of Claim — institutional arbitration", "ODR complaint intake"), choosing its **purpose**: `intake` (opens a case), `filing` (a party submission inside a case), `task_outcome` (staff or neutral completes a human task), or `declaration` (consent, disclosure, conflict declaration).
3. Adds sections and fields: core fields and custom fields ([[PKG-metadata-management-entity]]), form-only questions, repeating groups (for example "add another respondent"), and calculated read-only fields that use the shared closed expression grammar.
4. Sets conditions (show/hide, required-when), validation, and **field visibility per case role** (for example a confidentiality field visible to the tribunal and secretariat only); links legal text from the declaration register ([[I18N-legal-declaration-and-consent]]).
5. Previews in each enabled language, at mobile width and as each case role; runs the automatic accessibility and completeness checks.
6. Submits for review; a second admin reviews the diff and approves; a holder of `form:publish` publishes ([[PKG-configuration-lifecycle]], maker-checker).
7. Attaches the published form version to a blueprint step (`form_request`, `human_task` outcome, or case-type intake). The blueprint pins the form version; a newer form version reaches running cases only through a blueprint version and, if needed, a migration ([[WF-workflow-versioning]]).
8. Party opens the filing link → form runner (multi-step with save-and-resume, [[PKG-stepper-and-multi-step-form]]) → reviews answers → submits with consequential confirmation → receives a receipt with a reference and a PDF copy of the answers.

<!-- section:screens -->
## Screens

| Screen | Purpose | Key content | Primary action | Secondary actions |
|---|---|---|---|---|
| Forms list (`/admin/workflows/forms`) | Find and manage forms | Name, key, purpose, status (draft / in review / approved / published / superseded / retired), latest version, used by (case types and blueprint steps, with pinned versions), last edited | New form | Duplicate, view versions, retire (blocked while a current blueprint version uses it) |
| Form editor | Build structure | Left: field palette (core, custom, form-only, layout); centre: canvas of sections and fields (keyboard-reorderable list, not drag-only); right: properties panel (label per locale, help, required, validation, conditions, visibility tier) | Save draft | Undo/redo, preview, validate, submit for review |
| Condition editor (dialog) | Define show/hide and required-when rules | Rule rows "When [field] [operator] [value]"; AND/OR grouping (max depth 2) | Apply | Remove |
| Preview | See the form as a filler would | Locale switcher, device width switcher (360 px, 768 px, 1280 px), case-role switcher (claimant, respondent counsel, tribunal, secretariat), sample data | Run checks | Back to editor |
| Checks report | Show validation and accessibility results | Errors (block submit) and warnings: missing labels in a locale, fields without help for legal terms, conditions referencing removed fields, personal-data fields without purpose note | Fix (jumps to field) | Export report |
| Review and publish | Approver compares versions | Side-by-side diff of fields, conditions and legal text; author, reason | Publish (step-up) | Reject with comment |
| Form runner (party) | Complete and submit | Steps, progress, fields, inline help, save status, review page | Next / Submit | Save and exit, back |
| Submission receipt | Confirm what was submitted | Reference, time (tenant time zone and UTC), answers summary, PDF download | Go to case | Print |

<!-- section:states -->
## States per screen

| Screen | Loading | Empty | Error | Partial | Permission denied | Success |
|---|---|---|---|---|---|---|
| Forms list | Skeleton rows | "No forms yet. Start from a template or create a form." with both actions | "We could not load your forms. Try again." + retry | Some usage counts unavailable: show "—" with tooltip | Non-admin: generic not-found page | — |
| Form editor | Skeleton canvas | New form: "Add your first section" | Save failed: banner "Your changes are not saved yet. Retrying…"; conflict: "Someone else changed this form. Review their changes." with compare | Custom field definitions failed to load: palette shows core fields and a retry link | Read-only view for reviewers without edit permission | "Draft saved 10:42" status text (live region, polite) |
| Preview | Spinner with text | — | Render error identifies the field | Locale missing translations: banner listing fields falling back to default language | — | — |
| Checks report | Progress text | "No problems found" | Check service failed: retry | Warnings only: submit allowed | — | — |
| Review and publish | Skeleton diff | — | Publish failed: reason shown (e.g. "Depends on a retired custom field") | — | Author sees "You cannot publish your own change" | "Version 4 published. New filings will use it; cases already started keep version 3." |
| Form runner | Skeleton per step | — | Field errors listed at top with links, and inline; server error: "Your answers are saved. We could not submit just now." | Upload still scanning: "Your file is being checked; you can continue." | Link expired or not invited: plain explanation and contact route | Receipt page |

<!-- section:validation -->
## Validation and business rules

- Builder rules: every field needs a label in the tenant's default locale; field keys unique within a form; conditions may only reference earlier fields (no cycles); max 200 fields and 20 steps per form (proposed); required fields cannot be hidden by a condition without also being conditionally required.
- Runner validation is generated from the form definition plus the metadata definition (`zodFor`), executed in the browser for feedback and again on the server as the authority.
- Business rules that depend on case data (for example "claim amount must exceed the ODR threshold") call the rules engine ([[PKG-rules-and-decision-engine]]) from the server on step submit, not hard-coded in the form.
- Legal text blocks reference versioned entries in the declaration register; the accepted version is stored with the submission.
- Repeating groups: minimum and maximum instances (default 1 to 20); validation runs per instance; conditions may reference fields in the same instance or earlier fields only.
- Calculated fields use only the closed expression grammar (`@nomology/expr`) over earlier fields; they are read-only and recomputed on the server at submit.
- Field visibility per case role is enforced on the server: the runner receives only the fields the user's case role may see, and submitted values for hidden fields are rejected.
- A form used by a published blueprint cannot have a field removed in a new version without a blueprint diff warning, because blueprint facts may read that field ([[WF-process-definition-model#entities]]).
- Requirement prefix `FRM-FR-`: **FRM-FR-1** every published form passes the accessibility checks; **FRM-FR-2** server validation is the authority; **FRM-FR-3** each submission stores the form version and legal-text versions accepted; **FRM-FR-4** publishing requires `form:publish` and an approver other than the author.

<!-- section:content -->
## Content and copy

- Labels and help text follow the platform voice ([[APP-voice-tone-and-content-style]]) and glossary ([[I18N-platform-glossary-and]]); the builder warns on banned synonyms.
- Plain-language guidance for unrepresented parties ([[DOC-plain-language-guidance-for]]): help text suggested for legal terms; reading-level indicator on help text (proposed).
- Legal and declaration text is never typed into a form directly; it is picked from the register and approved by the tenant's legal owner.
- Error messages come from [[APP-error-message-catalogue]] with field-specific variables.

<!-- section:accessibility -->
## Accessibility

WCAG 2.2 AA [R1] criteria needing attention:
- **Builder**: reordering fields must not depend on drag and drop — provide move up/down buttons and keyboard shortcuts (2.5.7 Dragging Movements); properties panel fully keyboard operable (2.1.1); focus visible and not obscured by sticky panels (2.4.11 Focus Not Obscured); status messages for save and check results announced (4.1.3).
- **Builder checks enforce runner accessibility**: every field has a programmatic label (1.3.1, 3.3.2), required state exposed, error identification (3.3.1) and suggestions (3.3.3), grouping of radio/checkbox sets in fieldsets with legends, autocomplete attributes for personal fields (1.3.5), no information conveyed by colour only.
- **Runner**: errors summarised at top with links and announced; no time limits on steps (2.2.1) — sessions extend on activity and drafts are saved; redundant entry avoided (3.3.7) — answers carried from earlier steps or the profile; accessible authentication on resume ([[PKG-accessible-authentication-and]]); target size ≥ 24×24 px (2.5.8).
- Patterns follow the ARIA Authoring Practices for listbox, combobox and dialog [R2].

<!-- section:responsive -->
## Devices and responsiveness

Builder: desktop and tablet landscape (≥ 1024 px); below that, read-only preview with a notice. Runner: mobile first from 320 px CSS width; one column below 768 px; file upload offers camera capture on mobile; review page collapses sections into expandable summaries.

<!-- section:questions -->
## Open questions

- [x] Repeating groups and calculated fields: decided, in scope (see Validation).
- [ ] Should forms support e-signature of the submission ([[INT-e-signature]]) or is consequential confirmation with step-up enough for filings?
- [ ] Is a reading-level indicator required for SEBI ODR investor-facing forms? Owner: product with legal.
- [ ] Offline or low-bandwidth mode for the runner?
- [ ] Should the admin copilot generate a first draft of a form from an uploaded paper form (PDF)? Proposed: yes, as a draft for review, subject to [[AI-tenant-ai-policy]]. Owner: AI group.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenancy and branding

Forms are tenant-owned configuration artefacts under forced RLS; the runner resolves the form version pinned on the case or the published version for the tenant resolved from the host; tenant branding and legal text come from the same tenant. Platform templates are copies, never shared live objects.

<!-- check:security -->
### Access and data exposure

All validation is repeated on the server from the definition; the runner receives only the fields the user may see (visibility tiers via `metadata.project`); uploads go through signed URLs and scanning; form definitions cannot contain scripts or HTML beyond the sanitised rich-text subset. Field visibility per case role is enforced server-side; publishing needs `form:publish` with maker-checker.

<!-- check:accessibility -->
### Accessibility (WCAG 2.2 AA)

The builder's checks block publishing a form that lacks labels, groupings or error text, so runner accessibility does not depend on each tenant admin's knowledge; the builder itself avoids drag-only interactions and is tested with keyboard and screen readers (NVDA, JAWS, VoiceOver) as part of [[TST-accessibility-testing]].

<!-- check:i18n -->
### Localisation

Labels, help and option texts are stored per locale; the preview shows missing translations; dates, numbers and currency in the runner use the locale and tenant time zone ([[I18N-l10n]]); right-to-left layout is supported by the design system components.

<!-- check:consequential -->
### Consequential actions

Submitting a filing uses the consequential confirmation pattern ([[PKG-modal-dialog-and-consequential]]): summary of what will be filed and who will see it, step-up where the case type requires, and a receipt with reference, timestamps and a PDF of answers stored as an immutable document version.

<!-- check:resilience -->
### Errors and resilience

The runner autosaves drafts server-side every 10 seconds of change and on step change; idempotency keys make submit safe to retry; concurrent edits in the builder are detected with optimistic versioning and resolved with a compare view.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WCAG",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C WAI",
    "id": "R2",
    "ident": "ARIA APG",
    "kind": "standard",
    "title": "ARIA Authoring Practices Guide",
    "url": "https://www.w3.org/WAI/ARIA/apg/"
  }
]
```

<!-- end -->
