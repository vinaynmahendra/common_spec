---
id: "PKG-stepper-and-multi-step-form"
title: "Stepper and multi-step form"
parent: "PKG-ui-design-system"
order: 10
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Filing wizard (Statement of Claim, Response) with save-and-resume"
links: []
rev: 2
syncHash: "091f8173f4c9bbcb"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.10 Stepper and multi-step form

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Filing wizard (Statement of Claim, Response) with save-and-resume

<!-- section:purpose -->
## Purpose and when to use

`MultiStepForm` runs long filings as a sequence of steps with save-and-resume: Statement of Claim, Response, Counterclaim, SEBI ODR complaint intake for investors, and MSME claim intake. `Stepper` is the visual progress indicator. Drafts are saved on the server, so a party can stop and come back days later on another device. The final step is a review page followed by [[PKG-modal-dialog-and-consequential]].

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Stepper | Yes | `<nav aria-label="Filing steps"><ol>`; each step a link (completed or current) or text (future), current has `aria-current="step"` |
| Step heading | Yes | `<h1>` "Step 2 of 6: Parties" |
| Step body | Yes | Form fields |
| Save status | Yes | "Saved at 14:32" text with polite announcement |
| Navigation | Yes | Back (secondary), Save and continue (primary), Save and exit (tertiary) |
| Review step | Yes | Summary list per step with "Change" links |

<!-- section:variants -->
## Variants and sizes

Linear (default for filings; next step requires current step valid) and non-linear (tenant admin setup; any step reachable). Stepper display: full list on wide screens, "Step 2 of 6" with a disclosure on narrow screens.

<!-- section:states -->
## States

Step: not started, in progress, complete, has errors (icon and text "Needs attention"), locked (not yet reachable). Form: saving, saved, save failed (warning Alert with Retry; data kept locally), resumed (Alert "You are continuing a draft started on 2 November"), expired (draft past retention, see below).

<!-- section:api -->
## Props API

```ts
type StepDef<T> = { id: string; title: string; schema: z.ZodType<Partial<T>>; render: (ctx: StepCtx<T>) => ReactNode; isApplicable?: (draft: Partial<T>) => boolean };
export type MultiStepFormProps<T> = {
  steps: StepDef<T>[];
  draft: { id: string; version: number; data: Partial<T>; updatedAt: string };
  saveDraft: (d: { id: string; version: number; data: Partial<T> }) => Promise<{ version: number; updatedAt: string }>;  // optimistic concurrency
  onSubmit: (data: T, ctx: { idempotencyKey: string }) => Promise<{ receiptRef: string }>;
  currentStepId: string; onStepChange: (id: string) => void;   // held in the URL: /cases/new/claim/[draftId]/[step]
  linear?: boolean;
};
```

<!-- section:behaviour -->
## Behaviour

Autosave on step change and every 30 seconds after changes (debounced), to a server-side draft row (`filing_draft`, tenant-owned, RLS) through a tRPC mutation; `version` provides optimistic concurrency, so a second tab gets "This draft was changed elsewhere. Reload to continue." Uploaded files attach to the draft. Drafts expire after a tenant-configured period (proposed default 90 days) with a reminder notification 7 days before. Each step's URL is bookmarkable; Back uses browser history. Data entered in earlier steps is reused, never asked for again (WCAG 3.3.7). The review step validates the full schema server-side before showing the confirmation dialog.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

Standard form keyboard behaviour. On step change focus moves to the step `<h1>`. On validation failure focus moves to the error summary. Completed step links in the stepper are reachable by Tab. WCAG: 1.3.1, 2.4.2 (page title includes step), 2.4.3, 2.4.6, 2.2.1 (no session-based time limit; autosave protects data), 3.3.7 [R1], 3.3.4.

<!-- section:content -->
## Content guidelines

Step titles are nouns ("Parties", "Claim details", "Documents", "Fees", "Review"). Resume message gives the date. Save status uses absolute time. For unrepresented parties, each step starts with one sentence explaining why the information is needed ([[DOC-plain-language-guidance-for]]).

<!-- section:tokens -->
## Tokens used

`stepper.marker.{complete,current,future,error}`, `stepper.connector`, status tones for step state icons, `typography.label.md`, `space.stack.lg`.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md` the stepper collapses to "Step 2 of 6: Parties" with a disclosure listing steps; navigation buttons stack with primary last.

<!-- section:examples -->
## Usage examples

```tsx
<MultiStepForm steps={claimSteps} draft={draft} saveDraft={trpc.filings.saveDraft.mutate}
  onSubmit={(data, { idempotencyKey }) => trpc.filings.submitClaim.mutate({ data, idempotencyKey })}
  currentStepId={params.step} onStepChange={(s) => router.push(`/cases/new/claim/${draft.id}/${s}`)} linear />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: resume from another session, concurrent edit conflict, save failure and retry, focus on step heading, and an end-to-end Playwright journey for Statement of Claim keyboard-only.

<!-- section:questions -->
## Open questions

- [ ] Draft retention period and whether drafts are visible to the tenant secretariat before filing (proposed: not visible) (owner: legal, with [[PKG-retention-and-deletion-schedule]]).
- [ ] Can counsel share a draft with co-counsel before filing (owner: product).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Stepper is an ordered list in a labelled nav with `aria-current="step"`; focus to step heading on change; page title includes step; no time limit because drafts autosave; earlier answers are reused (3.3.7).

<!-- check:i18n -->
### Localisation and long content

Step titles and "Step 2 of 6" use ICU messages; the compact stepper avoids fixed widths so long translated titles wrap; dates in resume messages are absolute in the user's locale and zone.

<!-- check:security -->
### Data safety in the component

Drafts are tenant-owned rows under RLS, visible only to the author and permitted co-authors; draft data is not put in URLs (only draft ID and step ID).

<!-- check:resilience -->
### Async, errors and edge cases

Server-side drafts with optimistic concurrency, autosave every 30 seconds and on step change, save failure keeps data and offers Retry, idempotent final submit.

<!-- check:testing -->
### Test and documentation coverage

Stories per step state and form state (saving, saved, save failed, resumed, conflict); interaction tests for keyboard-only completion and focus on step heading; Playwright end-to-end Statement of Claim journey with resume from a second browser context.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "clause": "3.3.7 Redundant Entry",
    "id": "R1",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  }
]
```

<!-- end -->
