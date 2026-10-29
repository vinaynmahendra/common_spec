---
id: "PKG-typography-and-multi-script"
title: "Typography and multi-script fonts"
parent: "PKG-design-tokens-and-foundations"
order: 2
type: "requirement"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "Type scale, legal and data typography, per-script font stacks (Latin, Indic, CJK), self-hosted per region"
links: []
rev: 2
syncHash: "0fcca2316b2f91bb"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.1.2 Typography and multi-script fonts

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Type scale, legal and data typography, per-script font stacks (Latin, Indic, CJK), self-hosted per region

<!-- section:purpose -->
## Purpose and scope

Defines font families per script, the type scale, line heights, weights, composite typography tokens for UI, legal text and data, and how fonts are self-hosted per region. Consumers: `@nomology/ui`, all route groups, the email renderer (system font stacks only) and the PDF renderer ([[PKG-print-and-formal-document-theme]]) which embeds the same families. Translation and locale formatting are owned by [[I18N-i18n]] and [[I18N-l10n]].

<!-- section:architecture -->
## Token architecture and naming

Primitive font tokens (`font.family.*`, `font.size.*`, `font.weight.*`, `font.line-height.*`) are in `src/primitive/font.tokens.json`. Composite DTCG `typography` tokens [R1] in `src/semantic/typography.tokens.json` combine family, size, weight, line height and letter spacing. Components use only composites (for example `typography.body.md`). Per-script family switching is done in CSS with `:lang()` selectors on the semantic family tokens, so components do not know which script is in use.

<!-- section:colour -->
## Colour

Not covered here. Text colours are in [[PKG-colour-and-contrast#colour]].

<!-- section:typography -->
## Typography

**Families (proposed; all open-licence fonts, self-hosted).**

| Token | Latin | Devanagari (hi, mr) | Tamil | Kannada | Telugu | Bengali | Traditional Chinese (zh-Hant) | Simplified Chinese (zh-Hans) |
|---|---|---|---|---|---|---|---|---|
| `font.family.sans` | Inter | Noto Sans Devanagari | Noto Sans Tamil | Noto Sans Kannada | Noto Sans Telugu | Noto Sans Bengali | Noto Sans TC | Noto Sans SC |
| `font.family.serif` (legal) | Source Serif 4 | Noto Serif Devanagari | Noto Serif Tamil | Noto Serif Kannada | Noto Serif Telugu | Noto Serif Bengali | Noto Serif TC | Noto Serif SC |
| `font.family.mono` | JetBrains Mono | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Each stack ends with system fallbacks (`system-ui, "Segoe UI", Roboto, "Noto Sans", sans-serif`). Arabic and Hebrew are not in the initial tenant set; the grammar allows adding `Noto Sans Arabic` / `Noto Sans Hebrew` without component changes.

**Type scale** (rem at 16 px root):

| Token | Size | Line height (Latin) | Line height (Indic) | Weight |
|---|---|---|---|---|
| `font.size.xs` | 0.75rem (12) | 1.5 | 1.7 | 400 |
| `font.size.sm` | 0.875rem (14) | 1.5 | 1.7 | 400 |
| `font.size.md` | 1rem (16) | 1.5 | 1.7 | 400 |
| `font.size.lg` | 1.125rem (18) | 1.5 | 1.7 | 400 |
| `font.size.xl` | 1.25rem (20) | 1.4 | 1.6 | 600 |
| `font.size.2xl` | 1.5rem (24) | 1.3 | 1.5 | 600 |
| `font.size.3xl` | 1.875rem (30) | 1.25 | 1.45 | 600 |
| `font.size.4xl` | 2.25rem (36) | 1.2 | 1.4 | 700 |

Line heights are unitless so they scale with text resizing [R2]. Weights loaded: 400, 600 and 700 for sans; 400 and 700 for serif.

**Composite tokens.**

| Token | Composition | Use |
|---|---|---|
| `typography.heading.xl` / `lg` / `md` / `sm` | sans, 4xl / 3xl / 2xl / xl, 700 / 600 / 600 / 600 | Page and section headings |
| `typography.body.lg` / `md` / `sm` | sans, lg / md / sm, 400 | Party-facing body text uses `lg` on the public and party pages |
| `typography.label.md` | sans, sm, 600 | Field labels |
| `typography.legal.body` | serif, md (screen) / 11 pt (print), 1.6 | Awards, procedural orders, declarations shown in full |
| `typography.legal.heading` | serif, xl, 700 | Award section headings |
| `typography.legal.footnote` | serif, xs (screen) / 8.5 pt (print) | Footnotes |
| `typography.data.cell` | sans, sm, 400, `font-variant-numeric: tabular-nums` | Table cells |
| `typography.data.numeric` | sans, md, 600, tabular-nums | Amounts, counts |
| `typography.code.ref` | mono, sm | Case references, hashes, bundle page refs |

Minimum on-screen size for any text is 12 px (`xs`), used only for metadata. Locale-specific digits (for example Devanagari numerals) are produced by `Intl.NumberFormat` with the user's numbering system in [[I18N-l10n]]; the fonts above include those glyphs, and tabular figures apply to them where the font supports it.

**Loading.** Fonts are served as WOFF2 from the regional app origin (`/fonts/{family}-{subset}-{weight}.{hash}.woff2`), never from a third-party CDN, so no font request leaves the tenant's region and CSP `font-src 'self'` holds. Each script is a separate `@font-face` with `unicode-range`, so Devanagari or CJK files download only when such characters are on the page. CJK fonts are split into Unicode-range slices (about 100 slices per weight) as Google Fonts does, to keep each request small. `font-display: swap` with metric-matched fallback faces (`size-adjust`, `ascent-override`) to keep layout shift under CLS 0.1 [R3]. Only Inter 400 and 600 are preloaded on party pages.

**Missing tenant font.** Tenants may choose a heading family only from an allow-list that we host (Inter, Source Serif 4, Noto Sans, Noto Serif). Tenant font uploads are not supported. If a selected family fails to load, the stack falls back to the next family with no layout change beyond metric-matched differences.

<!-- section:spacing -->
## Spacing, sizing and layout

Text containers never have fixed heights. Paragraph spacing is `space.stack.md` (1rem) so the WCAG 1.4.12 override (2 × font size) does not overlap content [R4]. Legal text is limited to `size.measure.legal` (42rem, about 70 Latin characters per line).

<!-- section:theming -->
## Theming and tenant branding

Tenants may select `typography.brand.heading-family` from the allow-list only. Body, legal and data typography are locked, because readability of legal text and dense tables must not depend on tenant choice.

<!-- section:governance -->
## Governance, versioning and deprecation

Adding a script (for example Arabic) is a minor release: add the family to the per-script table, add `@font-face` slices, add an RTL fixture to visual regression, and have a native reader review legal typography samples. Changing the default Latin or legal family is a major release because it changes award PDFs.

<!-- section:questions -->
## Open questions

- [ ] Confirm the font choices (Inter, Source Serif 4, JetBrains Mono, Noto families) with product design, and check each licence for embedding in PDFs (owner: design lead; legal for licence confirmation).
- [ ] Which Indian languages do launch tenants issue documents in? This decides which serif Indic families are bundled into the PDF renderer (owner: product).
- [ ] Is Arabic or Hebrew needed by any Singapore or US tenant in the next 12 months (owner: CCO).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

All sizes are in rem with unitless line heights; nothing has a fixed text height, so 200 percent zoom and text-spacing overrides do not clip. Minimum text size is 12 px for metadata only; body is 16 px, and 18 px on party pages for readers with low vision or low literacy.

<!-- check:single-source -->
### Single source of truth and drift

Families and sizes are defined once in `packages/tokens`; the PDF renderer reads `dist/pdf/print.json` for the same families in points, so screen and print typography cannot drift.

<!-- check:i18n -->
### Scripts, languages and direction

Per-script stacks via `:lang()`, taller line heights for Indic scripts (1.7), unicode-range subsetting so scripts load only when used, tabular figures for data, locale digits via Intl. Legal typography is reviewed per document language before a tenant issues documents in it.

<!-- check:performance -->
### Runtime cost and first paint

Typical party page loads 2 Latin WOFF2 files (about 70 KB total, proposed budget). Indic and CJK files load only when needed. Fallbacks are metric-matched to keep CLS under 0.1. Fonts are immutable, hash-named files with long-lived caching.

<!-- check:surfaces -->
### Coverage across surfaces and formal outputs

Email uses system font stacks only (web fonts are unreliable in email clients). PDFs embed Source Serif 4 and the Noto families for the document language. Data tables use tabular figures.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C Design Tokens Community Group",
    "id": "R1",
    "ident": "DTCG Format",
    "kind": "standard",
    "title": "Design Tokens Format Module 2025.10",
    "url": "https://www.designtokens.org/tr/2025.10/format/",
    "version": "2025.10"
  },
  {
    "body": "W3C",
    "excerpt": "Text can be resized up to 200 percent without loss of content or functionality.",
    "id": "R2",
    "ident": "WCAG 2.2 SC 1.4.4",
    "kind": "standard",
    "title": "Understanding SC 1.4.4 Resize Text",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/resize-text"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Web Vitals",
    "url": "https://web.dev/articles/vitals",
    "vendor": "Google"
  },
  {
    "body": "W3C",
    "excerpt": "No loss of content with line height 1.5, paragraph spacing 2x, letter spacing 0.12em, word spacing 0.16em.",
    "id": "R4",
    "ident": "WCAG 2.2 SC 1.4.12",
    "kind": "standard",
    "title": "Understanding SC 1.4.12 Text Spacing",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/text-spacing"
  }
]
```

<!-- end -->
