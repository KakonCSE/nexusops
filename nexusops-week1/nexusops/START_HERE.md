# Start here: run NexusOps Week 1 on your laptop

This folder is the Week 1 starter project. Follow the steps below in order. Every command is run from the project folder (`~/nexuxops`) in a terminal.

## 1. Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Python | 3.11 or newer | `python3 --version` |
| venv module | comes with Python | `python3 -m venv --help` |
| git | any recent version | `git --version` |
| make (optional) | any | `make --version` |

On Ubuntu/Debian, if `python3 -m venv` fails, install the venv package first:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git make
```

## 2. Go to the project folder and start git

```bash
cd ~/nexuxops
git init                      # only the first time
git add .
git commit -m "Week 1 starter"
```

`.gitignore` already keeps `.venv/` and the generated data in `data/raw/` out of git.

## 3. Create the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate     # your prompt now starts with (.venv)
python -m pip install --upgrade pip
```

Run `source .venv/bin/activate` again every time you open a new terminal.

## 4. Install the requirements

There is no `requirements.txt`. The dependencies live in `pyproject.toml` (numpy, pandas, pyarrow, pyyaml, plus pytest, jupyterlab and ruff for development). Install the project and its dev extras in editable mode:

```bash
pip install -e ".[dev]"
```

"Editable" means your changes in `src/` take effect immediately, without reinstalling.

## 5. Generate the dataset

```bash
python scripts/generate_telemetry.py --config configs/telemetry_v0.yaml --out-dir data/raw
```

Expected: a JSON manifest is printed, ending like this:

```
  "rows": 80640,
  "content_hash": "d39d3d08801c5478",
  "incidents": 35,
  "anomaly_rate": 0.0252,
  "slo_breach_rate": 0.0164,
  "will_breach_15m_rate": 0.0225
```

Three files appear in `data/raw/`: `telemetry_v0.parquet`, `telemetry_v0_incidents.csv`, `telemetry_v0_manifest.json`. A copy of these is already in the folder, so this step overwrites them with identical data. If your `content_hash` differs, check your numpy/pandas versions (the reference was numpy 2.x and pandas 3.0); the row count and rates should still match.

## 6. Explore the dataset

```bash
python scripts/explore_telemetry.py --data data/raw/telemetry_v0.parquet
```

Expected (start and end of the output):

```
== shape: 80,640 rows x 13 columns
== time range: 2026-01-05 00:00:00+00:00  ->  2026-01-18 23:59:00+00:00
== services: ['api-gateway', 'auth-svc', 'ledger-db', 'payments-api']
...
== label rates
  is_anomaly       2.52%
  slo_breach       1.64%
  will_breach_15m  2.25%

== correlation of metrics with p95_latency_ms (Pearson)
error_rate_pct        0.695
tcp_retransmit_pct    0.390
...
```

## 7. Run the non-ML baseline

```bash
python scripts/rule_baseline.py --data data/raw/telemetry_v0.parquet
```

Expected:

```
Evaluated on days 8-14 only (the 'unseen' half).

static_thresholds    {'TP': 856, 'FP': 0, 'FN': 288, 'TN': 39176, 'precision': 1.0, 'recall': 0.748}
zscore_k3.0          {'TP': 1047, 'FP': 243, 'FN': 97, 'TN': 38933, 'precision': 0.812, 'recall': 0.915}
```

These are the numbers every later ML model must beat.

## 8. Run the tests

```bash
python -m pytest -q
```

Expected: `10 passed`. You may also see a few `Pandas4Warning: DatetimeIndex.dayofweek is deprecated` warnings. They are harmless for now.

## Shortcut: the Makefile

If you have `make`, these do the same as steps 3 to 8 (no need to activate the venv, it uses `.venv/bin/python`):

```bash
make setup      # step 3 + 4
make data       # step 5
make explore    # step 6
make baseline   # step 7
make test       # step 8
make clean      # deletes generated data and caches (keeps code and config)
```

## If something goes wrong

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'nexusops'` | The venv is not active or step 4 was skipped. Run `source .venv/bin/activate` then `pip install -e ".[dev]"`. |
| `ensurepip is not available` when creating the venv | Install `python3-venv` (see step 1). |
| `requires a different Python: 3.10...` | Your Python is too old. Install 3.11+ (for example `sudo apt install python3.12 python3.12-venv`, then use `python3.12 -m venv .venv`). |
| `FileNotFoundError: data/raw/telemetry_v0.parquet` | Run step 5 first, and run commands from the project folder. |

## What next

Read `docs/notes/week01-engineering-notes.md` and `PROGRESS.md`, then do the Week 1 assignment from the lesson before starting Week 2.
