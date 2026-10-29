---
id: "PKG-status-and-deadline-badges"
title: "Status and deadline badges"
parent: "PKG-ui-design-system"
order: 12
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Case stage, document status and deadline countdown, never colour alone"
links: []
rev: 2
syncHash: "c1359224c95666e0"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.12 Status and deadline badges

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Case stage, document status and deadline countdown, never colour alone

<!-- section:purpose -->
## Purpose and when to use

`StatusBadge` shows the current status of a case, document, invoice or task; `DeadlineBadge` shows when something is due and how long is left. Used in the case list, case header, document list and transcriber queue. Both always combine text and an icon with colour, so meaning never depends on colour alone (WCAG 1.4.1) [R1].

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Container | Yes | `<span>` (not a live region, not interactive) |
| Icon | Yes | Tone icon `aria-hidden` |
| Label | Yes | Status label ("Awaiting response") or deadline text ("Due in 3 days") |
| Full text (deadline) | Yes | Visually hidden or tooltip-free text: "Response due Friday 7 November 2026, 5:00 pm IST, 3 days left" |

<!-- section:variants -->
## Variants and sizes

`StatusBadge` tones: the seven tones in [[PKG-colour-and-contrast#colour]]. The status → tone and status → label mapping comes from the entity state machine definition ([[WF-entity-state-machines]]), not from the calling page. `DeadlineBadge` thresholds (proposed; tenant-configurable within limits):

| Remaining | Tone | Text |
|---|---|---|
| More than 7 days | neutral | "Due 14 Nov" |
| 7 days or less | attention | "Due in 5 days" |
| 48 hours or less | critical | "Due in 30 hours" |
| Overdue | critical, with "Overdue" text | "Overdue by 2 days" |
| Met | success | "Filed on time" |
| Extended | info | "Extended to 21 Nov" |

Sizes: `sm` (tables) and `md` (headers).

<!-- section:states -->
## States

Static. `DeadlineBadge` updates its text at most once per minute while on screen (not announced; if a deadline passes while the user is on the page, a polite announcement "The response deadline has passed" is made once by the page, not by every badge).

<!-- section:api -->
## Props API

```ts
export type StatusBadgeProps = { tone: StatusTone; label: string; size?: 'sm' | 'md' };   // label required
export type DeadlineBadgeProps = {
  dueAt: string; timeZone: string;            // instant + zone the deadline is defined in
  viewerTimeZone: string;
  state?: 'open' | 'met' | 'extended';
  extendedTo?: string;
  thresholds?: { attentionDays: number; criticalHours: number };  // defaults 7 and 48
  label: string;                              // what is due: "Response"
  size?: 'sm' | 'md';
};
```
Remaining time is computed from server time offset (provided by `UiProvider`) so a wrong device clock does not change the badge. Business-day wording ("3 working days left") is used when the rule set counts business days; the count comes from [[PKG-calendars-and-deadline]] via props, never computed in the component.

<!-- section:behaviour -->
## Behaviour

Server component by default (renders the text at request time); a small client update loop only when the badge is on screen and within 48 hours.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

Not focusable. Full text is available to screen readers; the visible short text is a substring of it. WCAG: 1.3.1, 1.4.1, 1.4.3 (each tone pair is in the manifest at 4.5:1).

<!-- section:content -->
## Content guidelines

Labels come from the state machine catalogue and tenant terminology. Deadlines always show the absolute date in the full text; relative text alone is never used in legal contexts.

<!-- section:tokens -->
## Tokens used

`color.status.{tone}.{fg,bg}`, `badge.radius` (radius.sm), `badge.padding`, `typography.label.md` (sm size: `font.size.xs` weight 600). High contrast: outlined with 2 px tone border.

<!-- section:responsive -->
## Responsive behaviour and direction

Badges wrap to a new line rather than truncating; in tables the short text is shown with full text for screen readers.

<!-- section:examples -->
## Usage examples

```tsx
<StatusBadge tone={stateMeta.tone} label={t(stateMeta.labelKey)} />
<DeadlineBadge label={t('deadline.response')} dueAt={d.dueAt} timeZone={d.timeZone} viewerTimeZone={userTz} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: unit tests for threshold boundaries and time-zone display; forced-colours snapshot shows icon and text.

<!-- section:questions -->
## Open questions

- [ ] Should deadline thresholds be tenant-configurable (proposed: yes, within 1–14 days and 12–72 hours) (owner: product).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Text and icon always present; full text with absolute date and zone for screen readers; tone pairs at 4.5:1 or better in all modes; outlined in high contrast.

<!-- check:api-design -->
### API design and misuse resistance

`label` is required; tone and label mappings come from the state machine metadata so pages cannot invent statuses.

<!-- check:i18n -->
### Localisation and long content

Absolute date in the viewer's zone and locale, with the defining zone shown when it differs; plural rules via ICU for "1 day" and "3 days".

<!-- check:resilience -->
### Async, errors and edge cases

Uses server time offset, not the device clock; business-day counts come from the calendars package.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Colour is not used as the only visual means of conveying information.",
    "id": "R1",
    "ident": "WCAG 2.2 SC 1.4.1",
    "kind": "standard",
    "title": "Understanding SC 1.4.1 Use of Color",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/use-of-color"
  }
]
```

<!-- end -->
