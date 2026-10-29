---
id: "I18N-content"
title: "Content"
parent: "I18N"
order: 3
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "per-tenant language packs, legal-document templates by jurisdiction"
links: []
rev: 2
syncHash: "fef65f2a618c63cb"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 4.3 Content

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> per-tenant language packs, legal-document templates by jurisdiction

<!-- section:purpose -->
## Purpose and scope

`@nomology/content` resolves the localised content a tenant uses: **language packs** (tenant overrides and additions layered over platform message catalogues) and **jurisdiction- and locale-specific variants of legal document templates** (procedural orders, awards, notices, receipts) selected by tenant, jurisdiction or seat, procedure type and locale. It is imported by `apps/web`, `apps/worker-jobs` (notifications) and `apps/worker-temporal` (document generation activities).

It does **not** render documents or send notifications ([[PKG-document-and-notification]], [[PKG-notifications]]), does not decide which strings tenants may override ([[PKG-tenant-terminology-and-copy]]), and does not hold the legal text register ([[I18N-legal-declaration-and-consent]]), though it serves the text versions that register points to.

<!-- section:consumers -->
## Consumers and use cases

1. Next.js server components load the merged messages for the active tenant and locale on each request (`getMessages`).
2. A Temporal activity generating a procedural order asks for the template variant for tenant `arb-inst`, seat `SG`, procedure `arbitration`, locale `en` (`resolveTemplate`), then passes it to the document renderer.
3. The notifications worker loads the tenant's email and SMS copy for `hi-IN`, falling back to `en-IN`.
4. A tenant admin publishes a new language pack version from the tenant admin console ([[APP-tenant-admin-console]]) after preview.
5. The legal text register resolves the exact text of version 3 of a declaration in `en` for display and for acceptance recording.

<!-- section:api -->
## Public API

```ts
// @nomology/content (server-only)
export type Locale = string;                      // BCP 47, e.g. 'en-IN', 'hi-IN'
export type Namespace = string;                   // e.g. 'cases', 'filing', 'notifications'

export function getMessages(ctx: TenantContext, locale: Locale, namespaces: Namespace[]):
  Promise<{ locale: Locale; messages: Record<string, string>; fallbacks: string[]; packVersion: number }>;

export function resolveTemplate(ctx: TenantContext, q: {
  templateKey: string;                            // e.g. 'procedural-order.standard'
  jurisdiction?: string;                          // ISO 3166-1 alpha-2 or seat code, e.g. 'SG', 'IN'
  procedureType?: 'arbitration' | 'conciliation' | 'mediation' | 'negotiation';
  locale: Locale;
  version?: number;                               // omit = latest published
}): Promise<TemplateVersion>;                     // throws TemplateNotFoundError

export interface TemplateVersion {
  templateKey: string; version: number; locale: Locale; jurisdiction: string | null;
  source: 'platform' | 'tenant'; body: string;    // template source for the renderer
  variables: JsonSchema; contentHash: string; publishedAt: string; approvedBy: string[];
}

export function getTextVersion(ctx: TenantContext, textKey: string, version: number, locale: Locale):
  Promise<{ body: string; contentHash: string; authoritativeLocale: Locale }>;

// Admin (requires permission content.manage)
export function draftLanguagePack(ctx: TenantContext, locale: Locale, overrides: Record<string, string>): Promise<DraftId>;
export function previewLanguagePack(ctx: TenantContext, draftId: DraftId, route: string): Promise<PreviewUrl>;
export function publishLanguagePack(ctx: TenantContext, draftId: DraftId): Promise<{ version: number }>;
export function rollbackLanguagePack(ctx: TenantContext, locale: Locale, toVersion: number): Promise<void>;

// Events (outbox): content.pack.published, content.template.published, content.pack.rolled_back
```

Errors: `TemplateNotFoundError`, `LockedMessageError` (override of a locked ID), `InvalidMessageError` (ICU syntax or disallowed markup), `MissingTenantContextError`.

<!-- section:usage -->
## Usage examples

```ts
// apps/web/app/[locale]/(counsel)/layout.tsx
const { messages, fallbacks } = await getMessages(ctx, locale, ['common', 'cases', 'filing']);
if (fallbacks.length) logger.warn({ fallbacks: fallbacks.length }, 'content.fallback');

// worker activity
try {
  const tpl = await resolveTemplate(ctx, { templateKey: 'procedural-order.standard', jurisdiction: 'SG', procedureType: 'arbitration', locale: 'en' });
  return renderer.render(tpl, data);
} catch (e) {
  if (e instanceof TemplateNotFoundError) throw ApplicationFailure.nonRetryable(e.message);
  throw e;
}
```

<!-- section:tenant -->
## Tenant context

Tenant context comes from the `TenantContext` argument (set by middleware for requests and by the Temporal / BullMQ interceptors for workers) and every read runs through `withTenant` ([[MT-prisma-client-extension-wraps]]). Tables `tenant_language_packs`, `tenant_message_overrides` and `tenant_document_template_versions` are tenant-owned with forced RLS ([[MT-isolation-strategy]]); `platform_message_catalogues` and `platform_document_template_versions` are platform-level read-only tables ([[MT-platform-level-tables]]). Missing context throws `MissingTenantContextError`; there is no "default tenant". Cache keys are `content:{region}:{tenantId}:{locale}:{packVersion}` through `@nomology/cache` ([[PKG-caching]]).

<!-- section:config -->
## Configuration

| Setting | Default | Where | Who changes |
|---|---|---|---|
| Enabled locales per tenant | `['en-IN']` / `['en-SG']` / `['en-US']` by region | Tenant settings ([[PKG-settings]]) | Platform admin on contract |
| Default locale | first enabled | Tenant settings | Tenant admin |
| Fallback chain | `<locale> → <language> → en` | Code | Engineering |
| Locked message IDs | list in `packages/i18n/locked.json` (legal, security, privacy) | Repo | Content design + legal |
| Cache TTL | 10 minutes, invalidated on publish | Code | Engineering |

<!-- section:adapters -->
## Providers and extension points

Template sources are pluggable behind `TemplateSource` (`platform`, `tenant`); a future `tms` source can sync tenant packs from the translation management system. Interface: `list(ctx, key)`, `get(ctx, key, version, locale)`.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `MissingTenantContextError` | No | Bug: fix the caller |
| `TemplateNotFoundError` | No | Show a configuration error to the secretariat; do not fall back to another jurisdiction |
| `LockedMessageError` | No | Show which IDs are locked in the admin UI |
| `InvalidMessageError` | No | Show ICU or markup error per message |
| `ContentStoreUnavailableError` | Yes | Retry with backoff; web falls back to platform catalogue for non-legal strings only |

<!-- section:nfr -->
## Performance and limits

`getMessages` p95 under 5 ms from cache, under 50 ms on miss (proposed). Language pack: up to 5,000 overrides per locale; template body up to 1 MB.

<!-- section:versioning -->
## Versioning and compatibility

Package API follows semver within the monorepo [R1]. Data versions: each publish creates an immutable version; documents and acceptances record `templateKey@version` and `contentHash`, so past outputs can be reproduced exactly.

<!-- section:testing -->
## Test contract

Integration tests with real Postgres and RLS: tenant A's overrides never appear for tenant B; locked IDs cannot be overridden; fallback order; template resolution never crosses jurisdiction; reproducing a past version by hash.

<!-- section:questions -->
## Open questions

- [ ] Boundary with [[PKG-document-and-notification]]: who owns template authoring UI and approval? Proposal: that package owns authoring; this package owns storage and resolution of locale and jurisdiction variants.
- [ ] Do jurisdiction variants key on seat, governing law or tenant only?
- [ ] Should tenant packs sync to the TMS for translation, or are tenant overrides written directly per locale?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All tenant reads go through `withTenant` with forced RLS; cache keys include region, tenant and pack version; no default tenant; tests prove tenant A overrides never reach tenant B.

<!-- check:security -->
### Security of the API surface

Override values are validated as ICU with tag placeholders only (no HTML); locked IDs protect legal and security text; admin functions require `content.manage`; server-only package.

<!-- check:residency -->
### Region awareness

Tenant packs and templates are stored in the tenant's home region database; platform catalogues are code shipped in the image.

<!-- check:audit -->
### Audit events

Publish, rollback and template publish emit audit events with actor, tenant, locale, versions and content hashes ([[PKG-audit-trail]]).

<!-- check:change-safety -->
### Change and release safety

Immutable versions, preview before publish and one-step rollback; documents pin `templateKey@version`.

<!-- citations -->
## Citations

```json
[
  {
    "body": "semver.org",
    "excerpt": "MAJOR for incompatible API changes, MINOR for backwards-compatible functionality, PATCH for backwards-compatible fixes.",
    "id": "R1",
    "ident": "Semantic Versioning",
    "kind": "standard",
    "title": "Semantic Versioning 2.0.0",
    "url": "https://semver.org/",
    "version": "2.0.0"
  }
]
```

<!-- end -->
