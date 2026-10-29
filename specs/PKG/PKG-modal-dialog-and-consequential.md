---
id: "PKG-modal-dialog-and-consequential"
title: "Modal dialog and consequential confirmation"
parent: "PKG-ui-design-system"
order: 8
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Dialog pattern plus confirmation for actions with legal or financial effect (file, issue award, pay)"
links: []
rev: 2
syncHash: "618f4ad51ed60117"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.8 Modal dialog and consequential confirmation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Dialog pattern plus confirmation for actions with legal or financial effect (file, issue award, pay)

<!-- section:purpose -->
## Purpose and when to use

`Dialog` is a modal window for short focused tasks (edit party details, add a note). `ConsequentialConfirmDialog` is a preset that stands in front of any action with legal or financial effect: filing a submission, issuing an award or procedural order, paying a fee, withdrawing a claim, appointing a neutral, serving a notice. It shows exactly what will happen, to whom, and that it cannot be undone, and may require a typed confirmation or step-up authentication ([[PKG-mfa-session-management-device]]). APG pattern: Dialog (Modal); native `<dialog>` with `showModal()` [R1].

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Backdrop | Yes | `::backdrop` |
| Container | Yes | `<dialog aria-labelledby aria-describedby>` (role dialog; `alertdialog` for consequential) |
| Title | Yes | `<h2>` |
| Body | Yes | Content; for consequential: summary list of effects |
| Effects summary (consequential) | Yes | Definition list: Action, Case, Recipients (who will be notified or served), Amount (if payment), Irreversible: yes / no |
| Acknowledgement (consequential) | Optional | Checkbox "I confirm …" or typed text (for example the case reference) |
| Footer actions | Yes | Confirm (primary or danger) and Cancel (secondary) |
| Close button | Dialog only | `IconButton` "Close"; consequential dialogs close with Cancel or Escape |

<!-- section:variants -->
## Variants and sizes

`Dialog` sizes `sm` (28rem), `md` (40rem), `lg` (56rem). `ConsequentialConfirmDialog` levels: `confirm` (summary + confirm), `acknowledge` (summary + checkbox), `typed` (summary + type the case reference; used for issue award, withdraw claim), `step-up` (summary + re-authentication before the action is sent).

<!-- section:states -->
## States

Closed; opening (fade, reduced-motion: instant); open; submitting (Confirm in loading state, Cancel disabled, Escape ignored, dialog cannot close); success (dialog closes, focus returns, toast or inline confirmation with the receipt reference); error (inline `Alert` in the dialog, Confirm enabled again, nothing assumed sent); step-up pending.

<!-- section:api -->
## Props API

```ts
export type DialogProps = {
  open: boolean; onOpenChange: (open: boolean) => void;
  title: string; description?: string; size?: 'sm' | 'md' | 'lg';
  initialFocus?: RefObject<HTMLElement>;   // default: first focusable in body, else title
  children: ReactNode; footer: ReactNode;
};
export type ConsequentialConfirmDialogProps = {
  open: boolean; onOpenChange: (o: boolean) => void;
  title: string;                         // "Issue final award"
  effects: { action: string; caseRef: string; recipients: string[]; amount?: { value: string; currency: string }; irreversible: boolean };
  level: 'confirm' | 'acknowledge' | 'typed' | 'step-up';
  acknowledgementText?: string;          // required for 'acknowledge'
  typedConfirmation?: string;            // required for 'typed', e.g. case reference
  confirmLabel: string;                  // "Issue award"
  tone: 'primary' | 'danger';
  onConfirm: (ctx: { idempotencyKey: string; stepUpToken?: string }) => Promise<{ receiptRef: string }>;
};
```
The dialog generates one idempotency key when it opens and passes it to `onConfirm`; repeated confirms reuse it, so the server mutation ([[APP-server-actions-and-mutation]], [[APP-api-versioning-rate-limiting]]) cannot act twice.

<!-- section:behaviour -->
## Behaviour

On open: background is inert (native modal), focus moves to `initialFocus`; for consequential dialogs focus goes to the title so the summary is read first, then Tab reaches the acknowledgement and Cancel before Confirm. While submitting the dialog cannot be dismissed. On success the parent shows the receipt reference and the audit event is written by the server action ([[PKG-audit-trail]]). On a session timeout during step-up, the user re-authenticates in the dialog without losing the form. Client component.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

| Key | Action |
|---|---|
| Tab / Shift+Tab | Cycle within dialog |
| Escape | Close (not while submitting) |
| Enter | Activates the focused button only; Enter in the typed-confirmation field does not submit |

On close, focus returns to the element that opened the dialog, or to a sensible target if it no longer exists (for example the case header after a withdrawal). WCAG: 1.3.1, 2.1.2 (no trap beyond the modal), 2.4.3, 2.4.11, 3.3.4 (error prevention for legal and financial actions: reversible, checked or confirmed) [R2], 4.1.2.

<!-- section:content -->
## Content guidelines

Title states the action ("Issue final award in ARB-2026-0142?"). Effects use plain words ("All parties and counsel will be notified by email and in the platform. You will not be able to edit the award after this."). Confirm label repeats the verb ("Issue award"), never "OK" or "Yes". Legal wording here is part of the legal text register ([[I18N-legal-declaration-and-consent]]); the version shown is recorded with the action.

<!-- section:tokens -->
## Tokens used

`dialog.bg` (surface.overlay), `dialog.backdrop` (neutral.950 at 60 percent), `elevation.3`, `radius.lg`, `space.inset.lg`, `typography.heading.md`, button tokens, `color.feedback.warning.*` for the irreversible note.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md` dialogs become full-screen sheets with a sticky footer; content scrolls inside. At 400 percent zoom the footer stays reachable and the body scrolls.

<!-- section:examples -->
## Usage examples

```tsx
<ConsequentialConfirmDialog open={open} onOpenChange={setOpen} title={t('award.issueTitle', { ref })}
  effects={{ action: t('award.issue'), caseRef: ref, recipients: recipientNames, irreversible: true }}
  level="typed" typedConfirmation={ref} confirmLabel={t('award.issueCta')} tone="primary"
  onConfirm={({ idempotencyKey }) => issueAward({ caseId, awardDraftId, idempotencyKey })} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: double-confirm sends one request with the same idempotency key; focus return after success, error and cancel; Escape ignored while submitting.

<!-- section:questions -->
## Open questions

- [ ] Which actions require `typed` or `step-up` level? Proposed: issue award and withdraw claim typed; change bank details and payouts step-up (owner: product, security lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Native modal `<dialog>` (inert background), labelled and described, focus to title for consequential summaries, focus return on close, Escape except while submitting, full-screen sheet on mobile with reachable footer; meets 3.3.4 error prevention for legal and financial actions.

<!-- check:api-design -->
### API design and misuse resistance

Level-specific props are required by type (`acknowledgementText` for acknowledge, `typedConfirmation` for typed); `onConfirm` receives the idempotency key.

<!-- check:security -->
### Data safety in the component

Effects summary is built from server data passed by the caller; step-up tokens are passed to the server action, never stored; the server action writes the audit event and records the version of the wording shown.

<!-- check:resilience -->
### Async, errors and edge cases

One idempotency key per dialog open prevents duplicate filings or payments; errors keep the dialog open with nothing assumed sent; step-up re-authentication happens in place.

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
    "clause": "3.3.4 Error Prevention (Legal, Financial, Data)",
    "id": "R2",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  }
]
```

<!-- end -->
