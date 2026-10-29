# Template: UI component (`component`)

Generated from `component.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies one reusable UI component in the shared design system: what it is for, its parts, variants, states, props API, keyboard and assistive-technology behaviour, content rules, tokens and tests, so it is built once, accessibly, and used the same way in every persona app and tenant.

**Depth:** 2–6 pages per component. The states table, props API and keyboard table must be complete and exact; they are the contract for design, engineering and testing. Link to Figma and Storybook rather than embedding pixel detail. Split into child nodes for sub-components that are used on their own (for example Data table → column header sort, row selection, pagination).

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and when to use (level 1)

What problem the component solves, where it is used in our product, when to use it and when to use something else instead. Name the closest APG pattern if one applies.

Illustrative example (not a requirement):

> **File upload dropzone** lets a party, counsel or the secretariat add one or more documents to a filing or case file, see each file's upload and virus-scan status, and fix problems before submitting.
> 
> - Use for: Statement of Claim filing, exhibit upload, transcriber uploading a corrected transcript
> - Do not use for: a single avatar or logo (use *Image picker*), importing a bundle index (use *CSV import*)
> - Pattern basis: native `<input type="file">` plus a list of file rows with status; drag and drop is an enhancement, never the only way

### `anatomy` Anatomy (level 1)

The named parts of the component, which are required or optional, and the HTML element or ARIA role each part maps to. A labelled diagram link plus a table is ideal.

Illustrative example (not a requirement):

> | Part | Required | Element / role | Notes |
> |---|---|---|---|
> | Label | Yes | `<label>` for the file input | "Exhibits" |
> | Hint | No | text linked by `aria-describedby` | "PDF or DOCX, up to 50 MB each" |
> | Drop area | Yes | container; contains the *Choose files* button | Visual target only |
> | Choose files button | Yes | `<button>` that opens the native picker | Keyboard path |
> | File list | Yes once files added | `<ul>` of file rows | |
> | File row | — | `<li>`: name, size, status, remove button | |
> | Live status region | Yes | `role="status"` | Announces "3 files uploaded, 1 failed" |

### `variants` Variants and sizes (level 1)

Each visual or behavioural variant, what it is for, and the sizes or densities it supports. Keep the list short; every variant is a cost in testing and theming.

Illustrative example (not a requirement):

> | Variant | Use | Differences |
> |---|---|---|
> | `default` | Filing forms | Full drop area, file list below |
> | `compact` | Secretariat case file side panel | Button only, no drop area, dense rows |
> | `single` | Replace one document version | One file, replaces existing on success |
> 
> Densities follow the design system (`comfortable`, `compact`). No tenant-specific variants.

### `states` States (level 1)

Every interaction and data state (default, hover, focus, active, disabled, read-only, loading, error, success and domain states), with what changes visually and what is announced to assistive technology.

Illustrative example (not a requirement):

> | State | Visual | Announced |
> |---|---|---|
> | Idle | Dashed border, *Choose files* | Label + hint |
> | Drag over | `color.action.primary.border`, 2 px | — |
> | Uploading | Progress bar per row with % | "Uploading Exhibit C-12, 40%" (throttled to every 25%) |
> | Scanning | Spinner + "Checking file" | "Checking Exhibit C-12" |
> | Failed | Danger icon + text reason, *Retry* | "Exhibit C-12 failed: larger than 50 MB" |
> | Ready | Check icon + size | "Exhibit C-12 ready" |
> | Disabled (deadline passed) | Muted, explanation text | Reason in hint text |
> 
> Disabled is avoided where possible; when used, the reason is always visible as text.

### `api` Props API (level 1)

The TypeScript props contract: names, types, defaults, required flags, events and slots, controlled versus uncontrolled usage, ref forwarding and which DOM attributes pass through. This is the contract consumers code against.

Illustrative example (not a requirement):

> ```ts
> export interface FileDropzoneProps {
>   label: string;                         // required; becomes the accessible name
>   hint?: string;
>   accept: AcceptSpec;                    // e.g. { 'application/pdf': ['.pdf'] }
>   maxSizeBytes: number;
>   maxFiles?: number;                     // default 50
>   variant?: 'default' | 'compact' | 'single';
>   files?: UploadItem[];                  // controlled
>   defaultFiles?: UploadItem[];           // uncontrolled
>   onFilesChange?: (files: UploadItem[]) => void;
>   upload: (file: File, signal: AbortSignal) => Promise<UploadResult>; // injected, tenant-scoped by caller
>   disabledReason?: string;               // presence disables and shows reason
>   id?: string;
> }
> export type UploadItem =
>   | { status: 'queued' | 'uploading'; id: string; name: string; size: number; progress?: number }
>   | { status: 'scanning' | 'ready'; id: string; name: string; size: number; documentId: string }
>   | { status: 'failed'; id: string; name: string; size: number; error: UploadErrorCode };
> ```
> No `className` overrides of internal parts; layout via wrapper only. Ref forwards to the native file input.

### `behaviour` Behaviour (level 2)

How the component responds to input, timing, async work and data limits; what is client-side versus server-side; how it behaves inside forms (React Hook Form, Zod validation) and whether it is a server or client component.

Illustrative example (not a requirement):

> - Client component (`'use client'`); the page passing `upload` stays a server component and provides a server action or tRPC mutation
> - Validates type and size before upload; server re-validates (client checks are convenience only)
> - Uploads up to 3 files in parallel; each can be cancelled (AbortSignal)
> - Duplicate file name in the same filing: warns and asks "Keep both" or "Replace"
> - Integrates with React Hook Form via `Controller`; form submit is blocked until all rows are `ready`
> - Navigating away with uploads in progress shows the browser leave-page prompt

### `keyboard` Keyboard, focus and assistive technology (level 1)

Keyboard interaction table, focus order and where focus goes after each action, ARIA roles, states and properties, accessible names, live announcements, and the WCAG 2.2 criteria this component must meet.

Illustrative example (not a requirement):

> | Key | Where | Action |
> |---|---|---|
> | Tab | Page | Moves to *Choose files*, then each row's *Retry* / *Remove* |
> | Enter / Space | *Choose files* | Opens native file picker |
> | Enter / Space | *Remove* | Removes the file; focus moves to next row's *Remove*, or to *Choose files* if none |
> 
> - *Remove* has the name "Remove Exhibit C-12" (visible text "Remove" is included, per 2.5.3)
> - Drag and drop has a keyboard and single-pointer alternative (2.5.7)
> - Focus ring uses `color.focus.ring`, never hidden by the sticky filing footer (2.4.11)
> - Tested with NVDA + Firefox, JAWS + Chrome, VoiceOver + Safari (macOS and iOS), TalkBack + Chrome

### `content` Content guidelines (level 2)

Rules and examples for labels, hints, error messages, empty and success text, including tone, length limits, legal wording and which strings are translatable or tenant-overridable.

Illustrative example (not a requirement):

> - Label names the document set, not the action: "Exhibits", not "Upload here"
> - Errors say what happened and what to do: "Exhibit C-12 is 72 MB. Files must be 50 MB or smaller. Compress it or split it into parts."
> - Never blame the user; never show technical codes alone
> - All strings come from the i18n catalogue (`upload.error.tooLarge`) with ICU plurals ("1 file", "3 files")
> - Tenants may override terminology through the terminology keys (e.g. "Exhibits" vs "Annexures"), not individual component strings

### `tokens` Tokens used (level 2)

Every design token the component uses, by part and state. Only semantic or component-tier tokens; list any new component tokens this spec introduces.

Illustrative example (not a requirement):

> | Part / state | Token |
> |---|---|
> | Drop area border | `color.border.input`, `border.width.dashed` |
> | Drop area border, drag over | `color.action.primary.border` |
> | Row text | `type.body.sm`, `color.text.default` |
> | Failed icon + text | `color.feedback.danger.text` |
> | Progress bar | `color.action.primary.bg`, `motion.duration.moderate` |
> | Row spacing | `space.2` (compact), `space.3` (comfortable) |
> | Focus | `color.focus.ring`, `focus.ring.width`, `focus.ring.offset` |
> 
> New component tokens: `dropzone.border.style` (alias of `border.style.dashed`).

### `responsive` Responsive behaviour and direction (level 2)

What changes at each breakpoint and on touch devices, behaviour at 320 CSS px width and 200–400% zoom, long-content handling and right-to-left layout.

Illustrative example (not a requirement):

> - Below `bp.md`: drop area text hidden (touch users cannot drag), *Choose files* full width, rows stack name over status
> - 320 px / 400% zoom: no horizontal scrolling (1.4.10); long file names wrap with `overflow-wrap: anywhere`, full name in the accessible name
> - RTL: icon and remove button positions mirror via logical properties; the progress bar fills from inline-start
> - Touch targets for *Remove* at least 44 × 44 px in comfortable density

### `examples` Usage examples (level 2)

Copy-pasteable code for the common cases, plus do and don't examples. Each example should have a matching Storybook story.

Illustrative example (not a requirement):

> ```tsx
> <FileDropzone
>   label={t('filing.exhibits.label')}
>   hint={t('filing.exhibits.hint', { max: '50 MB' })}
>   accept={{ 'application/pdf': ['.pdf'] }}
>   maxSizeBytes={50 * 1024 * 1024}
>   upload={(file, signal) => uploadExhibit({ caseId, file, signal })}
>   disabledReason={deadlinePassed ? t('filing.deadlinePassed', { date }) : undefined}
> />
> ```
> - Do: one dropzone per document category in the Statement of Claim form
> - Don't: hide the dropzone after the deadline; disable it and say why
> - Stories: `Default`, `WithErrors`, `ManyFiles` (200 rows), `DeadlinePassed`, `RTL`, `HKIACTheme`, `Dark`

### `testing` Testing (level 2)

Which stories exist, what interaction, accessibility and visual regression tests run on them in CI, the theme and mode matrix, thresholds, and the manual assistive-technology test schedule.

Illustrative example (not a requirement):

> | Test | Tool | Runs | Passes when |
> |---|---|---|---|
> | Interaction | Storybook interaction tests | Every PR | Add, fail, retry, remove, keyboard-only path |
> | Automated a11y | axe-core via Storybook | Every PR, every story | Zero violations (no exemptions without an issue) |
> | Visual regression | Storybook visual tests / Playwright `toHaveScreenshot` | Every PR touching `packages/ui` or tokens | Diff ≤ 0.1% or approved |
> | Matrix | — | — | Base + every active tenant theme × light/dark × LTR/RTL |
> | Manual AT | NVDA, VoiceOver, TalkBack | Each minor release | Checklist signed off |

### `questions` Open questions (level 3)

Unresolved items as a checklist, each with an owner.

Illustrative example (not a requirement):

> - [ ] Do we allow folder upload for large exhibit sets? (Product)
> - [ ] Should virus-scan failure reveal the detection name to parties? (Security)
> - [ ] Resumable uploads for files over 500 MB on poor networks? (Engineering)

## Checks

### `accessibility` Assistive technology conformance

**Question:** Does the component expose the correct name, role, value and state to assistive technologies and follow the matching APG pattern, so that it works with keyboard, screen readers, voice control and magnification on the browsers our users actually use?

- Which APG pattern does it follow, and where does it deliberately deviate (with reasons)? Is a native HTML element used wherever one exists instead of ARIA?
- How is the accessible name computed in each usage (visible label, `aria-labelledby`), and does it contain the visible label text so voice-control users can say it (2.5.3)?
- Where does focus go after open, close, delete, error and async completion, and is it ever lost to `<body>` or hidden behind sticky headers or footers (2.4.11)?
- Which changes are announced through live regions, how often, and are announcements throttled so they do not flood a screen reader?
- Does any content appear on hover or focus (tooltips, previews), and can it be dismissed, hovered and kept visible (1.4.13)?
- Which screen reader and browser pairs are tested manually, how often, and where are the results recorded?
- Does the component work in Windows forced-colours mode with visible focus and selection?

**Good answer:** A named APG pattern with a keyboard table, focus-management rules for every action, live-region rules, and a dated manual test record across at least NVDA, JAWS, VoiceOver (macOS and iOS) and TalkBack. Automated axe checks run on every story and the remaining criteria are covered by a written manual checklist.

**Red flags:**

- `div` or `span` with click handlers instead of buttons or links.
- Focus not managed after async actions or removal.
- Only automated axe checks, no manual screen reader testing.
- Icon-only controls with no accessible name.

### `api-design` API design and misuse resistance

**Question:** Is the props API small, typed so that invalid combinations do not compile, consistent with the rest of the library, and stable enough that consuming apps will not break on upgrade?

- Are mutually exclusive props expressed as TypeScript discriminated unions (for example `files` plus `onFilesChange` versus `defaultFiles`) so misuse fails at compile time?
- Does it support both controlled and uncontrolled use where it holds state, and does it warn when switched between them?
- Are naming and event conventions the same as sibling components (`onXChange`, `disabled`, `size`, `variant`), and is that checked by review or lint?
- What escape hatches exist (`className`, `asChild`, slots, ref forwarding, passthrough `data-*` and `aria-*`), and which are deliberately not offered to prevent visual drift?
- Which props are required for accessibility (such as `label`) and therefore cannot be omitted?
- What counts as a breaking change for this component (prop rename, default change, DOM structure change that breaks tests or styling), and what is the deprecation path?
- Does it work as a server component, or which parts require `'use client'`, and is that boundary documented?

**Good answer:** A typed props contract with discriminated unions for exclusive modes, accessibility-critical props marked required, documented escape hatches, and a written definition of breaking change tied to semver with a deprecation period and codemod where practical.

**Red flags:**

- Boolean prop explosion (`isCompact`, `isSmall`, `isDense`) instead of a single variant.
- Optional `label` with no enforced alternative.
- Arbitrary `style` or `className` reaching internal parts.
- Breaking changes shipped in minor versions.

### `theming` Tenant themes and modes

**Question:** Does the component look correct and stay accessible under every active tenant theme, colour mode, density and forced-colours setting, using only semantic and component tokens?

- Does the component reference only semantic or its own component tokens, with no primitives or raw values (checked by lint)?
- Which tokens does each state use, and are all its state pairs (text on background, border on surface, focus ring on every surface) in the contrast manifest?
- How does it render under each active tenant theme (for example an HKIAC theme and a SEBI ODR institution theme) with long tenant terminology and their logo sizes?
- Does it behave correctly in dark mode, high-contrast mode, `forced-colors: active` and reduced motion?
- Is any part tenant-configurable beyond tokens and terminology? If so, why, and where is that configuration validated?

**Good answer:** A complete token table per part and state, lint showing zero raw values, Storybook stories for every active tenant theme × mode in visual regression, and confirmation that each state pair is covered by the design system contrast check.

**Red flags:**

- Hard-coded colours or spacing inside the component.
- Tenant-specific branches in component code (`if tenant === ...`).
- Only the default theme in visual tests.

### `i18n` Localisation and long content

**Question:** Does the component handle translated text, other scripts, right-to-left direction, locale formatting and extreme content lengths without clipping, overlap or loss of meaning?

- Are all built-in strings (button text, announcements, error messages) externalised with ICU plural and gender support, and are any passed in by the caller instead?
- How does it handle 30–40% longer translations, very long single words or file names, and CJK text?
- Does it mirror correctly in RTL using logical properties, and are directional icons mirrored while non-directional ones are not?
- Are numbers, dates, file sizes and currencies formatted through the platform locale utilities rather than inside the component?
- What happens with zero items, one item and very many items (for example 5,000 rows in a document list or 200 parties in a picker)?

**Good answer:** All strings from the i18n catalogue with plural rules, formatting delegated to locale utilities, RTL and long-content stories in visual regression, and stated limits with the behaviour beyond them (virtualisation, truncation with full text available).

**Red flags:**

- Concatenated strings or English plurals built in code.
- Truncation that hides essential information with no way to reveal it.
- No RTL story.

### `security` Data safety in the component

**Question:** Can this component leak case data or personal data, render untrusted content unsafely, or let a user act on data from another tenant or case?

- Does it ever render caller- or user-supplied HTML, Markdown or SVG? If so, which sanitiser, and is `dangerouslySetInnerHTML` banned in the component?
- For data-fetching components (party picker, case search combobox), is the fetch function injected by the caller so tenant and permission scoping stays on the server, and is client-side cache keyed by tenant and user?
- Does it put personal or case data into URLs, `data-*` attributes, analytics events, error messages sent to monitoring, or browser storage?
- Do copy, download and preview actions respect the user's permission on that document and log an audit event where required?
- Does it keep sensitive values masked (such as KYC numbers) in the accessible name and screenshots used by visual tests?

**Good answer:** The component renders text only (or sanitises through one approved function), receives data-access functions from the caller rather than calling APIs itself, emits analytics without case content, and documents which actions require server-side authorisation and audit.

**Red flags:**

- Component calls APIs directly with its own tenant logic.
- Raw HTML rendering of user content.
- Personal data in analytics or `data-testid` attributes.
- Real case data in Storybook fixtures or visual baselines.

### `resilience` Async, errors and edge cases

**Question:** What does the component do when data is slow, missing, invalid, huge or changes underneath it, and does the user always keep their work and understand what happened?

- What is shown while loading, and after how long does a skeleton or spinner appear (avoid flashes under 300 ms)?
- How are errors surfaced inline, and can the user retry without losing other input?
- Does it prevent double submission or duplicate actions (double-click on *File*, repeated *Remove*)?
- How does it behave when the session expires or permission is withdrawn mid-interaction?
- What are the tested size limits (rows, options, characters), and what happens beyond them (virtualisation, pagination, server search)?
- How does it behave offline or on a flaky 3G connection?

**Good answer:** Defined loading, empty, error and limit behaviour with copy for each, protection against duplicate actions, tested maximum sizes with a stated performance target, and no data loss on error or session expiry.

**Red flags:**

- Error state not designed.
- Unbounded lists rendered in full.
- User input cleared after a failed request.

### `performance` Performance and bundle cost

**Question:** What does the component add to bundle size and render time, and does it stay fast at realistic data sizes on low-end devices?

- What is its compressed JavaScript size, including dependencies, and is there a budget checked in CI?
- Can it be imported per component (tree-shaken), and does importing it pull in other heavy modules (date libraries, PDF viewers)?
- Which part must run on the client, and can static parts render as server components?
- Does it cause layout shift on load, image load or font swap (CLS)?
- How long does an interaction take with large data (for example typing in a combobox over 10,000 neutrals), measured on a mid-range Android phone, against an Interaction to Next Paint target of 200 ms?

**Good answer:** A size budget with CI measurement, documented server/client split, lazy loading for heavy parts, and a measured interaction time at the stated maximum data size on a reference low-end device.

**Red flags:**

- Whole library imported for one helper.
- No size budget.
- Performance measured only on a developer laptop.

### `testing` Test and documentation coverage

**Question:** Does every documented variant and state have a story, and do automated interaction, accessibility and visual regression tests run on all of them across the theme matrix on every relevant change?

- Is there a story for each variant × state in this spec, plus edge cases (long text, many items, RTL, error)?
- Do interaction tests cover the keyboard-only path and focus movement, not just mouse clicks?
- Which visual regression tool runs, with what diff threshold, on which matrix of tenant themes, modes and directions, and who approves diffs?
- Are visual baselines rendered in a pinned browser and font environment so they do not flake?
- Does Storybook autodocs show the props table, do and don't guidance and accessibility notes from this spec, and is it published to the team?
- What is the manual assistive-technology test cadence, and who signs it off?

**Good answer:** A story inventory mapped to the states table, interaction tests including keyboard paths, zero-violation axe checks, visual regression on the full theme × mode × direction matrix with named approvers, and published Storybook docs generated from the same source.

**Red flags:**

- Stories only for the default state.
- Visual tests with thresholds so loose that colour changes pass.
- Accessibility violations suppressed without a tracked issue.

