# NexusOps — Intelligent Infrastructure Reliability & MLOps Platform

A self-hosted, production-inspired ML platform that learns from infrastructure telemetry to
**detect anomalies** and **predict service degradation (SLO breach in the next 15 minutes)**,
then serves, monitors, retrains and governs those models.

> Lab-grade learning project. All data is synthetic. No employer data, real IPs, or credentials.

## Status

| Milestone | State |
|---|---|
| M1 ML fundamentals | Week 1 done |
| M2 Telemetry dataset | v0 generator done (Week 1) |
| M3 Validation & versioning | Week 2 |
| M4–M15 | planned |

## Quick start

```bash
make setup      # python venv + editable install
make data       # generates data/raw/telemetry_v0.parquet (+ manifest, incident list)
make explore    # dataset summary
make baseline   # non-ML baseline detectors (static thresholds, z-score)
make test       # data tests
```

## Repository layout

```
configs/telemetry_v0.yaml      generator config (seed, services, SLO, incident mix)
src/nexusops/telemetry/        schema (data contract) + generator
scripts/                       CLIs: generate, explore, rule_baseline
tests/                         data tests (schema, ranges, reproducibility, labels)
docs/adr/                      architecture decision records
docs/notes/                    engineering notebook
data/raw/                      generated data (git-ignored, reproducible)
```

## Dataset v0 (seed 42)

80,640 rows (4 services x 14 days x 1440 min), 7 metrics, 4 labels, 35 injected incidents.
See `docs/notes/week01-engineering-notes.md` for the full description.

## Baseline to beat (days 8–14)

| Detector | Precision | Recall |
|---|---|---|
| Static thresholds | 1.000 | 0.748 |
| Z-score (k=3) | 0.812 | 0.915 |
