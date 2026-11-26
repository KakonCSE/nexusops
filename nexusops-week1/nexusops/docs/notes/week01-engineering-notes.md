# Week 1 Engineering Notes — ML Foundations and the NexusOps Dataset

## 1. Definitions

| Term | Definition | Infra analogy |
|---|---|---|
| AI | Any technique that makes a machine perform tasks that normally need human judgment. Includes rule engines. | The whole "automation" field. |
| Machine Learning (ML) | A subset of AI where behaviour is **learned from data** instead of hand-coded rules. | Instead of writing `if cpu > 90: alert`, you let the system learn what "abnormal" looks like from history. |
| Deep Learning (DL) | ML using multi-layer neural networks; strong on images, text, audio, very large data. | A very large, opaque rule-set learned automatically. |
| Generative AI | DL models that **produce** content (text, code, images). LLMs belong here. | The future incident assistant in M13. |
| Data Science | The discipline of extracting insight from data (analysis, statistics, experiments). Output is often a decision or report. | Capacity planning analysis. |
| MLOps | Engineering practices that make ML systems reproducible, deployable, observable and governable in production. | DevOps + SRE, applied to data and models. |

## 2. Traditional programming vs ML

```
Traditional:   rules + data  ->  program  ->  answers
ML (training): data + answers (labels)  ->  learning algorithm  ->  model (learned rules)
ML (inference): model + new data  ->  predictions
```

A **model** is a function `f(x) -> y` whose internal numbers (**parameters**) were set by training.
**Hyperparameters** are knobs set by the engineer before training (e.g. z-score threshold `k`, tree depth).

## 3. Learning types

| Type | Needs labels? | Question | NexusOps use |
|---|---|---|---|
| Supervised – classification | Yes | Which category? | `will_breach_15m` (yes/no) |
| Supervised – regression | Yes | What number? | Forecast p95 latency in 15 min |
| Unsupervised – clustering | No | Which items are similar? | Group services by behaviour |
| Unsupervised – anomaly detection | No (or few) | What is unusual? | `is_anomaly` without using labels |
| Reinforcement learning | Reward signal | Which action maximises reward? | Out of scope (auto-remediation is risky) |

## 4. Core vocabulary

- **Sample / row**: one observation — here, one service at one minute.
- **Feature (x)**: an input column (cpu_pct, tcp_retransmit_pct, ...).
- **Label / target (y)**: the answer we want to predict (will_breach_15m).
- **Training**: fitting parameters on historical data. **Inference**: using the fitted model on new data.
- **Generalisation**: performing well on data the model has not seen. The only thing that matters.
- **Overfitting**: memorising training noise; great on train, bad on test. (A firewall rule-set written for last week's attack only.)
- **Underfitting**: too simple to capture the pattern. (A single `cpu > 90` rule.)
- **Bias / variance**: bias = systematic error from a too-simple model; variance = sensitivity to the specific training sample. Reducing one usually increases the other.
- **Data leakage**: information at training time that will not be available at inference time. Example: using `slo_breach` at t+5 as a feature for predicting breach at t+15.

## 5. Statistics used this week

- **Mean** μ = Σx / n — sensitive to outliers (one 1,380 ms spike moves it).
- **Median** — middle value; robust to outliers. Latency SLOs use percentiles for this reason.
- **Variance** σ² = Σ(x − μ)² / n; **standard deviation** σ = √σ² — typical distance from the mean.
- **Z-score** z = (x − μ) / σ — "how many σ from normal". |z| > 3 is a classic outlier rule (≈0.3% of a normal distribution).
- **Pearson correlation** r ∈ [−1, 1] — linear relationship strength. Correlation ≠ causation.

## 6. Evaluation basics

|  | Actual incident | Actual normal |
|---|---|---|
| Predicted incident | TP | FP (false alarm / pager noise) |
| Predicted normal | FN (missed incident) | TN |

- **Precision** = TP / (TP + FP): of the alerts fired, how many were real? (alert fatigue)
- **Recall** = TP / (TP + FN): of the real incidents, how many did we catch? (missed outages)
- **Accuracy is misleading on imbalanced data**: with 2.5% anomalies, "always normal" scores 97.5% accuracy and catches nothing.

## 7. The ML lifecycle (what NexusOps will automate)

1. Problem framing (what decision, what metric, what cost of error)
2. Data collection / generation
3. Data validation
4. Feature engineering
5. Training
6. Evaluation against a baseline
7. Registration and approval
8. Deployment / serving
9. Monitoring (system, data, model)
10. Retraining → back to 3

## 8. Dataset v0 — telemetry_v0

- Services: api-gateway, payments-api, auth-svc, ledger-db (fictional)
- Resolution: 1 min; 14 days; 80,640 rows; seed 42; content_hash `d39d3d08801c5478`
- Metrics: rps, cpu_pct, mem_pct, p95_latency_ms, error_rate_pct, tcp_retransmit_pct, db_pool_in_use_pct
- Labels: is_anomaly (2.52%), incident_type, slo_breach (1.64%), will_breach_15m (2.25%)
- SLO: p95 latency > 450 ms OR error rate > 2% = breach
- Incidents: 35; types cpu_saturation, memory_leak, packet_loss, db_pool_exhaustion; 40% ramp then plateau
- Missing data: ~0.2% of metric cells (failed scrapes), labels computed before blanking

## 9. Week 1 baseline (days 8–14)

| Detector | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|
| Static thresholds | 856 | 0 | 288 | 1.000 | 0.748 |
| Z-score k=3 (μ,σ from days 1–7) | 1047 | 243 | 97 | 0.812 | 0.915 |

Interpretation: thresholds miss the early ramp (low recall); z-score catches more but fires false alarms.
Precision 1.0 for thresholds is a synthetic-data artefact — normal noise never crosses 90% here.

## 10. Lab-grade vs production

| Aspect | Week 1 lab | Production |
|---|---|---|
| Data source | Seeded generator | Prometheus / OTel pipeline, many sources |
| Labels | Perfect ground truth | Sparse, delayed, noisy (incident tickets) |
| Storage | Local Parquet | Object storage + versioning + access control |
| Validation | 10 pytest checks | Schema registry, data contracts, CI gates |
| Lineage | JSON manifest | Data catalog / lineage tooling |
