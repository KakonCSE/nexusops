# ADR-0001: Start with synthetic, labelled telemetry

- Status: Accepted
- Date: 2026-11-26
- Milestone: M2 (dataset)

## Context

NexusOps needs infrastructure telemetry to learn anomaly detection and degradation prediction.
Real production telemetry is confidential (employer data, IPs, topology) and, more importantly,
has no ground-truth labels: nobody marks every minute as "normal" or "incident".
Without labels we cannot measure precision/recall, so we cannot tell a good model from a bad one.

## Decision

Generate synthetic telemetry with a seeded, config-driven Python generator
(`src/nexusops/telemetry/generator.py`, `configs/telemetry_v0.yaml`).

- 4 fictional services, 1-minute resolution, 14 days, 7 metrics.
- 4 injected failure modes with a gradual ramp (early-warning phase).
- Labels: `is_anomaly`, `incident_type`, `slo_breach`, `will_breach_15m`.
- ~0.2% missing metric cells to simulate failed scrapes.
- Output: Parquet + incident list CSV + JSON manifest (seed, config hash, content hash).

## Consequences

Positive
- Zero confidentiality risk; safe for a public portfolio repo.
- Ground truth exists, so evaluation is honest and measurable.
- Fully reproducible: same config + seed + library versions => same `content_hash`.
- We control difficulty: we can add drift, cascades, and label noise later on purpose.

Negative / risks
- Models can learn the generator's simplifications (e.g. thresholds alone already get precision 1.0).
  Results on synthetic data are NOT evidence of real-world performance.
- Real telemetry has correlated multi-service failures, deploy events and seasonality drift that v0 lacks.

## Follow-ups
- Week 2: schema validation and data versioning of v0.
- Later: optionally replay a public dataset (e.g. NAB) or a self-hosted lab cluster scraped by Prometheus,
  to test whether models trained on synthetic data transfer.
