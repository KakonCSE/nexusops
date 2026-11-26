"""First look at the dataset: shape, missing values, per-service statistics, incidents.

This is the "show ip int brief" of a dataset: before you model anything, you look.

Usage:
    python scripts/explore_telemetry.py --data data/raw/telemetry_v0.parquet
"""

import argparse

import pandas as pd

from nexusops.telemetry.schema import METRIC_COLUMNS

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/raw/telemetry_v0.parquet")
    args = ap.parse_args()

    df = pd.read_parquet(args.data) if args.data.endswith(".parquet") else pd.read_csv(args.data, parse_dates=["timestamp"])
    metrics = list(METRIC_COLUMNS)

    print(f"== shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"== time range: {df['timestamp'].min()}  ->  {df['timestamp'].max()}")
    print(f"== services: {sorted(df['service'].unique())}\n")

    print("== missing values per metric (failed scrapes)")
    print(df[metrics].isna().sum().to_string(), "\n")

    print("== per-service mean / median / std for p95_latency_ms")
    print(df.groupby("service")["p95_latency_ms"].agg(["mean", "median", "std", "max"]).round(1), "\n")

    print("== normal vs incident minutes: median of each metric")
    print(df.groupby("is_anomaly")[metrics].median().round(2).T, "\n")

    print("== incident minutes by type")
    print(df.loc[df["is_anomaly"] == 1, "incident_type"].value_counts().to_string(), "\n")

    print("== label rates")
    for col in ["is_anomaly", "slo_breach", "will_breach_15m"]:
        print(f"  {col:<16} {df[col].mean():.2%}")

    print("\n== correlation of metrics with p95_latency_ms (Pearson)")
    print(df[metrics].corr()["p95_latency_ms"].drop("p95_latency_ms").sort_values(ascending=False).round(3).to_string())


if __name__ == "__main__":
    main()
