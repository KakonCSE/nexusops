# NexusOps progress tracker

## Completed weeks
- **Week 1 (2026-11-26)** — ML foundations, capstone architecture, dataset v0 generator, non-ML baseline.

## Skills learned
- AI vs ML vs DL vs GenAI vs Data Science vs MLOps
- Supervised / unsupervised / RL; classification vs regression; anomaly detection
- Features, labels, parameters, hyperparameters, training vs inference
- Overfitting, underfitting, bias/variance, data leakage (concept)
- Mean, median, variance, std dev, z-score, Pearson correlation
- Confusion matrix, precision, recall, why accuracy fails on imbalanced data

## Labs completed
- [ ] Lab 1.1 Environment setup (venv, editable install)
- [ ] Lab 1.2 Generate telemetry_v0 and confirm content_hash `d39d3d08801c5478`
- [ ] Lab 1.3 Explore the dataset
- [ ] Lab 1.4 Non-ML baseline (thresholds vs z-score)
- [ ] Lab 1.5 Data tests (10 passing)

## Project milestones
- M1 ML fundamentals: in progress (Week 1 done)
- M2 Telemetry dataset: v0 done

## Technical decisions
- ADR-0001 Synthetic, labelled telemetry first
- ADR-0002 Parquet + JSON manifest; DVC deferred to Week 2

## Baseline to beat
- Static thresholds: P=1.000 R=0.748 ; Z-score k=3: P=0.812 R=0.915 (days 8–14)

## Known knowledge gaps (to revisit)
- Probability distributions, sampling, confidence intervals (Week 2–3)
- Time-series specifics: autocorrelation, why random train/test splits leak (Week 3)

## Before Week 2
1. All 5 labs above checked.
2. Assignment deliverable committed in a private Git repo `nexusops` (local is fine).
3. `docs/notes/week01-dataset-card.md` written by you.
4. Reflection answers written in `docs/notes/week01-reflection.md`.
