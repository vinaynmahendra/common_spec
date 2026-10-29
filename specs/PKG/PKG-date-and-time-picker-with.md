---
id: "PKG-date-and-time-picker-with"
title: "Date and time picker with time zones"
parent: "PKG-ui-design-system"
order: 5
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Hearing scheduler and deadline entry across participants' time zones"
links: []
rev: 2
syncHash: "7737702aa182f182"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.5 Date and time picker with time zones

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Hearing scheduler and deadline entry across participants' time zones

<!-- section:purpose -->
## Purpose and when to use

`DatePicker` enters a calendar date (deadline, date of agreement); `DateTimePicker` enters an instant in a stated time zone (hearing start, extension expiry); `TimeZoneSelect` picks an IANA zone. Used by the hearing scheduler in `(secretariat)`, deadline entry and extension orders in `(neutral)`, and filing forms. The component stores and emits unambiguous values; deadline arithmetic (business days, holidays) is owned by [[PKG-calendars-and-deadline]]. APG patterns: date picker dialog / combobox date picker [R1].

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element / role |
|---|---|---|
| Label | Yes | `<label>` / group label |
| Segmented input | Yes | Day, month, year (and hour, minute) segments as `role="spinbutton"` each with label, in locale order |
| Calendar button | Yes | `IconButton` "Choose date" |
| Calendar popup | On open | `role="dialog"` with `role="grid"` month view |
| Time zone | DateTimePicker | `TimeZoneSelect` (combobox) showing "Asia/Kolkata (IST, UTC+05:30)" |
| Participant preview | Optional | List of the same instant in each participant's zone |
| Hint and error | As form fields | |

<!-- section:variants -->
## Variants and sizes

`DatePicker` (date only), `DateTimePicker` (date, time, zone), `DateRangePicker` (availability windows). Granularity: minute, with 5-minute steps by default for hearings.

<!-- section:states -->
## States

Default, focus (per segment), open, invalid (impossible date, out of `min`/`max`, falls on a non-business day when `businessDaysOnly`), disabled, read-only. Non-business and holiday dates in the calendar are marked with text ("Holiday: Diwali") and a pattern, not colour only. DST gaps and overlaps show a warning: "This time does not exist in Europe/London on 29 March; choose another time" or "This time occurs twice; choose which one".

<!-- section:api -->
## Props API

```ts
import type { CalendarDate, ZonedDateTime } from '@internationalized/date';

export type DatePickerProps = FieldCommon & {
  value: CalendarDate | null; onValueChange: (v: CalendarDate | null) => void;
  min?: CalendarDate; max?: CalendarDate;
  isDateUnavailable?: (d: CalendarDate) => { unavailable: boolean; reason?: string };  // from calendars package
};
export type DateTimePickerProps = FieldCommon & {
  value: ZonedDateTime | null; onValueChange: (v: ZonedDateTime | null) => void;
  defaultTimeZone: string;           // IANA, from user preference, else tenant seat zone
  allowTimeZoneChange?: boolean;     // default true
  participants?: Array<{ label: string; timeZone: string }>;   // preview list
  minuteStep?: 1 | 5 | 15;           // default 5
};
```
Values are emitted as `CalendarDate` (no zone, for date-only deadlines whose zone is defined by the rule set) or `ZonedDateTime`; the API layer serialises `ZonedDateTime` as an ISO 8601 instant plus the IANA zone. The component never emits a bare local time.

<!-- section:behaviour -->
## Behaviour

Each user sees times in their own preferred zone by default with the zone always shown in text ([[I18N-l10n]]). The scheduler preview lists the hearing time for each participant (for example "Singapore 9:00 am Tue 4 Nov, New York 8:00 pm Mon 3 Nov") so cross-day effects are visible. Typing is always possible; the calendar is optional. Unavailable dates come from `isDateUnavailable`, implemented by the caller using the tenant's holiday calendars. Client component; the calendar popup code is lazy-loaded on first open.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

| Context | Key | Action |
|---|---|---|
| Segment | Up / Down | Increment / decrement |
| Segment | Digits | Type value; moves to next segment when complete |
| Segment | Left / Right | Previous / next segment |
| Segment | Backspace | Clear segment |
| Calendar grid | Arrows | Move by day / week |
| Calendar grid | Page Up / Down | Previous / next month (Shift: year) |
| Calendar grid | Home / End | Start / end of week |
| Calendar grid | Enter / Space | Select and close; focus returns to the calendar button |
| Calendar | Escape | Close without change; focus returns to the button |

Each segment has an accessible name ("Day", "Month", "Year", "Hour", "Minute"); the grid has a heading with month and year; unavailable dates have the reason in their accessible description. WCAG: 1.3.1, 2.1.1, 2.4.3, 3.3.1, 3.3.2, 4.1.2.

<!-- section:content -->
## Content guidelines

Always display absolute dates with weekday and zone ("Tuesday 4 November 2026, 9:00 am SGT"). Never "tomorrow" in legal contexts. Errors: "Enter a hearing date after 3 November 2026", "The deadline cannot fall on a public holiday in Hong Kong; the next working day is 5 November".

<!-- section:tokens -->
## Tokens used

Field tokens, `calendar.day.bg.{selected,today,hover}`, `calendar.day.unavailable.pattern`, `color.text.muted`, `elevation.2`, `radius.lg`.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md` the calendar opens as a bottom sheet; segments remain typeable. Locale decides segment order (DD/MM/YYYY for en-IN and en-SG, MM/DD/YYYY for en-US) and 12 or 24-hour clock. RTL mirrors the grid order.

<!-- section:examples -->
## Usage examples

```tsx
<DateTimePicker label={t('hearing.start')} value={start} onValueChange={setStart}
  defaultTimeZone={userTz ?? tenant.seatTimeZone}
  participants={tribunal.concat(parties).map(p => ({ label: p.displayName, timeZone: p.timeZone }))} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: unit tests across DST transitions (Europe/London, America/New_York) and zones without DST (Asia/Kolkata, Asia/Singapore, Asia/Hong_Kong); locale order tests for en-IN, en-US, zh-Hant; holiday marking with a fixture calendar.

<!-- section:questions -->
## Open questions

- [ ] For date-only deadlines, confirm whose time zone defines end of day: the seat of arbitration, the institution, or the filing party (owner: legal, with [[PKG-calendars-and-deadline]]).
- [ ] Confirm `@internationalized/date` as the date library (ties to the React Aria ADR) (owner: frontend lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Segmented spinbuttons each with a name, typeable entry with the calendar optional, APG grid keyboard model, unavailable dates explained in text, focus returns to the trigger on close.

<!-- check:i18n -->
### Localisation and long content

Locale-driven segment order and clock, IANA zones with the zone always displayed, participant preview across zones, DST gap and overlap handling; formatting via [[I18N-l10n]].

<!-- check:resilience -->
### Async, errors and edge cases

The component never emits an ambiguous local time; impossible or ambiguous DST times raise inline errors; unavailable dates are validated on the server again by the calendars package.

<!-- check:performance -->
### Performance and bundle cost

Calendar popup is lazy-loaded; proposed budget 30 KB compressed including the date library.

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
  }
]
```

<!-- end -->
