---
id: "PKG-document-and-notification"
title: "Document and notification templates"
parent: "PKG-configuration-and-customisation"
order: 4
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Document and notification templates per tenant, unit, locale and jurisdiction: variable schemas, versioned maker-checker publishing, provider approvals (WhatsApp, India DLT), locked prescribed formats, preview, test send and rendering"
links: []
rev: 3
syncHash: "0603626215ef76e1"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.4 Document and notification templates

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Document and notification templates per tenant, unit, locale and jurisdiction: variable schemas, versioned maker-checker publishing, provider approvals (WhatsApp, India DLT), locked prescribed formats, preview, test send and rendering

<!-- section:purpose -->
## Purpose and scope

`@nomology/templates` manages and renders **document templates** (procedural orders, notices of arbitration acknowledgement, awards shells, receipts, invoices, certificates of service) and **notification templates** (email, SMS, WhatsApp, in-app, push) per tenant, unit (where allowed), language and jurisdiction, with versioning, required-variable schemas, preview, test sends and maker-checker publishing. Generated documents are stored as immutable document versions with a content hash.

Split of responsibilities: this package owns template **structure, variables, versions, administration and rendering**; which template an event uses is set in the notification policy ([[PKG-notification-policies]]); final wording standards for notifications are in [[PKG-notification-copy]]; legal and declaration text is referenced from [[I18N-legal-declaration-and-consent]]; tenant string overrides from [[PKG-tenant-terminology-and-copy]]; print styling from [[PKG-print-and-formal-document-theme]]; accessibility of generated PDFs from [[DOM-accessible-documents-and]]; content-class checks for channel templates from [[INT-connector-data-policies]].

**Administration**

| Action | Who (role keys) | Permission | Notes |
|---|---|---|---|
| Edit draft, preview, test send to self | `content_admin`, `tenant_admin` | `template.document:update` / `template.notification:update` | Preview uses synthetic sample data only |
| Submit for review | `content_admin` | `template.document:update` / `template.notification:update` | Validation must pass: variables, locales required by `notify.template.required_locales`, channel limits, DLT ID and whitelisted URLs for India SMS [R1], provider category for WhatsApp |
| Approve | second `content_admin` or `tenant_admin` | `template.document:approve` / `template.notification:approve` | Maker-checker (`notify.template.publish_requires_approval`, locked true for `legal_service`) |
| Publish | approver or author after approval | `template.document:publish` / `template.notification:publish` | WhatsApp templates wait in `pending_provider_approval` |
| Lock template (statutory or institution-prescribed format) | `platform_admin` for platform defaults; `tenant_owner` for tenant formats | `template.document:configure` / `template.notification:configure` | Locked templates allow only translation edits by approved translators |
| Unit variant | `unit_admin` where `notify.template.allow_unit_variants` | `template.document:update` / `template.notification:update` (unit scope) | Variant of a tenant template, same variables |
| Retire | `content_admin` | `template.document:publish` / `template.notification:publish` | Blocked while a published policy or blueprint references it |

Console: `/admin/notifications/templates`, `/admin/notifications/templates/[key]` (versions, locales, channels, usage by policy and blueprint), `/admin/content/document-templates`, `/admin/content/document-templates/[key]`. Admin API: `/admin/v1/templates/...` ([[INT-tenant-admin-api]]). The admin copilot may draft a template or a translation as a draft for human review ([[APP-admin-copilot]]); AI-drafted text is labelled until approved ([[AI-ai-generated-text-labelling-and]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Template |
|---|---|
| Notifications ([[PKG-notifications]]) | `hearing.reminder`, `filing.received`, `deadline.approaching` per channel and locale, selected by the notification policy |
| Case workflows (Temporal Activities) | `case.acknowledgement` letter, `service.certificate` PDF |
| Neutral workspace | Procedural order and award skeletons that the tribunal edits before issuing |
| Billing ([[DOM-invoices-and-vendor-bills]]) | Invoice and receipt PDFs per billing entity (NTPL, TAPL, US entity) |
| SEBI ODR tenant | Statutory-format notices where the format is prescribed (format to be confirmed by legal); locked |
| Tenant admin console | Template editor, preview, test send, coverage report |
| Configuration packages ([[PKG-configuration-packages]]) | Templates travel with case-type blueprints and tenant blueprints |

<!-- section:api -->
## Public API

```ts
// packages/templates/src/index.ts (server-only)
export type TemplateKind = 'document' | 'email' | 'sms' | 'whatsapp' | 'in_app' | 'push';
export type TemplateState = 'draft' | 'in_review' | 'approved' | 'pending_provider_approval' | 'published' | 'provider_rejected' | 'superseded' | 'retired';

export interface TemplateDef {
  key: string;                         // 'hearing.reminder'
  kind: TemplateKind;
  variables: import('zod').ZodObject<any>;  // required variables and types; each tagged with a data kind (personal, case_metadata, ...)
  locales: string[];                   // available translations
  jurisdiction?: string;               // optional variant e.g. 'IN', 'SG'
  unitId?: string;                     // unit variant
  locked?: { by: 'platform' | 'tenant'; reason: string };   // prescribed formats
  channelMeta?: { smsDltTemplateId?: string; smsSenderId?: string; whatsappTemplateName?: string; whatsappCategory?: 'utility' | 'authentication'; emailStream?: 'notices' | 'bulk' };
  body: TemplateBody;                  // logic-less template (sections, placeholders, conditionals on booleans, loops over arrays)
}

export function resolve(tx: TenantTx, p: { key: string; kind: TemplateKind; locale: string; jurisdiction?: string; unitId?: string; at?: Date }): Promise<ResolvedTemplate>; // unit variant → tenant override → product default; locale fallback chain
export function render(t: ResolvedTemplate, vars: unknown): Promise<Rendered>;        // validates vars; HTML-escapes by default
export interface Rendered { kind: TemplateKind; subject?: string; text: string; html?: string; templateVersionId: string; locale: string }

export function renderDocument(tx: TenantTx, p: { key: string; locale: string; vars: unknown; output: 'pdf' | 'docx';
  storeAs: { caseId: string; documentType: string; visibility: Visibility } }): Promise<{ documentVersionId: string; sha256: string }>;

export function preview(tx: TenantTx, draftId: string, sample: 'default' | Record<string, unknown>): Promise<Rendered | { pdfObjectId: string }>;
export function testSend(tx: TenantTx, draftId: string, p: { channel: TemplateKind; to: 'self' }): Promise<{ deliveryId: string }>;   // only to the admin's own verified contact points
export function validateForPublish(tx: TenantTx, draftId: string): Promise<ValidationReport>;  // variables, locales, channel limits, DLT, data-kind rules
export function coverage(tx: TenantTx): Promise<Array<{ key: string; kind: TemplateKind; missingLocales: string[]; usedBy: string[] }>>;
// Lifecycle via @nomology/config-core kinds 'document_template' and 'notification_template' (PKG-configuration-lifecycle)
```

Template language: a logic-less syntax (for example a Liquid-compatible subset rendered by a sandboxed engine with filters limited to `date`, `money`, `upper`, `lower`, `default`): no custom code, no includes from outside the tenant's templates, no network access.

<!-- section:usage -->
## Usage examples

```ts
const t = await templates.resolve(tx, { key: 'hearing.reminder', kind: 'email', locale: recipient.locale });
const msg = await templates.render(t, { caseRef: c.reference, hearingAtLocal, joinUrl });
// msg.templateVersionId is stored with the notification for evidence of what was sent
```

<!-- section:tenant -->
## Tenant context

Tenant templates are tenant-owned artefacts (forced RLS); `resolve` looks up the tenant override first, then the product default shipped as reference data. Rendering runs with the tenant context, and the variable schema prevents a template from pulling data the caller did not pass. Generated documents are written to the tenant's storage prefix and recorded under the case with the template version ID.

<!-- section:config -->
## Configuration

Settings from [[PKG-settings-notifications]] group G: `notify.template.required_locales`, `notify.template.locale_fallback` (default: user → unit default → tenant default → `en`), `notify.template.publish_requires_approval`, `notify.template.allow_unit_variants`. Package rules that are not configurable:

| Rule | Value |
|---|---|
| PDF engine | HTML + print CSS rendered by headless Chromium in a regional worker (open question vs Typst / docx engines) |
| PDF/UA tagging | Required for generated orders, awards and receipts ([[DOM-accessible-documents-and]]) |
| India SMS | `smsDltTemplateId` mandatory for SMS templates used in the India region, and every URL or call-back number in the template must be on the sender's whitelist; publish blocked otherwise [R1] |
| WhatsApp | Template must be approved by the provider before publish completes (`pending_provider_approval`); utility and authentication categories only; recipients must have opted in to the tenant [R2] |
| Channel content | SMS, WhatsApp and push templates may use only variables tagged `system_reference`, the case reference and the recipient's own contact data ([[INT-connector-data-policies#policy]]) |
| Email stream | `legal_service`, `auth`, `transactional` → `notices`; `digest`, `reminder` → `bulk` |

<!-- section:adapters -->
## Providers and extension points

`DocumentRenderer` interface (`renderPdf(html, theme)`, `renderDocx(model)`) with a Chromium-based renderer; provider template sync adapters for WhatsApp Business template approval and DLT template registration status (India), implemented in [[INT-messaging-providers]].

<!-- section:errors -->
## Error model

`TemplateNotFoundError` (no override or default for key/kind/locale), `TemplateVariableError` (missing or wrong-typed variable; never renders partially), `ProviderTemplateNotApprovedError` (WhatsApp/SMS), `RenderTimeoutError` (retryable, PDF > 30 s).

<!-- section:nfr -->
## Performance and limits

Text render p95 ≤ 5 ms; PDF render p95 ≤ 5 s for 20 pages, ≤ 60 s for 300 pages; renderer workers isolated (no network except storage upload).

<!-- section:versioning -->
## Versioning and compatibility

Template versions are immutable artefacts; every rendered output records `templateVersionId`. Changing a template's variable schema requires a new version and all callers passing the new variables; the validator checks registered callers' variable types against the schema in CI.

<!-- section:testing -->
## Test contract

Snapshot tests per default template and locale; variable-schema tests; XSS tests (variables are escaped in HTML outputs); PDF/UA validation in CI for document templates; DLT ID presence check for India SMS templates.

<!-- section:questions -->
## Open questions

- [ ] PDF engine: headless Chromium vs alternatives; accessibility tagging quality decides. Owner: platform engineering with accessibility lead.
- [ ] Do tribunals need DOCX output for orders and awards to edit offline? Proposed: yes for drafts, PDF for issued versions.
- [ ] Which documents have formats prescribed by regulators or institutions (for example SEBI ODR notices)? Legal to list; such templates are locked.
- [ ] Who may edit translations of locked templates: tenant translators, or only certified translators recorded per language? (Legal + content)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Templates are tenant-owned with forced RLS and fall back to product defaults only; rendering uses only variables passed in by the caller; outputs are stored under the tenant prefix.

<!-- check:security -->
### Security of the API surface

Logic-less, sandboxed template language with a fixed filter list; HTML escaping by default; no includes, network or file access; renderer workers have no network egress except storage upload.

<!-- check:data-protection -->
### Personal data handling

Variable schemas mark personal variables so rendered notification bodies stored for evidence are covered by retention and erasure; previews use synthetic sample data, never real case data.

<!-- check:residency -->
### Region awareness

Templates are stored in the regional database; renderer workers run in the tenant's region and write outputs to regional storage. Provider template registration (WhatsApp, DLT) sends template text only, never case data.

<!-- check:audit -->
### Audit events

Draft, submit, approve, publish, lock and retire of templates are audited with diffs and approver (`admin.template.*`); each generated document and sent notification records the template version ID, so what was sent can be reproduced; test sends are logged as such and never count as evidence.

<!-- check:resilience -->
### Failure behaviour

Rendering is deterministic for a template version and variables; PDF rendering runs as a Temporal Activity with a 120-second timeout and retries; `renderDocument` is idempotent by `(template version, variables hash, case)`, so a retry returns the stored document version instead of creating a duplicate.

<!-- check:testing -->
### Testing

Snapshot tests per template and locale, variable-schema checks against registered callers in CI, XSS escaping tests, PDF/UA validation for document templates, and the DLT ID presence check for India SMS templates.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "From 1 September 2024 messages containing URLs, APKs, OTT links or call-back numbers that are not whitelisted are not permitted; a content template may not be linked to more than one header.",
    "id": "R1",
    "issuer": "Telecom Regulatory Authority of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "TRAI Direction of 20 August 2024 under the Telecom Commercial Communications Customer Preference Regulations, 2018",
    "url": "https://trai.gov.in/sites/default/files/Direction_20082024.pdf"
  },
  {
    "excerpt": "Opt-in must state that the person agrees to receive WhatsApp messages and name the business; opt-out requests for message categories must be honoured.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Meta",
    "retrieved": "2026-10-28",
    "title": "WhatsApp Business Platform: Get opt-in for WhatsApp",
    "url": "https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in"
  }
]
```

<!-- end -->
