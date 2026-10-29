---
id: "PKG-settings-data-and-privacy"
title: "Data retention and privacy settings"
parent: "PKG-settings-catalogue"
order: 6
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of `data.*` settings: retention periods and sweeps (tenant may extend above platform and regional minimums), legal-hold policy, privacy notices and consent purposes, data principal rights handling, exports and downloads, file handling, classification defaults and statistics participation, with regional legal bounds and blueprint defaults"
links: []
rev: 1
syncHash: "fb4d55928926b69a"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.6 Data retention and privacy settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of `data.*` settings: retention periods and sweeps (tenant may extend above platform and regional minimums), legal-hold policy, privacy notices and consent purposes, data principal rights handling, exports and downloads, file handling, classification defaults and statistics participation, with regional legal bounds and blueprint defaults

<!-- section:purpose -->
## Purpose and scope

Registers every setting that decides how long tenant data is kept, how it leaves the platform, what people are told and asked before their data is processed, and how their rights requests are handled.

Consumed by:
- [[PKG-data-retention-legal-hold-and]] and [[PKG-retention-and-deletion-schedule]] (retention periods, sweeps, legal holds);
- [[SEC-consent-and-notice-management]], [[SEC-privacy-notice-copy]] and [[I18N-legal-declaration-and-consent]] (notices and consent);
- [[SEC-data-principal-rights-requests]] (intake, identity checks, response targets, erasure approvals);
- [[PKG-storage]], [[PKG-encryption-at-rest-signed-urls]] and [[APP-document-viewer-and-sandbox]] (downloads, watermarks, file types);
- [[SEC-data-classification]] and [[PKG-rbac-abac-case-level-party]] (default confidentiality tier);
- [[RPT-industry-marketing]] (participation in aggregated statistics).

**Not here:** the legal minimum periods themselves are reviewed data in [[PKG-retention-and-deletion-schedule]] (this catalogue holds the platform, regional and tenant values that sit on top of them); backup retention is infrastructure ([[INF-backup-and-disaster-recovery]]); log and telemetry retention is in [[OBS-foundations]]; AI data use (training opt-out, prompt logging) is in [[PKG-settings-ai]]; sign-in and session security in [[PKG-settings-security-and-identity]]; the case data model's own classification of fields is in [[PKG-metadata-management-entity]]. Moving a tenant's home region is a tenant lifecycle operation ([[MT-data-residency-2]]), shown here read-only.

**Legal basis (summary, to be confirmed by legal for each tenant type).** India: the DPDP Act 2023 requires erasure once the purpose is no longer served unless retention is required by law (section 8(7)) [R1]; the DPDP Rules 2025 were notified on 13 November 2025, with most obligations commencing on 13 May 2027, and set a minimum one-year retention of personal data and associated logs for specified purposes, and 90 days for grievance redressal [R2]. Singapore: the PDPA retention limitation obligation (section 25) [R3]. EU data subjects (some international arbitrations): GDPR storage limitation and the legal-claims exception to erasure [R4]. These shape the bounds below; they do not by themselves fix the periods, which legal sets per record type.

<!-- section:scopes -->
## Scopes that apply

| Scope | Used for | Administered by |
|---|---|---|
| `platform` | Code defaults, hard bounds, sweep controls | `platform_admin`; legal / DPO approve |
| `region` | Regional legal minimums and requirements (DPDP notice in India, nomination right, minimum log retention), destructive-run switch per region | `platform_admin` with legal approval; `regional_ops` cannot change these alone |
| `offering` | Not used: privacy law differs by region and tenant type, not by product line | — |
| `tenant` | Tenant extensions of retention, notices, consent purposes, rights handling, exports, file policy | `tenant_owner`, `tenant_admin`, `security_admin` (see [[PKG-settings-catalogue#design]]) |
| `unit` | Download watermarking and list masking for units with stricter needs | `unit_admin`, tenant admins |
| `case_type` | Retention of documents, awards and recordings per process; default confidentiality tier; allowed file types | `workflow_designer` inside the blueprint, approved by a tenant admin holding `settings.data:approve` |
| `case` | Not used: retention per case is controlled only by legal holds ([[PKG-data-retention-legal-hold-and]]), which are records, not settings | — |
| `user` | Not used: a person's privacy choices are consent records ([[SEC-consent-and-notice-management]]), not preferences | — |

Targeted platform values by tenant type ([[PKG-configuration-scope-hierarchy]]) are used for SEBI ODR institutions and court programmes, whose minimums may differ (assumption pending legal).

<!-- section:catalogue -->
## Settings catalogue

**Retention periods** (`/admin/settings/data/retention`). Tenants may extend periods above the effective minimum; they can never shorten below it ([[PKG-data-retention-legal-hold-and]] `setTenantExtension`).

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.retention.case_record_years` | int 1–30, `stricter_only` (longer) | 8 (proposed) | platform, region, tenant | managed | all | `settings.data:write` | running_cases (end dates recomputed where the clock has not expired) | maker_checker |
| `data.retention.documents_years` | int 1–30, ≥ minimum | 8 (proposed) | platform, region, tenant, case_type | managed | all | `settings.data:write` | running_cases | maker_checker |
| `data.retention.awards_policy` | enum{same_as_case, fixed_years, permanent} | same_as_case | platform, tenant, case_type | managed | all | `settings.data:write` | running_cases | maker_checker |
| `data.retention.awards_years` | int 8–99 (used when `fixed_years`) | — | tenant, case_type | no | all | `settings.data:write` | running_cases | maker_checker |
| `data.retention.recordings_years_after_close` | int 1–10 | 2 (proposed) | platform, region, tenant, case_type | managed | all | `settings.data:write` | running_cases | maker_checker |
| `data.retention.transcripts_years` | int 1–30 | 8 (proposed) | platform, region, tenant, case_type | managed | all | `settings.data:write` | running_cases | maker_checker |
| `data.retention.general_notifications_days` | int 365–3650 | 365 | platform, region, tenant | platform | all | `settings.data:write` | running_cases | sensitive |
| `data.retention.inactive_account_years` | int 1–10 | 3 | platform, region, tenant | no | all | `settings.data:write` | next_job_run | sensitive |
| `data.retention.keep_anonymised_case_skeleton` | bool | true | platform, tenant | no | all | `settings.data:write` | next_job_run | sensitive |
| `data.retention.dry_run_report_recipients` | set⊆{tenant_owner, tenant_admin, security_admin, auditor} | [tenant_owner, security_admin] | tenant | no | all | `settings.data:write` | immediate | standard |

**Retention operations** (platform console only, `/platform/settings?domain=data`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.retention.destructive_runs_enabled` | bool | false | platform, region | platform | all | `settings.platform:write` with legal as checker | next_job_run | maker_checker |
| `data.retention.sweep_window` | object(time window, region local) | 01:00–05:00 | platform, region | platform | all | `settings.platform:write` | next_job_run | standard |
| `data.retention.batch_size` | int 100–5000 | 500 | platform, region | platform | all | `settings.platform:write` | next_job_run | standard |
| `data.retention.offboarding_export_days` | int 30–180 | 90 | platform, region, tenant | platform | all | `settings.platform:write` (tenant value set from the contract) | immediate | maker_checker |

**Legal holds** (`/admin/settings/data/retention#holds`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.hold.placer_roles` | set⊆{tenant_owner, tenant_admin, security_admin, secretariat} | [tenant_owner, security_admin] | tenant | no | all | `settings.data:write` | immediate | maker_checker |
| `data.hold.review_interval_days` | int 30–365 | 180 | platform, tenant | no | all | `settings.data:write` | next_job_run | standard |
| `data.hold.notify_on_blocked_deletion` | bool | true | tenant | no | all | `settings.data:write` | immediate | standard |

**Notices and consent** (`/admin/settings/data/privacy`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.notice.dpdp_notice_required` | bool | `region = in`: true (locked); others: false | platform, region, tenant | yes | all | `settings.data:write` | immediate | maker_checker |
| `data.notice.privacy_notice` | ref(privacy_notice) (one version per enabled locale) | Regional platform template ([[SEC-privacy-notice-copy]]) | platform, region, tenant | managed | all | `settings.data:write` | next_sign_in (re-notice before further processing) | maker_checker |
| `data.notice.fiduciary_contact` | object(business contact: role title, email, optional phone) | — (required before go-live) | tenant | no | all | `settings.data:write` | immediate | sensitive |
| `data.notice.grievance_contact` | object(business contact) | Same as fiduciary contact | tenant, unit | no | all | `settings.data:write` | immediate | sensitive |
| `data.consent.optional_purposes` | set⊆{product_updates, research_statistics, party_ai_assistance, whatsapp_channel} | [] | platform, region, tenant | yes | all | `settings.data:write` | immediate (consent collected at next interaction) | maker_checker |
| `data.consent.reconsent_on_notice_change` | enum{material_changes, every_change} | material_changes | platform, tenant | no | all | `settings.data:write` | immediate | sensitive |
| `data.consent.consent_manager_enabled` | bool | false | region, tenant | platform | all | `settings.data:write` | immediate | maker_checker |
| `data.consent.guardian_flow_enabled` | bool | `region = in`: true (locked) | platform, region, tenant | yes | all | `settings.data:write` | immediate | maker_checker |

**Rights requests** (`/admin/settings/data/rights`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.rights.response_target_days` | int 1–90, bounded by region | 30 | platform, region, tenant | no | all | `settings.data:write` | new requests only | sensitive |
| `data.rights.intake_channels` | set⊆{portal_form, in_app, email} | [portal_form, in_app] | tenant | no | all | `settings.data:write` | immediate | standard |
| `data.rights.identity_check` | enum{signed_in_session, otp_to_registered_contact, manual_review}, `stricter_only` | signed_in_session | platform, tenant | yes | all | `settings.data:write` | new requests only | sensitive |
| `data.rights.erasure_approval` | enum{single_reviewer, maker_checker}, `stricter_only` | maker_checker | platform, tenant | platform | all | `settings.data:write` | new requests only | maker_checker |
| `data.rights.nomination_enabled` | bool | `region = in`: true (locked) | platform, region, tenant | yes | all | `settings.data:write` | immediate | sensitive |
| `data.rights.handler_roles` | set⊆ref(role) | [tenant_owner, security_admin] | tenant | no | all | `settings.data:write` | immediate | maker_checker |

**Exports, downloads and files** (`/admin/settings/data/handling`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.export.bulk_case_export_enabled` | bool | false | tenant | no | `feature.data.bulk_export` | `settings.data:write` | immediate | maker_checker |
| `data.export.require_approval` | bool, `stricter_only` | true | platform, tenant | yes | all | `settings.data:write` | immediate | sensitive |
| `data.export.download_link_ttl_min` | int 5–60 | 15 | platform, tenant | yes | all | `settings.data:write` | immediate | standard |
| `data.export.watermark_downloads` | bool | false | tenant, unit, case_type | yes | all | `settings.data:write` | immediate | standard |
| `data.files.allowed_types` | set⊆ platform allow-list (PDF, DOCX, XLSX, images, audio, video, email formats) | Platform allow-list | platform, tenant, case_type | yes | all | `settings.data:write` | immediate | sensitive |
| `data.files.allow_unscannable_with_review` | bool | false | platform, tenant | yes | all | `settings.data:write` | immediate | sensitive |
| `data.masking.contact_details_in_lists` | bool | true | tenant, unit | yes | all | `settings.data:write` | next_request | standard |

**Classification, residency and statistics** (`/admin/settings/data`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.classification.default_document_tier` | enum{case_participants, side_restricted, tribunal_only, institution_internal} | case_participants | tenant, case_type | yes | all | `settings.data:write` | new_cases_only | maker_checker |
| `data.residency.home_region` | enum{in, sg, us} (read-only in the tenant console) | Set at provisioning | tenant | platform | all | `platform.tenant:update` (move workflow only) | scheduled (tenant move, [[MT-data-residency-2]]) | maker_checker |
| `data.statistics.include_in_industry_figures` | bool | false | tenant | no | all | `settings.data:write` | next_job_run | sensitive |
| `data.subprocessors.notify_on_change` | bool | true | tenant | platform | all | `settings.data:write` | immediate | standard |

Total: 42 keys. Old keys `storage.allowUnscannableWithReview` and the flag `retention.destructive.<region>` move here (see migration).

<!-- section:validation -->
## Validation and dependencies

| Rule | Enforced | Message to the admin |
|---|---|---|
| Every retention value ≥ the effective minimum for its record type: the larger of the schedule's platform minimum ([[PKG-retention-and-deletion-schedule]]), the region value and any targeted value for the tenant type | Save | "Minimum for this region and tenant type is 8 years." |
| Assumption: in India, records of processing and logs that DPDP Rules require for one year are never configured below 365 days (`data.retention.general_notifications_days` minimum 365) [R2]; to be confirmed by legal | Platform bound | — |
| `data.retention.awards_years` is required when `awards_policy = fixed_years` and must be ≥ `documents_years` | Save | "Awards must be kept at least as long as other case documents." |
| Shortening a tenant extension recomputes end dates; impact analysis lists records whose end date moves into the past, which are then deleted by the next sweep after a 30-day grace period and only after the dry-run report has gone to `dry_run_report_recipients` | Publish | "1,240 documents will become due for deletion on 28 Nov 2026." |
| `data.retention.destructive_runs_enabled` can be set to true for a region only after a dry-run report for that region has been approved by legal (recorded as the checker) | Publish | — |
| `data.notice.privacy_notice` must have a published version for every language in `locale.languages.enabled` ([[PKG-settings-branding-content]]) | Publish | "Privacy notice missing for hi-IN." |
| `data.notice.fiduciary_contact` and `data.notice.grievance_contact` are required before a tenant leaves onboarding ([[MT-tenant-lifecycle]]); they must be role-based business contacts, not personal mobile numbers (warning) | Tenant activation | — |
| Each purpose in `data.consent.optional_purposes` needs a consent text in every enabled language ([[I18N-legal-declaration-and-consent]]); `party_ai_assistance` also requires the AI policy to allow party-facing AI ([[AI-tenant-ai-policy]]); `whatsapp_channel` requires the notification channel to be enabled ([[PKG-settings-notifications]]) | Publish | — |
| `data.rights.response_target_days` ≤ the regional maximum: India 90 (DPDP Rules grievance period [R2]); Singapore 30 (assumption, PDPC guidance); US 45 (assumption, common state-law response period); EU data subjects 30 (GDPR one month [R4]); legal to confirm all four | Platform bound by region | — |
| `data.rights.erasure_approval` and `data.export.require_approval` are `stricter_only`: a tenant cannot drop below the platform value | Save | — |
| `data.files.allowed_types` ⊆ the platform allow-list; executable and macro-enabled formats are never allowed | Save | — |
| `data.classification.default_document_tier = tribunal_only` for a case type requires the case type to have a tribunal stage | Publish | — |
| `data.statistics.include_in_industry_figures` only allows aggregated, suppressed figures ([[RPT-industry-marketing]]); turning it off removes the tenant from the next publication, not from published ones | Save | — |

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `data.retention.case_record_years` | 8 | 8, managed minimum (assumption: SEBI and MII record-keeping requirements to be confirmed) | 8 | Per court records rules (assumption: often longer; confirm with the first court customer) |
| `data.retention.awards_policy` | permanent (assumption: institutions keep awards) | fixed_years (10, assumption) | same_as_case | permanent |
| `data.retention.recordings_years_after_close` | 2 | 2 | 1 | Per court rules |
| `data.notice.dpdp_notice_required` | true in India, false elsewhere | true (locked by region) | true (locked by region) | true in India |
| `data.consent.optional_purposes` | [] | [] | [product_updates] | [] |
| `data.rights.identity_check` | signed_in_session | otp_to_registered_contact | signed_in_session | manual_review |
| `data.rights.response_target_days` | 30 | 30 | 30 | 30 |
| `data.export.bulk_case_export_enabled` | true (if entitled) | false | false | false |
| `data.export.watermark_downloads` | false | false | false | true |
| `data.classification.default_document_tier` | case_participants | case_participants | case_participants | case_participants |
| `data.masking.contact_details_in_lists` | true | true | true | true |
| `data.statistics.include_in_industry_figures` | false (asked at onboarding) | false | true | false |

Why they differ: SEBI ODR institutions handle large numbers of retail investors identified mainly by phone, so a one-time code to the registered contact is the default identity check; court programmes need strict records rules and watermarked downloads; CORD is Nomology's own service, so it participates in Nomology's anonymised ODR statistics by default (with notice to parties).

<!-- section:admin_ux -->
## Where it is administered

| Settings group | Console page | API | Copilot may propose |
|---|---|---|---|
| Retention and holds | Data and privacy → Retention (`/admin/settings/data/retention`) with a table per record type showing the minimum, the tenant value and the resulting end rule, plus the last dry-run report | `GET/PATCH /admin/v1/settings/data.retention.*`, `data.hold.*` | Yes (draft only; every change is maker-checker) |
| Notices and consent | Data and privacy → Privacy (`/admin/settings/data/privacy`) with notice versions per language and preview | `/admin/v1/settings/data.notice.*`, `data.consent.*` | Yes, except contacts |
| Rights requests | Data and privacy → Rights requests (`/admin/settings/data/rights`) | `/admin/v1/settings/data.rights.*` | Yes |
| Exports, downloads and files | Data and privacy → Data handling (`/admin/settings/data/handling`) | `/admin/v1/settings/data.export.*`, `data.files.*`, `data.masking.*` | Yes |
| Classification, residency, statistics | Data and privacy → Overview (`/admin/settings/data`); home region shown read-only with a "Request region move" link | `/admin/v1/settings/data.classification.*` etc. | Classification only |
| Platform and region values | `/platform/settings?domain=data`, region tabs, with legal sign-off status per value | `/platform/v1/settings/data.*` | No |

Regional locks show their reason ("Required in the India region under the DPDP Act"); managed minimums show "Minimum set by Nomology for SEBI ODR institutions".

<!-- section:change_control -->
## Change control and audit

- `maker_checker` for every retention period, hold placer roles, notices, consent purposes, consent manager, guardian flow, erasure approval, rights handler roles, bulk export, classification default and home region. The checker needs `settings.data:approve`; proposed default checkers are `tenant_owner` and `security_admin`.
- Platform and region values in this domain need legal or the DPO as a named checker in the platform change set ([[PKG-configuration-lifecycle]]).
- Notified on publish: tenant owner, security admins and auditors; for notice and consent changes also the content admins (translations) and, where the tenant has one, the grievance contact.
- Rollback: reverting a retention change restores the previous period and recomputes end dates. Deletions already executed by a sweep cannot be undone; this is why shortening has a 30-day grace period and a dry-run report.
- Audit: `admin.settings.published` with old and new values, scope, actor, approver and reason; retention-relevant changes also appear in the retention run reports, which record the effective setting version used ([[PKG-data-retention-legal-hold-and]]).

<!-- section:migration -->
## Versioning and migration

- Renamed: `storage.allowUnscannableWithReview` ([[PKG-settings#consumers]]) → `data.files.allow_unscannable_with_review`; `case.readAfterCloseDays` moves to the cases catalogue ([[PKG-settings-cases-and-workflows]]).
- The release flag `retention.destructive.<region>` in [[PKG-data-retention-legal-hold-and]] becomes the region-scope setting `data.retention.destructive_runs_enabled`: it is a standing policy decision, not a code rollout ([[PKG-feature-flags]] boundary).
- Tenant extensions stored in `retention.tenant_retention_extension` become the values of the `data.retention.*_years` keys; the retention package reads them through `@nomology/settings` and the extension table is retired after one release.
- When legal changes a schedule minimum, values below the new minimum are flagged by the drift scan and clamp to the minimum (`onOutOfBounds: clamp`).
- Packages: retention, notice and consent values travel in blueprints; tenant contacts and home region never travel in packages.

<!-- section:testing -->
## Testing

- Resolution tests: minimum from schedule, region and targeted tenant-type values; tenant extension above and below minimum; managed minimum.
- End-to-end: shorten a period in a sandbox tenant, verify the dry-run report lists exactly the expected records, that the grace period holds, and that holds still block deletion.
- Notice completeness and consent-purpose dependency tests per enabled language.
- Regional bound tests for response targets and log retention per region.
- Registry sync check for all 42 keys.

<!-- section:questions -->
## Open questions

- [ ] Legal / DPO to confirm every proposed period and every regional bound in this catalogue per tenant type and region. (owner: DPO)
- [ ] Assumption: the DPDP Third Schedule erasure timelines and 48-hour pre-erasure notice apply only to the listed classes of data fiduciaries (large e-commerce, gaming and social media platforms) and not to our tenants; to be confirmed. (owner: legal)
- [ ] Who is the data fiduciary for party data in each tenant type (the institution, with Nomology as processor), and therefore who must be named in `data.notice.fiduciary_contact`? (owner: legal)
- [ ] Do SEBI circulars or MII agreements require minimum retention of ODR records? (owner: legal)
- [ ] Should a dedicated `privacy_officer` tenant role own this catalogue instead of `security_admin`? (owner: authz group, DPO)

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Retention values resolve as the larger of the schedule minimum, the region value, any targeted tenant-type value and the tenant's own value (bounds only tighten, tenants only extend). Case-type values apply per process and are pinned with the blueprint; the `running_cases` effect recomputes end dates for records whose clock has not expired. Locks and managed values are shown with their legal reason.

<!-- check:permissions -->
### Who may change what

Changes need `settings.data:write` (decision D2: one write permission per catalogue, covering retention and privacy keys), held by `tenant_owner`, `tenant_admin` and `security_admin` by default; nearly every key is maker-checker. Region values need a platform change set with legal as checker. The home region can only change through the tenant move workflow.

<!-- check:safety -->
### Safe bounds

Main risks: deleting legally required records (minimums cannot be undercut; dry-run reports, a 30-day grace period and legal holds protect against mistakes; destructive runs are off per region until legal approves); keeping data longer than allowed (periods have upper bounds and the sweep is monitored); processing without notice (notice required before go-live and for every enabled language); exporting case data in bulk without control (entitlement, maker-checker and approval). A tenant cannot weaken identity checks for rights requests below the platform floor.

<!-- check:timing -->
### When changes take effect

Retention changes apply to records whose clock has not expired (running_cases), with a grace period before any newly due deletion; notice changes apply at the next sign-in or interaction; rights settings apply to new requests only, so open requests keep their target; classification defaults apply to new cases only.

<!-- check:audit -->
### Audit and rollback

Value history plus change sets give the value on any date; retention run reports record the setting versions used for every deletion, so "why was this deleted on that date" can be answered from records. Rollback restores the setting but cannot restore deleted data, which is stated in the console before publish.

<!-- check:sync -->
### Catalogue matches code

Registry check in CI; the retention package refuses to start a sweep if any `data.retention.*` key it reads is missing from the registry.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Section 8(7) requires erasure of personal data when consent is withdrawn or it is reasonable to assume the specified purpose is no longer being served, unless retention is necessary for compliance with law.",
    "id": "R1",
    "issuer": "Parliament of India",
    "jurisdiction": "IN",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "status": "in force in phases",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "Rules notified 13 November 2025; most obligations (Rules 3, 5-16, 22-23) commence 13 May 2027; minimum one-year retention of personal data and associated logs; 48-hour notice before erasure for the classes in the Third Schedule; grievances answered within 90 days.",
    "id": "R2",
    "kind": "web",
    "publisher": "SCC Online",
    "title": "MeitY notifies Digital Personal Data Protection Rules, 2025 (summary)",
    "url": "https://www.scconline.com/blog/post/2025/11/14/meity-notified-digital-personal-data-protection-rules-2025/"
  },
  {
    "excerpt": "An organisation must cease to retain personal data, or remove the means by which it can be associated with individuals, as soon as it is reasonable to assume the purpose is no longer served and retention is no longer necessary for legal or business purposes.",
    "id": "R3",
    "issuer": "Personal Data Protection Commission",
    "jurisdiction": "SG",
    "kind": "regulation",
    "ref": "PDPA 2012, section 25 (Retention Limitation Obligation)",
    "status": "in force",
    "title": "PDPC Advisory Guidelines on Key Concepts in the PDPA (revised 17 May 2022)",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/ag-on-key-concepts/advisory-guidelines-on-key-concepts-in-the-pdpa-17-may-2022.pdf"
  },
  {
    "excerpt": "Article 5(1)(e) storage limitation; Article 17 right to erasure, with exceptions including the establishment, exercise or defence of legal claims (Article 17(3)(e)).",
    "id": "R4",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "status": "in force",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  }
]
```

<!-- end -->
