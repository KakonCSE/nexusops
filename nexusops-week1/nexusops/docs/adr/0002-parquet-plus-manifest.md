# ADR-0002: Store raw datasets as Parquet with a JSON manifest

- Status: Accepted
- Date: 2026-11-26

## Context
We need a file format for raw telemetry that preserves types (UTC timestamps, int8 labels),
is compact, and is fast to read column-by-column. We also need lightweight lineage before
adopting a data-versioning tool.

## Decision
- Primary format: Parquet (columnar, typed, compressed). CSV export is available for eyeballing only.
- Every dataset ships with `<name>_manifest.json`: generator version, config hash, seed, row count,
  content hash, label rates.

## Alternatives considered
| Option | Why not (for now) |
|---|---|
| CSV only | Loses dtypes and timezone, larger, slower. |
| PostgreSQL / TimescaleDB | Useful later for ingestion and serving; overkill for a static training dataset in Week 1. |
| DVC immediately | Solves versioning, but we first need to understand WHAT we are versioning. Introduced in Week 2. |

## Consequences
- The content hash lets tests and CI prove two runs produced identical data.
- Generated files are git-ignored; they are reproducible from code + config.
