#!/usr/bin/env python3
"""One-command local pipeline: data → marts → churn model → dashboard screenshots."""
from __future__ import annotations

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
    py = sys.executable
    run([py, "src/data/generate_synthetic.py", "--n-customers", "5000", "--out-dir", "data/raw"])
    run([py, "src/data/build_marts.py", "--raw-dir", "data/raw", "--out-dir", "data/marts"])
    run([py, "src/models/train_churn.py", "--features", "data/processed/churn_features.csv", "--out-dir", "artifacts/model"])
    run([py, "src/viz/generate_dashboards.py", "--marts", "data/marts", "--artifacts", "artifacts/model", "--out", "reports/screenshots"])
    print("\n✓ Pipeline complete.")
    print("  Marts:       data/marts/")
    print("  Model:       artifacts/model/")
    print("  Screenshots: reports/screenshots/")


if __name__ == "__main__":
    main()
