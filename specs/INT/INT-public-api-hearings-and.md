---
id: "INT-public-api-hearings-and"
title: "Public API — Hearings and scheduling"
parent: "INT-public-api-and-webhooks"
order: 4
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Read and propose hearing slots, time zones, virtual room links and transcript availability"
links: []
rev: 2
syncHash: "6e758f62c0ec5bbc"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.4.4 Public API — Hearings and scheduling

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Read and propose hearing slots, time zones, virtual room links and transcript availability

<!-- section:purpose -->
## Purpose, audience and surface

Read hearings for cases the caller can see, propose hearing slots, see room status and join links, and find transcripts and recordings. Callers: institution systems publishing hearing calendars, counsel-firm calendars, transcription partners checking availability. Scheduling decisions remain with the secretariat or tribunal ([[DOM-hearings]]); the API can **propose** slots, not fix them.

Not exposed: provider join tokens, breakout rooms, attendance of other participants (secretariat only), tribunal private sessions.

<!-- section:resources -->
## Resources and identifiers

```
/v1/cases/{case_id}/hearings
/v1/hearings/{hearing_id}
    /slot-proposals/{proposal_id}
    /room
    /transcripts
```
IDs `hrg_`, `hsp_` (slot proposal). Transcripts and recordings are documents (`doc_`), downloaded through [[INT-public-api-documents-and-filings]].

<!-- section:operations -->
## Operations

| Method and path | Summary | Scope | Safe / idempotent |
|---|---|---|---|
| `GET /v1/cases/{case_id}/hearings` | List hearings | `hearings:read` | safe |
| `GET /v1/hearings/{hearing_id}` | Hearing: type, mode (virtual / hybrid / in person), `starts_at`, `ends_at`, `time_zone`, status, venue | `hearings:read` | safe |
| `GET /v1/hearings?starts_after=&starts_before=` | Calendar view across visible cases | `hearings:read` | safe |
| `POST /v1/hearings/{hearing_id}/slot-proposals` | Propose up to 10 candidate slots for a hearing in `scheduling` status, on behalf of a party | `hearings:write` | Idempotency-Key |
| `GET /v1/hearings/{hearing_id}/slot-proposals` | List proposals visible to caller | `hearings:read` | safe |
| `POST /v1/hearings/{hearing_id}/slot-proposals/{id}/actions/withdraw` | Withdraw own proposal | `hearings:write` | Idempotency-Key |
| `GET /v1/hearings/{hearing_id}/room` | Room status (`not_open`, `lobby_open`, `in_session`, `ended`) and `join_url` (platform URL requiring sign-in) | `hearings:read` | safe |
| `GET /v1/hearings/{hearing_id}/transcripts` | Transcript versions with status (`in_progress`, `draft`, `approved`) and `document_id` when available | `hearings:read` | safe |

<!-- section:schemas -->
## Request and response schemas

```ts
const Hearing = z.object({
  id: z.string(), case_id: z.string(),
  kind: z.string(),                                   // 'procedural', 'merits', 'case_management' (tenant-configurable)
  mode: z.enum(['virtual', 'hybrid', 'in_person']),
  status: z.string(),                                 // 'scheduling', 'scheduled', 'in_session', 'adjourned', 'concluded', 'cancelled'
  starts_at: z.string().datetime().nullable(),        // UTC
  ends_at: z.string().datetime().nullable(),
  time_zone: z.string(),                              // IANA zone of the seat or tribunal choice, e.g. 'Asia/Kolkata'
  venue: z.object({ name: z.string(), address: Address.nullable() }).nullable(),
  recording_available: z.boolean(), transcript_status: z.string().nullable(),
});

const SlotProposalCreate = z.object({
  on_behalf_of_party_id: z.string(),
  slots: z.array(z.object({ starts_at: z.string().datetime(), ends_at: z.string().datetime() }).strict()).min(1).max(10),
  note: z.string().max(1000).optional(),
}).strict();
```
Slots must fall inside the scheduling window set by the secretariat and are checked against holiday calendars of the seat ([[PKG-calendars-and-deadline]]); conflicts are returned as warnings, not errors.

<!-- section:errors -->
## Error model

Shared problem types plus: `hearing-not-in-scheduling` (409), `slot-outside-window` (422, with the window), `slot-invalid-range` (422, end before start or longer than 12 h), `too-many-proposals` (409, max 3 open proposals per party per hearing).

<!-- section:auth -->
## Authentication, scopes and permissions

Scopes `hearings:read`, `hearings:write`. A client may propose only for parties it represents or, as secretariat integration, for any party. `join_url` is a platform URL that requires the human participant to sign in; the API never returns provider tokens ([[INT-video-conferencing-for-hearings]]).

<!-- section:tenancy -->
## Tenancy and region routing

The tenant is taken only from the credential (API key or OAuth token), which is bound to one tenant and one region ([[INT-public-api-and-webhooks#auth]]). The auth middleware opens the request transaction and sets `app.tenant_id` through the Prisma extension ([[MT-prisma-client-extension-wraps]]); forced RLS ([[MT-rls-enabled-and-forced-on]]) is the final layer under the object-level policy checks. No path, query or body field can select a tenant; `tenant_id` is not accepted in any write schema (`additionalProperties: false`). A credential used against another region's base URL gets `421` problem `wrong-region`. A suspended tenant gets read access and the protected due-process actions only; other writes return `403` problem `tenant-suspended-readonly`. Unknown and forbidden IDs both return the same `404 not-found`.

<!-- section:pagination -->
## Pagination, filtering and sorting

Cursor pagination; calendar query limited to 92-day ranges; order by `starts_at, id`. Index `(tenant_id, starts_at)` on hearings, joined with case visibility.

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

Slot proposals require `Idempotency-Key`. No long-running operations in this family.

<!-- section:events -->
## Webhooks and events

`hearing.scheduled`, `hearing.rescheduled`, `hearing.cancelled`, `hearing.recording_available`, `transcript.available` ([[INT-webhook-event-catalogue]]).

<!-- section:limits -->
## Rate limits and quotas

Standard limits; calendar query counts as a normal read; proposals 30 per minute per client.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

Additive only within `/v1`; `kind` and `status` values may grow and must be tolerated.

<!-- section:questions -->
## Open questions

- [ ] Do institutions want the API to **fix** a hearing time (secretariat integration), not only propose? Proposed: later version.
- [ ] Should participant availability (busy / free) be accepted from counsel calendars through the API?
- [ ] Is exposing `venue.address` for in-person hearings acceptable to all tenants?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Hearings are visible only through case visibility for the client's principal; private sessions and breakouts are not modelled in the public schema at all.

<!-- check:security -->
### Attack surface and abuse resistance

No provider tokens or bearer join links are returned; `join_url` requires a signed-in participant, so a leaked URL does not admit anyone.

<!-- check:consumability -->
### Developer experience and onboarding

All times in UTC with an explicit IANA `time_zone`, matching other families; calendar range queries for direct calendar sync.

<!-- end -->
