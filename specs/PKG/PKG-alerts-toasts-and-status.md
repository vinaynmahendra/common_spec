---
id: "PKG-alerts-toasts-and-status"
title: "Alerts, toasts and status messages"
parent: "PKG-ui-design-system"
order: 9
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Inline alerts, toasts and live-region announcements"
links: []
rev: 2
syncHash: "b7c1ecea705b9e05"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.9 Alerts, toasts and status messages

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Inline alerts, toasts and live-region announcements

<!-- section:purpose -->
## Purpose and when to use

Three ways to tell users something happened: `Alert` (inline, persistent, in the page flow: form error summary, "Payment overdue" on the case page), `Toast` (short-lived confirmation of an action the user just took: "Draft saved") and `Announcer` (screen-reader-only status messages for changes that are visible but not focused: "12 results"). Implements WCAG 4.1.3 Status Messages [R1]. Important information never appears only in a toast.

<!-- section:anatomy -->
## Anatomy

| Part | Alert | Toast | Announcer |
|---|---|---|---|
| Container | `<div role="alert">` for critical errors after an action; otherwise `<div>` with heading, not a live region | Item inside `ToastRegion` (`<section aria-label="Notifications">` with `role="status"` live list) | Two visually hidden live regions (`polite`, `assertive`) mounted once by `UiProvider` |
| Icon | Tone icon, `aria-hidden` | Tone icon | — |
| Title | Optional `<h2>`–`<h4>` | — | — |
| Message | Yes | Yes (max about 80 characters) | Text |
| Action | Optional link or button | Optional single action (Undo, View, Retry) | — |
| Dismiss | Optional | Yes (`IconButton` "Dismiss notification") | — |

<!-- section:variants -->
## Variants and sizes

Tones: `info`, `success`, `warning`, `critical`, using feedback tokens. Alert styles: `inline` (inside a section) and `banner` (page-level, below header, for tenant-wide notices such as planned maintenance).

<!-- section:states -->
## States

Toast lifecycle: enter → visible → paused (on hover or focus) → exit. Default visible time 8 seconds for success and info; `warning` and `critical` toasts do not auto-dismiss. Toasts with an action stay at least 10 seconds and pause on focus (WCAG 2.2.1). Maximum 3 visible; older ones collapse into "2 more notifications".

<!-- section:api -->
## Props API

```ts
export type AlertProps = { tone: Tone; title?: string; headingLevel?: 2 | 3 | 4; children: ReactNode; action?: ReactNode; onDismiss?: () => void; announce?: 'none' | 'polite' | 'assertive' };
export function useToast(): { show(t: { tone: Tone; message: string; action?: { label: string; onPress: () => void }; durationMs?: number }): string; dismiss(id: string): void };
export function useAnnouncer(): { announce(message: string, politeness?: 'polite' | 'assertive'): void };
```
`announce` defaults to `none` on `Alert` because most alerts are present at page load; set `assertive` only for errors that result from the user's last action.

<!-- section:behaviour -->
## Behaviour

`useAnnouncer` de-duplicates identical messages within 1 second and queues others so they are not cut off. Toasts are rendered into the single `ToastRegion` in the root layout. Server-rendered alerts (for example "Your response is due in 2 days") are plain content, not live regions. Notifications about events by other users (a new filing by the other party) go to the in-app notification centre from [[PKG-notifications]], not to toasts.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

Toasts do not take focus. A keyboard shortcut (F6 cycles landmarks; plus Alt+T proposed) moves focus to the toast region if a toast has an action. Dismiss buttons are reachable by Tab when focus is in the region. After a toast is dismissed with focus inside, focus returns to where it was before. WCAG: 1.3.1, 2.2.1, 4.1.3.

<!-- section:content -->
## Content guidelines

Lead with the outcome: "Response filed. Receipt RCP-2026-0918 sent to all parties." Errors say what to do next. No exclamation marks, no blame. Copy from [[APP-voice-tone-and-content-style]] and [[APP-error-message-catalogue]].

<!-- section:tokens -->
## Tokens used

`color.feedback.{tone}.{fg,bg,border}`, `elevation.3` (toasts), `radius.md`, `space.inset.md`, `motion.duration.base`, `motion.easing.standard`.

<!-- section:responsive -->
## Responsive behaviour and direction

Toasts appear bottom-centre on narrow screens above any sticky footer, bottom inline-end on wide screens; never covering the focused element (2.4.11).

<!-- section:examples -->
## Usage examples

```tsx
<Alert tone="warning" title={t('fees.dueTitle')}>{t('fees.dueBody', { date })}<ButtonLink href={payHref}>{t('fees.pay')}</ButtonLink></Alert>
const { show } = useToast(); show({ tone: 'success', message: t('draft.saved') });
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: screen reader verification that toasts and announcer messages are read once (NVDA and VoiceOver handle live regions differently, so this is a manual check each release).

<!-- section:questions -->
## Open questions

- [ ] Agree the keyboard shortcut for reaching toasts and check it does not clash with screen reader shortcuts (owner: accessibility lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Status messages use pre-mounted live regions so they are announced without focus; critical action errors use `role="alert"`; toasts never take focus, pause on hover and focus, and warning or critical toasts do not auto-dismiss.

<!-- check:i18n -->
### Localisation and long content

Messages are passed in already translated; toast width grows with text up to 28rem and wraps; region label "Notifications" comes from `UiMessages`; layout mirrors in RTL.

<!-- check:security -->
### Data safety in the component

Toast and alert messages are text props, never HTML; messages about other users' actions go through the notification centre with its permission checks.

<!-- check:resilience -->
### Async, errors and edge cases

Announcer de-duplicates and queues; at most 3 toasts are visible; important information is never only in a toast.

<!-- check:testing -->
### Test and documentation coverage

Stories for each tone × alert style, toast with and without action, queue of 5 toasts, announcer de-duplication; interaction tests that toasts never take focus and pause on focus; visual matrix as for all components; manual NVDA and VoiceOver check each release that each message is read exactly once.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Status messages can be programmatically determined so that assistive technologies can present them without receiving focus.",
    "id": "R1",
    "ident": "WCAG 2.2 SC 4.1.3",
    "kind": "standard",
    "title": "Understanding SC 4.1.3 Status Messages",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/status-messages"
  }
]
```

<!-- end -->
