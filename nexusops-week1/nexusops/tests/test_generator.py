"""Week 1 data tests for the telemetry generator.

These are the first "data tests" of the capstone. They check the dataset contract,
reproducibility, and that labels are sane. CI will run them from Week 6 onwards.
"""

from pathlib import Path

import numpy as np
import pytest

from nexusops.telemetry.generator import _future_any, content_hash, generate, load_config
from nexusops.telemetry.schema import ALL_COLUMNS, METRIC_COLUMNS, VALID_RANGES

CONFIG = Path(__file__).resolve().parents[1] / "configs" / "telemetry_v0.yaml"


@pytest.fixture(scope="module")
def small_cfg():
    cfg = load_config(CONFIG)
    cfg["days"] = 3  # keep tests fast
    return cfg


@pytest.fixture(scope="module")
def df(small_cfg):
    data, _ = generate(small_cfg)
    return data


def test_schema_columns_and_order(df):
    assert list(df.columns) == list(ALL_COLUMNS)


def test_row_count(df, small_cfg):
    expected = small_cfg["days"] * 1440 // small_cfg["freq_minutes"] * len(small_cfg["services"])
    assert len(df) == expected


def test_no_duplicate_keys(df):
    assert not df.duplicated(["timestamp", "service"]).any()


def test_value_ranges(df):
    for col, (lo, hi) in VALID_RANGES.items():
        s = df[col].dropna()
        assert (s >= lo).all(), f"{col} below {lo}"
        if hi is not None:
            assert (s <= hi).all(), f"{col} above {hi}"


def test_missing_rate_close_to_config(df, small_cfg):
    rate = df[list(METRIC_COLUMNS)].isna().to_numpy().mean()
    assert abs(rate - small_cfg["missing_rate"]) < 0.001


def test_same_seed_same_data(small_cfg):
    a, _ = generate(small_cfg)
    b, _ = generate(small_cfg)
    assert content_hash(a) == content_hash(b)


def test_different_seed_different_data(small_cfg):
    other = {**small_cfg, "seed": small_cfg["seed"] + 1}
    a, _ = generate(small_cfg)
    b, _ = generate(other)
    assert content_hash(a) != content_hash(b)


def test_labels_are_binary_and_not_empty(df):
    for col in ["is_anomaly", "slo_breach", "will_breach_15m"]:
        assert set(df[col].unique()) <= {0, 1}
        assert 0.001 < df[col].mean() < 0.5, f"{col} rate looks wrong: {df[col].mean():.4f}"


def test_incident_type_consistent_with_is_anomaly(df):
    assert ((df["incident_type"] != "none") == (df["is_anomaly"] == 1)).all()


def test_future_label_looks_forward_not_at_now():
    flags = np.array([0, 0, 0, 1, 0, 0])
    # horizon 2: t=1 and t=2 see the breach at t=3; t=3 itself does not (it's "now", not future)
    assert _future_any(flags, 2).tolist() == [0, 1, 1, 0, 0, 0]
