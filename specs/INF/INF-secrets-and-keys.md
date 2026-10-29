---
id: "INF-secrets-and-keys"
title: "Secrets and keys"
parent: "INF"
order: 9
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Customer-managed KMS keys per region and purpose, Secrets Manager / Key Vault for credentials, rotation, separation of key admins and users, break-glass"
links: []
rev: 2
syncHash: "517403ffc66554a5"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.9 Secrets and keys

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Customer-managed KMS keys per region and purpose, Secrets Manager / Key Vault for credentials, rotation, separation of key admins and users, break-glass

<!-- section:purpose -->
## Purpose and responsibilities

Provides the key stores and secret stores used by every component: KMS keys for encryption at rest and envelope encryption, and Secrets Manager (Azure: Key Vault) for credentials. The application-side helpers (envelope and field-level encryption, the secrets client) are specified in [[PKG-encryption-utilities-key]]; per-tenant OAuth credentials for integrations are stored through [[INT-integration-framework]] using keys from here.

Depended on by: [[INF-database]], [[INF-redis]], [[INF-temporal]] (payload codec key, mTLS CA), [[PKG-storage]] / [[PKG-encryption-at-rest-signed-urls]], [[APP-webhooks-outbound]] (per-tenant signing secrets), [[INF-backup-and-disaster-recovery]] (backup vault keys).

<!-- section:topology -->
## Topology per region

**Keys per region and environment (AWS KMS, symmetric, customer-managed)**

| Alias | Encrypts | Key users (roles) |
|---|---|---|
| `alias/<env>-<region>-rds` | Postgres storage, snapshots, replicas, Performance Insights | RDS service |
| `alias/<env>-<region>-redis` | ElastiCache at rest | ElastiCache service |
| `alias/<env>-<region>-documents` | Document and bundle buckets (SSE-KMS, bucket keys on) | `web`, `worker-temporal-documents`, malware scanner |
| `alias/<env>-<region>-temporal-payload` | Data key for the Temporal payload codec | Temporal workers, `web` (client), codec server |
| `alias/<env>-<region>-field` | Field-level encryption data keys (for example bank details, identity document numbers) | Data-access package roles that need them |
| `alias/<env>-<region>-secrets` | Secrets Manager secrets | Each task role for its own secrets |
| `alias/<env>-<region>-logs` | CloudWatch Logs and telemetry stores | Logs service, collector |
| `alias/<env>-<region>-backup` | Backup vault (in the backup account) | AWS Backup |

**Secrets (Secrets Manager, per region)**: `db/<role>` for each database role, `redis/<user>`, `temporal/mtls/*` (or ACM Private CA issued), third-party provider credentials per region (`providers/sms/<vendor>` etc.), `app/session-signing`, `app/csrf`. Per-tenant webhook signing secrets and integration tokens are **not** individual Secrets Manager entries (cost and count); they are stored in Postgres encrypted with the `field` key through envelope encryption.

Azure: one Key Vault per region and environment (Premium tier for HSM-backed keys), RBAC authorisation mode, purge protection on, private endpoint only.

<!-- section:sizing -->
## Sizing and scaling

About 10 keys and 40–60 secrets per production region at launch. KMS request rates are dominated by S3 SSE-KMS (bucket keys reduce this) and field-level decrypts (data keys cached in memory for 5 minutes per [[PKG-encryption-utilities-key]]). No scaling action expected; watch KMS throttling metrics.

<!-- section:config -->
## Configuration baseline

- Automatic annual rotation on all symmetric KMS keys.
- Key policies separate **key administrators** (Infrastructure role through break-glass; can manage but not use keys) from **key users** (service roles; can use but not manage). No `kms:*` for any human role.
- Deletion window 30 days; deletion of any production key requires two approvals and raises a security alert.
- Secrets Manager rotation: database application roles every 30 days (managed rotation for RDS where available [R1]; Lambda rotation for PgBouncer auth user and Redis ACL users); third-party API keys every 90 days or per vendor capability.
- Services read secrets at start-up through ECS `secrets` injection; long-running workers refresh database credentials by re-reading the secret on authentication failure (supports rotation without restart). Rotation uses the alternating-users strategy for database roles so old connections keep working until recycled.
- Resource policies deny access from outside the account's VPC endpoints (`aws:SourceVpce`).

<!-- section:resilience -->
## High availability and DR

- KMS and Secrets Manager are regional, multi-AZ managed services; a regional outage of KMS stops decrypts (new connections, document reads) — treated as a region incident.
- Accidental key deletion is prevented by the 30-day window plus alerting; scheduled deletion can be cancelled.
- Backups are encrypted with the backup account's own key, so loss or compromise of the production account's keys does not make backups unreadable ([[INF-backup-and-disaster-recovery]]).
- Multi-Region keys are **not** used (they would replicate key material across regions); a DR region in the same country gets its own keys.

<!-- section:security -->
## Security

- Every decrypt and secret read is logged in CloudTrail (data events for Secrets Manager and KMS) to the regional log archive and analysed for anomalies ([[OBS-security-events]]).
- Break-glass: named Infrastructure engineers can assume a key-admin role for 1 hour with MFA and a ticket; use pages the security lead.
- No secrets in environment files committed to git, Terraform state or container images ([[FND-environment-management]]); secret scanning in CI ([[SEC-vulnerability-management]]).
- Client-managed keys (BYOK) for specific institutions are not offered at launch; see questions.

<!-- section:operations -->
## Runbook

- Rotate a leaked secret: trigger immediate rotation, force new deployment of consumers, review CloudTrail for use of the old value, open a security incident ([[SEC-security-incident-response-and]]).
- Add a provider credential: create the secret through IaC (value entered by the owner through a one-time console form or CLI with `put-secret-value`), grant only the consuming task role.
- Rotation failure: alert; old credential stays valid until fixed (alternating users).

<!-- section:observability -->
## Monitoring and alerts

- Rotation failures (Secrets Manager rotation events) → ticket; for database roles → page if the next rotation is within 3 days.
- KMS throttling or `AccessDenied` spikes → security ticket.
- Key scheduled for deletion → security page.
- Decrypt volume anomaly per role (for example `field` key decrypts 10× baseline) → security alert; may indicate bulk data access.

<!-- section:cost -->
## Cost

Small: about USD 1 per key per month plus requests; Secrets Manager per secret per month. Envelope encryption of per-tenant secrets in Postgres avoids hundreds of individual secrets.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Key set per region with admin / user separation | Not started |
| Rotation for DB roles tested with live connections | Not started |
| CloudTrail data events for KMS and Secrets Manager | Not started |
| Break-glass key admin tested | Not started |

<!-- section:questions -->
## Open questions

- [ ] Do any institutions (for example arbitral institutions or SEBI-regulated tenants) require customer-managed or customer-held keys (BYOK / HYOK) for their documents? This would need per-tenant KMS keys and changes to the storage and field encryption design.
- [ ] HSM-backed keys (AWS CloudHSM / Azure Managed HSM) required by any contract or audit?
- [ ] Rotation period for database credentials: 30 days proposed — agree with ISMS policy ([[SEC-isms-controls]])?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Separate key administrators and key users, no human with `kms:*`, automatic annual rotation, CloudTrail data events for every decrypt and secret read, VPC-endpoint-only access, 30-day deletion window with alerting, and break-glass key admin access with MFA and paging.

<!-- check:residency -->
### Data residency

Keys and secrets exist per region; Multi-Region KMS keys are deliberately not used. Per-tenant secrets live in the tenant's regional database encrypted with the regional `field` key. A DR region in the same country gets its own keys.

<!-- check:dr -->
### Resilience and recovery

Backups use a key in the separate backup account so production key compromise cannot lock us out of backups. Scheduled key deletion can be cancelled within 30 days. Regional KMS outage is handled as a region incident.

<!-- check:iac -->
### Infrastructure as code and change control

Keys, key policies, secrets (without values) and rotation schedules are defined in the `security` stack; secret values are set inside Secrets Manager and never appear in Terraform state.

<!-- check:lifecycle -->
### Operations and lifecycle

Rotation is automated for database and Redis credentials using the alternating-users strategy so live connections are not broken; runbooks cover leaked-secret rotation and provider credential onboarding.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Some services manage rotation of their secrets in Secrets Manager without a Lambda rotation function.",
    "id": "R1",
    "kind": "vendor",
    "title": "AWS Secrets Manager: managed rotation",
    "url": "https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_managed.html",
    "vendor": "AWS"
  }
]
```

<!-- end -->
