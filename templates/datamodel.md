# Template: Data model and schema (`datamodel`)

Generated from `datamodel.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies the physical data model for one bounded context or shared package: tables, columns, constraints, indexes, Row-Level Security policies, retention and the migrations that get there, so the schema enforces tenancy and business invariants rather than relying on application code.

**Depth:** 3-10 pages plus the Prisma schema and migration SQL, linked from the repository. Every table, column, constraint, index and RLS policy in scope must be listed exactly; vague types ("string", "date") are not acceptable. Write the diagram and tables first, then the migration plan. Split into children when a context has more than about 15 tables, or when a table family (for example audit or document versions) has its own retention and partitioning design.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Scope and ownership (level 1)

Which bounded context or package this schema belongs to, which team owns it, which Prisma schema file and Postgres schema it lives in, and which other contexts may read or reference it (and how: foreign key, ID only, or via API).

Illustrative example (not a requirement):

> **Cases schema.** Owner: Case domain team. Prisma file `packages/db/prisma/cases.prisma`, Postgres schema `app`.
> 
> | Consumer | Access |
> |---|---|
> | Hearings | FK to `case(tenant_id, id)` |
> | Documents | FK to `case` and `party` |
> | Reporting warehouse | Read-only replica via reporting role (3.3.5.3) |
> | Billing | Case ID only; no FK (separate lifecycle) |
> 
> Out of scope: neutral profiles (Neutrals schema), file bytes (object storage; only metadata here).

### `entities` Entities and relationships (level 1)

Entity-relationship diagram (Mermaid) and a short table of relationships with cardinality and ownership. Mark aggregate roots and which tables are tenant-owned, platform-level or shared reference data.

Illustrative example (not a requirement):

> ```mermaid
> erDiagram
>   tenant ||--o{ case : owns
>   case ||--o{ party : has
>   party ||--o{ party_representative : "represented by"
>   case ||--o{ case_status_event : history
>   case }o--|| rule_set : "governed by"
> ```
> 
> | Table | Class | Aggregate |
> |---|---|---|
> | `case` | Tenant-owned | Root |
> | `party`, `party_representative` | Tenant-owned | Case |
> | `case_status_event` | Tenant-owned, append-only | Case |
> | `rule_set` | Tenant-owned, versioned (HKIAC 2024, SEBI ODR) | Own root |
> | `country`, `currency` | Platform reference, no tenant_id | n/a |

### `tables` Tables and columns (level 1)

For each table: every column with exact Postgres type, nullability, default, meaning and data classification (public, internal, personal, confidential, sensitive personal). State naming conventions and types for IDs, money, timestamps and enums once.

Illustrative example (not a requirement):

> **`party`**
> 
> | Column | Type | Null | Default | Meaning | Class |
> |---|---|---|---|---|---|
> | `tenant_id` | `uuid` | no | from `app.tenant_id` | Owning tenant | internal |
> | `id` | `uuid` | no | UUIDv7 from app | PK | internal |
> | `case_id` | `uuid` | no | | Case | internal |
> | `role` | `party_role` enum | no | | claimant, respondent, intervener | internal |
> | `kind` | `text` check in ('individual','organisation') | no | | | internal |
> | `display_name` | `text` | no | | Name as filed | personal |
> | `email` | `citext` | yes | | Service address | personal |
> | `tax_id_enc` | `bytea` | yes | | PAN / UEN, app-encrypted | sensitive personal |
> | `created_at` | `timestamptz` | no | `now()` | | internal |
> | `version` | `integer` | no | `1` | Optimistic concurrency | internal |
> 
> Conventions: snake_case; `timestamptz` only (stored UTC); money as `numeric(18,2)` + `char(3)` currency; no `float` for money or durations.

### `keys` Keys and constraints (level 1)

Primary keys, foreign keys (with ON DELETE behaviour), unique, check and exclusion constraints. Foreign keys between tenant-owned tables include tenant_id so a row can never reference another tenant's row. Say which business rules the database enforces and which are left to application code, and why.

Illustrative example (not a requirement):

> ```sql
> ALTER TABLE party
>   ADD PRIMARY KEY (tenant_id, id),
>   ADD CONSTRAINT party_case_fk FOREIGN KEY (tenant_id, case_id)
>       REFERENCES "case"(tenant_id, id) ON DELETE RESTRICT,
>   ADD CONSTRAINT party_email_chk CHECK (email IS NULL OR position('@' in email) > 1);
> 
> -- one presiding arbitrator per tribunal
> CREATE UNIQUE INDEX tribunal_one_presiding
>   ON tribunal_member (tenant_id, case_id) WHERE role = 'presiding' AND ended_at IS NULL;
> 
> -- no double-booked hearing room
> ALTER TABLE hearing ADD CONSTRAINT hearing_room_no_overlap
>   EXCLUDE USING gist (tenant_id WITH =, room_id WITH =, tstzrange(starts_at, ends_at) WITH &&);
> ```
> Left to application: deadline calculation (Rules engine), conflict checks (Neutrals domain).

### `tenancy` Tenancy and RLS policies (level 1)

Classify every table (tenant-owned, platform-level, shared reference) and give the exact RLS SQL for each tenant-owned table: ENABLE and FORCE, the policy for each command, and the roles it applies to. Note any table with a policy beyond tenant equality (for example case-participant visibility) and any role that bypasses RLS.

Illustrative example (not a requirement):

> ```sql
> ALTER TABLE party ENABLE ROW LEVEL SECURITY;
> ALTER TABLE party FORCE ROW LEVEL SECURITY;
> 
> CREATE POLICY party_tenant ON party
>   FOR ALL TO app_rw
>   USING (tenant_id = current_setting('app.tenant_id')::uuid)
>   WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
> 
> GRANT SELECT, INSERT, UPDATE ON party TO app_rw;   -- no DELETE: parties are withdrawn, not deleted
> GRANT SELECT ON party TO reporting_ro;              -- reporting replica only
> ```
> | Role | RLS | Used by |
> |---|---|---|
> | `app_rw` | enforced | Next.js app, Temporal and BullMQ workers |
> | `migrator` | owner, bypasses | `prisma migrate deploy` in CI only |
> | `reporting_ro` | own cross-tenant policy | Warehouse loader |
> 
> `current_setting` without `missing_ok` raises an error if the tenant was not set, so a forgotten context fails closed.

### `indexes` Indexes and access patterns (level 2)

List the main queries (from API list endpoints, UI screens, workflows and reports) and the index that serves each. Tenant-owned indexes normally lead with tenant_id. Note partial, expression, GIN and unique indexes and why each exists; remove any index no query needs.

Illustrative example (not a requirement):

> | Access pattern | Source | Index |
> |---|---|---|
> | Cases by status, newest first | `GET /v1/cases?status=` and secretariat dashboard | `(tenant_id, status, created_at DESC, id)` |
> | Case by institution reference | `external_ref` filter | unique `(tenant_id, external_ref) WHERE external_ref IS NOT NULL` |
> | Parties of a case | Case page | `(tenant_id, case_id)` |
> | Party lookup by email for invitations | Onboarding | `(tenant_id, email)` |
> | Upcoming hearings for a neutral | Neutral workspace | `(tenant_id, neutral_id, starts_at) WHERE status = 'scheduled'` |
> 
> Production indexes on existing large tables are created with `CREATE INDEX CONCURRENTLY` in a separate, non-transactional migration.

### `history` Status, history and concurrency (level 2)

How status columns map to the domain state machine, how history is kept (append-only event table, temporal versions, or audit only), how deletes work (soft delete, withdrawal, hard delete) and how concurrent updates are detected.

Illustrative example (not a requirement):

> - `case.status` is an enum mirrored from the code-defined state machine; it is only changed by the `transitionCase` command, which also inserts a row into `case_status_event (tenant_id, case_id, from_status, to_status, actor_id, reason, occurred_at)`.
> - `case_status_event` is append-only: `app_rw` has `INSERT, SELECT` only.
> - Parties are never hard-deleted while the case is open; `withdrawn_at` is set instead.
> - Updates use `WHERE id = $1 AND version = $2` and increment `version`; zero rows updated means a concurrent edit (API returns 412).

### `protection` Data classification and protection (level 2)

Which columns hold personal, sensitive or confidential data, how each is protected beyond RLS (application-level encryption, hashing, masking views, separate table with tighter grants), and where those values must never be copied (logs, search index, warehouse, JSONB blobs).

Illustrative example (not a requirement):

> | Column | Class | Protection | Not copied to |
> |---|---|---|---|
> | `party.tax_id_enc` | Sensitive personal | AES-256-GCM via KMS data key per tenant (5.4.1); `tax_id_hash` (HMAC) for lookup | Search, warehouse, logs |
> | `party.email` | Personal | RLS; masked in warehouse view | Logs |
> | `deliberation_note.body` | Confidential (tribunal only) | Separate table, policy adds `is_tribunal_member(case_id)` | Search, AI index unless tenant enables |
> | `kyc_check.raw_response` | Sensitive personal | Encrypted, 90-day retention | Everything |

### `retention` Retention, archival and deletion (level 2)

Per table: how long rows are kept, what starts the clock, what happens at the end (hard delete, anonymise, archive, crypto-shred), legal holds, and how tenant offboarding deletes or exports the data. Note partitioning used to make deletion cheap.

Illustrative example (not a requirement):

> | Table | Keep for | Clock starts | At end | Legal hold |
> |---|---|---|---|---|
> | `case`, `party` | Per tenant setting (default 10 years) | `case.closed_at` | Anonymise parties, keep case shell | `case.legal_hold = true` blocks |
> | `case_status_event` | Same as case | `case.closed_at` | Delete with case | Yes |
> | `api_idempotency_key` | 24 hours | `created_at` | Hard delete (daily job) | No |
> | `login_event` | 1 year | `occurred_at` | Drop monthly partition | No |
> | All tenant tables | n/a | Tenant offboarding + export confirmation + 30 days | Hard delete by tenant_id; backups expire on their own schedule | Contractual |

### `migrations` Migrations and rollout (level 1)

The ordered list of migrations needed, with the expand-and-contract steps for anything that changes existing data, how RLS and other SQL Prisma cannot generate is added (raw SQL in migration files), backfill method, lock and statement timeouts, and the rollback or roll-forward plan. Migrations run per region.

Illustrative example (not a requirement):

> Change: split `party.name` into `display_name` + `legal_name`.
> 
> | Step | Migration / release | Lock risk |
> |---|---|---|
> | 1 Expand | `20261102_add_party_names`: add nullable columns | Brief `ACCESS EXCLUSIVE`; `SET lock_timeout = '3s'` |
> | 2 Dual write | App release writes both old and new | none |
> | 3 Backfill | Temporal job, 1,000 rows per batch per tenant, resumable | Row locks only |
> | 4 Enforce | `ADD CONSTRAINT ... CHECK (display_name IS NOT NULL) NOT VALID`, then `VALIDATE CONSTRAINT` | Validation does not block writes |
> | 5 Contract | Next release stops reading `name`; later migration drops it | Brief |
> 
> Run with `prisma migrate deploy` from CI as `migrator`, India then Singapore then US. Every migration that creates a tenant table must also contain its `ENABLE`/`FORCE ROW LEVEL SECURITY` and policy SQL (3.3.4.4).

### `prisma` Prisma schema mapping (level 2)

How tables map to Prisma models: model and field names, `@map` / `@@map`, enums, composite keys and relations, and the list of database features that exist only in raw SQL (RLS, partial and exclusion indexes, check constraints, triggers) so reviewers know Prisma's view is incomplete.

Illustrative example (not a requirement):

> ```prisma
> model Party {
>   tenantId    String    @map("tenant_id") @db.Uuid
>   id          String    @db.Uuid
>   caseId      String    @map("case_id") @db.Uuid
>   role        PartyRole
>   displayName String    @map("display_name")
>   email       String?   @db.Citext
>   version     Int       @default(1)
>   case        Case      @relation(fields: [tenantId, caseId], references: [tenantId, id])
> 
>   @@id([tenantId, id])
>   @@index([tenantId, caseId])
>   @@map("party")
> }
> ```
> Raw SQL only: RLS policies, `party_email_chk`, partial unique `tribunal_one_presiding`, exclusion constraint on `hearing`. Drift between Prisma and the database is checked with `prisma migrate diff` in CI.

### `seed` Seed and reference data (level 2)

Reference data the schema depends on (countries, currencies, languages, case types, rule sets), where each comes from, who may change it, and how it is versioned and loaded per region. Separate production reference data from development and test fixtures.

Illustrative example (not a requirement):

> | Data | Table | Source | Changed by | Load |
> |---|---|---|---|---|
> | Countries, currencies | `country`, `currency` (platform) | ISO 3166 / ISO 4217 lists | Platform team, migration | Idempotent upsert in migration |
> | Default rule sets (e.g. institution rules templates) | `rule_set` (per tenant) | Tenant onboarding template | Tenant admin after provisioning | Tenant lifecycle workflow |
> | Party role labels per locale | `label` | Language packs (4.3) | Content team | Language pack import |
> | Demo tenants, synthetic cases | various | Faker-based script | Engineers | `prisma db seed`, never in production |

### `volume` Volume, growth and performance (level 2)

Expected rows and size per table at launch, after one year and after five, the largest tenant's share, hot tables, and the thresholds at which partitioning, archiving or a different design is needed.

Illustrative example (not a requirement):

> | Table | Launch | 1 year | 5 years | Notes |
> |---|---|---|---|---|
> | `case` | 20k | 400k | 5M | SEBI ODR volume dominates in India region |
> | `party` | 50k | 1M | 12M | |
> | `case_status_event` | 150k | 3M | 40M | Partition by month above 50M rows |
> | `audit_event` | 2M | 80M | 1B+ | Partitioned by month from day one |
> 
> Target: every list query in the API node under 50 ms p95 at the 5-year size for the largest tenant.

### `questions` Open questions (level 3)

Unresolved items as a checklist, each with an owner. Mark assumptions explicitly.

Illustrative example (not a requirement):

> - [ ] Is the tenant's retention period set per tenant or per rule set? (Legal)
> - [ ] Do we need case-participant RLS (beyond tenant) on `filing`, or is application policy enough? (Security)
> - [ ] UUIDv7 generated in app or by a Postgres function? (Platform)
> - [ ] Assumption: no foreign keys across Postgres schemas owned by different teams.

## Checks

### `tenancy` Tenant isolation in the schema

**Question:** Is it impossible, at the database level, for a row of one tenant to be read, written or referenced from another tenant's context, including through joins, views, functions, sequences and partitions?

- Does every tenant-owned table in this node, including join tables, history tables and partitions, have a non-null tenant_id, ENABLE and FORCE ROW LEVEL SECURITY, and policies for every command with both USING and WITH CHECK?
- Do all foreign keys between tenant-owned tables include tenant_id, so a row cannot point at another tenant's parent even when written by a privileged role?
- Are views created with `security_invoker = true` and functions free of SECURITY DEFINER unless reviewed, so they cannot read past RLS?
- Can a unique constraint or sequence leak information across tenants (for example a global unique email, or a shared counter that reveals another tenant's case volume)?
- Which roles bypass RLS (owner, `migrator`, BYPASSRLS), and does any application, Temporal or BullMQ worker connect with one of them?
- If `app.tenant_id` is unset or set to an empty string, does every query fail or return nothing, rather than return all rows?
- For platform-level and reference tables without tenant_id, is it confirmed that none of them store tenant-specific or personal data?

**Good answer:** Lists every table with its class and the exact RLS SQL, with composite (tenant_id, id) keys and foreign keys throughout. Names each RLS-bypassing role and confirms none is used at runtime. Shows the catalogue query or lint (for example checking `pg_class.relrowsecurity` and `relforcerowsecurity`) that runs in CI and fails if any tenant table lacks forced RLS.

**Red flags:**

- Foreign keys on `id` alone between tenant tables
- Unique constraints without tenant_id on tenant data (for example global unique email)
- Views or functions that run as owner without review
- Policies with USING but no WITH CHECK on writable tables

### `integrity` Invariants enforced by the database

**Question:** Which business invariants from the Domain node are guaranteed by constraints in the database, which are left to application code, and is each choice justified given concurrent writers (UI, public API, Temporal, BullMQ)?

- For each numbered business rule in the Domain node that concerns stored data, is it a constraint (not null, check, unique, exclusion, FK), a trigger, or application-only, and why?
- Which rules could be broken by two concurrent transactions that each pass an application check (for example two presiding arbitrators, double-booked hearing slots, two invoices for one fee), and what database mechanism prevents that?
- Are enum and status columns constrained to valid values, and are allowed transitions enforced somewhere that every writer passes through?
- Are money, quantities and durations stored in exact types with currency and units, with checks on sign and range?
- Which constraints are DEFERRABLE, and is there any reason a constraint is missing because the migration was easier without it?
- How is JSONB used, if at all, and is its shape validated (check constraint or application schema) so it cannot become a dumping ground for unmodelled fields?

**Good answer:** Maps each relevant business rule ID to a constraint or a named application guard, with race conditions handled by unique, exclusion or row-locking mechanisms rather than read-then-write checks. Status columns are constrained and only changed through one command path. JSONB fields, if any, have a documented schema and validation.

**Red flags:**

- Uniqueness enforced only by a 'check then insert' in code
- Money stored as float or without currency
- Large untyped JSONB columns holding core case data
- No mapping between domain rules and schema

### `migration-safety` Zero-downtime and reversible migrations

**Question:** Can every migration in this node be applied to a live, multi-region database with the previous and next application versions running, without long locks, data loss or a manual fix, and what is the recovery if it fails part way?

- For each migration, which lock does each statement take, for how long at the 5-year table size, and are `lock_timeout` and `statement_timeout` set so it fails fast instead of queuing behind traffic?
- Is every destructive change (drop, rename, type change, new NOT NULL) split into expand, backfill and contract steps across separate releases, so N-1 and N app versions both work?
- How are backfills run (batched, resumable, throttled, per tenant), and how is progress observed?
- Are indexes on large tables created CONCURRENTLY in their own non-transactional migration, and is an invalid index from a failed run detected and cleaned up?
- Does the migration contain the RLS, grants and policy SQL for new tables in the same file, so a table never exists without its policy?
- Is the migration tested against a production-sized, anonymised snapshot before release, and rehearsed in staging for each region?
- What is the roll-forward or rollback plan, and which steps cannot be undone (dropped columns, deleted rows) without restoring from backup?

**Good answer:** Gives a step table per change with lock level, expected duration, timeouts, and which release each step ships with. Backfills run as resumable jobs with metrics. Migrations are applied by CI with the `migrator` role region by region, after a rehearsal on realistic data, with a stated roll-forward plan and the point of no return identified.

**Red flags:**

- Renaming or dropping a column in the same release that stops using it
- Adding NOT NULL or a foreign key to a large table without NOT VALID and a later VALIDATE
- Backfills inside the migration transaction
- Running migrations by hand from a developer machine

### `privacy` Personal data, erasure and the legal record

**Question:** Where does personal data live in this schema, including copies, and how are DPDP, GDPR and PDPA rights (access, correction, erasure) and retention limits carried out without breaking the legal record an institution must keep?

- Which columns, JSONB keys, history rows and audit payloads contain personal data, and is there a machine-readable classification (for example column comments or a catalogue) that tools can read?
- When a party asks for erasure, which rows are deleted, which are anonymised, which are kept under a legal-record or legal-hold exemption, and how is the decision recorded?
- Is personal data duplicated into history tables, audit events, search indexes or the warehouse, and does erasure or anonymisation reach every copy?
- How long do backups and point-in-time recovery keep deleted personal data, and is that stated in the retention schedule and privacy notice?
- Is sensitive personal data (identity numbers, bank details, KYC results) encrypted at the application level with per-tenant keys, so crypto-shredding is possible on offboarding?
- Does the schema collect anything not needed for the stated purpose (data minimisation), such as date of birth where age band would do?

**Good answer:** Provides a column-level classification for every table and a per-table erasure and retention rule, including history, audit, search and warehouse copies. States the legal-record exemption and who decides it. Sensitive fields are encrypted with tenant-scoped keys, and backup retention is documented as part of the deletion promise.

**Red flags:**

- No column-level classification
- Erasure that deletes from the main table but not from history or search
- Identity or bank numbers stored in plaintext
- Personal data in platform-level tables without RLS

### `residency` Region placement and cross-region references

**Question:** Does every table in this node live only in the regional database of the tenant that owns its rows, and are there any global tables, IDs or references that would require data to move between regions?

- Which tables (if any) must exist in a global control plane rather than per region (for example tenant registry or region directory), and do they hold anything beyond routing metadata?
- Are reference and platform tables kept identical across regions through migrations and seeds, and how is drift detected?
- Can a row in one region reference a row in another region (for example a neutral empanelled with institutions in India and Singapore)? If so, how is that modelled without copying personal data across regions?
- Are IDs globally unique so data can be moved or merged later without collisions, without encoding the region in a way that leaks information?
- Do read replicas, the warehouse and backups for this schema stay in the same region, and is that true of disaster-recovery copies?
- If a tenant changes region, what is the documented export and import path for these tables?

**Good answer:** States that all tenant tables are regional and lists any global tables with their exact columns, showing they contain no personal or case data. Cross-region relationships are modelled by opaque IDs and per-region profiles rather than copies. Replicas, warehouse loads, backups and DR copies are confirmed in region, and a region-move procedure is referenced.

**Red flags:**

- A global users or parties table shared by all regions
- Cross-region foreign data wrappers or replication of tenant tables
- Disaster-recovery copies in a different country without legal sign-off

### `audit` History, immutability and evidence

**Question:** For the legally significant records in this schema, can we prove what the data was at any past moment, who changed it and when, and that the history itself has not been altered?

- Which tables are append-only, and is that enforced by grants (no UPDATE or DELETE for the app role) or triggers rather than by convention?
- For mutable records (case metadata, party details), is a history kept (status event table, versioned rows, or audit events with before and after values), and which one is the legal source of truth?
- Are submitted filings, served documents and awards stored as immutable versions with a content hash, so a later edit creates a new version rather than changing the old one?
- Do audit rows include tenant, actor, acting-for user, request ID, timestamp from the database clock and policy or rule-set version?
- Is the audit table protected against tampering by privileged roles (hash chaining, periodic anchoring, export to write-once storage)?
- Can an institution's secretariat produce a full, ordered history of a case from these tables for a court challenge without engineering help?

**Good answer:** Identifies each legally significant table and its history mechanism, with append-only enforced by grants. Immutable versions with content hashes are used for filings and awards. The audit design names its tamper-evidence mechanism and storage, and there is a defined query or export that reconstructs a case history.

**Red flags:**

- Status changed by plain UPDATE with no history
- App role able to UPDATE or DELETE audit or event rows
- Filings overwritten in place when corrected

### `performance` Query performance under RLS and growth

**Question:** Will the queries this schema must serve stay within their latency targets at the five-year data size for the largest tenant, with RLS policies applied, and what will we do before they stop doing so?

- Have the main queries been run with EXPLAIN ANALYZE on a realistic data set under the app role (so RLS predicates are included), and do the plans use the listed indexes?
- Are RLS policy expressions simple and index-friendly (tenant equality on a leading index column), and are any functions used in policies marked STABLE or LEAKPROOF where appropriate so the planner can use indexes?
- Which tables will need partitioning or archiving, at what row count, and is the partition key compatible with tenant_id in primary keys and indexes?
- Are there unbounded queries (no limit, counts over whole tables, OFFSET pagination) coming from the API or UI?
- What is the write rate on the hottest tables, and are autovacuum and index bloat considered for append-heavy tables like status events and audit?
- Are N+1 query patterns from Prisma relations checked, and are heavy reads moved to the reporting replica?

**Good answer:** Provides captured plans for the top queries at projected volume under RLS, an index for each, and named thresholds for partitioning or archiving with the design already chosen. Pagination is keyset-based, and heavy reporting runs on the replica or warehouse.

**Red flags:**

- Performance only tested with a superuser (RLS skipped)
- Complex subqueries or joins inside RLS policies on large tables
- No size estimates for append-only tables

### `testing` Schema verification

**Question:** Which automated checks prove, on every change, that the schema matches the spec, that tenant isolation and constraints hold, and that migrations apply cleanly from the current production state?

- Is there a CI check that compares the Prisma schema, the migration history and a freshly migrated database (`prisma migrate diff`) and fails on drift?
- Do isolation tests run as `app_rw` against a real Postgres through PgBouncer in transaction mode, attempting cross-tenant reads, writes and foreign-key references on every new table?
- Is there a migration linter that flags locking or unsafe operations (non-concurrent index, column type change, NOT NULL without NOT VALID)?
- Do tests exercise each database constraint (insert invalid data and expect a specific error), so a dropped constraint is noticed?
- Are migrations applied in CI on top of a copy of the current production schema (not only from empty), including the per-region order?
- Are retention and deletion jobs tested to confirm they remove exactly the intended rows and respect legal holds?

**Good answer:** Names the CI jobs for drift detection, migration linting, RLS catalogue checks, cross-tenant tests and constraint tests, all running on a real Postgres with the runtime role. Migrations are tested against a production-shaped schema, and retention jobs have tests including legal-hold cases.

**Red flags:**

- Tests run against SQLite or a mocked client
- Tests run as a superuser or table owner
- No drift detection between Prisma and the database

