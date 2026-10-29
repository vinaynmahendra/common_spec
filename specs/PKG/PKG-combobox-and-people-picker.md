---
id: "PKG-combobox-and-people-picker"
title: "Combobox and people picker"
parent: "PKG-ui-design-system"
order: 4
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Searchable picker for parties, counsel and neutrals with server-side, tenant-scoped search"
links: []
rev: 2
syncHash: "7f646eb3e0e323ca"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.4 Combobox and people picker

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Searchable picker for parties, counsel and neutrals with server-side, tenant-scoped search

<!-- section:purpose -->
## Purpose and when to use

`Combobox` is a text input with a popup list for choosing one or many options with search. `PeoplePicker` is a preset for choosing parties, counsel, neutrals and secretariat staff from server-side, tenant-scoped search (for example appointing an arbitrator from the tenant's panel, adding co-counsel to a case). Follows the APG Combobox pattern with a listbox popup [R1]. Use `Select` for short static lists.

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element / role |
|---|---|---|
| Label | Yes | `<label>` |
| Input | Yes | `<input role="combobox" aria-expanded aria-controls aria-autocomplete="list">` |
| Toggle button | No | `IconButton` "Show options", `tabIndex=-1` |
| Popup | Yes | `role="listbox"` |
| Option | Yes | `role="option"` with `aria-selected`; people options show name, role, organisation and a conflict flag |
| Selected chips (multi) | When `multiple` | List of tags each with a remove `IconButton` |
| Status line | Yes | Polite live region: "5 results", "No neutrals match", "Searching…" |

<!-- section:variants -->
## Variants and sizes

Single or multiple selection; static options or async loader; `PeoplePicker` adds avatar initials, role badge and an optional "Not available" or "Conflict declared" indicator (text + icon) driven by data from [[DOM-neutrals]].

<!-- section:states -->
## States

| State | Visual | Announced |
|---|---|---|
| Closed | Input | Name, value |
| Open with results | Popup, first option not auto-selected | Count of results |
| Option active | `selected` background + 2 px inline-start bar | Via `aria-activedescendant` |
| Loading | Spinner in status line after 300 ms | "Searching…" once |
| No results | Text in popup | "No results for {query}" |
| Error | Inline error in popup with Retry | Error text |
| Option disabled (for example conflicted neutral) | Muted, reason shown | `aria-disabled` with reason in description |
| Invalid | Field error styling | As form fields |

<!-- section:api -->
## Props API

```ts
type Option<T> = { id: string; label: string; description?: string; disabled?: boolean; disabledReason?: string; data: T };
type Loader<T> = (query: string, signal: AbortSignal) => Promise<{ options: Option<T>[]; truncated: boolean }>;

type ComboboxBase<T> = FieldCommon & {
  loader?: Loader<T>;                // async mode; caller supplies a tRPC-backed function
  options?: Option<T>[];             // static mode
  minQueryLength?: number;           // default 2 in async mode
  debounceMs?: number;               // default 250
  renderOption?: (o: Option<T>) => ReactNode;  // text-only slot; no HTML strings
};
export type ComboboxProps<T> = ComboboxBase<T> & (
  | { multiple?: false; value: Option<T> | null; onValueChange: (v: Option<T> | null) => void }
  | { multiple: true; value: Option<T>[]; onValueChange: (v: Option<T>[]) => void; maxSelected?: number }
);
export type PeoplePickerProps = Omit<ComboboxProps<PersonSummary>, 'renderOption'> & {
  roles: Array<'party' | 'counsel' | 'neutral' | 'secretariat'>;
  caseId?: string;                   // passed to the loader for conflict and ethical-wall filtering
};
```
`loader` and `options` are mutually exclusive (union in the real types). `PersonSummary` contains only display fields (id, display name, role, organisation, availability flag); never email or phone.

<!-- section:behaviour -->
## Behaviour

Search is server-side: the `loader` calls a tRPC procedure (for example `neutrals.searchForAppointment`) that runs inside the tenant transaction with RLS ([[MT-isolation-strategy]]) and applies ethical walls ([[PKG-ethical-walls-conflict-based]]) and case permissions ([[PKG-rbac-abac-case-level-party]]). The client never filters a downloaded full list. Requests are debounced (250 ms), cancelled with `AbortSignal` when the query changes, and limited to 50 results with "Refine your search" when `truncated`. TanStack Query keys are built by the caller as `['people', tenantId, userId, roles, caseId, query]` per [[APP-client-state-and-data-fetching]]. Client component.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

| Key | Action |
|---|---|
| Down / Up | Open popup; move active option |
| Enter | Select active option (multi: toggle) |
| Escape | Close popup; second Escape clears input |
| Home / End | Move caret in input |
| Backspace in empty input (multi) | Focus the last chip; again removes it |
| Tab | Close popup and move on without selecting |

Focus stays in the input; the active option is conveyed with `aria-activedescendant`. After removing a chip, focus moves to the next chip or the input. Result counts are announced politely, at most once per completed search. WCAG: 1.3.1, 2.1.1, 2.4.3, 4.1.2, 4.1.3 [R2].

<!-- section:content -->
## Content guidelines

Label names the role: "Arbitrator", "Co-counsel". Hint explains scope: "Search the institution's panel by name or specialisation". No-results text suggests the next step: "No neutrals match. Check the spelling or search by surname."

<!-- section:tokens -->
## Tokens used

Field tokens plus `listbox.bg` (`surface.overlay`), `listbox.option.bg.active`, `listbox.option.indicator` (2 px brand bar), `elevation.2`, `radius.lg`, `chip.bg`, `chip.fg`.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md` the popup becomes a full-screen sheet with its own search input and a Done button, keeping the same roles. Options wrap long names and organisations; no truncation of names.

<!-- section:examples -->
## Usage examples

```tsx
<PeoplePicker label={t('appointment.arbitrator')} roles={['neutral']} caseId={caseId}
  loader={(q, signal) => trpc.neutrals.searchForAppointment.query({ caseId, q }, { signal })}
  value={arbitrator} onValueChange={setArbitrator} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: interaction tests with a mocked loader for debounce, cancellation and truncation; 200-option and 0-option stories; screen reader check that counts are announced once.

<!-- section:questions -->
## Open questions

- [ ] Should neutrals with declared conflicts be hidden or shown as disabled with the reason (proposed: shown disabled for secretariat, hidden for parties) (owner: domain lead, neutrals; legal).
- [ ] Minimum query length of 2 characters for CJK names may be too high; confirm 1 for CJK locales (owner: i18n lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

APG combobox with listbox popup, `aria-activedescendant` for the active option, polite single announcement of result counts, disabled options carry a reason, mobile sheet keeps the same roles.

<!-- check:api-design -->
### API design and misuse resistance

Single and multiple modes are a discriminated union; `loader` and `options` are mutually exclusive; `renderOption` returns React nodes, not HTML strings.

<!-- check:security -->
### Data safety in the component

The fetch is injected by the caller and runs server-side under RLS, ethical walls and case permissions; options carry display data only (no email or phone); query keys include tenant and user; nothing is filtered client-side from a full list.

<!-- check:resilience -->
### Async, errors and edge cases

Requests are cancelled on new input; errors show inline with Retry; truncated results ask for refinement; selection survives a failed search.

<!-- check:performance -->
### Performance and bundle cost

Debounced server search capped at 50 results means typing cost does not grow with panel size (target INP under 200 ms p75 for a panel of 10,000 neutrals); options list is virtualised above 100 rows.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WAI-ARIA APG",
    "kind": "standard",
    "title": "ARIA Authoring Practices Guide: Patterns",
    "url": "https://www.w3.org/WAI/ARIA/apg/patterns/"
  },
  {
    "body": "W3C",
    "excerpt": "Status messages can be programmatically determined so that assistive technologies can present them without receiving focus.",
    "id": "R2",
    "ident": "WCAG 2.2 SC 4.1.3",
    "kind": "standard",
    "title": "Understanding SC 4.1.3 Status Messages",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/status-messages"
  }
]
```

<!-- end -->
