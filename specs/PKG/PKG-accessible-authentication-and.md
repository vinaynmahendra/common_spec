---
id: "PKG-accessible-authentication-and"
title: "Accessible authentication and identity / KYC alternatives"
parent: "PKG-authentication"
order: 4
type: "feature"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "WCAG 3.3.8, no puzzle CAPTCHAs, OTP timing, alternatives to liveness checks (Pragya Prasun directions), guardian / representative flows"
links: []
rev: 3
syncHash: "f37b17edd658ef62"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.4 Accessible authentication and identity / KYC alternatives

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> WCAG 3.3.8, no puzzle CAPTCHAs, OTP timing, alternatives to liveness checks (Pragya Prasun directions), guardian / representative flows

<!-- section:scope -->
## Scope and surfaces

Covers every authentication and identity step on the platform: sign-in (email + password, magic link, email, SMS or WhatsApp OTP, passkeys, tenant SSO hand-off, social and government sign-in buttons), MFA and step-up before consequential actions (including the method picker filtered by the required strength from [[PKG-authentication-policies]]), account recovery and assisted recovery, invitation acceptance, home-realm discovery prompts ([[PKG-domain-verification]]), identity verification of external participants at levels `ivl1`–`ivl3` ([[PKG-external-party-identity]]), and identity / KYC verification of parties and payees through the provider in [[INT-kyc-and-sanctions-screening]]. Surfaces: `(public)` sign-in and invitation routes ([[APP-public-and-sign-in-surfaces]]), step-up dialogs in all route groups, own security settings (factors, devices), and verification journeys in the party portal. It also covers acting on behalf of another person (lawful guardian, authorised representative).

Out of scope: the tenant's own identity provider pages behind SSO and third-party social or government sign-in pages (their operators' responsibility, stated in the tenant's accessibility statement); video hearing identity checks ([[DOM-hearing-room-accessibility]]).

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

| Region / tenant type | Instrument | Who carries it | Points to | Status |
|---|---|---|---|---|
| India, all tenants (service providers) | RPwD Act 2016, accessibility of services [R1] | Tenant and Nomology as provider of the service | Rules under the Act; WCAG via standards | In force; exact section and rule references to be confirmed by legal |
| India, SEBI-regulated tenants and MIIs | SEBI circular on digital accessibility, 31 July 2025 [R2] | Tenant (regulated entity); Nomology by contract | Accessibility standards referenced in the circular | In force; applicability to ODR institutions to be confirmed by legal |
| India, KYC | Supreme Court, Pragya Prasun v. Union of India (2025), directions on accessible digital KYC | Regulated entities doing KYC; KYC provider; Nomology where we run the journey | Alternatives to liveness steps that users with visual or facial impairments cannot perform | Assumption: directions apply to KYC journeys we host for regulated tenants; to be confirmed by legal, with exact directions summarised |
| India, consent | DPDP Act 2023, s.9 (consent by lawful guardian of a person with disability) [R3] | Data fiduciary (tenant or Nomology per processing) | Guardian consent flow | In force |
| Singapore, US | Contractual WCAG 2.2 AA commitments; US ADA exposure for specific tenants | Nomology by contract | WCAG 2.2 AA | Assumption: no statutory duty confirmed; legal to review per tenant |

Legal sign-off required before this table is used in any ACR or contract.

<!-- section:target -->
## Conformance target and baseline

WCAG 2.2 AA [R4], including 3.3.8 Accessible Authentication (Minimum) [R5] and 2.2.1 Timing Adjustable. Platform rules beyond AA: no puzzle or image-recognition CAPTCHA at all (AA would allow object recognition); 3.3.9 (AAA) met for platform-hosted sign-in, because every route offers a method that needs no cognitive function test. Baseline: not yet measured.

<!-- section:criteria -->
## Success criteria mapping

| Criterion | Where met | How | Test |
|---|---|---|---|
| 3.3.8 Accessible Authentication | Sign-in, recovery, step-up | Password fields allow paste and password managers (`autocomplete="current-password"`, `new-password`); magic link and passkeys offered; OTP field accepts paste and `autocomplete="one-time-code"`; no transcription of characters from images | Playwright: paste into every auth field; manual with 1Password and browser manager |
| 2.2.1 Timing Adjustable | OTP, magic link, step-up | OTP valid 10 minutes (proposed), resend after 30 seconds, unlimited resends rate-limited per [[PKG-input-sanitisation-csrf-rate]]; no countdown that discards entry; magic link valid 15 minutes and a new one can be requested | Unit tests on expiry; manual |
| 3.3.1, 3.3.3 Error identification and suggestion | All forms | Errors in text with next step ("That code has expired. We have sent a new code to ••••42.") | Storybook + Playwright |
| 1.3.5 Identify input purpose | Email, name, phone fields | `autocomplete` tokens | Lint |
| 2.4.3, 2.4.6 | Multi-step sign-in | Focus to heading per step | Playwright keyboard test |
| 3.2.2 On input | OTP | No auto-submit on 6th digit unless the user enabled it; single input field, not six boxes | Interaction test |
| 4.1.3 Status messages | "Code sent" | Announcer polite | Manual AT |
| 1.1.1 Non-text content | Bot protection | No visual CAPTCHA; risk-based checks and rate limits instead | Inspection |
| 2.5.8 Target size | All | Design system components | Automated |

<!-- section:components -->
## Component and pattern requirements

Uses [[PKG-form-fields]] (`TextField` with required `autoComplete`), [[PKG-button-and-icon-button]], [[PKG-alerts-toasts-and-status]] and [[PKG-modal-dialog-and-consequential]] (`step-up` level). OTP entry is a single `TextField` with `inputMode="numeric"` and `autoComplete="one-time-code"`.

<!-- section:at -->
## Assistive technology support matrix

As [[PKG-design-system-component#at]], with sign-in additionally tested with password managers on each platform and with iOS and Android OTP autofill from SMS.

<!-- section:documents -->
## Documents, media and generated output

Identity documents uploaded for KYC go through [[PKG-file-upload-dropzone]]. Users may choose which accepted document to provide; the journey never requires reading text from an image within a time limit.

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Tenants choose which sign-in methods are enabled (`auth.methods.*` in [[PKG-settings-security-and-identity]]) and which strengths their policies require. Guardrails enforced by the settings validator and policy editor:
- A tenant cannot disable every method that avoids a cognitive function test for `party` and `counsel`: at least one of magic link, passkey or OTP with paste must stay enabled ([[PKG-settings-security-and-identity#validation]]).
- A policy rule that requires `strength.phishing_resistant` or `strength.device_bound` for parties shows a warning that some users cannot use security keys, and requires an alternative route (assisted verification by the case manager) to be named before publish.
- Step-up for parties may use email OTP where the action class allows, so a party never needs a separate authenticator app to file.
- Tenant SSO pages are the tenant's responsibility and this is stated in the tenant's accessibility statement.

**KYC and identity verification alternatives.** Where the verification provider uses liveness checks (blinking, head movement, reading digits aloud), the journey must offer at least one alternative at the same identity verification level that does not depend on sight, facial movement or speech, for example an assisted video call with a trained operator using text chat, an in-person or document-based verification route agreed with the tenant (`manual_document_review`), or verification by an authorised representative. The provider contract must support this ([[INT-third-party-component]]). Assumption: specific acceptable alternatives depend on the tenant's regulator and must be confirmed by legal.

**Guardian and representative flows.** A party may be represented by a lawful guardian (DPDP Act s.9 [R3]) or an authorised representative. The representative signs in with their own account, the case shows "Acting for {party}" on every page and in the audit trail, consent is captured from the guardian, and notices go to both where the tenant's rules require. The representation record and its approval are specified in [[PKG-external-party-identity#policy]].

<!-- section:testing -->
## Testing method

Automated: Playwright journeys for each sign-in method using keyboard only, paste into every field, axe on each state (enter email, code sent, code expired, locked, step-up). Manual: AT matrix each release; password-manager tests; one round per year with disabled participants focused on sign-in and KYC (including blind users and users with motor impairments). Sample per WCAG-EM: every state of every auth method plus KYC start, liveness alternative and representative setup.

<!-- section:exceptions -->
## Known exceptions and remediation plan

Unknown until the KYC provider is chosen. Any provider step without an accessible alternative is recorded as an exception with the alternative route and owner.

<!-- section:reporting -->
## Conformance reporting

Feeds the platform ACR ([[APP-accessibility-conformance]]) and the evidence pack for SEBI-regulated tenants ([[RPT-accessibility-audit-evidence-for]]).

<!-- section:support -->
## Feedback, accommodation and grievance

Users who cannot complete sign-in or KYC can use "Get help signing in" on the sign-in page, which opens the accessibility feedback route ([[APP-accessibility-feedback]]) without needing an account; assisted verification requests route to the tenant's nodal officer with a response target (proposed: 2 working days).

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm the exact Pragya Prasun directions that apply to our KYC and identity verification journeys and which tenants they cover (owner: legal).
- [ ] Choose the KYC provider per region and confirm it supports a non-liveness alternative route (owner: integrations lead).
- [ ] Confirm the accessibility of Singpass and DigiLocker consent screens with their published conformance information before enabling them (owner: accessibility lead).
- [ ] Should OTP auto-submit be offered as a user setting at all (owner: product).
- Answered: OTP validity (default 10 minutes, `auth.otp.ttl_seconds`) and magic-link validity (default 15 minutes, `auth.magic_link.ttl_minutes`) are set in [[PKG-settings-security-and-identity]] with bounds that never go below 5 minutes.

<!-- checks -->
## Template checks

<!-- check:applicability -->
### Legal applicability and allocation

India: RPwD Act for service providers, SEBI 31 July 2025 circular for SEBI-regulated tenants, DPDP s.9 for guardian consent, and the Pragya Prasun KYC directions (scope to be confirmed by legal). Singapore and US: contractual WCAG 2.2 AA unless legal confirms statutory exposure per tenant.

<!-- check:tenancy -->
### Tenant customisation and content

Tenant choices that could break conformance (methods, policy strengths, verification methods) are checked at save: the validator blocks removing all non-cognitive methods and warns, with a required alternative, when a strength excludes common assistive setups. Tenant SSO and third-party IdP pages are listed as tenant or provider responsibility in the accessibility statement.

<!-- check:regression -->
### Preventing regression

Playwright keyboard-only journeys for every sign-in method with paste checks run in CI; axe on every auth state; manual AT and password-manager checks each release.

<!-- check:identity -->
### Authentication and identity verification

Every platform sign-in route offers a method with no cognitive function test (magic link, passkey, or OTP with paste); password fields allow paste and password managers; no CAPTCHA of any kind; OTP valid up to 10 minutes with resend; a tenant cannot disable all such methods for parties or counsel (settings validator); policy rules requiring security keys for parties need a named alternative route; identity verification liveness steps must have a non-sight, non-facial, non-speech alternative at the same level; guardians and representatives act through their own accounts with "Acting for" shown and audited; step-up uses the same accessible methods.

<!-- check:third-party -->
### Third-party and embedded components

The KYC provider and any SSO identity provider are third-party surfaces; the provider must supply a dated ACR and support an alternative to liveness; tenant SSO pages are the tenant's responsibility and stated as such in its accessibility statement.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 49 of 2016",
    "title": "Rights of Persons with Disabilities Act, 2016",
    "url": "https://indiacode.nic.in/bitstream/123456789/15939/1/the_rights_of_persons_with_disabilities_act%2C_2016.pdf"
  },
  {
    "id": "R2",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "id": "R3",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "body": "W3C",
    "id": "R4",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C",
    "excerpt": "A cognitive function test is not required for any step in an authentication process unless an alternative, a mechanism to assist, or an exception applies.",
    "id": "R5",
    "ident": "WCAG 2.2 SC 3.3.8",
    "kind": "standard",
    "title": "Understanding SC 3.3.8 Accessible Authentication (Minimum)",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication.html"
  }
]
```

<!-- end -->
