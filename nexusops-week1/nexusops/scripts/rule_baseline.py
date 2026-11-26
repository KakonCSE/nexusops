"""Week 1 baseline: detect anomalies WITHOUT machine learning.

Two hand-written detectors, the way a NOC would do it today:
  1. static thresholds (classic Nagios/Zabbix style alerting)
  2. z-score per service (statistics: "how many standard deviations from normal?")

We score both against the ground-truth `is_anomaly` label with precision and recall.
Every ML model we train later must BEAT this baseline, or it is not worth deploying.

Usage:
    python scripts/rule_baseline.py --data data/raw/telemetry_v0.parquet
"""

import argparse

import pandas as pd

METRICS = ["cpu_pct", "mem_pct", "p95_latency_ms", "error_rate_pct", "tcp_retransmit_pct", "db_pool_in_use_pct"]


def confusion(pred: pd.Series, truth: pd.Series) -> dict:
    tp = int(((pred == 1) & (truth == 1)).sum())
    fp = int(((pred == 1) & (truth == 0)).sum())
    fn = int(((pred == 0) & (truth == 1)).sum())
    tn = int(((pred == 0) & (truth == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "precision": round(precision, 3), "recall": round(recall, 3)}


def static_thresholds(df: pd.DataFrame) -> pd.Series:
    rule = (
        (df["cpu_pct"] > 90)
        | (df["mem_pct"] > 90)
        | (df["p95_latency_ms"] > 450)
        | (df["error_rate_pct"] > 2.0)
        | (df["tcp_retransmit_pct"] > 2.0)
        | (df["db_pool_in_use_pct"] > 90)
    )
    return rule.astype(int)


def zscore_detector(df: pd.DataFrame, k: float = 3.0) -> pd.Series:
    # Learn "normal" mean/std per service from the FIRST 7 DAYS only (a mini train/test split).
    cutoff = df["timestamp"].min() + pd.Timedelta(days=7)
    train = df[df["timestamp"] < cutoff]
    stats = train.groupby("service")[METRICS].agg(["mean", "std"])

    flags = pd.Series(0, index=df.index)
    for m in METRICS:
        mu = df["service"].map(stats[(m, "mean")])
        sd = df["service"].map(stats[(m, "std")])
        z = (df[m] - mu) / sd
        flags |= (z.abs() > k).astype(int)  # NaN comparisons are False -> missing rows are not flagged
    return flags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/raw/telemetry_v0.parquet")
    ap.add_argument("--k", type=float, default=3.0, help="z-score threshold")
    args = ap.parse_args()

    df = pd.read_parquet(args.data)
    test = df["timestamp"] >= df["timestamp"].min() + pd.Timedelta(days=7)
    truth = df.loc[test, "is_anomaly"]

    print("Evaluated on days 8-14 only (the 'unseen' half).\n")
    for name, pred in [("static_thresholds", static_thresholds(df)), (f"zscore_k{args.k}", zscore_detector(df, args.k))]:
        print(f"{name:<20} {confusion(pred[test], truth)}")


if __name__ == "__main__":
    main()
