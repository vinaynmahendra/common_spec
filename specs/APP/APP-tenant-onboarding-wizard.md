---
id: "APP-tenant-onboarding-wizard"
title: "Tenant provisioning and onboarding wizard"
parent: "APP-platform-admin-and-support"
order: 1
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Platform-console wizard that provisions a tenant from a blueprint (arbitral institution, SEBI ODR institution, CORD tenant, court or government programme) and the tenant owner's first-run setup checklist"
links: []
rev: 1
syncHash: "62bf7afe9d663954"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.6.1 Tenant provisioning and onboarding wizard

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Platform-console wizard that provisions a tenant from a blueprint (arbitral institution, SEBI ODR institution, CORD tenant, court or government programme) and the tenant owner's first-run setup checklist

<!-- section:scope -->
## Scope, audiences and surfaces

Two linked surfaces that take a tenant from contract to first case:

1. **Provisioning wizard** at `/platform/tenants/new` in the platform console ([[APP-platform-admin-and-support]]), used by `platform_admin` (and `regional_ops` for drafts). It collects everything the lifecycle workflow needs, chooses a **tenant blueprint**, previews what will be created, and starts provisioning ([[MT-tenant-lifecycle]]).
2. **First-run setup checklist** at `/admin/setup` in the tenant admin console ([[APP-tenant-admin-console]]), used by the new `tenant_owner` and other admins. It walks them through the tasks only the institution can do (accept ownership, add a second owner, confirm branding, connect SSO, invite staff, review case types, set notification sender details, accept the data processing terms text) and shows progress.

Blueprints available at launch (configuration packages owned by [[PKG-configuration-packages]]; default values per blueprint are in each `PKG-settings-*` catalogue's defaults section):

| Blueprint | Offering | Tenant type | Typical use |
|---|---|---|---|
| Arbitral institution | TERES | `arbitral_institution` | Institutional arbitration with secretariat, tribunal secretaries, scrutiny, eBundles and transcription |
| SEBI ODR institution | CORD | `odr_institution` | SEBI ODR conciliation and arbitration, MII intake, NSE reporting, high-volume party onboarding |
| CORD tenant | CORD | `cord` | Online dispute resolution programmes with party self-service filing |
| Court or government programme | CORD or TERES | `court_programme` | Court-annexed mediation or government grievance programmes with stricter support access and accessibility obligations |

Out of scope: the workflow steps themselves ([[MT-tenant-lifecycle]]); blueprint authoring (platform console `/platform/blueprints`); plan pricing ([[BIL-plans-entitlements-and-usage]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(platform-admin)/platform/tenants/new/
  layout.tsx            # wizard shell with stepper (PKG-stepper-and-multi-step-form); draft ID in URL
  page.tsx              # resume or start: list of this operator's drafts
  [draftId]/
    basics/             # 1. legal name, display name, slug, offering, tenant type, contract reference
    region/             # 2. home region, billing entity, data residency confirmation
    blueprint/          # 3. blueprint + version, parameters (seat time zone, locale, case types to enable)
    plan/               # 4. plan, seats, entitlements, sandbox yes/no
    access/             # 5. first tenant owner, optional additional admins with roles, SSO metadata (optional), custom domain (optional)
    review/             # 6. preview of everything to be created, warnings, start
  ../[tenantId]/lifecycle/   # after start: live progress (polls workflow status query)

app/(tenant-admin)/admin/setup/
  page.tsx              # checklist with progress; each item links to the real admin page
```
`proxy.ts` and `requireOp('platform.tenant.create')` guard the wizard; `/admin/setup` requires any admin role and shows items according to the user's ops (an `auditor` sees progress only).

<!-- section:rendering -->
## Rendering and caching strategy

Both surfaces are dynamic, `private, no-store`. The review step renders a server-computed preview (no caching). The lifecycle progress page polls the `status` query every 5 seconds while running and stops at a terminal state. The setup checklist is computed per request from tenant state (for example "SSO connected" is true when a published SSO connection exists), not from stored checkboxes, so it never goes stale.

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `platform.tenantDraft.save` | Server Action per step | Saves the wizard draft (platform-level table `tenant_provisioning_draft`, retained 30 days); validates the step |
| `platform.tenantDraft.checkSlug` | tRPC query | Checks the global directory and reserved list; debounced 300 ms |
| `platform.tenantDraft.preview` | tRPC query | Expands the blueprint with parameters: roles, permission sets, settings with values and sources, case types, templates, notification policies, AI defaults; returns warnings |
| `platform.tenant.create` + `platform.tenant.provision` | Server Action (one submit) | Creates the `draft` tenant row and starts the lifecycle workflow; step-up; idempotent on draft ID |
| `admin.setup.status` | Server Component read | Computes checklist items from tenant state |
| `admin.setup.dismissItem` | Server Action | Owner may dismiss optional items with a reason (audited `admin.setup.item_dismissed`) |

Every action goes through `runAdminOp` ([[APP-administration-model#design]]). The provisioning input schema is shared with the `ProvisionTenant` trigger in [[MT-tenant-lifecycle#trigger]].

<!-- section:state -->
## Client state and URL state

Wizard state lives in the server-side draft, keyed by draft ID in the URL, so an operator can stop and resume or hand over to a colleague (the draft records the last editor). The stepper allows going back without losing later steps; changing the blueprint or offering invalidates dependent steps, which are marked "needs review". No wizard data is stored in the browser.

<!-- section:forms -->
## Forms, validation and uploads

React Hook Form with Zod schemas shared with the server. Specifics:
- **Slug**: `^[a-z0-9-]{3,40}$`, not in `platform.tenant.reserved_slugs`, unique across regions (TM-R2); suggestion generated from the display name.
- **Region**: only regions where `platform.region.provisioning_open` is true and the tenant type is in `platform.region.allowed_tenant_types`; the billing entity list is filtered by `platform.region.allowed_billing_entities` (for example India → NTPL).
- **Blueprint**: only published versions allowed for the offering and region; parameters rendered from the blueprint's parameter schema.
- **First owner**: email required; must not be a Nomology workforce domain (ADM-R5); optional phone.
- **SSO metadata**: optional upload of SAML metadata XML or OIDC discovery URL; validated server-side; can be skipped and done by the tenant at `/admin/security/sso`.
- **Redundant entry is avoided** (WCAG 2.2 success criterion 3.3.7 [R1]): values already given (legal name, contract reference, contact email) are carried forward, not re-asked.
- The review step requires ticking "Contract reference and region confirmed with the account manager" and step-up before Start.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Slug taken or reserved | Inline error with up to three suggestions |
| Region not open for this tenant type | The option is disabled with the reason; link to the region sign-off record |
| Blueprint value outside current region bounds | Review step lists the conflict; start is blocked until a newer blueprint version or a parameter change resolves it |
| Workflow start failure | Error with Temporal error class and runbook link; draft kept |
| Step failed during provisioning | Lifecycle page shows the failed step, attempts, last error class and the `retry` / `abandon` actions (see [[MT-tenant-lifecycle#failure]]) |
| Owner invitation bounced | Lifecycle page and checklist show "Invitation not delivered"; platform admin can correct the email and resend |

<!-- section:performance -->
## Performance budgets

Desktop budgets of the platform console (≤ 250 KB gzip first-load JS). The preview query must return in under 2 s for the largest blueprint (about 400 settings and 12 case types). Provisioning itself targets under 30 minutes end to end excluding DNS ([[MT-tenant-lifecycle#observability]]).

<!-- section:security -->
## Security headers and browser session

Wizard pages inherit the platform console security (zero-trust network, workforce IdP with phishing-resistant MFA, strict CSP). Start requires step-up. The wizard never collects secrets: SSO client secrets and integration credentials are entered later by the tenant into the secrets manager through [[INT-connections-admin]] and [[PKG-sso-saml-oidc-per-tenant]]. The first owner's email is personal data stored in the draft for at most 30 days and then in the invitation (deleted 30 days after acceptance, [[MT-tenancy-and-identity-schema#protection]]). On the tenant side, `/admin/setup` shows nothing beyond configuration state.

<!-- section:i18n -->
## Localisation hookup

The platform wizard is English only, like the rest of `(platform-admin)`. The tenant setup checklist uses the `admin` namespace and the tenant's default locale; blueprint display names and descriptions are translatable fields of the blueprint.

<!-- section:theming -->
## Tenant theming hookup

The wizard uses the fixed platform theme. The tenant setup checklist uses the tenant theme once branding is published; before that, the blueprint's default theme. The "Confirm branding" item opens the branding editor with preview ([[PKG-branding-and-theming]]).

<!-- section:observability -->
## Frontend observability

Metrics: wizard drafts started and abandoned per step, time from draft to start, provisioning outcomes per blueprint, time from activation to setup completion per blueprint, checklist items most often dismissed. Audit: `admin.tenant.created`, `admin.tenant.provisioning_started`, `admin.setup.item_completed`, `admin.setup.item_dismissed`.

<!-- section:testing -->
## Testing strategy

- Playwright: complete the wizard for each of the four blueprints in staging; tenant reaches `active`; owner receives the invitation; `/admin/setup` shows the expected items.
- Negative: slug collision across regions (directory stub), region closed for tenant type, blueprint value outside region bound, Nomology email as owner, start without step-up.
- Resume: leave at step 4, resume from another operator's session.
- Accessibility: stepper keyboard path, error summary focus, no redundant entry.
- Checklist computation unit tests per item against tenant fixtures.

<!-- section:questions -->
## Open questions

- [ ] Should a tenant owner be able to self-serve a sandbox from `/admin/sandboxes`, or only through the wizard and platform admins? (owner: product, with [[PKG-settings-billing-and-plans]])
- [ ] Which checklist items are mandatory before the first case can be created (for example "second owner added", "data processing terms accepted")? (owner: product with legal)
- [ ] Do court or government programmes need a separate approval step (for example a signed order or MoU reference) before provisioning? (owner: account management)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

The wizard writes only platform-level drafts and starts the lifecycle workflow; the tenant row and all seeded data are created by the workflow in the target region. The setup checklist reads only the session tenant's state.

<!-- check:data-exposure -->
### Server boundary and data exposure

No case data exists at this stage. The first owner's contact details are visible only to platform staff on the draft and to the tenant's admins after activation; drafts are deleted after 30 days.

<!-- check:session -->
### Sessions in the browser

Platform console session rules (15 min idle, 8 h absolute) apply; because drafts are server-side, an expired session loses nothing.

<!-- check:resilience -->
### Failure, deploys and version skew

Drafts survive browser crashes and releases; provisioning runs in Temporal and continues if the operator closes the tab; the lifecycle page reconstructs progress from the status query.

<!-- check:accessibility -->
### App-level accessibility mechanics

Stepper follows [[PKG-stepper-and-multi-step-form]]; each step has an error summary that receives focus; previously entered information is not requested again (WCAG 2.2 3.3.7).

<!-- check:residency -->
### Region, residency and telemetry privacy

The target region is chosen explicitly and the workflow runs only in that region; the draft is held in the platform-admin host's region, which must match the chosen region (the wizard on the India console can only provision India tenants).

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Understanding Success Criterion 3.3.7: Redundant Entry",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html",
    "version": "2.2"
  }
]
```

<!-- end -->
