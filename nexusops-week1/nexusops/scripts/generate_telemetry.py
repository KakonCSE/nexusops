"""CLI: generate the synthetic telemetry dataset.

Usage:
    python scripts/generate_telemetry.py --config configs/telemetry_v0.yaml --out-dir data/raw
"""

import argparse
import json

from nexusops.telemetry.generator import generate, load_config, write_dataset


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate NexusOps synthetic telemetry")
    ap.add_argument("--config", default="configs/telemetry_v0.yaml")
    ap.add_argument("--out-dir", default="data/raw")
    ap.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    ap.add_argument("--seed", type=int, help="override the seed in the config")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.seed is not None:
        cfg["seed"] = args.seed

    df, incidents = generate(cfg)
    manifest = write_dataset(df, incidents, cfg, args.out_dir, fmt=args.format)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
