#!/usr/bin/env python3
"""One-command local pipeline: data → (optional API source) → marts → churn → Power BI → (optional API sink)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("\n" + "=" * 60)
    print("→", " ".join(cmd))
    print("=" * 60)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run customer insights pipeline")
    parser.add_argument(
        "--source",
        choices=["file", "api", "both"],
        default="file",
        help="file=generate raw CSVs; api=JSONPlaceholder engagement pull; both=file then api",
    )
    parser.add_argument(
        "--sink",
        choices=["none", "api"],
        default="none",
        help="api=POST KPI snapshot to local landing + JSONPlaceholder",
    )
    parser.add_argument("--skip-model", action="store_true")
    parser.add_argument("--skip-viz", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    if args.source in ("file", "both"):
        run([py, "src/data/generate_source_data.py", "--n-customers", "5000", "--out-dir", "data/raw"])

    if args.source in ("api", "both"):
        print("\n" + "=" * 60)
        print("→ pull_api (JSONPlaceholder engagement)")
        print("=" * 60)
        from src.integrations.api_source import fetch_engagement
        print(fetch_engagement(use_network=True))

    run([py, "src/data/build_marts.py", "--raw-dir", "data/raw", "--out-dir", "data/marts"])

    if not args.skip_model:
        run([py, "src/models/train_churn.py", "--features", "data/processed/churn_features.csv", "--out-dir", "artifacts/model"])
    if not args.skip_viz:
        run([py, "src/viz/generate_powerbi_pages.py", "--marts", "data/marts", "--artifacts", "artifacts/model", "--out", "powerbi/screenshots"])

    if args.sink == "api":
        print("\n" + "=" * 60)
        print("→ push_api (KPI snapshot sink)")
        print("=" * 60)
        from src.integrations.api_sink import push_kpi_snapshot
        import json
        print(json.dumps(push_kpi_snapshot(), indent=2, default=str))

    print("\n✓ Pipeline complete.")
    print("  Marts:        data/marts/")
    print("  Model:        artifacts/model/")
    print("  Power BI:     powerbi/screenshots/")
    print("  (mirrored)    reports/powerbi/screenshots/")


if __name__ == "__main__":
    main()
