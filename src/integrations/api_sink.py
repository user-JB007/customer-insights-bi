"""API sink: POST retention/support KPI snapshot to local landing API + JSONPlaceholder."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.integrations.http_client import post_json

ROOT = Path(__file__).resolve().parents[2]


def _load_cfg() -> dict[str, Any]:
    path = ROOT / "config" / "pipeline.yaml"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _sink_cfg() -> dict[str, Any]:
    cfg = _load_cfg().get("api_sink", {})
    return {
        "local_url": os.getenv("SINK_API_URL", cfg.get("local_url", "http://127.0.0.1:8089/ingest")),
        "external_url": os.getenv(
            "EXTERNAL_SINK_URL", cfg.get("external_url", "https://jsonplaceholder.typicode.com/posts")
        ),
        "timeout": float(os.getenv("API_HTTP_TIMEOUT", cfg.get("timeout", 20))),
        "retries": int(os.getenv("API_HTTP_RETRIES", cfg.get("retries", 3))),
    }


def build_kpi_snapshot(marts_dir: Path | None = None) -> dict[str, Any]:
    marts = marts_dir or (ROOT / "data" / "marts")
    snap: dict[str, Any] = {
        "pipeline": "customer-insights-bi",
        "snapshot_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kpis": {},
    }

    c360 = marts / "customer_360.csv"
    if c360.exists():
        df = pd.read_csv(c360)
        snap["kpis"]["customers"] = int(len(df))
        if "is_churned" in df.columns:
            snap["kpis"]["churn_rate"] = round(float(df["is_churned"].mean()), 4)
        if "mrr" in df.columns:
            snap["kpis"]["total_mrr"] = round(float(df["mrr"].sum()), 2)
        if "customer_health_score" in df.columns:
            snap["kpis"]["avg_health"] = round(float(df["customer_health_score"].mean()), 1)

    retention = marts / "retention_monthly.csv"
    if retention.exists():
        df = pd.read_csv(retention)
        m0 = df[df["months_since_signup"] == 0] if "months_since_signup" in df.columns else df
        snap["kpis"]["retention_rows"] = int(len(df))
        if "retention_rate" in df.columns and len(df):
            snap["kpis"]["avg_retention_rate"] = round(float(df["retention_rate"].mean()), 4)

    support = marts / "support_sla.csv"
    if support.exists():
        df = pd.read_csv(support)
        snap["kpis"]["support_sla_rows"] = int(len(df))
        for col in ("pct_within_sla", "avg_csat", "pending_tickets"):
            if col in df.columns:
                snap["kpis"][col] = round(float(df[col].mean()), 4) if "pct" in col or "avg" in col else int(df[col].sum())

    eng = marts / "engagement_events.csv"
    if eng.exists():
        df = pd.read_csv(eng)
        snap["kpis"]["engagement_events"] = int(len(df))
        if "event_type" in df.columns:
            snap["kpis"]["engagement_by_type"] = df["event_type"].value_counts().to_dict()

    return snap


def _write_receipt(name: str, payload: dict[str, Any], response: Any) -> Path:
    receipts = ROOT / "data" / "sink_receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = receipts / f"{ts}_{name}.json"
    path.write_text(json.dumps({"request": payload, "response": response}, indent=2, default=str), encoding="utf-8")
    return path


def push_kpi_snapshot(
    *,
    post_local: bool = True,
    post_external: bool = True,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scfg = _sink_cfg()
    body = payload or build_kpi_snapshot()
    result: dict[str, Any] = {"payload_keys": list(body.keys()), "deliveries": {}}

    if post_local:
        try:
            resp = post_json(scfg["local_url"], body, timeout=scfg["timeout"], retries=scfg["retries"])
            receipt = _write_receipt("local", body, resp)
            result["deliveries"]["local"] = {"ok": True, "url": scfg["local_url"], "receipt": str(receipt), "response": resp}
        except Exception as exc:
            landing = ROOT / "data" / "landing"
            landing.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            fallback = landing / f"kpi_snapshot_{ts}.json"
            fallback.write_text(json.dumps(body, indent=2, default=str), encoding="utf-8")
            result["deliveries"]["local"] = {"ok": False, "error": str(exc), "fallback_file": str(fallback)}

    if post_external:
        try:
            ext_body = {
                "title": "customer-insights-bi KPI snapshot",
                "body": json.dumps(body, default=str)[:5000],
                "userId": 1,
            }
            resp = post_json(scfg["external_url"], ext_body, timeout=scfg["timeout"], retries=scfg["retries"])
            receipt = _write_receipt("external_jsonplaceholder", ext_body, resp)
            result["deliveries"]["external"] = {
                "ok": True,
                "url": scfg["external_url"],
                "receipt": str(receipt),
                "response": resp,
            }
        except Exception as exc:
            result["deliveries"]["external"] = {"ok": False, "error": str(exc)}

    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Push KPI snapshot to HTTP sinks")
    parser.add_argument("--no-local", action="store_true")
    parser.add_argument("--no-external", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(push_kpi_snapshot(post_local=not args.no_local, post_external=not args.no_external), indent=2, default=str))


if __name__ == "__main__":
    main()
