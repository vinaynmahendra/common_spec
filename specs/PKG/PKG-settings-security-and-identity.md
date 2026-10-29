---
id: "PKG-settings-security-and-identity"
title: "Security and identity settings"
parent: "PKG-settings-catalogue"
order: 11
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of 82 `auth.*` settings across platform, region, offering, tenant, unit and case-type scopes: sign-in methods, MFA and passkeys, SSO, domains, provisioning, sessions and step-up, network and device rules, external identity levels, API credentials and recovery, with bounds, validation and tenant blueprint defaults"
links: []
rev: 1
syncHash: "a36c865d5d07bbdf"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.11 Security and identity settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of 82 `auth.*` settings across platform, region, offering, tenant, unit and case-type scopes: sign-in methods, MFA and passkeys, SSO, domains, provisioning, sessions and step-up, network and device rules, external identity levels, API credentials and recovery, with bounds, validation and tenant blueprint defaults

<!-- section:purpose -->
## Purpose and scope

Covers how people and systems prove who they are on the platform and how long that proof lasts: sign-in methods, passwords and codes, MFA and passkeys, federation, domains and home-realm discovery, provisioning and invitations, sessions and step-up, network and device conditions, external party identity verification, API credentials and recovery.

Consumed by:
- [[PKG-authentication]] and its children [[PKG-email-password-magic-link-otp]], [[PKG-sso-saml-oidc-per-tenant]], [[PKG-mfa-session-management-device]], [[PKG-accessible-authentication-and]]
- [[PKG-authentication-policies]] (policy rules reference these keys as defaults and bounds)
- [[PKG-domain-verification]], [[PKG-user-provisioning-scim]], [[PKG-external-party-identity]], [[PKG-api-clients-and-keys]]
- Sign-in surfaces [[APP-public-and-sign-in-surfaces]] and the security pages of [[APP-tenant-admin-console]]

Not settings here:
- **Objects with their own lifecycle**: SSO connections, verified domains, network zones, authentication policies and rules, API clients, SCIM connections. They are versioned objects administered in their own nodes; settings only reference them by ID.
- **Secrets**: IdP client secrets, SP keys, SCIM tokens, API keys (secrets manager and hashes, [[PKG-encryption-utilities-key]], [[INF-secrets-and-keys]]).
- **Release flags** ([[PKG-feature-flags]]) and deployment configuration ([[FND-environment-management]]), for example the regional SMS provider credentials.
- **Who may do what** after sign-in: access control settings are in [[PKG-settings-access-control]].
- **A user's own security choices** (enrolled factors, trusted devices, notification of new sign-ins channel): these are user data, not settings; personal display preferences are in [[PKG-settings-personal]].

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Notes |
|---|---|---|---|
| `platform` | yes | `platform_security` (writes need `platform_owner` approval) | Floors and hard bounds: MFA floor, breach check, maximum session lengths, blocked countries |
| `region` | yes | `regional_ops` with `platform_security` approval | Method availability that depends on local providers and law: SMS and WhatsApp OTP, government login, KYC methods |
| `offering` | yes | `platform_admin` | CORD (consumer-facing, social sign-in on for parties) vs TERES (institutional, stricter defaults) |
| `tenant` | yes | `security_admin`, `tenant_owner`; `tenant_admin` read-only | Most keys |
| `unit` | limited | `unit_admin` (tighten only) | Only session lengths, network zones and HRD mode; a unit can make a value stricter, never looser |
| `case_type` | limited | `workflow_designer` with `security_admin` approval | Only external identity requirements and invitation expiry, because they depend on the procedure |
| `case` | no | — | Sign-in happens before a case is chosen; the identity level required for a case is pinned from `case_type` at case start |
| `user` | no | — | Users manage their own factors and devices as data, not settings |

<!-- section:catalogue -->
## Settings catalogue

Columns follow [[PKG-settings-catalogue]]. "Lockable" means a higher scope can lock the value for lower scopes; "locked" means fixed at platform. Plan names refer to [[BIL-plans-entitlements-and-usage]] (assumption: plan names are placeholders until billing confirms). Total: 82 settings.

### A. Sign-in methods

Which first-factor methods are offered, to which personas. Personas use the tenant persona keys (`party`, `counsel`, `neutral`, `transcriber`, `secretariat`, `observer`, `staff_admin` = any tenant administrative role).

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.methods.password.personas` | set of persona keys | all except `staff_admin` where SSO is enforced | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.methods.magic_link.personas` | set of persona keys | `party`, `counsel`, `observer` | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.methods.email_otp.personas` | set of persona keys | `party`, `counsel`, `observer` | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.methods.sms_otp.personas` | set of persona keys (`staff_admin` never allowed) | `in`: `party`; `sg`, `us`: none | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.methods.sms_otp.allowed_countries` | list of ISO 3166-1 alpha-2, max 20 | region home country (`IN`, `SG`, `US`) | platform, region, tenant | yes | all | `settings.security:write` | next OTP request | sensitive |
| `auth.methods.whatsapp_otp.enabled` | bool | false (assumption: only offered in `in`, see questions) | platform, region, tenant | yes | `standard` and `enterprise` | `settings.security:write` | next OTP request | sensitive |
| `auth.methods.passkey.first_factor` | bool (passwordless sign-in with a passkey) | true | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | standard |
| `auth.methods.social.providers` | set of `google`, `microsoft_consumer`, `apple`, `linkedin` | CORD: `google`, `microsoft_consumer`; TERES: none | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.methods.social.personas` | set of `party`, `counsel`, `observer` | `party` | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.methods.government_login.providers` | set of `singpass` (region `sg` only); others reserved | none | platform, region, tenant | yes | `enterprise` | `settings.security:write` | next sign-in | maker-checker |

### B. Passwords, one-time codes and links

Bounds follow [[PKG-email-password-magic-link-otp]]. There is deliberately no password expiry key: periodic forced change is not allowed [R1].

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.password.min_length` | int 15–64 | 15 | platform, tenant | yes | all | `settings.security:write` | next password change | sensitive |
| `auth.password.breach_check` | enum `required` | `required` (locked at platform) | platform | locked | all | `settings.platform:write` | next password change | sensitive |
| `auth.otp.ttl_seconds` | int 300–600 | 600 | platform, tenant | yes | all | `settings.security:write` | next OTP request | standard |
| `auth.otp.max_attempts` | int 3–5 | 5 | platform, tenant | yes | all | `settings.security:write` | next OTP request | standard |
| `auth.otp.resend_cooldown_seconds` | int 30–120 | 30 | platform, tenant | yes | all | `settings.security:write` | next OTP request | standard |
| `auth.magic_link.ttl_minutes` | int 5–15 | 15 | platform, tenant | yes | all | `settings.security:write` | next link request | standard |
| `auth.sms.daily_budget` | int 0–entitlement (messages per tenant per day) | 500 | platform, tenant | yes | metered | `settings.security:write` | immediately | standard |

### C. Multi-factor authentication and passkeys

Assurance values (`aal1`, `aal2`, `aal2-phr`, `aal3`) are defined in [[PKG-authentication#policy]]. Named authentication strengths are defined in [[PKG-authentication-policies#policy]].

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.mfa.required_personas` | set of persona keys | `staff_admin`, `secretariat`, `neutral`, `transcriber`, `counsel` (floor: `staff_admin`, `secretariat`, `neutral`, `transcriber` locked) | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | maker-checker |
| `auth.mfa.allowed_factors` | set of `passkey`, `security_key`, `totp`, `email_otp`, `sms_otp` | `passkey`, `security_key`, `totp`, `email_otp` | platform, region, offering, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.mfa.phishing_resistant_roles` | set of role keys | `tenant_owner`, `security_admin` | platform, tenant | yes | all | `settings.security:write` | next sign-in | maker-checker |
| `auth.mfa.enrolment_grace_days` | int 0–14 (sign-ins allowed before a required factor is enrolled) | 0 for administrative and staff roles; 7 for `counsel` | platform, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.passkey.allow_synced` | bool | true | platform, tenant | yes | all | `settings.security:write` | next enrolment | sensitive |
| `auth.passkey.device_bound_roles` | set of role keys that must use a device-bound key (no synced passkeys) | none (platform staff always) | platform, tenant | yes | `enterprise` | `settings.security:write` | next sign-in | maker-checker |
| `auth.passkey.aaguid_allow_list` | list of AAGUIDs, max 50; empty = any | empty | platform, tenant | yes | `enterprise` | `settings.security:write` | next enrolment | maker-checker |
| `auth.passkey.user_verification` | enum `preferred`, `required` | `required` | platform, tenant | yes | all | `settings.security:write` | next ceremony | sensitive |
| `auth.mfa.recovery_codes_enabled` | bool | true | platform, tenant | yes | all | `settings.security:write` | immediately | sensitive |
| `auth.mfa.reset_cooldown_hours` | int 0–72 (new factor cannot satisfy step-up for consequential actions) | 24 | platform, tenant | yes | all | `settings.security:write` | next reset | sensitive |

### D. Federation (SSO)

Connections themselves are objects managed in [[PKG-sso-saml-oidc-per-tenant]], not settings.

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.sso.enforce_for_verified_domains` | bool | false | tenant | no | `standard` and `enterprise` | `settings.security:write` | next sign-in | maker-checker |
| `auth.sso.break_glass_admins_min` | int 1–3 | 1 (floor 1) | platform, tenant | yes | all | `settings.security:write` | on publish (validated) | maker-checker |
| `auth.sso.idp_initiated_allowed` | bool | false | tenant | no | `standard` and `enterprise` | `settings.security:write` | immediately | maker-checker |
| `auth.sso.trust_idp_mfa` | bool (map IdP `acr`/`amr` or `AuthnContextClassRef` to `aal2`) | true | tenant | no | `standard` and `enterprise` | `settings.security:write` | next sign-in | sensitive |
| `auth.sso.force_reauth_for_step_up` | bool | false | tenant | no | `standard` and `enterprise` | `settings.security:write` | next step-up | standard |
| `auth.sso.single_logout` | bool | false | tenant | no | `standard` and `enterprise` | `settings.security:write` | next sign-out | standard |
| `auth.sso.max_connections` | int 0–entitlement | entitlement (`standard` 2, `enterprise` 10) | platform, tenant | yes | entitlement | `settings.platform:write` | immediately | standard |

### E. Domains and home-realm discovery

Owned by [[PKG-domain-verification]].

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.domains.auto_join` | enum `off`, `suggest`, `automatic` | `off` | tenant | no | `standard` and `enterprise` | `settings.security:write` | immediately | maker-checker |
| `auth.domains.auto_join_role` | role key from the tenant's non-administrative roles | none (required when `auto_join` is not `off`) | tenant | no | `standard` and `enterprise` | `settings.security:write` | immediately | maker-checker |
| `auth.domains.reverify_interval_hours` | int 24 | 24 (locked) | platform | locked | all | `settings.platform:write` | next check | standard |
| `auth.hrd.mode` | enum `email_first`, `buttons`, `email_first_with_buttons` | `email_first` | tenant, unit | yes | all | `settings.security:write` | immediately | standard |

### F. Provisioning, invitations and lifecycle

Owned by [[PKG-user-provisioning-scim]].

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.provisioning.scim_enabled` | bool | false | tenant | no | `enterprise` | `settings.security:write` | immediately | maker-checker |
| `auth.provisioning.jit_enabled` | bool | false | tenant | no | `standard` and `enterprise` | `settings.security:write` | next SSO sign-in | maker-checker |
| `auth.provisioning.jit_default_role` | role key (never administrative) | none (required if JIT on) | tenant, unit | no | `standard` and `enterprise` | `settings.security:write` | next SSO sign-in | maker-checker |
| `auth.provisioning.source_of_authority` | enum `platform`, `idp` | `platform`; becomes `idp` for SCIM-managed users | tenant | no | `enterprise` | `settings.security:write` | next sync | maker-checker |
| `auth.provisioning.deprovision_action` | enum `suspend`, `end` | `suspend` | tenant | no | `enterprise` | `settings.security:write` | next SCIM call | maker-checker |
| `auth.provisioning.suspended_to_ended_days` | int 0–365 | 30 | tenant | no | all | `settings.security:write` | next daily run | sensitive |
| `auth.provisioning.stale_account_days` | int 30–365 (no sign-in → review task; staff only) | 90 | platform, tenant | yes | all | `settings.security:write` | next daily run | standard |
| `auth.invitations.staff_ttl_days` | int 1–14 | 7 | platform, tenant | yes | all | `settings.security:write` | new invitations | standard |
| `auth.invitations.case_participant_ttl_days` | int 1–30 | 14 | platform, tenant, case_type | yes | all | `settings.security:write` | new invitations | standard |
| `auth.invitations.require_email_match` | bool (accepting account email must equal invited email) | true | platform, tenant | yes | all | `settings.security:write` | new invitations | sensitive |

### G. Sessions and step-up

Mechanics in [[PKG-mfa-session-management-device]]; values per persona are a map keyed by persona. Upper bounds follow [R1] reauthentication guidance.

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.session.idle_timeout_min` | map persona → int; bounds: `staff_admin` 5–30; `secretariat`, `neutral`, `counsel` 5–60; `transcriber`, `party`, `observer` 5–120 | `staff_admin` 15, `transcriber` 60, others 30 | platform, region, offering, tenant, unit | yes | all | `settings.security:write` | next request | sensitive |
| `auth.session.absolute_hours` | map persona → int; bounds: `staff_admin` 1–8, others 1–12 | `staff_admin` 8, others 12 | platform, region, offering, tenant, unit | yes | all | `settings.security:write` | next request | sensitive |
| `auth.session.max_concurrent` | int 0–20 (0 = unlimited) | 0; `staff_admin` 3 | platform, tenant | yes | all | `settings.security:write` | next sign-in | standard |
| `auth.session.trusted_device_days` | int 0–30 (0 = off; never for `staff_admin`) | 30 | platform, tenant | yes | all | `settings.security:write` | next sign-in | sensitive |
| `auth.session.network_change_action` | enum `none`, `step_up`, `revoke` | `step_up` for `staff_admin`, `none` otherwise | platform, tenant | yes | all | `settings.security:write` | next request | sensitive |
| `auth.step_up.window_minutes` | int 1–15 | 5 | platform, tenant | yes | all | `settings.security:write` | next request | sensitive |
| `auth.step_up.strength_by_action_class` | map action class (`consequential`, `financial`, `export`, `admin_security`) → strength key | `admin_security`: `strength.phishing_resistant`; others `strength.mfa` | platform, tenant | yes | all | `settings.security:write` | next request | maker-checker |

### H. Network, device and risk

Conditions used by policy rules in [[PKG-authentication-policies]]. Network zones are named objects; these keys reference them.

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.network.admin_allowed_zones` | list of network zone IDs; empty = any | empty | tenant, unit | no | `enterprise` | `settings.security:write` | next request | maker-checker |
| `auth.network.staff_allowed_zones` | list of network zone IDs; empty = any | empty | tenant, unit | no | `enterprise` | `settings.security:write` | next request | maker-checker |
| `auth.network.blocked_countries` | list of ISO country codes | platform list (assumption: comprehensively sanctioned jurisdictions; legal to confirm) | platform, region, tenant | yes (additive only) | all | `settings.security:write` | next request | maker-checker |
| `auth.device.managed_required_roles` | set of role keys | none | tenant | no | `enterprise` | `settings.security:write` | next sign-in | maker-checker |
| `auth.device.managed_signal` | enum `idp_claim`, `client_certificate` | `idp_claim` | tenant | no | `enterprise` | `settings.security:write` | next sign-in | maker-checker |
| `auth.risk.impossible_travel_action` | enum `alert`, `step_up`, `block` | `step_up` | platform, tenant | yes | all | `settings.security:write` | next request | sensitive |
| `auth.risk.new_device_notice` | bool (email the user on sign-in from a new device) | true (locked for `staff_admin`) | platform, tenant | yes | all | `settings.security:write` | next sign-in | standard |

### I. External party and counsel identity

Owned by [[PKG-external-party-identity]]. Identity verification levels `ivl0`–`ivl3` are defined there.

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.external.required_ivl` | map case role → `ivl0`–`ivl3` | all case roles `ivl1` | platform, region, offering, tenant, case_type | yes | all | `settings.security:write` | new cases (pinned at case start) | maker-checker |
| `auth.external.ivl2_methods` | set of `digilocker`, `aadhaar_offline_ekyc`, `pan_verify`, `singpass_myinfo`, `document_selfie`, `manual_document_review` | per region: `in` `digilocker`, `pan_verify`, `manual_document_review`; `sg` `singpass_myinfo`, `manual_document_review`; `us` `document_selfie`, `manual_document_review` | platform, region, tenant | yes | KYC add-on | `settings.security:write` | next verification | maker-checker |
| `auth.external.counsel_check` | enum `self_declared`, `secretariat_verified`, `registry_verified` | `self_declared` | platform, tenant, case_type | yes | all | `settings.security:write` | new representations | sensitive |
| `auth.external.representation_proof_required` | bool (authority document before counsel acts) | true | tenant, case_type | no | all | `settings.security:write` | new representations | sensitive |
| `auth.external.verification_reuse_days` | int 0–730 (reuse a verification within the same tenant) | 365 | platform, tenant | yes | all | `settings.security:write` | next case join | sensitive |
| `auth.external.name_mismatch_action` | enum `block`, `review_task` | `review_task` | tenant, case_type | no | all | `settings.security:write` | next verification | standard |
| `auth.external.retain_evidence_documents` | bool (keep ID document images after verification) | false | platform, region, tenant | yes | all | `settings.security:write` | next verification | maker-checker |

### J. API clients, keys and OAuth apps

Owned by [[PKG-api-clients-and-keys]].

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.api_clients.allowed_auth_methods` | set of `api_key`, `private_key_jwt`, `client_secret_basic`, `mtls` | `api_key`, `private_key_jwt` | platform, tenant | yes | API add-on | `settings.security:write` | new credentials | maker-checker |
| `auth.api_clients.max_credential_days` | int 30–730 | 365 | platform, tenant | yes | API add-on | `settings.security:write` | new credentials | sensitive |
| `auth.api_clients.unused_disable_days` | int 30–365 | 90 | platform, tenant | yes | API add-on | `settings.security:write` | next daily run | sensitive |
| `auth.api_clients.admin_scope_requires_ip_allowlist` | bool | true | platform, tenant | yes | API add-on | `settings.security:write` | new grants and next request | maker-checker |
| `auth.api_clients.sender_constrained_for_admin_scopes` | bool (DPoP or mTLS-bound tokens) | false | platform, tenant | yes | `enterprise` | `settings.security:write` | next token | maker-checker |
| `auth.api_clients.access_token_ttl_seconds` | int 60–3600 | 600 | platform, tenant | yes | API add-on | `settings.security:write` | next token | standard |
| `auth.oauth_apps.user_consent` | enum `disabled`, `allow_listed_only`, `admin_approval` | `disabled` | platform, tenant | yes | `enterprise` | `settings.security:write` | next authorisation | maker-checker |
| `auth.scim.token_max_days` | int 30–730 | 365 | platform, tenant | yes | `enterprise` | `settings.security:write` | new tokens | sensitive |

### K. Recovery and administrator protection

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `auth.recovery.self_service_methods` | set of `email_link`, `recovery_code`, `other_factor` | all three | platform, tenant | yes | all | `settings.security:write` | next recovery | sensitive |
| `auth.recovery.assisted_requires_reproof` | bool | true (locked) | platform | locked | all | `settings.platform:write` | next recovery | maker-checker |
| `auth.admin.maker_checker_security` | bool (security changes need a second approver when the tenant has ≥ 2 holders of `settings.security:write`) | true | platform, tenant | yes | all | `settings.security:write` | next change | maker-checker |
| `auth.admin.alert_recipients` | set of role keys | `security_admin`, `tenant_owner` | tenant | no | all | `settings.security:write` | immediately | standard |
| `auth.policy.new_rules_report_only_days` | int 0–30 (a new policy rule starts in report-only mode) | 7 | platform, tenant | yes | all | `settings.security:write` | on publish | sensitive |

<!-- section:validation -->
## Validation and dependencies

Cross-setting rules (enforced by the registry validator in `packages/settings/registry/auth.ts`; an invalid draft cannot move to `in_review`):

| Rule | Error shown to the admin |
|---|---|
| Every persona in use must have at least one enabled first-factor method after `auth.methods.*` and SSO enforcement are applied | "Counsel would have no way to sign in. Enable at least one method for Counsel." |
| `party` and `counsel` must keep at least one method with no cognitive function test (magic link, passkey or OTP with paste) [[PKG-accessible-authentication-and#tenant]] | "Parties must keep a sign-in method that does not need a password (WCAG 3.3.8)." |
| `auth.sso.enforce_for_verified_domains = true` requires an enabled, tested connection and at least `auth.sso.break_glass_admins_min` admins holding a phishing-resistant factor outside SSO | Lists the admins missing a passkey |
| `auth.mfa.allowed_factors` must contain at least one phishing-resistant factor (`passkey` or `security_key`) — NIST requires an AAL2 phishing-resistant option [R1] | "At least one phishing-resistant method must stay available." |
| `sms_otp` cannot be the only allowed factor for any persona in `auth.mfa.required_personas` | "Text message codes cannot be the only second factor." |
| `auth.passkey.device_bound_roles` ⊆ roles whose holders can enrol security keys; publishing warns with the count of affected users lacking one | Warning with count and an "Invite to enrol" action |
| `auth.domains.auto_join ≠ off` requires `auth.domains.auto_join_role` and at least one verified domain | "Choose the role new colleagues receive." |
| `auth.provisioning.jit_enabled` requires an enabled SSO connection with JIT allowed on the connection; `jit_default_role` cannot be an administrative role | "Administrative roles cannot be granted automatically." |
| `auth.network.admin_allowed_zones` non-empty: the publishing admin's current IP must be inside a listed zone, or publish is blocked (lock-out protection) | "You would lock yourself out." |
| `auth.session.idle_timeout_min` ≤ `auth.session.absolute_hours` × 60 for every persona | Field error |
| A unit value may only be stricter than the tenant value (shorter session, fewer zones) | "Units can tighten this setting but not loosen it." |
| `auth.external.required_ivl` at `ivl2` requires at least one method in `auth.external.ivl2_methods` available in the tenant's region and an active KYC connection ([[INT-kyc-and-sanctions-screening]]) | "No verification provider is connected for this region." |
| `auth.api_clients.sender_constrained_for_admin_scopes = true` requires `private_key_jwt` or `mtls` in allowed methods | Field error |

Platform hard bounds (cannot be changed by any tenant): passwords ≥ 15 characters and breach-checked; MFA for administrative roles, secretariat, neutrals and transcribers; session absolute lifetime ≤ 12 h (≤ 8 h for `staff_admin`); step-up window ≤ 15 min; no SMS OTP for `staff_admin`; no trusted-device skip for `staff_admin`; Nomology staff only via workforce SSO with device-bound WebAuthn.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution (TERES) | SEBI ODR institution | CORD tenant | Court or government programme | Why they differ |
|---|---|---|---|---|---|
| `auth.methods.password.personas` | all | all except `party` | all | staff only | SEBI investors and court users are infrequent, mobile-first users; passwords add risk without benefit |
| `auth.methods.sms_otp.personas` | none | `party` | `party` | `party` | Parties in India commonly prefer mobile OTP |
| `auth.methods.social.providers` | none | none | `google`, `microsoft_consumer` | none | Consumer-facing CORD matters benefit from familiar sign-in; regulated tenants avoid consumer IdPs |
| `auth.mfa.required_personas` | floor + `counsel` | floor + `counsel` | floor | floor + `counsel` | CORD counsel are often occasional users; tenant can raise |
| `auth.mfa.phishing_resistant_roles` | `tenant_owner`, `security_admin` | all administrative roles | `tenant_owner` | all administrative roles and `secretariat` | Regulated and government tenants expect phishing-resistant admin access |
| `auth.sso.enforce_for_verified_domains` | true once tested | false | false | true once tested | Institutions and courts usually have a workforce IdP |
| `auth.session.idle_timeout_min` (`secretariat`) | 30 | 30 | 30 | 15 | Government security guidelines tend to be stricter (assumption) |
| `auth.session.trusted_device_days` | 30 | 14 | 30 | 0 | Shared and public-access terminals are more likely in court programmes |
| `auth.external.required_ivl` (`claimant`) | `ivl1` | `ivl1` (assumption: SEBI ODR circulars do not mandate KYC by the ODR institution; legal to confirm) | `ivl1` | `ivl2` | Court programmes may require stronger proof before filing |
| `auth.external.counsel_check` | `secretariat_verified` | `self_declared` | `self_declared` | `registry_verified` | Institutional arbitration often checks authority before counsel acts |
| `auth.provisioning.scim_enabled` | true (`enterprise`) | false | false | false | Large institutions run staff joiner/leaver from their IdP |
| `auth.network.admin_allowed_zones` | empty | empty | empty | office zones | Government networks commonly restrict admin access (assumption) |
| `auth.api_clients.sender_constrained_for_admin_scopes` | false | true | false | true | Aggregator and regulator integrations carry higher risk |

<!-- section:admin_ux -->
## Where it is administered

Tenant admin console ([[APP-tenant-admin-console]]) → **Security**:

| Page (route) | Groups | Notes |
|---|---|---|
| `/admin/security/sign-in` | A, B, D (settings part), E (`auth.hrd.mode`) | Live preview of the sign-in page per persona |
| `/admin/security/mfa` | C | Coverage panel: users per persona with and without each factor |
| `/admin/security/sessions` | G | Shows the effective value per persona and unit, with the source |
| `/admin/security/policies` | H, `auth.policy.*` | Policy rules editor from [[PKG-authentication-policies]]; settings here are defaults the rules can refine |
| `/admin/organisation/domains` | E | Domain objects and verification status ([[PKG-domain-verification]]) |
| `/admin/security/provisioning` | F | SCIM connection, JIT and invitation settings ([[PKG-user-provisioning-scim]]) |
| `/admin/security/external-identity` | I | Per case-type requirement table ([[PKG-external-party-identity]]) |
| `/admin/security/api` | J | API client list ([[PKG-api-clients-and-keys]]) |
| `/admin/security/recovery` | K | |

Platform console: `/platform/settings/security` for platform, region and offering values, showing which tenants hold explicit overrides.

Display rules: each field shows the effective value, its source scope ("Platform default", "Locked by platform", "Set by Singapore office unit"), a lock icon when a higher scope locks it, and the plan badge when the plan does not include it (field read-only with a link to plan details).

API: `GET /admin/v1/settings/auth` and `PATCH /admin/v1/settings/auth` with `If-Match` ([[INT-tenant-admin-api]]); a PATCH creates a draft change set, never a direct publish, for keys marked maker-checker.

Admin copilot ([[APP-admin-copilot]]) may **propose** changes to groups A–C and E–K as drafts with a diff and explanation; it can never publish, never lower a value below the tenant's current one for `auth.mfa.*` without stating the risk, and cannot touch groups whose audit class is maker-checker without the human then routing it for approval.

<!-- section:change_control -->
## Change control and audit

- Lifecycle follows [[PKG-configuration-lifecycle]]: draft → in_review → approved → published.
- **Maker-checker** (approver must be a different holder of `settings.security:write`, see [[PKG-separation-of-duties]]): every key with audit class maker-checker, plus any change that weakens a value (shorter password minimum, removing a required persona from MFA, longer sessions, enabling a new first-factor method for `staff_admin`). Tenants with a single security admin route approval to `tenant_owner`; if those are the same person, a 24-hour cooling-off delay applies and all tenant admins are notified.
- **Step-up**: authoring and approving require `strength.phishing_resistant` within 5 minutes.
- **Notifications**: published security changes notify `auth.admin.alert_recipients` and are listed in the tenant's weekly security digest.
- **Rollback**: publishing a previous version in one action from [[APP-admin-change-history]]; rollback of a weakening still needs no approval (it restores a stricter state), rollback that weakens needs approval.
- **Audit record** (`admin.settings.published`, plus `admin.auth_policy.published` for policy objects): key, scope, scope ID, old value, new value, actor, approver, reason (required), change set ID, policy version, request ID, `acr` of the actor's session.
- **Platform changes** to floors need `platform_security` author plus `platform_owner` approval and are announced to tenant security admins 30 days ahead unless they are emergency tightenings.

<!-- section:migration -->
## Versioning and migration

- Keys are never reused; a renamed key keeps a read alias for two releases and the registry maps old drafts forward.
- A tightened platform floor applies to every tenant on its effective date; tenants whose explicit value falls outside the new bound are listed to `platform_security` and their value is clamped with a notice to their security admins.
- A changed platform default applies only to tenants still inheriting it; release notes list tenants with explicit values.
- Settings in this catalogue travel in configuration packages ([[PKG-configuration-packages]]) **except** values that reference tenant-specific objects (zone IDs, connection IDs, role keys of custom roles), which are exported as named references and re-bound on import; the import fails safe (strict default) if a reference cannot be bound.
- Tenant blueprints (`blueprint.arbitral_institution`, `blueprint.sebi_odr`, `blueprint.cord`, `blueprint.court_programme`) carry the defaults table above.

<!-- section:testing -->
## Testing

- The registry `packages/settings/registry/auth.ts` (Zod schema, bounds, scopes, lockability, entitlement, permission, audit class) is the source of truth. A CI script renders this catalogue table from the registry and fails if the node and the registry disagree.
- Resolution tests per key: platform floor beats tenant value; region lock; offering default; unit tighten-only; case_type pinning at case start for `auth.external.required_ivl`; entitlement off → platform default applies.
- Validation tests for each cross-setting rule above, including the lock-out checks (publishing admin's own IP outside zone; no break-glass admin).
- Property test: for random valid combinations, every persona still has at least one usable method and at least one phishing-resistant MFA option.
- E2E: change idle timeout and confirm the next request uses the new value; change `auth.methods.*` and confirm the sign-in page updates without redeploy.

<!-- section:questions -->
## Open questions

- [ ] Is WhatsApp OTP acceptable as a first factor for parties in India, and under which provider terms? (Security, Legal)
- [ ] Confirm whether any SEBI ODR circular or MII agreement requires investor identity verification beyond email or mobile control. (Legal)
- [ ] Confirm the platform blocked-countries list and its legal basis per entity. (Legal, Compliance)
- [ ] Should `unit_admin` be allowed to shorten session timeouts, or should only tenant scope exist? Current proposal: yes, tighten only. (Security)
- [ ] Plan names now follow [[BIL-plans-entitlements-and-usage]] (`starter`, `standard`, `enterprise`; decision D11). Open: which settings groups need their own entitlement key rather than a plan tier. (Billing)
- [ ] Is Singpass login (as opposed to Myinfo for verification) needed for any Singapore tenant at launch? (Product)

<!-- section:notes -->
## Notes

Pattern borrowed from: authentication strengths in Microsoft Entra Conditional Access [R2] and authentication policies in Okta Identity Engine [R3] (named method combinations referenced by settings rather than many boolean flags); verified-domain enrolment modes (`off`, `suggest`, `automatic`) are similar to verified domains in Clerk Organizations [R4].

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Resolution follows [[PKG-configuration-scope-hierarchy]]: platform floor → region → offering → tenant → unit (tighten-only) → case_type (only group I and case-participant invitation expiry, pinned at case start). Session values are maps per persona, so the effective value for a user is computed from their active persona in the active tenant, and the console shows the source scope next to each value. Keys at `user` and `case` scope do not exist, so there is no per-user exception path; per-user exceptions are expressed as policy rules with an expiry in [[PKG-authentication-policies]].

<!-- check:permissions -->
### Who may change what

All tenant writes need `settings.security:write` (held by `security_admin` and `tenant_owner` by default; `tenant_admin` reads only). Unit-scope writes need `settings.security:write` on that unit (granted to `unit_admin` only for the three tighten-only keys). Case-type values need `workflow.definition:update` plus `settings.security:write` approval. Platform values need `settings.platform:write` and `platform_owner` approval for floors. Plan entitlement gates are checked before permission.

<!-- check:safety -->
### Safe bounds

The validator blocks: personas with no sign-in method; removing every phishing-resistant MFA option; SMS as the only second factor; SSO enforcement without break-glass admins; IP zones that exclude the publishing admin; auto-join or JIT granting administrative roles; loosening below platform floors. Weakening changes need maker-checker and notify all security recipients. Changes to external identity requirements are pinned per case so a running case's parties are not suddenly locked out.

<!-- check:timing -->
### When changes take effect

Each row states when it applies. Session and network values apply on the next request (existing sessions are re-evaluated, and a session that no longer meets policy gets a step-up prompt, not a silent sign-out); method and MFA changes apply at next sign-in; credential lifetimes apply to new credentials only; external identity requirements apply to new cases only; daily jobs (stale accounts, unused API keys) apply at their next run.

<!-- check:audit -->
### Audit and rollback

Every publish writes `admin.settings.published` with old and new value, scope, actor, approver, reason and change set ID into the hash-chained audit trail ([[PKG-audit-log-schema]]). Settings versions are immutable, so the value in force at any date is a query over published versions; [[APP-admin-change-history]] offers one-click rollback to a previous version.

<!-- check:sync -->
### Catalogue matches code

The catalogue is generated from `packages/settings/registry/auth.ts`; CI fails on any drift between the registry and this node, on a registry key without a consumer, and on code reading an `auth.*` key not in the registry (ESLint rule `settings/known-key`).

<!-- citations -->
## Citations

```json
[
  {
    "body": "NIST",
    "id": "R1",
    "ident": "SP 800-63B-4",
    "kind": "standard",
    "title": "NIST SP 800-63B-4 Digital Identity Guidelines: Authentication and Authenticator Management",
    "url": "https://pages.nist.gov/800-63-4/sp800-63b.html",
    "version": "800-63-4 (final, July 2025)"
  },
  {
    "body": "Microsoft",
    "id": "R2",
    "kind": "vendor",
    "title": "Microsoft Entra: Conditional Access authentication strengths",
    "url": "https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-strengths"
  },
  {
    "body": "Okta",
    "id": "R3",
    "kind": "vendor",
    "title": "Okta Identity Engine: Sign-on policies and rules",
    "url": "https://help.okta.com/oie/en-us/content/topics/identity-engine/policies/about-policies.htm"
  },
  {
    "body": "Clerk",
    "id": "R4",
    "kind": "vendor",
    "title": "Clerk Organizations: Verified domains",
    "url": "https://clerk.com/docs/guides/organizations/verified-domains"
  }
]
```

<!-- end -->
