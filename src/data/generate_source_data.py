"""Generate source extracts for customer analytics (customers, transactions, support).

Produces operational CSVs under data/raw/ with retention and support/SLA signal
suitable for curated marts and churn modeling.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup"]
REGIONS = ["North America", "Europe", "APAC", "LATAM"]
PLANS = ["Free", "Starter", "Pro", "Business", "Enterprise"]
CHANNELS = ["Organic", "Paid Search", "Partner", "Referral", "Sales"]
PRODUCTS = ["Core Platform", "Analytics Add-on", "API Access", "Support Plus", "Storage Pack"]

SUPPORT_CATEGORIES = ["Billing", "Bug", "How-to", "Feature Request", "Outage"]
SUPPORT_CHANNELS = ["email", "chat", "phone", "portal"]
SLA_HOURS = {"low": 72, "medium": 48, "high": 24, "critical": 8}


def _dates_between(start: str, end: str, n: int) -> pd.Series:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    days = (end_ts - start_ts).days
    offsets = RNG.integers(0, days + 1, size=n)
    return pd.Series(pd.to_datetime(start_ts) + pd.to_timedelta(offsets, unit="D"))


def generate_customers(n: int = 5000, as_of: str = "2025-12-31") -> pd.DataFrame:
    as_of_ts = pd.Timestamp(as_of)
    signup = _dates_between("2022-01-01", "2025-11-30", n)

    segment = RNG.choice(SEGMENTS, size=n, p=[0.12, 0.28, 0.40, 0.20])
    region = RNG.choice(REGIONS, size=n, p=[0.40, 0.28, 0.22, 0.10])
    plan = RNG.choice(PLANS, size=n, p=[0.15, 0.30, 0.28, 0.17, 0.10])
    channel = RNG.choice(CHANNELS, size=n, p=[0.30, 0.25, 0.15, 0.18, 0.12])

    tenure_days = (as_of_ts - signup).dt.days.clip(lower=1)
    monthly_active_days = RNG.integers(0, 28, size=n).astype(float)
    plan_stickiness = np.array(
        [{"Free": 0.0, "Starter": 0.15, "Pro": 0.35, "Business": 0.50, "Enterprise": 0.65}[p] for p in plan]
    )
    support_tickets_90d = RNG.poisson(lam=1.2, size=n).astype(float)
    nps = RNG.normal(loc=35, scale=25, size=n).clip(-100, 100)
    feature_adoption = RNG.beta(2.2, 3.0, size=n)
    payment_failures_90d = RNG.poisson(lam=0.35, size=n).astype(float)
    seats = np.where(
        segment == "Enterprise",
        RNG.integers(50, 500, size=n),
        np.where(
            segment == "Mid-Market",
            RNG.integers(15, 80, size=n),
            np.where(segment == "SMB", RNG.integers(3, 25, size=n), RNG.integers(1, 8, size=n)),
        ),
    )

    logit = (
        -0.35
        + 1.1 * (plan == "Free").astype(float)
        + 0.65 * (plan == "Starter").astype(float)
        - 0.55 * plan_stickiness
        - 0.0012 * tenure_days.astype(float)
        - 0.055 * monthly_active_days
        + 0.28 * support_tickets_90d
        - 0.015 * nps
        - 1.4 * feature_adoption
        + 0.65 * payment_failures_90d
        + 0.25 * (region == "LATAM").astype(float)
        - 0.30 * (channel == "Partner").astype(float)
    )
    churn_prob = 1 / (1 + np.exp(-logit))
    is_churned = RNG.random(n) < churn_prob

    churn_date = pd.Series([pd.NaT] * n, dtype="datetime64[ns]")
    for i in np.where(is_churned)[0]:
        span = max(int((as_of_ts - signup.iloc[i]).days), 1)
        churn_date.iloc[i] = signup.iloc[i] + pd.Timedelta(days=int(RNG.integers(max(span // 4, 1), span + 1)))

    plan_mrr = {"Free": 0, "Starter": 29, "Pro": 79, "Business": 199, "Enterprise": 799}
    mrr = np.array([plan_mrr[p] * (seats[i] / 5 if p == "Enterprise" else 1) for i, p in enumerate(plan)], dtype=float)
    mrr = np.round(mrr * RNG.uniform(0.85, 1.15, size=n), 2)
    mrr = np.where(plan == "Free", 0.0, mrr)

    df = pd.DataFrame(
        {
            "customer_id": [f"C{str(i).zfill(6)}" for i in range(1, n + 1)],
            "signup_date": signup.dt.strftime("%Y-%m-%d"),
            "segment": segment,
            "region": region,
            "plan": plan,
            "acquisition_channel": channel,
            "seats": seats,
            "mrr": mrr,
            "tenure_days": tenure_days.astype(int),
            "monthly_active_days": np.round(monthly_active_days, 1),
            "support_tickets_90d": support_tickets_90d.astype(int),
            "nps_score": np.round(nps, 1),
            "feature_adoption_score": np.round(feature_adoption, 3),
            "payment_failures_90d": payment_failures_90d.astype(int),
            "is_churned": is_churned.astype(int),
            "churn_date": churn_date.dt.strftime("%Y-%m-%d"),
            "as_of_date": as_of,
        }
    )
    return df


def generate_transactions(customers: pd.DataFrame, avg_txns: float = 8.0) -> pd.DataFrame:
    rows = []
    txn_id = 1
    for _, c in customers.iterrows():
        signup = pd.Timestamp(c["signup_date"])
        end = pd.Timestamp(c["churn_date"]) if pd.notna(c["churn_date"]) and c["churn_date"] else pd.Timestamp(c["as_of_date"])
        months = max(1, (end.year - signup.year) * 12 + (end.month - signup.month) + 1)
        n_txns = max(1, int(RNG.poisson(avg_txns * (months / 12))))
        for _ in range(n_txns):
            day_offset = int(RNG.integers(0, max((end - signup).days, 1) + 1))
            txn_date = signup + pd.Timedelta(days=day_offset)
            if txn_date > end:
                txn_date = end
            product = RNG.choice(PRODUCTS, p=[0.45, 0.15, 0.15, 0.12, 0.13])
            base = max(c["mrr"], 19) if c["plan"] != "Free" else RNG.choice([0, 9, 19])
            amount = round(float(base * RNG.uniform(0.6, 1.4)), 2)
            if c["plan"] == "Free" and product == "Core Platform":
                amount = 0.0
            status = RNG.choice(["succeeded", "failed", "refunded"], p=[0.92, 0.05, 0.03])
            rows.append(
                {
                    "transaction_id": f"T{str(txn_id).zfill(8)}",
                    "customer_id": c["customer_id"],
                    "txn_date": txn_date.strftime("%Y-%m-%d"),
                    "product": product,
                    "amount": amount if status != "refunded" else -abs(amount),
                    "currency": "USD",
                    "status": status,
                    "billing_period": RNG.choice(["monthly", "annual"], p=[0.75, 0.25]),
                }
            )
            txn_id += 1
    return pd.DataFrame(rows)


def generate_support_events(customers: pd.DataFrame) -> pd.DataFrame:
    """Seed support tickets with opened/resolved/SLA clocks, status, channel, CSAT."""
    rows = []
    eid = 1
    for _, c in customers.iterrows():
        n = int(c["support_tickets_90d"]) + int(RNG.poisson(0.5))
        if n == 0:
            continue
        signup = pd.Timestamp(c["signup_date"])
        end = pd.Timestamp(c["churn_date"]) if pd.notna(c["churn_date"]) and c["churn_date"] else pd.Timestamp(c["as_of_date"])
        span = max((end - signup).days, 1)
        for _ in range(n):
            opened = signup + pd.Timedelta(
                days=int(RNG.integers(0, span + 1)),
                hours=int(RNG.integers(0, 24)),
                minutes=int(RNG.integers(0, 60)),
            )
            if opened > end:
                opened = end
            priority = str(RNG.choice(["low", "medium", "high", "critical"], p=[0.40, 0.35, 0.20, 0.05]))
            sla_hours = SLA_HOURS[priority]
            sla_due = opened + pd.Timedelta(hours=sla_hours)
            reason = str(RNG.choice(SUPPORT_CATEGORIES, p=[0.25, 0.20, 0.30, 0.15, 0.10]))
            channel = str(RNG.choice(SUPPORT_CHANNELS, p=[0.35, 0.30, 0.20, 0.15]))

            roll = float(RNG.random())
            if roll < 0.10:
                status = "pending"
                resolved = pd.NaT
                resolve_hours = None
                csat = None
            elif roll < 0.14:
                status = "escalated"
                resolved = pd.NaT
                resolve_hours = None
                csat = None
            else:
                if RNG.random() < 0.80:
                    resolve_hours = float(RNG.uniform(0.4, sla_hours * 0.95))
                    status = "resolved"
                else:
                    resolve_hours = float(RNG.uniform(sla_hours * 1.05, sla_hours * 3.0))
                    status = RNG.choice(["resolved", "closed_unresolved"], p=[0.88, 0.12])
                resolved = opened + pd.Timedelta(hours=resolve_hours)
                if status == "closed_unresolved":
                    csat = int(RNG.choice([1, 2, 3], p=[0.4, 0.4, 0.2]))
                elif resolve_hours <= sla_hours:
                    csat = int(RNG.choice([3, 4, 5], p=[0.15, 0.40, 0.45]))
                else:
                    csat = int(RNG.choice([1, 2, 3, 4], p=[0.15, 0.30, 0.40, 0.15]))

            within_sla = ""
            if pd.notna(resolved):
                within_sla = resolved <= sla_due

            rows.append(
                {
                    "event_id": f"E{str(eid).zfill(8)}",
                    "customer_id": c["customer_id"],
                    "opened_at": opened.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolved_at": resolved.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(resolved) else "",
                    "sla_due_at": sla_due.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": status,
                    "reason": reason,
                    "category": reason,  # keep category for backward-compatible marts
                    "priority": priority,
                    "channel": channel,
                    "csat": csat if csat is not None else "",
                    "resolved_hours": round(resolve_hours, 1) if resolve_hours is not None else "",
                    "within_sla": within_sla if within_sla != "" else "",
                    "created_at": opened.strftime("%Y-%m-%d"),  # legacy grain used by older marts
                }
            )
            eid += 1
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate customer analytics source extracts")
    parser.add_argument("--n-customers", type=int, default=5000)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    customers = generate_customers(n=args.n_customers)
    transactions = generate_transactions(customers)
    support = generate_support_events(customers)

    customers.to_csv(args.out_dir / "customers.csv", index=False)
    transactions.to_csv(args.out_dir / "transactions.csv", index=False)
    support.to_csv(args.out_dir / "support_events.csv", index=False)

    print(f"Wrote {len(customers):,} customers → {args.out_dir / 'customers.csv'}")
    print(f"Wrote {len(transactions):,} transactions → {args.out_dir / 'transactions.csv'}")
    print(f"Wrote {len(support):,} support events → {args.out_dir / 'support_events.csv'}")
    print(f"Churn rate: {customers['is_churned'].mean():.1%}")


if __name__ == "__main__":
    main()
