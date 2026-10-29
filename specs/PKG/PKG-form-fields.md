---
id: "PKG-form-fields"
title: "Form fields"
parent: "PKG-ui-design-system"
order: 3
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Text input, textarea, select, checkbox, radio with labels, hints and error messages; React Hook Form integration"
links: []
rev: 2
syncHash: "65dd9dbdb7cee621"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.3 Form fields

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Text input, textarea, select, checkbox, radio with labels, hints and error messages; React Hook Form integration

<!-- section:purpose -->
## Purpose and when to use

Text input, textarea, select, checkbox, checkbox group, radio group and the shared `Field` wrapper (label, hint, error). Used in every form: party details, filing metadata, fee payment details, tenant admin settings, and forms produced by [[PKG-forms-and-form-builder]]. Integrates with React Hook Form and Zod per [[APP-framework-dependencies]]. Searchable selection uses [[PKG-combobox-and-people-picker]]; dates use [[PKG-date-and-time-picker-with]].

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Label | Yes | `<label for>` (or `<legend>` for groups in `<fieldset>`) |
| Required / optional marker | When applicable | Text "(required)" or "(optional)" inside the label, not only an asterisk |
| Hint | No | `<p id>` referenced by `aria-describedby` |
| Control | Yes | `<input>`, `<textarea>`, `<select>`, `<input type=checkbox|radio>` |
| Error message | When invalid | `<p id>` with error icon, referenced by `aria-describedby`; `aria-invalid="true"` on control |
| Character count | Textarea with `maxLength` | Polite live region, updated after typing pauses |

<!-- section:variants -->
## Variants and sizes

`TextField` (types: text, email, tel, number-as-text with `inputMode`, password with show / hide), `Textarea` (auto-grow up to 12 lines), `Select` (native `<select>`; for more than about 15 options or search, use `Combobox`), `Checkbox`, `CheckboxGroup`, `RadioGroup` (vertical by default; horizontal only for 2–3 short options). Sizes follow density (`md` 40 px, `sm` 32 px in compact).

<!-- section:states -->
## States

| State | Visual | Announced |
|---|---|---|
| Default | `border.control` | Label, hint, required |
| Focus | 2 px focus ring | — |
| Invalid | `feedback.error.border`, error icon and text below | `aria-invalid="true"`, error text via `aria-describedby` |
| Disabled | `text.disabled`, no interaction | `disabled` |
| Read-only | No border, value as text, still selectable and focusable | `aria-readonly` / `readOnly` |
| Saved (autosave forms) | Subtle "Saved" text near field group | Polite announcement once per save |

<!-- section:api -->
## Props API

```ts
type FieldCommon = {
  label: string;                     // required, visible
  hint?: string;
  error?: string;                    // from RHF fieldState.error.message (already translated)
  required?: boolean;                // shows "(required)" and sets aria-required
  showOptional?: boolean;            // shows "(optional)" instead, for forms where most fields are required
  disabled?: boolean;
  readOnly?: boolean;
  id?: string;                       // generated if omitted
  name: string;
};
export type TextFieldProps = FieldCommon & {
  type?: 'text' | 'email' | 'tel' | 'password' | 'url';
  inputMode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email';
  autoComplete: string;              // required: 'name', 'email', 'one-time-code', 'off' ...
  maxLength?: number;
} & ({ value: string; onValueChange: (v: string) => void } | { defaultValue?: string });

// RHF adapters (client components)
export function RHFTextField<T extends FieldValues>(p: { control: Control<T>; name: Path<T> } & Omit<TextFieldProps, 'value' | 'onValueChange' | 'name' | 'error'>): JSX.Element;
// Same pattern for RHFTextarea, RHFSelect, RHFCheckbox, RHFRadioGroup.
```

`autoComplete` is required so that identity fields support autofill (WCAG 1.3.5). `ref` forwards to the control.

<!-- section:behaviour -->
## Behaviour

Validation timing: on blur for the first time, then on change once a field has been touched; on submit for all fields. On a failed submit, an error summary (`Alert` tone critical, listing links to each invalid field) appears at the top of the form and receives focus. Zod schemas are shared between client and server; server errors from the tRPC mutation are mapped back to fields by `name`. Inputs never auto-advance or auto-submit. Paste is always allowed.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

Native control keyboard behaviour (Tab, Space for checkbox, arrow keys within a radio group). Labels are programmatically associated; groups use `<fieldset>` and `<legend>`. Error summary links move focus to the field. WCAG: 1.3.1, 1.3.5, 2.4.6, 3.3.1 [R1], 3.3.2 [R2], 3.3.3, 3.3.7 (redundant entry: previously entered data is offered again in multi-step forms), 4.1.2.

<!-- section:content -->
## Content guidelines

Labels are short nouns ("Email address"); hints explain format or purpose ("We send notices of hearings to this address"); errors say what to do ("Enter an email address in the format name@example.com"), never "Invalid input". Error copy comes from [[APP-error-message-catalogue]]. Do not use placeholder text as a label.

<!-- section:tokens -->
## Tokens used

`field.border.{default,hover,invalid}`, `field.bg`, `color.text.default`, `color.text.muted` (hint), `color.feedback.error.fg`, `color.focus.ring`, `size.control.height`, `radius.sm`, `typography.label.md`, `typography.body.md`, `space.stack.sm`.

<!-- section:responsive -->
## Responsive behaviour and direction

Fields are full width below `md`; label always above the control (never beside it), so translations and zoom up to 400 percent do not overlap. Text direction of an input follows the content (`dir="auto"`) for names and addresses.

<!-- section:examples -->
## Usage examples

```tsx
<RHFTextField control={control} name="claimant.email" label={t('party.email')} hint={t('party.emailHint')} type="email" autoComplete="email" required />
<RHFRadioGroup control={control} name="representation" label={t('filing.representedQ')} options={[{ value: 'self', label: t('filing.self') }, { value: 'counsel', label: t('filing.counsel') }]} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: error summary receives focus and links work; `aria-describedby` includes hint and error; 1.4.12 text-spacing snapshot; autofill attributes present.

<!-- section:questions -->
## Open questions

- [ ] Do we mark required or optional fields by default across the platform (proposed: mark required, since most legal forms are mostly required) (owner: content design).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Visible labels with `<label for>`, `<fieldset>`/`<legend>` for groups, hints and errors linked via `aria-describedby`, `aria-invalid`, error summary that takes focus, required text not just an asterisk, `autoComplete` required for identity fields.

<!-- check:api-design -->
### API design and misuse resistance

`label`, `name` and `autoComplete` are required; controlled and uncontrolled are a discriminated union; RHF adapters keep validation wiring out of page code.

<!-- check:i18n -->
### Localisation and long content

Labels above controls, `dir="auto"` for free text, no fixed widths; built-in strings ("(required)", "Show password") come from `UiMessages`.

<!-- check:security -->
### Data safety in the component

Password inputs never echo values to logs; masked fields (KYC IDs, bank accounts) render masked in read-only state and in visual-test fixtures.

<!-- check:resilience -->
### Async, errors and edge cases

Paste allowed, no auto-submit, server validation errors mapped back to fields, and long forms are built on [[PKG-stepper-and-multi-step-form]] with save-and-resume so input is not lost on session expiry.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WCAG 2.2 SC 3.3.1",
    "kind": "standard",
    "title": "Understanding SC 3.3.1 Error Identification",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/error-identification"
  },
  {
    "body": "W3C",
    "id": "R2",
    "ident": "WCAG 2.2 SC 3.3.2",
    "kind": "standard",
    "title": "Understanding SC 3.3.2 Labels or Instructions",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions"
  }
]
```

<!-- end -->
