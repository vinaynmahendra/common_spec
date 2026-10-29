---
id: "PKG-data-table"
title: "Data table"
parent: "PKG-ui-design-system"
order: 7
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Case list, document list and transcriber queue: sorting, filtering, selection, pagination, virtualisation"
links: []
rev: 2
syncHash: "69891da6b33c5359"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.7 Data table

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Case list, document list and transcriber queue: sorting, filtering, selection, pagination, virtualisation

<!-- section:purpose -->
## Purpose and when to use

`DataTable` shows tabular data with sorting, filtering, row selection, bulk actions, pagination and virtualisation. Used for the secretariat case queue (hundreds of matters), document lists inside a case, the transcriber job queue and tenant admin user lists. It is a semantic `<table>` by default; it uses the APG Grid pattern only when cells contain interactive widgets that need arrow-key navigation [R1]. Charts' "View as table" alternative also uses it.

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Caption | Yes | `<caption>` (can be visually hidden) |
| Toolbar | No | Filters, search, column chooser, density toggle; `role="toolbar"` only if arrow-key navigation is implemented |
| Header cell | Yes | `<th scope="col">` with sort `Button` inside and `aria-sort` on the `<th>` |
| Selection checkbox column | When selectable | Checkbox per row with name "Select {row label}"; header "Select all on this page" |
| Body row / cell | Yes | `<tr>`, `<td>`; first meaningful column `<th scope="row">` |
| Bulk action bar | When rows selected | Region announcing "3 selected" with actions |
| Pagination | Server mode | `<nav aria-label="Pagination">` with page buttons and page size select |
| Empty / loading / error | Yes | Row spanning all columns |

<!-- section:variants -->
## Variants and sizes

`client` mode (up to 500 rows in memory; sort and filter client-side) and `server` mode (sort, filter and pagination parameters passed to the caller's loader). Virtualised rendering is enabled automatically above 200 rendered rows. Densities: comfortable (48 px rows) and compact (36 px, secretariat and transcriber only).

<!-- section:states -->
## States

| State | Visual | Announced |
|---|---|---|
| Loading first page | Skeleton rows after 300 ms | "Loading cases" |
| Loaded | Rows | Polite: "Showing 1–50 of 412 cases, sorted by deadline, ascending" after sort, filter or page change |
| Empty (no data) | Message and primary action | Text in table |
| Empty (filters) | "No cases match these filters" + Clear filters | Same |
| Error | Message + Retry | Assertive once |
| Row selected | `datatable.row.bg.selected` + checked checkbox + 2 px inline-start bar | Checkbox state |
| Row stale (data changed) | Banner "This list has updates. Refresh" | Polite |

<!-- section:api -->
## Props API

```ts
type Column<Row> = {
  id: string; header: string; cell: (row: Row) => ReactNode;  // text-first content
  sortable?: boolean; width?: 'auto' | 'min' | 'grow'; isRowHeader?: boolean; hideBelow?: 'md' | 'lg';
};
type Query = { sort?: { id: string; dir: 'asc' | 'desc' }; filters: Record<string, unknown>; page: number; pageSize: 25 | 50 | 100 };

export type DataTableProps<Row> = {
  caption: string; rowKey: (r: Row) => string; rowLabel: (r: Row) => string;   // rowLabel used in checkbox names
  columns: Column<Row>[];
  selection?: { mode: 'none' | 'multiple'; selected: Set<string>; onSelectedChange: (s: Set<string>) => void };
  bulkActions?: (selected: Set<string>) => ReactNode;
} & (
  | { mode: 'client'; rows: Row[] }
  | { mode: 'server'; query: Query; onQueryChange: (q: Query) => void; page: { rows: Row[]; total: number }; status: 'loading' | 'ready' | 'error'; onRetry: () => void }
);
```
Sort, filter and page state is held by the caller in the URL search params (per [[APP-client-state-and-data-fetching]]) so views are shareable and survive refresh.

<!-- section:behaviour -->
## Behaviour

In server mode the caller's tRPC query runs under RLS; the table never receives rows the user may not see. "Select all" selects the current page; selecting all matching rows across pages is an explicit second action ("Select all 412 matching cases") that passes a filter to the bulk action, never a list of hidden IDs. Bulk actions with legal effect go through [[PKG-modal-dialog-and-consequential]]. Virtualisation keeps DOM rows under about 60 while `aria-rowcount` and `aria-rowindex` keep the real counts for screen readers. Headers are sticky; focused rows scroll into view clear of the sticky header (2.4.11). Server component for static read-only tables; client component when sorting, selection or virtualisation is used.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

Semantic table mode: Tab moves through interactive elements (sort buttons, checkboxes, row links, row action buttons); screen reader table navigation works natively. Grid mode (opt-in, for the transcriber queue with inline status menus): arrow keys move between cells, Enter activates, Home / End move to row start / end, Ctrl+Home / End to first / last cell, Space toggles row selection. Sort buttons announce the new sort through `aria-sort` and the polite summary. WCAG: 1.3.1, 1.3.2, 2.1.1, 2.4.3, 2.4.11 [R2], 4.1.2, 4.1.3.

<!-- section:content -->
## Content guidelines

Caption names the table ("Open cases assigned to you"). Column headers are short nouns. Dates use absolute format with time zone where times are shown. Empty states say what to do next.

<!-- section:tokens -->
## Tokens used

`datatable.header.bg` (surface.subtle), `datatable.row.bg.{default,hover,selected}`, `datatable.row.height`, `datatable.border` (border.default), `typography.data.cell`, `typography.data.numeric`, `elevation.1` (sticky header), `color.focus.ring`.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md`, the table becomes a list of cards (one per row) with the row header as the card title and other columns as label / value pairs; selection and actions remain. Columns marked `hideBelow` move into the card body. At 400 percent zoom the card layout applies, so there is no two-dimensional scroll for content (1.4.10); wide numeric tables that genuinely need two dimensions (fee schedules) are allowed to scroll horizontally inside a labelled, focusable region.

<!-- section:examples -->
## Usage examples

```tsx
<DataTable mode="server" caption={t('queue.caption')} columns={caseColumns} rowKey={r => r.id} rowLabel={r => r.reference}
  query={query} onQueryChange={setQueryInUrl} page={data} status={status} onRetry={refetch}
  selection={{ mode: 'multiple', selected, onSelectedChange: setSelected }}
  bulkActions={(s) => <Button onPress={() => openAssign(s)}>{t('queue.assign')}</Button>} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: 5,000-row virtualised story with performance assertion (scroll at 60 fps target, sort under 100 ms client mode for 500 rows); screen reader check of `aria-rowcount` with virtualisation; card layout snapshot at 320 px.

<!-- section:questions -->
## Open questions

- [ ] Do secretariat users need saved views (named filter sets) in the first release (owner: product, secretariat console).
- [ ] Is grid mode needed beyond the transcriber queue (owner: frontend lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Semantic `<table>` with caption, scoped headers and `aria-sort`; grid pattern only when needed; selection checkboxes named per row; polite summary after sort, filter and page changes; virtualisation keeps `aria-rowcount`; sticky headers do not hide focus; card layout for reflow.

<!-- check:security -->
### Data safety in the component

Rows come from the caller's tRPC query under RLS; "select all matching" passes a server-side filter, not hidden IDs; row data is never put in `data-*` attributes or URLs other than the row's own route.

<!-- check:resilience -->
### Async, errors and edge cases

Skeleton after 300 ms, inline error with Retry, stale-data banner instead of silently reordering rows under the user, selection preserved across refetch when row keys persist.

<!-- check:performance -->
### Performance and bundle cost

Virtualisation above 200 rows keeps DOM size small; server mode for large queues; proposed budget 25 KB compressed.

<!-- check:testing -->
### Test and documentation coverage

Stories for client and server modes, empty, error, 5,000 rows, RTL and 320 px card layout; interaction tests for keyboard sorting and selection; visual matrix as for all components.

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
    "ident": "WCAG 2.2 SC 2.4.11",
    "kind": "standard",
    "title": "Understanding SC 2.4.11 Focus Not Obscured (Minimum)",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum"
  }
]
```

<!-- end -->
