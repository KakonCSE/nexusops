"""Dataset contract for telemetry v0.

Think of this like an API contract or a protobuf definition: every downstream stage
(validation, features, training, serving) depends on these column names and types.
Changing it is a breaking change and must bump the dataset version.
"""

# column -> pandas dtype
METRIC_COLUMNS = {
    "rps": "float64",                  # requests per second
    "cpu_pct": "float64",              # 0-100
    "mem_pct": "float64",              # 0-100
    "p95_latency_ms": "float64",       # 95th percentile request latency
    "error_rate_pct": "float64",       # % of requests returning 5xx
    "tcp_retransmit_pct": "float64",   # % of TCP segments retransmitted (network health)
    "db_pool_in_use_pct": "float64",   # % of DB connection pool in use
}

KEY_COLUMNS = {
    "timestamp": "datetime64[ns, UTC]",
    "service": "object",
}

# Ground-truth labels. ONLY exist because the data is synthetic.
# Real telemetry does not come with labels; we will discuss that gap in Week 3+.
LABEL_COLUMNS = {
    "is_anomaly": "int8",          # 1 if this minute is inside an injected incident window
    "incident_type": "object",     # "none" or the injected failure mode
    "slo_breach": "int8",          # 1 if p95 latency or error rate violates the SLO right now
    "will_breach_15m": "int8",     # 1 if slo_breach happens in the NEXT horizon minutes (prediction target)
}

ALL_COLUMNS = {**KEY_COLUMNS, **METRIC_COLUMNS, **LABEL_COLUMNS}

VALID_RANGES = {
    "rps": (0, None),
    "cpu_pct": (0, 100),
    "mem_pct": (0, 100),
    "p95_latency_ms": (0, None),
    "error_rate_pct": (0, 100),
    "tcp_retransmit_pct": (0, 100),
    "db_pool_in_use_pct": (0, 100),
}
