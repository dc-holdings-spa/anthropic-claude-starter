# Sample corpus para tests RAG

Documento sintético con secciones temáticas + identificadores únicos. Permite probar vector search (semántico) + BM25 (lexical exact-match).

## Section 1: Authentication

The auth module handles user login via JWT tokens. Implementation lives in `src/auth/jwt.py`. Tickets tracking: AUTH-2026-Q1-001 through AUTH-2026-Q1-015.

Recent incident: INC-2026-001 — JWT signature mismatch caused 30-minute outage on 2026-03-15. Root cause: secret rotation deployed without grace period.

## Section 2: Database

Postgres 16 with read replicas. Connection pooling via PgBouncer. Slow query budget: P99 <100ms.

Recent incident: INC-2026-002 — replica lag exceeded 5 seconds during batch import job BATCH-2026-Q1-042. Mitigation: throttled batch to 100 rows/sec.

## Section 3: Frontend

Next.js 15 with App Router. SWR for data fetching. Auth tokens in HttpOnly cookies.

No recent incidents. UX testing pending: tracking TICK-FE-2026-007.

## Section 4: Infrastructure

AWS us-east-1 primary, eu-west-1 DR. RDS for Postgres, ECS Fargate for app workers, S3 for static assets.

IAM rotation: every 90 days enforced via Lambda LAMBDA-IAM-ROT-2026.

## Section 5: Security

Annual pentest scheduled Q4 2026. Last engagement: ENG-2025-Q4-RT yielded 3 high findings, all remediated.

Compliance: SOC 2 Type II certification renewed 2026-02-10. Audit reference: AUDIT-SOC2-2026-001.

Cybersecurity team rotates on-call weekly. Current rotation index: OC-2026-W19.

## Section 6: Data privacy

PII tracking lives in `src/privacy_registry.py`. GDPR compliance: data retention 90 days for analytics, 7 years for billing.

Recent flag: PII-2026-014 — partner integration request for email-as-identifier was rejected per policy POL-DP-FRMK-v3.

## Section 7: Monitoring

OpenTelemetry collector ships to Grafana Cloud. Dashboards organized by team-namespace.

Critical alerts page on-call: AlertManager alerts AM-CRIT-2026-* notify PagerDuty service PD-PROD-RT.
