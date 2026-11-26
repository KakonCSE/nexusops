.PHONY: setup data explore baseline test clean

PY ?= .venv/bin/python

setup:            ## create venv and install the project in editable mode
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

data:             ## generate dataset v0
	$(PY) scripts/generate_telemetry.py --config configs/telemetry_v0.yaml --out-dir data/raw

explore:          ## print dataset summary
	$(PY) scripts/explore_telemetry.py --data data/raw/telemetry_v0.parquet

baseline:         ## run the non-ML baseline detectors
	$(PY) scripts/rule_baseline.py --data data/raw/telemetry_v0.parquet

test:             ## run data tests
	$(PY) -m pytest -q

clean:            ## remove generated data and caches (keeps code and config)
	rm -rf data/raw/* .pytest_cache **/__pycache__
