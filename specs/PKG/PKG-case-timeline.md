---
id: "PKG-case-timeline"
title: "Case timeline"
parent: "PKG-ui-design-system"
order: 11
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Chronological case events, deadlines and filings with filters"
links: []
rev: 2
syncHash: "11efea57e136faee"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.11 Case timeline

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Chronological case events, deadlines and filings with filters

<!-- section:purpose -->
## Purpose and when to use

`CaseTimeline` shows a case's events in chronological order: filings, orders, hearings, deadlines (past and upcoming), payments, appointments and status changes. Used on the case overview for all personas (each sees only what their permissions allow). It is a read-only list with filters, not an activity log for audit (that is [[PKG-audit-trail]]).

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Heading | Yes | `<h2>` "Case timeline" |
| Filter bar | No | `CheckboxGroup` of event types and a "Show upcoming deadlines" toggle |
| Date group | Yes | `<h3>` per day ("Tuesday 4 November 2026") |
| Event list | Yes | `<ol>` |
| Event item | Yes | `<li>` with `<article aria-labelledby>`: type icon, title (link to the item), actor ("Filed by Counsel for Claimant"), time with zone, status badge if relevant |
| "Today" marker | Yes | Separator `<li>` with text "Today" between past and upcoming |
| Load earlier | When paginated | Button |

<!-- section:variants -->
## Variants and sizes

`full` (case overview) and `compact` (side panel in the neutral workspace: titles and dates only). Order: newest first (default) or oldest first (user toggle, remembered per user).

<!-- section:states -->
## States

Loading (skeleton after 300 ms), loaded, empty ("No events yet"), filtered empty ("No events match these filters. Clear filters"), error with Retry, new events available (polite banner "2 new events. Show"), item states via [[PKG-status-and-deadline-badges]].

<!-- section:api -->
## Props API

```ts
type TimelineEvent = {
  id: string; type: 'filing' | 'order' | 'award' | 'hearing' | 'deadline' | 'payment' | 'appointment' | 'status' | 'notice';
  occurredAt: string;                // ISO instant; deadlines use dueAt
  title: string; href?: string; actorLabel?: string;
  status?: { tone: StatusTone; label: string };
  deadline?: { dueAt: string; timeZone: string };
};
export type CaseTimelineProps = {
  events: TimelineEvent[]; hasMore: boolean; onLoadMore: () => void;
  filters: Set<TimelineEvent['type']>; onFiltersChange: (f: Set<TimelineEvent['type']>) => void;
  order: 'newest' | 'oldest'; onOrderChange: (o: 'newest' | 'oldest') => void;
  timeZone: string; variant?: 'full' | 'compact';
};
```
Events are built server-side by a read model that applies case-level permissions and confidentiality tiers ([[SEC-data-classification]]); for example tribunal-only deliberation items never reach party views.

<!-- section:behaviour -->
## Behaviour

Server component for the initial render; filter and load-more interactions in a small client island. Filters are reflected in the URL. New events arrive through the case's in-app notification channel and are shown only after the user selects "Show", so the list never shifts under the reader.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

Normal document navigation: headings per day for screen reader heading navigation, links per event, Tab to filters and load more. After "Load earlier", focus moves to the first newly loaded item. WCAG: 1.3.1, 1.4.1, 2.4.4, 2.4.6, 4.1.3 for the new-events banner.

<!-- section:content -->
## Content guidelines

Titles name the document or event ("Statement of Defence filed", "Procedural Order No. 2 issued", "Hearing scheduled: 4 November 2026, 9:00 am SGT"). Actors are described by case role, not personal name, in party-facing views where the tenant's rules require it.

<!-- section:tokens -->
## Tokens used

`timeline.rail` (border.default), `timeline.marker.{type}` (neutral, with icon), `timeline.today` (action.primary.bg), status tones via badges, `typography.heading.sm`, `typography.body.md`, `space.stack.md`.

<!-- section:responsive -->
## Responsive behaviour and direction

The rail moves to the inline-start edge on narrow screens; long titles wrap. RTL mirrors the rail.

<!-- section:examples -->
## Usage examples

```tsx
<CaseTimeline events={events} hasMore={hasMore} onLoadMore={loadMore} filters={filters} onFiltersChange={setFilters}
  order={order} onOrderChange={setOrder} timeZone={userTz} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: 500-event story, permission fixtures (party view vs tribunal view data sets), focus after load more.

<!-- section:questions -->
## Open questions

- [ ] Which event types are visible to each persona and confidentiality tier; needs the domain matrix from [[DOM-cases]] (owner: domain lead, cases).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Day headings and an ordered list of articles; each event has a link and text status; "Today" separator is text; new events wait behind a polite banner instead of shifting content.

<!-- check:i18n -->
### Localisation and long content

All dates are absolute with zone in the viewer's preferred time zone; day grouping is computed in that zone, so an event late on 3 November in New York is grouped correctly for a Singapore viewer.

<!-- check:security -->
### Data safety in the component

Events come from a server read model that applies case permissions and confidentiality tiers, so the component never receives items the viewer may not see.

<!-- check:resilience -->
### Async, errors and edge cases

New events wait behind a "Show" banner rather than shifting the list; load-more errors show inline Retry without losing loaded events; empty and filtered-empty states are distinct.

<!-- check:performance -->
### Performance and bundle cost

Initial render is a server component, so no client JavaScript is needed to read the timeline; only filters and load-more hydrate. Events are paginated (50 per page) so very long cases do not grow the page without limit.

<!-- end -->
