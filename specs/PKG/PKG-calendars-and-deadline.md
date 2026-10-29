---
id: "PKG-calendars-and-deadline"
title: "Calendars and deadline computation"
parent: "PKG"
order: 16
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Holiday calendars per jurisdiction and seat, business-day and time-zone rules, deadline arithmetic used by workflows, rules and reports"
links: []
rev: 3
syncHash: "9df9ebb16f5fa6b7"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.16 Calendars and deadline computation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Holiday calendars per jurisdiction and seat, business-day and time-zone rules, deadline arithmetic used by workflows, rules and reports

<!-- section:purpose -->
## Purpose and scope

`@nomology/calendars` answers "when is this due?" correctly and reproducibly: holiday calendars per jurisdiction and seat, tenant closure days, business-day rules, time-zone handling and deadline arithmetic used by workflows (Temporal timers), the rules engine, the secretariat console and reports. Every computed deadline comes with an explanation and the calendar versions used, so an institution can show how a date was reached.

**Does not:** decide the period that applies (the rules engine decides "30 days from service"; this package turns that into a date); send reminders (workflows); define legal time-computation rules as fixed code — the counting conventions are parameters chosen by the rule set, because they vary by institution rules and law. Assumption: the conventions listed below cover the rule sets we know of; legal must confirm per tenant.

**Ownership (shared-model decision D13).** This package owns calendar **computation**: holiday and seat calendars, counting conventions, business-day and business-hour arithmetic, and the explanation of every computed date. [[WF-sla-and-business-calendars]] owns **configuration** of business schedules (`wf.business_schedule`: working hours, tenant and unit closures, bindings to region, tenant, unit and work queue) and of SLA policies; tenants edit them at `/admin/workflows/calendars` and `/admin/workflows/sla-policies`. The split is:

| Clock | Calendar | Configured in | Computed by |
|---|---|---|---|
| Procedural deadline (`case_deadlines`, [[DOM-cases-schema]]) | Seat calendars and the case's seat time zone | Rule set and decision tables pinned to the case; `case.deadline.*` settings ([[PKG-settings-cases-and-workflows]]) | This package |
| Service-level target (`wf.sla_clock`) | Business schedule of the work queue, unit, tenant or region | [[WF-sla-and-business-calendars]]; `workflow.calendar.*` settings | This package, reading the schedule by key |

The two kinds of clock are never mixed: a procedural deadline never uses a business schedule, and an SLA never uses a seat calendar.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| Case lifecycle workflows | Compute response and reply deadlines after service; set Temporal timers to the computed instant |
| Hearing scheduling | Business-day checks across participants' time zones; avoid seat holidays |
| Secretariat console | Deadline countdown badges ([[PKG-status-and-deadline-badges]]), extension previews |
| Rules engine built-ins | `addBusinessDays`, `isBusinessDay` inside decision outputs |
| SEBI ODR tenant reports | Elapsed days per stage for status reporting ([[RPT-example]]) |
| Human tasks ([[WF-human-tasks]]) and SLA clocks ([[WF-sla-and-business-calendars]]) | SLA due times in business hours, from the business schedule bound to the queue, unit or tenant |

<!-- section:api -->
## Public API

```ts
// packages/calendars/src/index.ts (server-only; pure functions over loaded calendar snapshots)
export type DurationUnit = 'calendar_days' | 'business_days' | 'hours' | 'business_hours' | 'weeks' | 'months';

export interface DeadlineSpec {
  start: Date;                               // the triggering event instant (e.g. deemed service time), UTC
  duration: { value: number; unit: DurationUnit };
  calendars: string[];                       // e.g. ['IN-NATIONAL', 'IN-KA', 'tenant:closures']; union of non-working days
  timeZone: string;                          // IANA tz of the seat or tenant, e.g. 'Asia/Kolkata'
  conventions: {
    excludeStartDay: boolean;                // count from the day after the event
    rollIfNonWorking: 'next_working_day' | 'previous_working_day' | 'none';
    dueAt: 'end_of_day' | { localTime: string };   // e.g. '23:59:59' or '17:00'
    monthOverflow?: 'last_day_of_month' | 'next_day';  // e.g. 31 Jan + 1 month
  };
}
export interface DeadlineResult {
  dueAt: Date;                               // UTC instant
  dueLocal: string;                          // ISO local date-time in spec.timeZone
  calendarVersions: Record<string, string>;  // calendar code -> dataset version used
  explanation: ExplanationStep[];            // human-readable steps, e.g. 'Skipped 2026-10-02 (Gandhi Jayanti, IN-NATIONAL)'
  specHash: string;                          // sha256 of canonical spec
}

export function computeDeadline(tx: TenantTx, spec: DeadlineSpec): Promise<DeadlineResult>;
export function isWorkingDay(tx: TenantTx, date: string /* YYYY-MM-DD */, calendars: string[]): Promise<boolean>;
export function workingDaysBetween(tx: TenantTx, from: Date, to: Date, calendars: string[], timeZone: string): Promise<number>;
export function loadSnapshot(tx: TenantTx, calendars: string[], range: { from: string; to: string }): Promise<CalendarSnapshot>; // for Temporal: pass into workflow input
export function computeWithSnapshot(snapshot: CalendarSnapshot, spec: DeadlineSpec): DeadlineResult;  // pure, synchronous

// Tenant and unit closures: written by the business-schedule configuration in WF-sla-and-business-calendars (permission checked there)
export function upsertTenantClosure(tx: TenantTx, day: { date: string; name: string; reason?: string }): Promise<void>;
export function onCalendarChanged(handler: (evt: { calendar: string; days: string[] }) => Promise<void>): void;  // lets workflows flag affected deadlines

export class CalendarNotLoadedError extends Error {}   // date outside loaded range (e.g. calendar not published that far ahead)
export class InvalidTimeZoneError extends Error {}
```

<!-- section:usage -->
## Usage examples

```ts
// Activity: compute a response deadline after service, then the workflow sleeps until it
const result = await calendars.computeDeadline(tx, {
  start: servedAt,
  duration: { value: 30, unit: 'calendar_days' },          // from rules engine 'response-deadline'
  calendars: ['IN-NATIONAL', 'IN-KA', 'tenant:closures'],
  timeZone: 'Asia/Kolkata',
  conventions: { excludeStartDay: true, rollIfNonWorking: 'next_working_day', dueAt: 'end_of_day' },
});
await deadlines.record(tx, { caseId, kind: 'RESPONSE', ...result });   // stored with versions and explanation
return result.dueAt;   // workflow: await sleep(dueAt - now)
```

<!-- section:tenant -->
## Tenant context

Public calendars (`ref.calendar`, `ref.calendar_day`) are shared reference data ([[PKG-reference-and-seed-data]]); tenant closures (`calendars.tenant_closure`, tenant-owned, forced RLS) are addressed as `tenant:closures` and resolved only for the context tenant. `computeDeadline` requires tenant context because tenant closures and the tenant's default seat calendars come from it. Computations are pure given a snapshot, so Temporal workflows receive a snapshot or call the Activity — they never call the database from workflow code.

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Level |
|---|---|---|
| Seat calendars and time zone | From the case seat; `case.deadline.seat_calendar_source` (`seat` or `tenant_default`) chooses the fallback ([[PKG-settings-cases-and-workflows]]) | Offering, tenant, case type |
| Business schedules for SLA clocks | `workflow.calendar.region_default_schedule`, `workflow.calendar.tenant_default_schedule`, `workflow.calendar.unit_schedule` ([[WF-sla-and-business-calendars]]) | Platform, region, tenant, unit |
| Calendar horizon | Public calendars loaded at least 18 months ahead (`workflow.calendar.public_calendar_horizon_months`); `CalendarNotLoadedError` beyond | Platform |
| Weekend days | Per calendar (`ref.calendar.weekend_days`) | Reference data |
| Tenant and unit closures | Closure days (`tenant:closures`, `unit:<id>:closures`) maintained with business schedules in [[WF-sla-and-business-calendars]]; they apply to procedural deadlines only where the rule set lists `tenant:closures` | Tenant, unit |
| Change handling | When a calendar changes, already-computed deadlines are **not** moved automatically; affected deadlines are listed for case-manager review (`case.deadline.calendar_change_review`) | Platform rule, tenant choice of review mode |

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `CalendarNotLoadedError` | No (until data loaded) | Human task to secretariat; alert operations to publish calendar |
| `InvalidTimeZoneError` | No | Configuration error |
| Validation errors on spec | No | Bug in caller or rule set |

<!-- section:nfr -->
## Performance and limits

`computeWithSnapshot` p99 ≤ 1 ms; `computeDeadline` with cold snapshot load ≤ 20 ms. Snapshots cached per calendar version in process.

<!-- section:versioning -->
## Versioning and compatibility

Package semver. Calendar data is versioned by dataset version; results record the versions used, so recomputation after a correction shows a difference instead of silently changing a stored date. Time-zone rules come from the IANA tzdb bundled with the Node.js runtime; the tzdb version is recorded with each result.

<!-- section:testing -->
## Test contract

- Table-driven tests for every convention combination, month-end overflow, leap years, DST transitions (US time zones), cross-midnight due times, and starts on non-working days.
- Golden examples reviewed by legal for each tenant type (assumption: legal provides worked examples per institution rule set).
- Property tests: result is never a non-working day when `rollIfNonWorking` is set; adding 0 business days on a working day returns the same day.
- Isolation: tenant closures of A never affect B.

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm counting conventions per tenant type (for example whether the day of service is excluded, what happens when the last day is a holiday, deemed service rules for email). Until confirmed, conventions are explicit parameters per rule set.
- [ ] Who publishes public holiday calendars per jurisdiction and how quickly after official notification? Owner: operations (see [[PKG-reference-and-seed-data#questions]]).
- [ ] Should a calendar correction create a human task for each affected open deadline, or a single digest for the secretariat?
- [ ] Multi-participant deadlines across time zones: is the seat's time zone always authoritative? Assumption: yes, unless the rule set says otherwise.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Public calendars are shared reference data without personal data; tenant closures are tenant-owned with forced RLS and resolved only for the context tenant.

<!-- check:residency -->
### Region awareness

Public calendars are loaded identically into each regional database from the repository; tenant closures and computed deadlines stay in the tenant's region. No external calendar API is called at run time.

<!-- check:audit -->
### Audit events

Tenant closure changes are audited; computed deadlines are stored by the domain with the explanation and versions, and deadline extensions are audited by the domain action.

<!-- check:observability -->
### Observability

Spans `calendars.compute` with attributes for calendar codes, versions and duration unit (no case data). Metrics: computations, `CalendarNotLoadedError` count by calendar (alert at any occurrence, because it means a calendar horizon is too short), and count of deadlines flagged after a calendar change.

<!-- check:resilience -->
### Failure behaviour

Computation is pure and deterministic given a snapshot; Activities are safe to retry. Results are stored with calendar versions, spec hash and explanation, so a retry or recomputation can be compared.

<!-- check:change-safety -->
### Change and release safety

Calendar corrections are new dataset versions and never move stored deadlines silently; affected deadlines are listed for secretariat review. Changes to counting conventions are parameters in rule sets, so code changes to the arithmetic are rare and must pass the legal-reviewed golden examples.

<!-- check:testing -->
### Testing

Table-driven convention tests, DST and leap-year cases, property tests, legal-reviewed golden examples per tenant type, and isolation tests.

<!-- end -->
