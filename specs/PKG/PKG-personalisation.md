---
id: "PKG-personalisation"
title: "User personalisation"
parent: "PKG-settings"
order: 2
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Personal settings area and per-user workspace shaping: saved views, dashboards, default filters, layout, shortcuts, language, time zone, formats, appearance and accessibility, with tenant and unit defaults that never override accessibility choices"
links: []
rev: 1
syncHash: "ee52afefd88ccfbc"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.2 User personalisation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Personal settings area and per-user workspace shaping: saved views, dashboards, default filters, layout, shortcuts, language, time zone, formats, appearance and accessibility, with tenant and unit defaults that never override accessibility choices

<!-- section:scope -->
## Scope, audiences and surfaces

Personalisation lets each person shape their own workspace without affecting anyone else: saved views, personal and shared dashboards, default filters, layout, keyboard shortcuts, language, time zone, date formats, appearance and accessibility preferences, notification preferences and connected accounts. It is a shared frontend capability used by every authenticated route group ([[APP-route-groups-per-persona]]); settings keys are in [[PKG-settings-personal]] and resolution follows [[PKG-configuration-scope-hierarchy]].

| Surface | Personas | What they can personalise |
|---|---|---|
| Personal settings `/me/settings/*` | every signed-in user | Profile display, language and region, appearance, accessibility, notifications, shortcuts, connected accounts, saved views and dashboards list |
| Lists and queues (case list, secretariat queues, transcriber queue, document lists, admin tables) | `secretariat`, `neutral`, `transcriber`, `counsel`, admins | Saved views (filters, sort, columns, grouping), default view per list, page size, density where allowed |
| Home dashboards | `secretariat`, `neutral`, `counsel`, `tenant_admin`, `unit_admin`, `auditor` | Personal dashboards built from approved widgets; tenant- or unit-published dashboards they may copy |
| Case workspace | `secretariat`, `neutral`, `counsel` | Panel layout (timeline, documents, tasks), pinned cases, case watch / mute |
| Party portal | `party` | Language, time zone, text and motion preferences, notification channels; no shortcuts, no dashboards (simplicity for unrepresented parties, [[DOC-plain-language-guidance-for]]) |

Tenant and unit administrators set **defaults** for their members (for example the default case-list view for the SEBI ODR desk) and may **publish shared views and dashboards**; they cannot see or change an individual's personal views. Administrators may lock some defaults (for example a mandatory column), but **never accessibility, language or time-zone preferences** (see [[PKG-settings-personal#validation]]).

Out of scope: tenant branding and default locale ([[PKG-branding-and-theming]], [[PKG-settings-branding-content]]), colour-mode mechanics ([[PKG-colour-modes-and-user]]), notification policy ([[PKG-notification-policies]]), sign-in and session security settings ([[PKG-mfa-session-management-device]]), AI assistant preferences ([[PKG-settings-ai]]).

Pattern borrowed from: a single, flat personal settings area with clear sections and per-workspace preferences, as in Linear and Notion; shortcuts with a discoverable command palette.

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(account)/me/settings/                 # rendered inside the shell of the user's active persona
  layout.tsx                               # requireSession(); left nav of sections; no tenant-admin access needed
  page.tsx                                 # redirect to ./profile
  profile/page.tsx                         # display name, pronouns (optional), avatar, contact points (links to identity)
  language-and-region/page.tsx             # language, time zone, date/time/number formats, week start
  appearance/page.tsx                      # mode, density (where allowed), sidebar, start page
  accessibility/page.tsx                   # motion, links, targets, focus, captions, announcements, timeout warnings
  notifications/page.tsx                   # channels, opt-ins with consent, quiet hours, digest, per-event toggles
  shortcuts/page.tsx                       # list, turn off single-key shortcuts, remap
  views/page.tsx                           # saved views and dashboards: rename, share, set default, delete
  connected-accounts/page.tsx              # calendar and other per-user connections (INT-connections-admin)
  loading.tsx  error.tsx
app/(secretariat)/cases/page.tsx?view=<viewId>   # every list accepts ?view= and explicit filter params
app/(secretariat)/home/page.tsx?dashboard=<id>
app/(tenant-admin)/admin/personalisation/  # tenant defaults, shared views and dashboards, widget catalogue, locks
app/(tenant-admin)/admin/organisation/units/[unitId]/personalisation/
```

`proxy.ts` does nothing personalisation-specific except pass the `nm_appearance` and `nm_locale` cookies through. The `(account)` group reuses the active persona's layout so a secretariat user stays in the secretariat shell; party users get the simplified party shell with only the sections that apply to them. Assumption: the `(account)` route group is added to the persona map in [[APP-route-groups-per-persona]] (owner: admin group).

<!-- section:rendering -->
## Rendering and caching strategy

| Route / element | Rendering | Cache |
|---|---|---|
| `/me/settings/*` | Dynamic, streamed per request (user-specific) | `Cache-Control: private, no-store`; no shared cache |
| Resolved personal preferences (locale, time zone, formats, appearance, a11y) | Read in the root layout from `nm_appearance` and `nm_locale` cookies, then confirmed from `@nomology/settings` | Per-user cache in [[PKG-caching]] namespace `settings:user:{tenantId}:{userId}`, 5 min, invalidated on write |
| Saved view definitions | Read server-side when a list page renders with `?view=` | Per-user cache key `views:{tenantId}:{userId}:{surface}`, tag `views-user-{userId}`; shared views tag `views-tenant-{tenantId}` |
| Dashboards | Layout read server-side; each widget streams in its own Suspense boundary and fetches its data through the data access layer under the viewer's permissions | Widget data never cached across users; layout cached per user |
| Widget catalogue | Static per release + tenant enablement | Tenant-scoped cache, tag `widgets-tenant-{tenantId}` |

Preferences that change the first paint (mode, density, motion, language, `dir`) are applied on `<html>` in the first byte of HTML as specified in [[PKG-colour-modes-and-user#modes]]; no client script reads `localStorage` before paint.

<!-- section:data -->
## Data fetching and mutations

**Reads**: Server Components call `@nomology/settings` `getMany()` for all `personal.*` keys in one round trip, and `personalisation.views.list(surface)` / `personalisation.dashboards.get(id)` from the data access layer. Client components use tRPC `me.preferences.*`, `me.views.*`, `me.dashboards.*` with TanStack Query keys `['me', tenantId, userId, ...]`.

**Writes**

| Operation | Mechanism | Validation | Effect |
|---|---|---|---|
| Change a preference | Server Action `updatePreference(key, value)` → `settings.set(level: 'user')` | Zod schema from the setting registry; bounds; lock check | Updates cookie mirror for first-paint keys; `revalidateTag('settings-user-{userId}')` |
| Save view | tRPC `me.views.save` | Filter schema of the surface (only fields the list exposes); max 50 views per surface | Optimistic update |
| Share view to unit / tenant | tRPC `me.views.share` | Needs `personalisation.view:publish` at that scope | Shared views are copies with an owner; editing creates a new version |
| Set default view | tRPC `me.views.setDefault` | View must be visible to the user | Stored as `personal.views.default.<surface>` |
| Dashboard layout change | tRPC `me.dashboards.updateLayout` (debounced 1 s) | Widget keys from the catalogue; max 12 widgets | |
| Opt in to SMS / WhatsApp | Server Action with consent capture | Phone verified by OTP; consent text version from [[I18N-legal-declaration-and-consent]] | Consent record via [[SEC-consent-and-notice-management]] |
| Connect calendar | Redirect to OAuth start | Tenant allows `user_connected` | See [[INT-connections-admin]] |

**Data model** (tenant-owned, forced RLS; personal settings themselves are `setting_value` rows at level `user` in [[PKG-settings-data-model]]):

```prisma
model SavedView {
  id          String   @id @db.Uuid
  tenantId    String   @db.Uuid
  ownerUserId String?  @db.Uuid          // null for tenant/unit-published views
  surface     String                     // 'secretariat.case_list', 'transcriber.queue', ...
  name        String   @db.VarChar(80)
  definition  Json                       // { filters, sort, columns, groupBy, pageSize } validated per surface schema
  visibility  String                     // 'private' | 'unit' | 'tenant'
  unitId      String?  @db.Uuid
  locked      Boolean  @default(false)   // tenant-published views can be locked against edits, never forced on a user
  version     Int      @default(1)
  updatedAt   DateTime @updatedAt
  @@index([tenantId, ownerUserId, surface])
}
model Dashboard { id String @id @db.Uuid; tenantId String @db.Uuid; ownerUserId String? @db.Uuid; name String; visibility String; unitId String? @db.Uuid; layout Json; version Int }
model CaseWatch { tenantId String @db.Uuid; userId String @db.Uuid; caseId String @db.Uuid; state String /* 'pinned'|'watching'|'muted' */; @@id([tenantId, userId, caseId]) }
```

A saved view stores filter definitions, never result rows, so a shared view always re-runs under the viewer's own permissions. Muting a case affects only `transactional` and `reminder` notifications for that case; mandatory and legal notices still arrive.

<!-- section:state -->
## Client state and URL state

| State | Where | Cleared on sign-out / tenant switch |
|---|---|---|
| Effective preferences | Server (settings) + cookie mirror for first-paint keys | Cookie kept (no personal data, values only); server cache keyed by tenant and user |
| Current list filters | URL search params (shareable, bookmarkable); the saved view ID is `?view=` | URL only |
| Unsaved view edits | URL + "modified" badge; `sessionStorage` draft keyed by tenant, user and surface | Cleared |
| Dashboard layout while editing | Local component state, persisted on save | Discarded |
| Command palette history | Memory only | Cleared |
| TanStack Query `['me', ...]` cache | Client | Cleared on sign-out and tenant switch ([[APP-client-state-and-data-fetching]]) |

Preferences are stored per tenant membership. A user may choose "Use these language, time-zone and accessibility settings in all my organisations in this region"; this writes the same values to each membership in the region and never crosses regions.

<!-- section:forms -->
## Forms, validation and uploads

All settings forms use React Hook Form with the Zod schema generated from the setting registry, so client and server validate identically; the server re-validates and checks locks and bounds. Each control shows: current value, its source ("Your choice", "Default from Singapore office", "Set by your organisation"), and a "Reset to default" action. Locked values appear read-only with the reason. Changes save per control (no global Save button) with an inline "Saved" status announced politely to screen readers; failures roll back the control and show the error next to it. The SMS and WhatsApp opt-in flows are two-step (verify the number with OTP, then confirm consent wording), and withdrawal is a single action, as easy as giving consent ([[SEC-consent-and-notice-management]]).

<!-- section:errors -->
## Error, loading and empty handling

| Error | Handling |
|---|---|
| `SettingLockedError` | Control shows locked state with source; no toast |
| `SettingOutOfBoundsError` / validation | Inline field error with the allowed range |
| View references a field no longer available (schema change) | View opens with that filter removed and a banner "1 filter was removed because it is no longer available" |
| Shared view or dashboard deleted | Falls back to the user's or tenant's default view, with a notice |
| Widget data permission denied | Widget shows "You do not have access to this information" (identical to not-found text, [[APP-error-message-catalogue]]) |
| Widget data error | Widget-level error boundary with retry; other widgets unaffected |
| Session expired while editing | Standard re-authentication flow; preference edits are single-field so nothing is lost |
| Loading | Skeletons per section and per widget; no layout shift for list pages because column definitions resolve server-side |

<!-- section:performance -->
## Performance budgets

- Personal preference resolution adds ≤ 5 ms p95 server time (one cached `getMany`), 0 client JavaScript for first-paint preferences.
- `/me/settings/*` pages: LCP ≤ 2.0 s p75, INP ≤ 200 ms, JS ≤ 120 KB gzipped per route, on the mid-range Android, 4G profile used by [[APP-frontend-performance-budgets]].
- Applying a saved view: server render of a list with the view ≤ 300 ms p95 additional to the list's own budget; view definitions limited to 20 filters to keep queries index-friendly.
- Dashboards: first widget visible ≤ 1.5 s p75; max 12 widgets; each widget's query has a 2 s server timeout.

<!-- section:security -->
## Security headers and browser session

Inherits headers and nonce-based CSP from the persona route group. Specific rules:
- All `me.*` procedures act only on the session user's own records; the user ID is never accepted from the client.
- Shared views and dashboards contain definitions only; they never grant access. Publishing at unit or tenant scope needs `personalisation.view:publish` with that scope.
- Shortcut remapping cannot bind browser-reserved or assistive-technology keys (list per platform) and is stored as data, never executed.
- Server Actions for consent changes require a recent sign-in (within 30 minutes) for phone number changes.
- No preference value is rendered as HTML; display names and view names are escaped and length-limited.

<!-- section:i18n -->
## Localisation hookup

Locale resolution: user preference (`personal.locale.language`) → unit default → tenant default ([[PKG-settings-branding-content]]) → `Accept-Language` among the tenant's enabled languages → `en`. `lang` and `dir` are set on `<html>` server-side. Time zone: user preference, or `auto` (browser zone detected on first sign-in and confirmed by the user, never silently changed afterwards). Hearing and deadline times show the user's zone and, where different, the seat or hearing zone side by side (`personal.locale.show_dual_time_zones`), using [[PKG-date-and-time-picker-with]]. Date, time and number formats follow the locale unless overridden (for example ISO dates, 24-hour time, Indian digit grouping), formatted with `Intl` per [[I18N-l10n]]. Settings pages themselves are fully translated, including setting descriptions from the registry.

<!-- section:theming -->
## Tenant theming hookup

Personal appearance (mode, density, motion) is applied on top of the tenant theme as defined in [[PKG-colour-modes-and-user]]; high contrast and forced colours ignore tenant brand colours. Tenants set the default mode and may restrict density options per persona, but cannot prevent a user from choosing high contrast or reduced motion.

<!-- section:observability -->
## Frontend observability

Events (pseudonymous, per [[OBS-usage]]): `personalisation.preference_changed` (key only, never value for free-text keys), `personalisation.view_saved`, `personalisation.view_shared`, `personalisation.dashboard_widget_added`, `personalisation.shortcut_disabled`. Adoption dashboards show which defaults users change most, which informs better tenant defaults. Errors in widgets carry widget key and surface, not data.

<!-- section:testing -->
## Testing strategy

- Unit tests for preference resolution with locks and per-membership values.
- Contract tests for `me.*` procedures including attempts to pass another user's ID.
- Playwright per persona: change language and time zone, verify `lang`, `dir` and dual-time display; save, share and apply a view; dashboard edit and reload; single-key shortcut turned off then pressed.
- Accessibility: axe on every settings page; keyboard-only run through all sections; screen reader announcement of "Saved"; 400% zoom reflow.
- Isolation: a user's private views are not listable by another user or an admin; a shared view re-runs under the viewer's permissions (a walled user sees fewer rows).
- Visual regression of settings pages in light, dark, high contrast, compact and RTL.

<!-- section:questions -->
## Open questions

- [ ] Should tenant admins see aggregate (not individual) preference statistics, for example "40% of counsel chose daily digests"? Proposed: yes, aggregated with a minimum group size of 10. (Product + privacy)
- [ ] Remappable shortcuts in Phase 5, or only "turn off single-key shortcuts" (which satisfies WCAG 2.2 SC 2.1.4 [R1]) at first? Proposed: turn-off first, remap later. (Accessibility lead)
- [ ] Do we allow export and import of a user's views between tenants they belong to? Proposed: no; definitions may reference tenant-specific custom fields. (Product)
- [ ] Confirm the `(account)` route group with the admin group's route map. (Admin group)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Saved views, dashboards, case watch rows and user-level settings are tenant-owned under forced RLS and keyed by tenant and user; caches use `tenantId` and `userId` in every key; `/me/settings` responses are `private, no-store`. "Apply to all my organisations" writes per membership and stays in one region.

<!-- check:data-exposure -->
### Server boundary and data exposure

Shared views and dashboards carry definitions only and re-run under the viewer's permissions; widgets fetch through the data access layer with authorisation checks; `me.*` procedures derive the user from the session. Personal views are invisible to admins.

<!-- check:session -->
### Sessions in the browser

Preference changes are low risk and save per field; phone-number and consent changes need recent sign-in; TanStack Query `me` caches are cleared on sign-out and tenant switch.

<!-- check:resilience -->
### Failure, deploys and version skew

Widgets fail independently behind their own error boundaries; a view whose fields disappeared opens with those filters removed; if the settings service is slow, the cookie mirror still renders the right appearance and language.

<!-- check:accessibility -->
### App-level accessibility mechanics

Single-key shortcuts can be turned off (WCAG 2.2 SC 2.1.4) [R1]; timeout warnings can be lengthened (SC 2.2.1); motion, contrast and colour scheme follow both user settings and media queries [R2]; accessibility preferences can never be locked by a tenant; all settings forms meet the form patterns in [[PKG-form-fields]].

<!-- check:residency -->
### Region, residency and telemetry privacy

All personalisation data is stored in the tenant's regional database; cookies hold only preference values; no third-party scripts are used for preferences or dashboards.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Includes SC 2.1.4 Character Key Shortcuts (single-key shortcuts can be turned off or remapped) and SC 2.2.1 Timing Adjustable.",
    "id": "R1",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C",
    "excerpt": "Defines prefers-color-scheme, prefers-reduced-motion, prefers-contrast and forced-colors.",
    "id": "R2",
    "ident": "Media Queries 5",
    "kind": "standard",
    "title": "Media Queries Level 5",
    "url": "https://www.w3.org/TR/mediaqueries-5/"
  }
]
```

<!-- end -->
