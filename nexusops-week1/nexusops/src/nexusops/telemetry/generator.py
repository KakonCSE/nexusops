"""Synthetic infrastructure telemetry generator (dataset v0).

What it simulates
-----------------
Four fictional services on a payment path, sampled once per minute:
    rps, cpu_pct, mem_pct, p95_latency_ms, error_rate_pct, tcp_retransmit_pct, db_pool_in_use_pct

Normal behaviour  = daily traffic cycle + weekend dip + random noise.
Abnormal behaviour = injected incidents (cpu_saturation, memory_leak, packet_loss,
                     db_pool_exhaustion) that RAMP UP gradually, so there is an early-warning
                     signal before the SLO actually breaks. That ramp is what makes
                     "predict degradation 15 minutes ahead" learnable later.

Lab-grade, not production: real telemetry has cross-service cascades, deploy events,
seasonality drift, and no ground-truth labels. We add those deliberately in later weeks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from nexusops.telemetry.schema import ALL_COLUMNS, METRIC_COLUMNS

GENERATOR_VERSION = "0.1.0"


@dataclass
class Incident:
    service: str
    kind: str
    start_idx: int
    duration: int


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def config_hash(cfg: dict) -> str:
    """Stable hash of the config, so we can prove which config produced a dataset."""
    canonical = json.dumps(cfg, sort_keys=True, default=str).encode()
    return hashlib.sha256(canonical).hexdigest()[:16]


def _severity_curve(duration: int, ramp_fraction: float) -> np.ndarray:
    """0 -> 1 linear ramp (the early-warning phase), then plateau at 1 (the outage phase)."""
    ramp_len = max(1, int(duration * ramp_fraction))
    ramp = np.linspace(0.05, 1.0, ramp_len)
    plateau = np.ones(duration - ramp_len)
    return np.concatenate([ramp, plateau])


def _sample_incidents(cfg: dict, n: int, rng: np.random.Generator) -> list[Incident]:
    inc_cfg = cfg["incidents"]
    kinds = list(inc_cfg["types"].keys())
    weights = np.array(list(inc_cfg["types"].values()), dtype=float)
    weights /= weights.sum()

    incidents: list[Incident] = []
    for service in cfg["services"]:
        busy = np.zeros(n, dtype=bool)  # prevents overlapping incidents on the same service
        count = rng.poisson(inc_cfg["per_service_per_day"] * cfg["days"])
        for _ in range(count):
            duration = int(rng.integers(inc_cfg["min_duration_minutes"], inc_cfg["max_duration_minutes"] + 1))
            start = int(rng.integers(0, n - duration))
            # keep a 30-minute gap so each incident is a separate, clean event
            lo, hi = max(0, start - 30), min(n, start + duration + 30)
            if busy[lo:hi].any():
                continue
            busy[start:start + duration] = True
            kind = str(rng.choice(kinds, p=weights))
            incidents.append(Incident(service, kind, start, duration))
    return incidents


def _future_any(flags: np.ndarray, horizon: int) -> np.ndarray:
    """out[t] = 1 if flags[t+1 .. t+horizon] contains any 1.

    Looks FORWARD in time. This is fine for creating a label, but a FEATURE built like this
    would be data leakage (the model would be reading the future). Remember this in Week 3.
    """
    s = pd.Series(flags[::-1].astype(float))
    # reversed rolling max over the next `horizon` values, then shift by one so t itself is excluded
    fut = s.rolling(horizon, min_periods=1).max().shift(1).fillna(0).to_numpy()[::-1]
    return fut.astype(np.int8)


def generate(cfg: dict) -> tuple[pd.DataFrame, list[Incident]]:
    rng = np.random.default_rng(cfg["seed"])
    n = int(cfg["days"] * 1440 / cfg["freq_minutes"])
    ts = pd.date_range(cfg["start"], periods=n, freq=f"{cfg['freq_minutes']}min", tz="UTC")

    minute_of_day = np.asarray(ts.hour * 60 + ts.minute)
    is_weekend = np.asarray(ts.dayofweek >= 5)
    # Daily traffic cycle: peak around 14:00 UTC, trough around 02:00 UTC.
    diurnal = 1.0 + 0.4 * np.cos(2 * np.pi * (minute_of_day - 840) / 1440)
    weekly = np.where(is_weekend, 0.7, 1.0)

    incidents = _sample_incidents(cfg, n, rng)
    slo = cfg["slo"]
    horizon = int(cfg["prediction_horizon_minutes"] / cfg["freq_minutes"])
    ramp_fraction = cfg["incidents"]["ramp_fraction"]

    frames = []
    for service, p in cfg["services"].items():
        load = diurnal * weekly * (1 + rng.normal(0, 0.05, n))
        rps = p["base_rps"] * load
        cpu = p["base_cpu_pct"] * (0.6 + 0.4 * load) + rng.normal(0, 2.0, n)
        mem = p["base_mem_pct"] + rng.normal(0, 1.5, n)
        retrans = 0.05 + np.abs(rng.normal(0, 0.02, n))
        pool = 30 * load + rng.normal(0, 3.0, n)
        lat_mult = np.ones(n)
        err_add = np.zeros(n)
        is_anom = np.zeros(n, dtype=np.int8)
        itype = np.full(n, "none", dtype=object)

        for inc in (i for i in incidents if i.service == service):
            sl = slice(inc.start_idx, inc.start_idx + inc.duration)
            s = _severity_curve(inc.duration, ramp_fraction)
            if inc.kind == "cpu_saturation":
                cpu[sl] += (97 - cpu[sl]) * s
                lat_mult[sl] *= 1 + 4.5 * s**2
                err_add[sl] += 1.5 * s**3
            elif inc.kind == "memory_leak":
                mem[sl] += (96 - mem[sl]) * s
                lat_mult[sl] *= 1 + 3.0 * s**3
                err_add[sl] += 4.0 * s**4          # OOM-kills near the end
            elif inc.kind == "packet_loss":
                retrans[sl] += 6.0 * s
                lat_mult[sl] *= 1 + 5.0 * s
                err_add[sl] += 2.5 * s
            elif inc.kind == "db_pool_exhaustion":
                pool[sl] += (100 - pool[sl]) * s
                lat_mult[sl] *= 1 + 6.0 * s**2
                err_add[sl] += 5.0 * s**3
            is_anom[sl] = 1
            itype[sl] = inc.kind

        cpu = np.clip(cpu, 0, 100)
        mem = np.clip(mem, 0, 100)
        pool = np.clip(pool, 0, 100)
        retrans = np.clip(retrans, 0, 100)
        # Latency grows non-linearly as CPU approaches saturation (queueing effect).
        latency = (
            p["base_latency_ms"]
            * (1 + 0.5 * (cpu / 100) ** 3)
            * rng.lognormal(0, 0.08, n)
            * lat_mult
        )
        errors = np.clip(p["base_error_pct"] * rng.lognormal(0, 0.2, n) + err_add, 0, 100)

        breach = ((latency > slo["p95_latency_ms"]) | (errors > slo["error_rate_pct"])).astype(np.int8)

        frames.append(pd.DataFrame({
            "timestamp": ts,
            "service": service,
            "rps": rps,
            "cpu_pct": cpu,
            "mem_pct": mem,
            "p95_latency_ms": latency,
            "error_rate_pct": errors,
            "tcp_retransmit_pct": retrans,
            "db_pool_in_use_pct": pool,
            "is_anomaly": is_anom,
            "incident_type": itype,
            "slo_breach": breach,
            "will_breach_15m": _future_any(breach, horizon),
        }))

    df = pd.concat(frames, ignore_index=True)

    # Simulate failed scrapes: blank out random metric cells AFTER labels are computed.
    metric_cols = list(METRIC_COLUMNS)
    mask = rng.random((len(df), len(metric_cols))) < cfg["missing_rate"]
    for j, col in enumerate(metric_cols):
        df.loc[mask[:, j], col] = np.nan

    df = df.sort_values(["timestamp", "service"], kind="stable").reset_index(drop=True)
    df = df.astype({c: t for c, t in ALL_COLUMNS.items() if c != "timestamp"})
    return df[list(ALL_COLUMNS)], incidents


def content_hash(df: pd.DataFrame) -> str:
    """Hash of the data values (not the file bytes). Same seed + config => same hash."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()[:16]


def write_dataset(df: pd.DataFrame, incidents: list[Incident], cfg: dict, out_dir: str | Path,
                  name: str = "telemetry_v0", fmt: str = "parquet") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data_path = out / f"{name}.{fmt}"
    if fmt == "parquet":
        df.to_parquet(data_path, index=False)
    elif fmt == "csv":
        df.to_csv(data_path, index=False)
    else:
        raise ValueError(f"unsupported format: {fmt}")

    pd.DataFrame([i.__dict__ for i in incidents]).to_csv(out / f"{name}_incidents.csv", index=False)

    manifest = {
        "dataset": name,
        "generator_version": GENERATOR_VERSION,
        "config_hash": config_hash(cfg),
        "seed": cfg["seed"],
        "rows": int(len(df)),
        "columns": list(df.columns),
        "content_hash": content_hash(df),
        "file": data_path.name,
        "file_bytes": data_path.stat().st_size,
        "incidents": len(incidents),
        "anomaly_rate": round(float(df["is_anomaly"].mean()), 4),
        "slo_breach_rate": round(float(df["slo_breach"].mean()), 4),
        "will_breach_15m_rate": round(float(df["will_breach_15m"].mean()), 4),
    }
    (out / f"{name}_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
