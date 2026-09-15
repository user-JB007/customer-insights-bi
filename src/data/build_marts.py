"""Build curated analytics marts from raw CSVs (local stand-in for Snowflake SQL).

Mirrors the logic in sql/marts/*.sql so the portfolio runs fully offline while
the SQL files remain the source of truth for warehouse deployment.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def load_raw(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(raw_dir / "customers.csv", parse_dates=["signup_date", "churn_date", "as_of_date"])
    transactions = pd.read_csv(raw_dir / "transactions.csv", parse_dates=["txn_date"])
    support = pd.read_csv(raw_dir / "support_events.csv", parse_dates=["created_at"])
    return customers, transactions, support


def mart_customer_360(customers: pd.DataFrame, transactions: pd.DataFrame, support: pd.DataFrame) -> pd.DataFrame:
    succ = transactions[transactions["status"] == "succeeded"]
    txn_agg = succ.groupby("customer_id").agg(
        lifetime_revenue=("amount", "sum"),
        txn_count=("transaction_id", "count"),
        last_txn_date=("txn_date", "max"),
        first_txn_date=("txn_date", "min"),
        avg_txn_amount=("amount", "mean"),
    ).reset_index()

    sup_agg = support.groupby("customer_id").agg(
        total_tickets=("event_id", "count"),
        avg_resolve_hours=("resolved_hours", "mean"),
        critical_tickets=("priority", lambda s: (s == "critical").sum()),
    ).reset_index()

    m = customers.merge(txn_agg, on="customer_id", how="left").merge(sup_agg, on="customer_id", how="left")
    m["lifetime_revenue"] = m["lifetime_revenue"].fillna(0)
    m["txn_count"] = m["txn_count"].fillna(0).astype(int)
    m["total_tickets"] = m["total_tickets"].fillna(0).astype(int)
    m["avg_resolve_hours"] = m["avg_resolve_hours"].fillna(0).round(1)
    m["critical_tickets"] = m["critical_tickets"].fillna(0).astype(int)
    m["avg_txn_amount"] = m["avg_txn_amount"].fillna(0).round(2)
    m["days_since_last_txn"] = (m["as_of_date"] - m["last_txn_date"]).dt.days
    m["is_active"] = ((m["is_churned"] == 0) & (m["mrr"] > 0)).astype(int)
    m["customer_health_score"] = (
        0.30 * (m["feature_adoption_score"] * 100)
        + 0.20 * (m["nps_score"].clip(-100, 100) + 100) / 2
        + 0.25 * (m["monthly_active_days"] / 28 * 100)
        + 0.15 * (100 - (m["support_tickets_90d"].clip(0, 10) * 10))
        + 0.10 * (100 - (m["payment_failures_90d"].clip(0, 5) * 20))
    ).round(1)
    return m


def mart_retention_monthly(customers: pd.DataFrame) -> pd.DataFrame:
    """Logo retention by signup cohort × months since signup."""
    rows = []
    cust = customers.copy()
    cust["cohort_month"] = cust["signup_date"].dt.to_period("M").astype(str)
    as_of = cust["as_of_date"].max()

    for cohort, g in cust.groupby("cohort_month"):
        cohort_start = pd.Period(cohort, freq="M").to_timestamp()
        size = len(g)
        max_m = min(24, ((as_of.year - cohort_start.year) * 12 + (as_of.month - cohort_start.month)))
        for m in range(0, max_m + 1):
            month_end = cohort_start + pd.offsets.MonthEnd(m + 1)
            still = g[
                (g["is_churned"] == 0)
                | ((g["is_churned"] == 1) & (g["churn_date"] > month_end))
            ]
            retained = len(still)
            rows.append(
                {
                    "cohort_month": cohort,
                    "months_since_signup": m,
                    "cohort_size": size,
                    "customers_retained": retained,
                    "retention_rate": round(retained / size, 4) if size else 0.0,
                }
            )
    return pd.DataFrame(rows)


def mart_revenue_cohorts(customers: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    cust = customers.copy()
    cust["cohort_month"] = cust["signup_date"].dt.to_period("M").astype(str)
    succ = transactions[transactions["status"] == "succeeded"].copy()
    succ["txn_month"] = succ["txn_date"].dt.to_period("M").astype(str)
    merged = succ.merge(cust[["customer_id", "cohort_month", "signup_date"]], on="customer_id")
    merged["months_since_signup"] = (
        (merged["txn_date"].dt.year - merged["signup_date"].dt.year) * 12
        + (merged["txn_date"].dt.month - merged["signup_date"].dt.month)
    ).clip(lower=0)

    agg = (
        merged.groupby(["cohort_month", "months_since_signup"], as_index=False)
        .agg(revenue=("amount", "sum"), paying_customers=("customer_id", "nunique"), txn_count=("transaction_id", "count"))
    )
    cohort_sizes = cust.groupby("cohort_month").size().rename("cohort_size").reset_index()
    agg = agg.merge(cohort_sizes, on="cohort_month")
    agg["revenue"] = agg["revenue"].round(2)
    agg["revenue_per_customer"] = (agg["revenue"] / agg["cohort_size"]).round(2)
    return agg.sort_values(["cohort_month", "months_since_signup"])


def mart_mrr_movement(customers: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """Approximate monthly MRR snapshot + new / churned / expansion proxy."""
    cust = customers.copy()
    as_of = cust["as_of_date"].max()
    months = pd.period_range("2022-01", as_of.to_period("M"), freq="M")
    rows = []
    for p in months:
        month_end = p.to_timestamp(how="end").normalize()
        active = cust[
            (cust["signup_date"] <= month_end)
            & ((cust["is_churned"] == 0) | (cust["churn_date"] > month_end))
            & (cust["mrr"] > 0)
        ]
        new = cust[(cust["signup_date"].dt.to_period("M") == p) & (cust["mrr"] > 0)]
        churned = cust[(cust["is_churned"] == 1) & (cust["churn_date"].dt.to_period("M") == p)]
        rows.append(
            {
                "month": str(p),
                "active_customers": len(active),
                "mrr": round(active["mrr"].sum(), 2),
                "arr": round(active["mrr"].sum() * 12, 2),
                "new_customers": len(new),
                "new_mrr": round(new["mrr"].sum(), 2),
                "churned_customers": len(churned),
                "churned_mrr": round(churned["mrr"].sum(), 2),
                "logo_churn_rate": round(len(churned) / max(len(active) + len(churned), 1), 4),
            }
        )
    df = pd.DataFrame(rows)
    df["net_new_mrr"] = (df["new_mrr"] - df["churned_mrr"]).round(2)
    df["mrr_growth_pct"] = (df["mrr"].pct_change() * 100).round(2)
    return df


def mart_segment_performance(c360: pd.DataFrame) -> pd.DataFrame:
    g = (
        c360.groupby(["segment", "region", "plan"], as_index=False)
        .agg(
            customers=("customer_id", "count"),
            active_customers=("is_active", "sum"),
            churned=("is_churned", "sum"),
            total_mrr=("mrr", "sum"),
            avg_mrr=("mrr", "mean"),
            avg_health=("customer_health_score", "mean"),
            avg_nps=("nps_score", "mean"),
            lifetime_revenue=("lifetime_revenue", "sum"),
        )
    )
    g["churn_rate"] = (g["churned"] / g["customers"]).round(4)
    g["total_mrr"] = g["total_mrr"].round(2)
    g["avg_mrr"] = g["avg_mrr"].round(2)
    g["avg_health"] = g["avg_health"].round(1)
    g["avg_nps"] = g["avg_nps"].round(1)
    g["lifetime_revenue"] = g["lifetime_revenue"].round(2)
    return g


def mart_product_revenue(transactions: pd.DataFrame) -> pd.DataFrame:
    succ = transactions[transactions["status"] == "succeeded"].copy()
    succ["txn_month"] = succ["txn_date"].dt.to_period("M").astype(str)
    return (
        succ.groupby(["txn_month", "product"], as_index=False)
        .agg(revenue=("amount", "sum"), txn_count=("transaction_id", "count"), customers=("customer_id", "nunique"))
        .assign(revenue=lambda d: d["revenue"].round(2))
        .sort_values(["txn_month", "product"])
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/marts"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    customers, transactions, support = load_raw(args.raw_dir)
    c360 = mart_customer_360(customers, transactions, support)
    retention = mart_retention_monthly(customers)
    rev_cohorts = mart_revenue_cohorts(customers, transactions)
    mrr = mart_mrr_movement(customers, transactions)
    segments = mart_segment_performance(c360)
    products = mart_product_revenue(transactions)

    outputs = {
        "customer_360": c360,
        "retention_monthly": retention,
        "revenue_cohorts": rev_cohorts,
        "mrr_movement": mrr,
        "segment_performance": segments,
        "product_revenue": products,
    }
    for name, df in outputs.items():
        csv_path = args.out_dir / f"{name}.csv"
        parquet_path = args.out_dir / f"{name}.parquet"
        df.to_csv(csv_path, index=False)
        df.to_parquet(parquet_path, index=False)
        print(f"  {name}: {len(df):,} rows → {csv_path.name}")

    # Also copy processed feature table for ML
    processed = Path("data/processed")
    processed.mkdir(parents=True, exist_ok=True)
    feature_cols = [
        "customer_id", "segment", "region", "plan", "acquisition_channel", "seats", "mrr",
        "tenure_days", "monthly_active_days", "support_tickets_90d", "nps_score",
        "feature_adoption_score", "payment_failures_90d", "lifetime_revenue", "txn_count",
        "total_tickets", "customer_health_score", "is_churned",
    ]
    c360[feature_cols].to_csv(processed / "churn_features.csv", index=False)
    c360[feature_cols].to_parquet(processed / "churn_features.parquet", index=False)
    print(f"  churn_features: {len(c360):,} rows → data/processed/")


if __name__ == "__main__":
    main()
