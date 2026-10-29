---
id: "PKG-settings-branding-content"
title: "Branding, content and locale settings"
parent: "PKG-settings-catalogue"
order: 4
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of `brand.*`, `content.*` and `locale.*` settings: tenant and unit identity and theme selection, email and document branding, footer and sign-in content, terminology and copy override sets, announcements and help, legal text versions, enabled languages, default time zone and formats, with defaults per tenant blueprint"
links: []
rev: 1
syncHash: "d9e79af812502a47"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.4 Branding, content and locale settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of `brand.*`, `content.*` and `locale.*` settings: tenant and unit identity and theme selection, email and document branding, footer and sign-in content, terminology and copy override sets, announcements and help, legal text versions, enabled languages, default time zone and formats, with defaults per tenant blueprint

<!-- section:purpose -->
## Purpose and scope

Registers every setting that controls how the platform looks and reads for a tenant: identity and theme, email and document branding, footer and sign-in content, terminology and copy overrides, help and announcements, terms of use, enabled languages, time zone and formats.

Consumed by:
- [[PKG-branding-and-theming]] and [[PKG-tenant-theme-schema-and]] (theme versions, brand slots, compile on activation);
- [[PKG-tenant-terminology-and-copy]] (override sets) and [[I18N-content]] (language packs, message bundles);
- [[I18N-l10n]] (time zones, dates, numbers) and [[PKG-typography-and-multi-script]] (scripts per enabled language);
- [[PKG-notifications]] and [[PKG-document-and-notification]] (email header and footer, document cover and letterhead);
- [[APP-public-and-sign-in-surfaces]] (sign-in page content), [[APP-accessibility-conformance]] (accessibility statement).

**Not here:** the theme itself (brand colours, logos, fonts) is a configuration artefact owned by [[PKG-tenant-theme-schema-and]], and this catalogue holds only which version is active; consent and privacy notice texts and their versions are in [[PKG-settings-data-and-privacy]]; email sender identity and channel settings are in [[PKG-settings-notifications]]; a person's own language, date format and colour mode are in [[PKG-settings-personal]]; holiday calendars are in [[PKG-settings-cases-and-workflows]]; custom domain verification is in [[PKG-domain-verification]] (this catalogue only selects the primary host); release flags such as a new theme engine are in [[PKG-feature-flags]].

<!-- section:scopes -->
## Scopes that apply

| Scope | Used for | Administered by |
|---|---|---|
| `platform` | Neutral base theme, platform attribution, hard bounds (attribution cannot be removed, lengths) | `platform_admin` |
| `region` | Default languages, time zone, number grouping and page size per region | `platform_admin`, `regional_ops` |
| `offering` | CORD and TERES default themes and terms of use | `platform_admin` |
| `tenant` | Almost everything in this catalogue | `content_admin`, `tenant_admin`, `tenant_owner` |
| `unit` | Display name suffix, theme choice among the tenant's published themes, default language, help contact, announcements | `unit_admin`, tenant admins |
| `case_type` | Case-type terminology, document page size, dual time-zone display | `workflow_designer` (inside the blueprint), with `content_admin` for terminology |
| `case` | Not used. The language of the proceedings and the seat are case attributes owned by [[DOM-cases]], not settings; branding never varies per case | — |
| `user` | Not used here; personal preferences are in [[PKG-settings-personal]], bounded by `locale.languages.enabled` | — |

<!-- section:catalogue -->
## Settings catalogue

**Identity and theme** (`/admin/settings/branding`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `brand.theme.active_version` | ref(theme) | Neutral base theme of the offering | platform, offering, tenant, unit | yes | `feature.branding.custom_theme` (unit scope also `feature.branding.unit_themes`) | `settings.branding:write` | immediate (≤ 60 s, after compile) | standard |
| `brand.theme.allow_unit_themes` | bool | false | tenant | no | `feature.branding.unit_themes` | `settings.branding:write` | immediate | standard |
| `brand.theme.default_mode` | enum{system, light, dark} | system | platform, tenant | no | all | `settings.branding:write` | next_request | standard |
| `brand.identity.display_name` | ltext≤60 | Tenant display name from provisioning | tenant | no | all | `settings.branding:write` | immediate | sensitive |
| `brand.identity.unit_label` | ltext≤60 | — (no suffix) | unit | no | all | `settings.branding:write` | immediate | standard |
| `brand.identity.short_name` | text≤20 | First 20 characters of display name | tenant | no | all | `settings.branding:write` | immediate | standard |
| `brand.identity.legal_name` | text≤200 | — | tenant | no | all | `settings.branding:write` | immediate | sensitive |
| `brand.domain.primary_host` | ref(tenant_domain, verified) | Tenant subdomain | tenant | no | `feature.custom_domain` | `settings.branding:write` | immediate (after certificate is active) | maker_checker |

**Footer and sign-in** (`/admin/settings/branding#footer`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `brand.footer.platform_attribution` | enum{full, compact} | full | platform, tenant | platform | `feature.branding.compact_attribution` | `settings.branding:write` | immediate | standard |
| `brand.footer.links` | object(footer_links): up to 5 × {ltext≤40 label, https URL} | [] | tenant | yes | all | `settings.branding:write` | immediate | sensitive |
| `brand.footer.show_unit_name` | bool | false | tenant, unit | yes | all | `settings.branding:write` | immediate | standard |
| `brand.footer.address` | ltext≤300 | — | tenant, unit | no | all | `settings.branding:write` | immediate | standard |
| `brand.signin.show_tenant_logo` | bool | true | tenant | no | all | `settings.branding:write` | immediate | standard |
| `brand.signin.message` | ltext≤280, plain text, no URLs | — | tenant | no | all | `settings.branding:write` | immediate | sensitive |

**Email and document branding** (`/admin/settings/branding#email-and-documents`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `brand.email.header_style` | enum{logo, logo_and_name, name_only} | logo_and_name | tenant, unit | no | all | `settings.branding:write` | immediate | standard |
| `brand.email.footer_note` | ltext≤300 | — | tenant, unit | no | all | `settings.branding:write` | immediate | standard |
| `brand.document.cover_logo` | enum{theme_print_logo, none} | theme_print_logo | tenant, case_type | no | all | `settings.branding:write` | immediate (new documents) | standard |
| `brand.document.letterhead_template` | ref(document_template) | Platform neutral letterhead | tenant, unit, case_type | yes | all | `settings.branding:write` | immediate (new documents) | standard |
| `brand.document.page_size` | enum{a4, us_letter} | a4 (`region = us`: us_letter) | platform, region, tenant, case_type | no | all | `settings.branding:write` | new_cases_only | standard |
| `brand.document.show_unit_name` | bool | false | tenant, unit | no | all | `settings.branding:write` | immediate (new documents) | standard |

**Terminology and copy** (`/admin/settings/content/terminology`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `content.terminology.override_set` | ref(terminology_overrides) | none (platform terms) | tenant | managed | all | `settings.branding:write` | immediate (≤ 60 s) | standard |
| `content.terminology.allow_case_type_terms` | bool | false | tenant | no | all | `settings.branding:write` | immediate | standard |
| `content.terminology.case_type_override_set` | ref(terminology_overrides) | none | case_type | no | all | `settings.branding:write` | immediate (≤ 60 s) | standard |
| `content.copy.review_overrides` | bool | false | tenant | no | all | `settings.branding:write` | immediate | sensitive |
| `content.copy.ai_translation_drafts` | bool | false | tenant | no | `feature.ai.summaries` | `settings.branding:write` | immediate | sensitive |

**Help, announcements and legal text** (`/admin/settings/content`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `content.help.support_contact` | ltext≤200 | Platform support text | tenant, unit | no | all | `settings.branding:write` | immediate | standard |
| `content.help.custom_help_url` | https URL ≤ 300 | — (platform help centre, [[DOC-tenant-facing-help-centre]]) | tenant, unit | no | all | `settings.branding:write` | immediate | sensitive |
| `content.announcement.banner` | object(banner): {ltext≤280 text, enum{info, warning} severity, start, end ≤ 30 days} | — | platform, region, tenant, unit | no | all | `settings.branding:write` | scheduled | standard |
| `content.accessibility.statement` | ref(content_page) | Platform statement template | tenant | managed | all | `settings.branding:write` | immediate | sensitive |
| `content.legal.terms_of_use` | ref(legal_text) | Offering terms of use | platform, region, offering, tenant | managed | all | `settings.branding:write` | next_sign_in (re-acceptance when the version changes) | maker_checker |
| `content.legal.tenant_rules_document` | ref(document) | — | tenant, case_type | no | all | `settings.branding:write` | new_cases_only | maker_checker |

**Languages, time and formats** (`/admin/settings/locale`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `locale.languages.enabled` | set⊆ref(platform_locale) | `region = in`: [en-IN]; `sg`: [en-SG]; `us`: [en-US] | platform, region, tenant | platform | `≤ limit.locales` | `settings.branding:write` | immediate | sensitive |
| `locale.languages.default` | ref(locale) ∈ enabled | First enabled | tenant, unit | yes | all | `settings.branding:write` | immediate | standard |
| `locale.languages.party_selectable` | bool | true | tenant | no | all | `settings.branding:write` | immediate | standard |
| `locale.languages.show_machine_translation_notice` | bool | true | platform | platform | all | `settings.platform:write` | immediate | standard |
| `locale.time.default_zone` | IANA time zone | `in`: Asia/Kolkata; `sg`: Asia/Singapore; `us`: America/New_York | region, tenant, unit | no | all | `settings.branding:write` | immediate | standard |
| `locale.time.show_dual_zones` | bool | true | tenant, case_type | no | all | `settings.branding:write` | immediate | standard |
| `locale.format.date_style` | enum{locale, dd_mm_yyyy, mm_dd_yyyy, iso} | locale | region, tenant | no | all | `settings.branding:write` | next_request | standard |
| `locale.format.number_grouping` | enum{locale, indian, international} | `in`: indian; others: international | region, tenant | no | all | `settings.branding:write` | next_request | standard |
| `locale.calendar.week_start` | enum{monday, sunday} | monday (`us`: sunday) | region, tenant | no | all | `settings.branding:write` | next_request | standard |

Total: 40 keys.

<!-- section:validation -->
## Validation and dependencies

| Rule | Enforced | Message to the admin |
|---|---|---|
| `locale.languages.default` must be in `locale.languages.enabled`; removing a language that is a unit default or a user's preference is refused until those are changed (impact analysis lists them) | Save and publish | "Hindi is the default language of 2 units and 140 users. Change them first or choose a replacement." |
| Enabling a language requires, for that language: a complete terminology override set (if one is active, [[PKG-tenant-terminology-and-copy]]), published privacy notice and consent texts ([[PKG-settings-data-and-privacy]]), terms of use, and accessibility statement | Publish | "Tamil cannot be enabled: missing privacy notice (ta-IN)." |
| `locale.languages.enabled` size ≤ `limit.locales` of the plan | Save | "Your plan includes 2 languages." |
| `brand.domain.primary_host` must be a verified domain of this tenant with an active certificate ([[PKG-domain-verification]]) | Save | "Domain not verified yet." |
| `brand.theme.active_version` must be a theme version that passed validation ([[PKG-tenant-theme-accessibility]]); unit scope only when `brand.theme.allow_unit_themes = true` and the version belongs to the tenant | Save | "This theme has not passed accessibility checks." |
| `brand.identity.display_name`, `short_name`, `legal_name`, `unit_label`: plain text (no `<`, `>`, control characters); must not contain "Nomology", "CORD", "TERES", or the name of a regulator or market infrastructure institution (for example SEBI, NSE, BSE, HKIAC, SIAC) unless platform review approves (impersonation control); must not equal another tenant's display name in the region | Save; names on the protected list create a platform review task | "This name needs review by Nomology because it contains a protected name." |
| `brand.footer.links` and `content.help.custom_help_url`: `https` only, no credentials or query parameters that look like tokens, host must be a verified tenant domain or on the tenant's allow-list approved at onboarding | Save | "Links must use https and point to your verified domains." |
| `brand.signin.message`: no URLs, no email addresses, no phone numbers (sign-in page phishing control) | Save | "Sign-in messages cannot contain links or contact details." |
| `brand.footer.platform_attribution`: platform bound forbids removing attribution; `compact` still shows "Secured by Nomology" and the privacy and accessibility links | Always | — |
| `content.copy.ai_translation_drafts` requires AI use allowed for content drafting by [[AI-tenant-ai-policy]] (`ai.*` keys in [[PKG-settings-ai]]) | Save | "Enable AI translation suggestions in AI settings first." |
| `content.announcement.banner`: end within 30 days of start; at most one active banner per scope; `warning` severity cannot imitate security alerts (fixed icon, no red) | Save | — |
| Length limits are checked per locale; labels that exceed component limits show a 320 px preview warning | Save | — |

<!-- section:defaults -->
## Defaults by tenant type

Values set by each tenant blueprint ([[PKG-configuration-packages]]). Blank means the platform default applies.

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `brand.theme.active_version` | Institution theme built at onboarding | Institution theme built at onboarding | CORD theme (offering default) | Programme theme; neutral if none |
| `brand.footer.platform_attribution` | full | full | full | full |
| `brand.document.page_size` | a4 (us_letter for US seats) | a4 | a4 | a4 |
| `brand.document.letterhead_template` | Institution letterhead | Institution letterhead | CORD letterhead | Programme letterhead with court emblem (if the court provides it) |
| `content.terminology.override_set` | "Matter", "Registrar" (if the institution uses them) | Investor-facing plain terms: "complaint", "investor", "market participant" (managed) | Platform terms | "Matter", "Registry" |
| `content.copy.review_overrides` | false | true | false | true |
| `content.legal.terms_of_use` | TERES terms | TERES terms plus ODR portal terms | CORD terms | Programme terms (managed) |
| `locale.languages.enabled` | [en-SG] or [en-IN] by region | [en-IN, hi-IN] | [en-IN] | [en-IN] plus the court's state language (assumption) |
| `locale.languages.party_selectable` | true | true | true | true |
| `locale.time.show_dual_zones` | true | false (single zone, India) | false | false |
| `locale.format.number_grouping` | international | indian | indian | indian |

Why they differ: SEBI ODR institutions serve retail investors, often unrepresented, so plain-language terms and Hindi are on by default and copy changes are reviewed (assumption: legal to confirm whether regulator-defined terms must be locked). Court programmes need formal records and reviewed copy. International arbitral institutions deal with parties across time zones.

<!-- section:admin_ux -->
## Where it is administered

| Settings group | Console page | API | Copilot may propose |
|---|---|---|---|
| Identity and theme | Tenant admin console → Branding (`/admin/settings/branding`); theme editor at `/admin/content/branding` with preview ([[PKG-branding-and-theming]]) | `GET/PATCH /admin/v1/settings/brand.*`; theme drafts via `/admin/v1/branding/draft` ([[INT-tenant-admin-api]]) | Yes (drafts; never activates a theme) |
| Footer and sign-in | Branding → Footer and sign-in | `/admin/v1/settings/brand.footer.*`, `brand.signin.*` | Yes, except `brand.signin.message` |
| Email and documents | Branding → Email and documents, with email and PDF cover preview | `/admin/v1/settings/brand.email.*`, `brand.document.*` | Yes |
| Terminology and copy | Content → Terminology (`/admin/settings/content/terminology`), editor with per-locale columns and preview | `/admin/v1/settings/content.terminology.*`; override sets as artefacts | Yes, including draft translations marked as AI suggestions |
| Help, announcements, legal | Content (`/admin/settings/content`) | `/admin/v1/settings/content.*` | Help and announcements only |
| Languages, time and formats | Language and region (`/admin/settings/locale`) | `/admin/v1/settings/locale.*` | Yes |
| Unit values | Units → [unit] → Settings (`/admin/organisation/units/[unitId]/settings`) | same, with `?unit=` | Yes |
| Platform, region, offering values | `/platform/settings?domain=brand,content,locale` | `/platform/v1/settings/...` | No |

Inherited values show their source ("Platform default", "India region", "Set for this organisation"); locked values show a lock with the source; `managed` values show "Managed by Nomology" with the reason; non-entitled settings show "Available on Standard" and are read-only.

<!-- section:change_control -->
## Change control and audit

- `maker_checker`: `brand.domain.primary_host`, `content.legal.terms_of_use`, `content.legal.tenant_rules_document`. The checker must hold `settings.branding:approve`.
- `sensitive` (step-up, reason, tenant owner and content admins notified): display and legal names, footer links, sign-in message, custom help URL, accessibility statement, enabled languages, AI translation drafts, override review toggle.
- All other keys are `standard`. Tenants can raise any of them to maker-checker with `access.change_control.review_all_changes` ([[PKG-configuration-lifecycle]]).
- Rollback: revert the change set; a theme rollback re-activates the previous compiled version in seconds. Changes to `content.legal.terms_of_use` cannot be "un-accepted": reverting publishes the old version as a new version and users accept again only if the text differs from what they accepted.
- Audit record: `admin.settings.published` with key, scope, scope ID, old value, new value, change set, actor, approver and reason. Theme activations also emit `branding.theme.activated`.

<!-- section:migration -->
## Versioning and migration

- Renames from earlier nodes: `branding.activeThemeVersionId` ([[PKG-settings#consumers]]) → `brand.theme.active_version`; "Enabled locales per tenant" and "Default locale" ([[I18N-content#config]]) → `locale.languages.enabled` (now tenant-editable within `limit.locales`, previously platform admin only) and `locale.languages.default`; `tenant.default_time_zone` and `tenant.default_locale` remain as provisioning values copied into tenant-scope settings at migration, after which the settings are the source of truth.
- Old keys are kept as deprecated aliases for one release ([[PKG-settings-data-model#migrations]]).
- New keys arrive with a platform default; blueprint defaults reach existing tenants only through an offered blueprint upgrade, never silently.
- In configuration packages these keys travel as `setting_values` components; `brand.domain.primary_host` is excluded from packages because domains are verified per tenant.

<!-- section:testing -->
## Testing

- Generated registry check: every key here exists in code with the same type, scopes, lock, plan, permission, effect and audit class (`settings:registry-check`).
- Resolution tests for each key with a unit value, a tenant lock and a non-entitled tenant.
- Validation tests for every rule above, including the protected-name list and the phishing rules for the sign-in message.
- Locale completeness: enabling a language with a missing legal text fails publish.
- Visual and accessibility regression of email, PDF cover and sign-in page for each blueprint's defaults ([[TST-accessibility-testing]]).

<!-- section:questions -->
## Open questions

- [ ] Should SEBI ODR institutions be prevented from renaming regulator-defined terms (managed terminology), or only warned? (owner: legal)
- [ ] May unit themes use different logos (a court programme inside a larger tenant) or only a different display label? Proposed: different theme versions owned by the tenant. (owner: product)
- [ ] Is `limit.locales` a commercial limit at all, or should all platform-supported languages be available on every plan? (owner: CCO)
- [ ] Protected-name list for impersonation control: who maintains it and how often? Proposed: platform security, reviewed quarterly. (owner: security lead)

<!-- section:notes -->
## Notes

Information architecture borrowed from collaboration tools that separate organisation-wide appearance (set by admins) from personal appearance (set by each user): tenants set the theme and default mode, each user may still choose light, dark or high contrast ([[PKG-colour-modes-and-user]]).

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Every key lists its scopes and lock behaviour; resolution follows [[PKG-configuration-scope-hierarchy]] with no exceptions. Unit values apply to cases owned by the unit and to users whose primary unit it is. Case-type values (page size, terminology, dual zones) come from the pinned blueprint version. User preferences live in another catalogue and are bounded by `locale.languages.enabled`.

<!-- check:permissions -->
### Who may change what

One permission, `settings.branding:write`, covers brand, content and locale keys (decision D2: one write permission per catalogue). A `content_admin` manages day-to-day branding alone; the high-risk keys (sign-in host, terms of use, tenant rules document) are maker-checker, so they cannot change without a second approver holding `settings.branding:approve`.

<!-- check:safety -->
### Safe bounds

Risks and controls: impersonating another institution or a regulator (protected-name review, platform attribution cannot be removed, locked trust cues in [[PKG-branding-and-theming]]); phishing through the sign-in message or footer links (no URLs in the message, https-only links on verified domains); excluding parties by language (a language cannot be removed while it is anyone's preference, and legal texts must exist for every enabled language); inaccessible themes (activation blocked on failed contrast checks).

<!-- check:timing -->
### When changes take effect

Most keys apply immediately (≤ 60 s for compiled themes and message bundles). Document page size is `new_cases_only` so bundles within a case stay consistent. Terms of use apply at next sign-in with re-acceptance. Announcements are scheduled with start and end.

<!-- check:audit -->
### Audit and rollback

Every change is a change set with old and new values; history tables give the value at any date ([[PKG-settings-data-model]]). Generated documents record the letterhead template version and theme version used, so a document can be re-explained later. Rollback is one action from the change set.

<!-- check:sync -->
### Catalogue matches code

The registry check fails CI if a key here and the code definition differ; the weekly comparison flags rows missing on either side ([[PKG-settings-catalogue#design]]).

<!-- end -->
