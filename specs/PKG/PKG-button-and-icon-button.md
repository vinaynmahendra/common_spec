---
id: "PKG-button-and-icon-button"
title: "Button and icon button"
parent: "PKG-ui-design-system"
order: 2
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Primary, secondary, danger and icon-only buttons with loading state and accessible names"
links: []
rev: 2
syncHash: "7c5c316836e4e9a3"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.2 Button and icon button

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Primary, secondary, danger and icon-only buttons with loading state and accessible names

<!-- section:purpose -->
## Purpose and when to use

`Button` triggers an action; `IconButton` is the same with only an icon visible. Used everywhere: "File submission", "Save draft", "Issue award", toolbar actions in the document viewer and row actions in the secretariat queue. Use a link (`<a>` via `Link`) for navigation, not a button. Use `ConsequentialConfirmDialog` ([[PKG-modal-dialog-and-consequential]]) in front of any button whose action has legal or financial effect. APG pattern: Button [R1]; native `<button>` is always used.

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Root | Yes | `<button type="button">` (or `type="submit"` when `type` prop says so) |
| Start icon | No | `<Icon aria-hidden>` |
| Label | Yes for `Button` | Text node |
| End icon | No | `<Icon aria-hidden>` (for example external, chevron) |
| Spinner | When `loading` | `<span aria-hidden>` with motion token |
| Accessible name for `IconButton` | Yes | `aria-label` from the required `label` prop; also shown as tooltip |

<!-- section:variants -->
## Variants and sizes

| Variant | Use | Limit |
|---|---|---|
| `primary` | The main action on a view (File, Save, Pay) | One per view or dialog |
| `secondary` | Other actions (Cancel, Add another party) | |
| `tertiary` (text style) | Low-emphasis actions in dense areas | Still has a visible focus ring and 24 px target |
| `danger` | Destructive or irreversible actions (Withdraw claim, Delete draft) | Usually opens a confirmation |

Sizes: `sm` (32 px, compact density only), `md` (40 px, default), `lg` (48 px, party pages on mobile). `IconButton` sizes are square and never below `size.target.min` (24 px); in `sm` the hit area is padded to 24 px even if the visible icon is 16 px.

<!-- section:states -->
## States

| State | Visual | Announced |
|---|---|---|
| Default | Variant tokens | Role button, name |
| Hover | `*.bg.hover` | — |
| Pressed | `*.bg.pressed` | `aria-pressed` only for toggle buttons |
| Focus-visible | 2 px `focus.ring` outline, 2 px offset | — |
| Loading | Spinner replaces start icon, label stays, width fixed | `aria-busy="true"`; announcement via `useAnnouncer` of the caller-supplied `loadingText` (for example "Filing your submission") |
| Disabled | `text.disabled`, no pointer events | `aria-disabled="true"`; stays focusable when `disabledReason` given, with the reason as `aria-describedby` |
| Toggle on / off | `selected` tokens | `aria-pressed="true|false"` |

<!-- section:api -->
## Props API

```ts
type ButtonBaseProps = {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'danger';   // default 'secondary'
  size?: 'sm' | 'md' | 'lg';                                   // default 'md'
  type?: 'button' | 'submit' | 'reset';                        // default 'button'
  loading?: boolean;
  loadingText?: string;              // required when loading can be true; enforced by lint
  disabled?: boolean;
  disabledReason?: string;           // keeps the button focusable and explains why
  onPress?: (e: PressEvent) => void; // pointer, keyboard and touch unified
  form?: string;
  'data-testid'?: string;
} & AriaPassthrough;                 // aria-describedby, aria-controls, aria-expanded, aria-haspopup

export type ButtonProps = ButtonBaseProps & { children: ReactNode; startIcon?: IconName; endIcon?: IconName };
export type IconButtonProps = ButtonBaseProps & { icon: IconName; label: string };   // label required
export type ToggleButtonProps = ButtonProps & { pressed: boolean; onPressedChange: (p: boolean) => void };
```

`ref` forwards to the `<button>`. No `className`, `style` or `asChild`. Links that look like buttons use `<ButtonLink href>` with the same visual props, rendered as `<a>`.

<!-- section:behaviour -->
## Behaviour

`onPress` is ignored while `loading` or `disabled`, which prevents double submission. Buttons are server-component safe when they have no handler (`type="submit"` inside a Server Action form); handlers make them client components. In a React Hook Form form, the submit button shows `loading` while `formState.isSubmitting`. Spinner appears only after 300 ms of loading to avoid flashes.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

| Key | Action |
|---|---|
| Enter, Space | Activate |
| Tab / Shift+Tab | Move focus in DOM order |

Native button semantics, accessible name from visible label (`Button`) or `label` (`IconButton`) [R2]. Label in name: an `IconButton` tooltip shows the same text as `aria-label`, so voice control users can say it (2.5.3). Focus stays on the button after activation unless the action opens a dialog or navigates. WCAG: 2.1.1, 2.4.7, 2.5.3, 2.5.8 (24 px target) [R3], 4.1.2.

<!-- section:content -->
## Content guidelines

Labels are verb-first and specific: "File response", "Pay fee", "Issue award", not "Submit" or "OK". Maximum about 30 characters in English to allow 40 percent expansion. Danger labels name the consequence: "Withdraw claim". Labels come from the app's message catalogue; tenants can override some labels through [[PKG-tenant-terminology-and-copy]] (for example "File" → "Lodge"), but not danger labels.

<!-- section:tokens -->
## Tokens used

`button.{variant}.bg.{default,hover,pressed}`, `button.{variant}.fg`, `button.{variant}.border`, `color.focus.ring`, `focus.ring.width`, `focus.ring.offset`, `size.control.height`, `size.target.min`, `radius.md`, `space.inset.md`, `typography.label.md`, `motion.duration.fast`. New component tokens: `button.tertiary.fg` (aliases `color.text.link`).

<!-- section:responsive -->
## Responsive behaviour and direction

At narrow widths, button groups in dialogs and the filing wizard stack vertically, primary last (closest to the thumb on mobile). Labels wrap rather than truncate. In RTL, start / end icons swap sides automatically.

<!-- section:examples -->
## Usage examples

```tsx
<Button variant="primary" type="submit" loading={isSubmitting} loadingText={t('filing.submitting')}>{t('filing.submit')}</Button>
<IconButton icon="download" label={t('document.download', { name: doc.title })} onPress={download} />
```
Don't: use `IconButton` without a label, put two primary buttons side by side, or disable the submit button to signal validation errors (show errors instead).

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: loading prevents a second `onPress` (interaction test double-clicks); `disabledReason` is announced; target size is at least 24 × 24 in `sm`.

<!-- section:questions -->
## Open questions

- [ ] Do we allow disabled buttons at all in party journeys, or always keep them enabled and show validation (proposed: avoid disabled) (owner: product design).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Native `<button>` only; name from visible text or the required `label`; tooltip text equals `aria-label`; loading sets `aria-busy` and announces `loadingText`; `disabledReason` keeps the control focusable with a description; minimum 24 px target in every size; outline-based focus ring survives forced colours.

<!-- check:api-design -->
### API design and misuse resistance

`IconButton` requires `label` at compile time; `ToggleButton` requires `pressed` and `onPressedChange` together; no `className` or `asChild`; navigation uses `ButtonLink`. Naming follows library conventions (`onPress`, `variant`, `size`).

<!-- check:theming -->
### Tenant themes and modes

Primary uses brand-derived `action.primary.*` tokens validated by [[PKG-tenant-theme-accessibility]]; danger and focus tokens are locked.

<!-- check:resilience -->
### Async, errors and edge cases

`onPress` is ignored while loading, preventing double filing or double payment; spinner only after 300 ms.

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
    "id": "R2",
    "ident": "AccName 1.2",
    "kind": "standard",
    "title": "Accessible Name and Description Computation 1.2",
    "url": "https://www.w3.org/TR/accname-1.2/"
  },
  {
    "body": "W3C",
    "excerpt": "Targets are at least 24 by 24 CSS pixels, with listed exceptions such as spacing.",
    "id": "R3",
    "ident": "WCAG 2.2 SC 2.5.8",
    "kind": "standard",
    "title": "Understanding SC 2.5.8 Target Size (Minimum)",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum"
  }
]
```

<!-- end -->
