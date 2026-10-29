---
id: "INF-networking"
title: "Networking"
parent: "INF"
order: 8
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Per-region VPC with public, private and data subnets, CDN and WAF in front of the load balancer, private endpoints for cloud services, egress allow-list, DNS and tenant custom domains"
links: []
rev: 2
syncHash: "568b76e2be5a5176"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.8 Networking

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Per-region VPC with public, private and data subnets, CDN and WAF in front of the load balancer, private endpoints for cloud services, egress allow-list, DNS and tenant custom domains

<!-- section:purpose -->
## Purpose and responsibilities

Provides the network each regional stack runs in and the path from the internet to it: DNS, CDN, WAF, load balancers, subnets, private endpoints to cloud services and controlled egress to third parties (messaging, payments, KYC, video, AI providers).

Depended on by: every workload; [[MT-tenant-resolution]] (subdomains and custom domains reach the right region); [[APP-security-headers-csp-cors]] (headers set at the edge or app); [[APP-document-viewer-and-sandbox]] (separate sandbox origin); [[PKG-input-sanitisation-csrf-rate]] (WAF rate rules complement app rate limits).

<!-- section:topology -->
## Topology per region

```
Internet
  │  DNS: <tenant>.<product domain> → region (from tenant directory, MT-data-residency-2)
  ▼
CDN (CloudFront) + AWS WAF  ── static assets cached; dynamic and API pass-through, not cached
  ▼
Public subnets (3 AZs): ALB (HTTPS 443), NAT gateways
  ▼
Private app subnets (3 AZs): web, workers, PgBouncer, Temporal, OTel collector
  ▼
Isolated data subnets (3 AZs): RDS, ElastiCache — no route to the internet
  +
VPC endpoints: S3 (gateway), ECR, Secrets Manager, KMS, CloudWatch Logs, STS, SQS/SNS if used
Egress: NAT → AWS Network Firewall with domain allow-list (providers per region)
```

| Region | Environment | VPC CIDR (proposed) | AZs |
|---|---|---|---|
| prod-in (ap-south-1) | prod | 10.10.0.0/16 | 3 |
| prod-sg (ap-southeast-1) | prod | 10.20.0.0/16 | 3 |
| prod-us (us-east-1) | prod | 10.30.0.0/16 | 3 |
| nonprod (ap-south-1) | dev / staging / UAT | 10.40.0.0/16, 10.41.0.0/16, 10.42.0.0/16 | 2 |
| Azure regions | prod | 10.50.0.0/16 and up | Zone-redundant subnets; Front Door + WAF; Private Endpoints |

CIDRs do not overlap so that a future peering for DR or support access is possible; **there is no peering between production regions**.

<!-- section:sizing -->
## Sizing and scaling

- Subnets /20 per AZ for private app subnets (4,091 addresses) — Fargate uses one IP per task.
- NAT: one NAT gateway per AZ in production (no cross-AZ dependency).
- WAF: start with AWS managed rule groups (core rule set, known bad inputs, IP reputation) plus custom rate rules; review false positives weekly during the first month.
- CDN: static assets only; expected high hit ratio. Bandwidth driver is document download, which goes through signed S3 URLs, not the CDN (assumption; see questions).

<!-- section:config -->
## Configuration baseline

| Setting | Value | Why |
|---|---|---|
| TLS at edge | TLS 1.2 minimum (TLS 1.3 preferred) security policy on CloudFront and ALB; HSTS set by app | |
| CDN caching | Cache only `/_next/static/*`, fonts and public images; everything else `Cache-Control: private, no-store`, CDN cache policy "CachingDisabled" | CDN edges are global; tenant HTML or API responses must never be stored at an edge outside the region |
| CDN logs | Standard logs delivered to a bucket **in the tenant region's account**; IP addresses truncated in processing | Residency and data minimisation |
| WAF rules | Managed core rule set, SQLi, known bad inputs, IP reputation; rate limit 2,000 requests / 5 min per IP on sign-in, OTP and public filing routes | Complements app-level limits |
| Origin protection | ALB accepts only CloudFront (managed prefix list + secret header) | No bypass of WAF |
| Custom domains | Per-tenant certificates from ACM (DNS-validated by the tenant's CNAME), attached through the CDN; limit and process in [[MT-tenant-resolution]] | |
| Sandbox origin | Separate registrable domain for document rendering ([[APP-document-viewer-and-sandbox]]) with its own distribution and strict headers | Origin isolation |
| Egress | AWS Network Firewall stateful domain allow-list per region (e.g. regional SMS / WhatsApp providers, payment gateways, KYC vendor, AI gateway providers) | Data exfiltration control |
| VPC flow logs | All VPCs, to the regional log archive bucket | Security evidence |
| DNS | Route 53 public zones for product domains; private hosted zones per region (`*.<region>.internal`) | |

<!-- section:resilience -->
## High availability and DR

- AZ loss: ALB, NAT and subnets in three AZs; one NAT per AZ.
- CDN or WAF misconfiguration: changes go through IaC with staging first; emergency rollback by reverting the PR. A "WAF count mode" toggle allows disabling a blocking rule quickly.
- Regional ALB loss: traffic for that region fails; DNS failover to a DR region only where a DR region is approved ([[INF-backup-and-disaster-recovery]]).
- DNS provider outage: Route 53 has a 100% availability SLA; registrar lock on product domains.

<!-- section:security -->
## Security

- Only the CDN and ALB are internet-facing; data subnets have no internet route; security groups reference each other, not CIDRs.
- WAF in front of all public routes, including the browser telemetry endpoint ([[OBS-frontend-real-user-monitoring]]) and webhook receivers.
- DDoS: AWS Shield Standard; Shield Advanced is an open question for clients with contractual availability terms.
- Egress allow-list blocks unknown destinations; blocked attempts are security events ([[OBS-security-events]]).
- Support / engineer access uses SSM Session Manager or no shell at all; no bastion hosts, no SSH.

<!-- section:operations -->
## Runbook

- Add a third-party provider: PR adding the domain to the regional allow-list, linked to the vendor record in [[SEC-vendor-sub-processor-management]].
- Tenant custom domain: issue certificate, wait for tenant CNAME validation, attach to distribution; runbook in [[MT-tenant-resolution]].
- WAF false positive: switch the specific rule to count mode for the route, add a scoped exception, review within 7 days.

<!-- section:observability -->
## Monitoring and alerts

- ALB 5xx rate, target response time, rejected connections (feed [[OBS-performance]]).
- WAF blocked requests by rule and tenant host (spikes alert security on-call).
- NAT / firewall dropped connections by destination (unexpected destination → security ticket).
- Certificate expiry for tenant custom domains (ACM auto-renews; alert if renewal is pending because the tenant removed its CNAME).

<!-- section:cost -->
## Cost

Drivers: NAT gateway hours and data processing (reduced by VPC endpoints for S3 / ECR), Network Firewall endpoints per AZ (significant fixed cost; may be one per region in non-production), CDN data transfer, WAF requests. Network Firewall in all three AZs per production region is the main fixed cost to review.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| VPC module with three subnet tiers and endpoints | Not started |
| CDN cache policy verified: no tenant response cached | Not started |
| WAF managed rules + rate rules in count mode, then block | Not started |
| Egress allow-list per region | Not started |
| Custom domain flow tested | Not started |

<!-- section:questions -->
## Open questions

- [ ] Is a global CDN acceptable to clients and under DPDP / PDPA for pass-through traffic (TLS terminates at edges outside the region), or must some tenants use a regional ALB with no CDN?
- [ ] Do large document downloads go through signed S3 URLs directly or through the CDN with signed cookies?
- [ ] AWS Shield Advanced: needed for any client SLA?
- [ ] Product domains per product (CORD, TERES) and per region — final naming scheme for tenant subdomains.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Only CDN and ALB are public; ALB accepts traffic only from the CDN; WAF covers all public routes; data subnets have no internet route; egress is restricted by a per-region domain allow-list; no bastion hosts. TLS 1.2+ everywhere.

<!-- check:residency -->
### Data residency

Each region has its own VPC with no peering to other production regions. The main residency risk is the global CDN: only static assets are cached, tenant responses are marked `private, no-store` and pass through, and CDN logs are delivered to the region's own bucket. Whether pass-through TLS termination at foreign edges is acceptable is raised as an open question.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

Network is shared by all tenants in a region; tenant isolation is in the data layer. WAF rate rules per IP and per tenant host limit one tenant's traffic spike (or an attack on one tenant) from consuming shared capacity; app-level rate limits per tenant are in [[PKG-input-sanitisation-csrf-rate]].

<!-- check:iac -->
### Infrastructure as code and change control

VPC, CDN, WAF, DNS and firewall rules come from the `network` and `edge` stacks; allow-list changes are PRs linked to vendor records.

<!-- check:cost -->
### Cost

NAT processing and Network Firewall endpoints are the main costs; VPC endpoints for S3 and ECR reduce NAT traffic. Non-production uses one firewall endpoint per VPC.

<!-- end -->
