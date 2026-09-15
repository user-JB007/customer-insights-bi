"""Generate Power BI–styled report page PNGs for GitHub visitors.

Exactly TWO reports (multi-page each):
  A) Customer Retention & Growth — retention, cohorts, active customers
  B) Support & SLA Performance — tickets, CSAT, within/beyond SLA, pending

Writes under powerbi/screenshots/ (and optionally reports/powerbi/screenshots/).

    python src/viz/generate_powerbi_pages.py
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

PBI_YELLOW = "#F2C811"
PBI_DARK = "#252423"
PBI_NAVY = "#118DFF"
PBI_TEAL = "#01B8AA"
PBI_RED = "#FD625E"
PBI_ORANGE = "#FE9666"
PBI_PURPLE = "#A66999"
PBI_GRAY = "#605E5C"
PBI_LIGHT = "#F3F2F1"
PBI_WHITE = "#FFFFFF"
PBI_BORDER = "#E1DFDD"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "figure.dpi": 140,
        "savefig.dpi": 160,
        "savefig.facecolor": PBI_LIGHT,
        "axes.facecolor": PBI_WHITE,
        "axes.edgecolor": PBI_BORDER,
        "axes.labelcolor": PBI_DARK,
        "xtick.color": PBI_GRAY,
        "ytick.color": PBI_GRAY,
        "text.color": PBI_DARK,
    }
)

RETENTION_TABS = ["Overview", "Cohorts", "Growth"]
SUPPORT_TABS = ["Overview", "SLA Performance", "Pending"]


def _chrome(
    fig: plt.Figure,
    report: str,
    tabs: list[str],
    page_idx: int,
    title: str,
    filters: str,
    dept: str = "Customer Insights · Retention",
) -> None:
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0, 0.965), 1, 0.035, transform=fig.transFigure,
            boxstyle="square,pad=0", facecolor=PBI_YELLOW, edgecolor="none",
            clip_on=False, zorder=0,
        )
    )
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0, 0.905), 1, 0.06, transform=fig.transFigure,
            boxstyle="square,pad=0", facecolor=PBI_DARK, edgecolor="none",
            clip_on=False, zorder=0,
        )
    )
    fig.text(0.02, 0.935, report, fontsize=9, color=PBI_YELLOW,
             fontweight="bold", va="center", transform=fig.transFigure)
    fig.text(0.02, 0.918, title, fontsize=14, color=PBI_WHITE, fontweight="bold",
             va="center", transform=fig.transFigure)
    fig.text(0.98, 0.935, dept, fontsize=8, color="#A19F9D",
             ha="right", va="center", transform=fig.transFigure)

    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0.02, 0.855), 0.96, 0.038, transform=fig.transFigure,
            boxstyle="round,pad=0.002,rounding_size=0.008", facecolor=PBI_WHITE,
            edgecolor=PBI_BORDER, linewidth=1, clip_on=False, zorder=1,
        )
    )
    fig.text(0.035, 0.874, f"Filters  |  {filters}", fontsize=8, color=PBI_GRAY,
             va="center", transform=fig.transFigure)

    n = len(tabs)
    tab_w = 0.96 / n
    for i, name in enumerate(tabs):
        x = 0.02 + i * tab_w
        active = i == page_idx
        fig.patches.append(
            mpatches.FancyBboxPatch(
                (x, 0.008), tab_w - 0.004, 0.032, transform=fig.transFigure,
                boxstyle="round,pad=0.001,rounding_size=0.004",
                facecolor=PBI_YELLOW if active else PBI_WHITE,
                edgecolor=PBI_BORDER, linewidth=0.8, clip_on=False, zorder=1,
            )
        )
        fig.text(x + (tab_w - 0.004) / 2, 0.024, name, fontsize=7.5,
                 ha="center", va="center", color=PBI_DARK if active else PBI_GRAY,
                 fontweight="bold" if active else "normal", transform=fig.transFigure)


def _kpi_card(ax, value: str, label: str, accent: str) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle(
        (0.02, 0.08), 0.96, 0.84, transform=ax.transAxes,
        facecolor=PBI_WHITE, edgecolor=PBI_BORDER, linewidth=1.2, zorder=0,
    ))
    ax.add_patch(plt.Rectangle(
        (0.02, 0.08), 0.04, 0.84, transform=ax.transAxes,
        facecolor=accent, edgecolor="none", zorder=1,
    ))
    ax.text(0.55, 0.58, value, ha="center", va="center", fontsize=18,
            fontweight="bold", color=PBI_DARK, transform=ax.transAxes)
    ax.text(0.55, 0.28, label, ha="center", va="center", fontsize=8,
            color=PBI_GRAY, transform=ax.transAxes)


# ── Report A: Customer Retention & Growth ───────────────────────────────────

def retention_01_overview(marts: Path, out: Path) -> None:
    mrr = pd.read_csv(marts / "mrr_movement.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Customer Retention & Growth", RETENTION_TABS, 0,
            "Active Book & Retention Overview",
            "As-of: latest month  ·  Segment: All  ·  Region: All  ·  Plan: All",
            dept="Customer Insights · Retention")
    gs = fig.add_gridspec(3, 4, left=0.05, right=0.97, top=0.83, bottom=0.07,
                          hspace=0.42, wspace=0.32)

    latest = mrr.iloc[-1]
    prev = mrr.iloc[-2] if len(mrr) > 1 else latest
    mom = (latest["mrr"] - prev["mrr"]) / prev["mrr"] * 100 if prev["mrr"] else 0
    active = int(c360["is_active"].sum()) if "is_active" in c360.columns else int(latest["active_customers"])
    retained_proxy = 100 - latest["logo_churn_rate"] * 100
    kpis = [
        (f"{active:,}", "Active Customers", PBI_TEAL),
        (f"{retained_proxy:.1f}%", "Logo Retention (mo)", PBI_NAVY),
        (f"{latest['logo_churn_rate']*100:.1f}%", "Logo Churn (mo)", PBI_RED),
        (f"{mom:+.1f}%", "MRR MoM Growth", PBI_ORANGE),
    ]
    for i, (v, lab, c) in enumerate(kpis):
        _kpi_card(fig.add_subplot(gs[0, i]), v, lab, c)

    ax1 = fig.add_subplot(gs[1, :2])
    ax1.plot(range(len(mrr)), (1 - mrr["logo_churn_rate"]) * 100, color=PBI_TEAL, linewidth=2.2)
    ax1.fill_between(range(len(mrr)), (1 - mrr["logo_churn_rate"]) * 100, color=PBI_TEAL, alpha=0.15)
    ax1.set_title("Monthly Logo Retention Rate (%)", fontsize=11, fontweight="bold", loc="left")
    step = max(len(mrr) // 8, 1)
    ax1.set_xticks(range(0, len(mrr), step))
    ax1.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax1.set_ylabel("Retention %", fontsize=8)
    ax1.grid(axis="y", alpha=0.25)

    ax2 = fig.add_subplot(gs[1, 2:])
    by_seg = c360.groupby("segment").agg(
        active=("is_active", "sum"), total=("customer_id", "count")
    )
    by_seg["active_rate"] = by_seg["active"] / by_seg["total"] * 100
    by_seg = by_seg.reindex(["Enterprise", "Mid-Market", "SMB", "Startup"]).dropna(how="all")
    if by_seg.empty:
        by_seg = c360.groupby("segment").agg(active=("is_active", "sum"), total=("customer_id", "count"))
        by_seg["active_rate"] = by_seg["active"] / by_seg["total"] * 100
    colors = [PBI_TEAL, PBI_NAVY, PBI_ORANGE, PBI_PURPLE][: len(by_seg)]
    ax2.barh(by_seg.index, by_seg["active_rate"], color=colors)
    ax2.set_xlabel("Active Rate (%)", fontsize=8)
    ax2.set_title("Active Rate by Segment", fontsize=11, fontweight="bold", loc="left")
    ax2.grid(axis="x", alpha=0.25)

    ax3 = fig.add_subplot(gs[2, :2])
    ax3.bar(range(len(mrr)), mrr["new_customers"], color=PBI_TEAL, alpha=0.9, label="New logos")
    ax3.bar(range(len(mrr)), -mrr["churned_customers"], color=PBI_RED, alpha=0.9, label="Churned logos")
    ax3.axhline(0, color=PBI_GRAY, linewidth=0.8)
    ax3.set_title("Logo Movement: New vs Churned", fontsize=11, fontweight="bold", loc="left")
    ax3.set_xticks(range(0, len(mrr), step))
    ax3.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax3.legend(fontsize=7, frameon=False)
    ax3.grid(axis="y", alpha=0.25)

    ax4 = fig.add_subplot(gs[2, 2:])
    ax4.fill_between(range(len(mrr)), mrr["active_customers"], color=PBI_NAVY, alpha=0.25)
    ax4.plot(range(len(mrr)), mrr["active_customers"], color=PBI_NAVY, linewidth=2.2)
    ax4.set_title("Active Customers Over Time", fontsize=11, fontweight="bold", loc="left")
    ax4.set_xticks(range(0, len(mrr), step))
    ax4.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax4.grid(axis="y", alpha=0.25)

    fig.savefig(out / "retention_01_overview.png")
    plt.close(fig)
    print("  wrote retention_01_overview.png")


def retention_02_cohorts(marts: Path, out: Path) -> None:
    ret = pd.read_csv(marts / "retention_monthly.csv")
    pivot = ret.pivot_table(
        index="cohort_month", columns="months_since_signup",
        values="retention_rate", aggfunc="mean",
    ).tail(18).iloc[:, :13]
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Customer Retention & Growth", RETENTION_TABS, 1,
            "Retention Cohorts",
            "Cohort window: last 18 months  ·  Months since signup: 0–12",
            dept="Customer Insights · Retention")
    ax = fig.add_axes([0.10, 0.10, 0.80, 0.70])
    sns.heatmap(pivot * 100, ax=ax, cmap="RdYlGn", vmin=40, vmax=100, annot=True, fmt=".0f",
                annot_kws={"size": 7}, linewidths=0.4, linecolor="white",
                cbar_kws={"label": "Retention %", "shrink": 0.8})
    ax.set_xlabel("Months Since Signup")
    ax.set_ylabel("Signup Cohort")
    ax.set_title("Logo Retention Heatmap", fontsize=12, fontweight="bold", loc="left", pad=10)
    fig.savefig(out / "retention_02_cohorts.png")
    plt.close(fig)
    print("  wrote retention_02_cohorts.png")


def retention_03_growth(marts: Path, out: Path) -> None:
    mrr = pd.read_csv(marts / "mrr_movement.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Customer Retention & Growth", RETENTION_TABS, 2,
            "Growth Drivers & Book Composition",
            "Net new logos · MRR growth · Plan / region mix",
            dept="Customer Insights · Retention")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    net_new = mrr["new_customers"] - mrr["churned_customers"]
    colors = [PBI_TEAL if v >= 0 else PBI_RED for v in net_new]
    ax1.bar(range(len(mrr)), net_new, color=colors, alpha=0.9)
    ax1.axhline(0, color=PBI_GRAY, linewidth=0.8)
    ax1.set_title("Net New Logos by Month", fontsize=11, fontweight="bold", loc="left")
    step = max(len(mrr) // 8, 1)
    ax1.set_xticks(range(0, len(mrr), step))
    ax1.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax1.grid(axis="y", alpha=0.25)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.fill_between(range(len(mrr)), mrr["mrr"] / 1000, color=PBI_TEAL, alpha=0.25)
    ax2.plot(range(len(mrr)), mrr["mrr"] / 1000, color=PBI_TEAL, linewidth=2.2)
    ax2.set_title("MRR Growth ($K)", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xticks(range(0, len(mrr), step))
    ax2.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax2.set_ylabel("MRR ($K)")
    ax2.grid(axis="y", alpha=0.25)

    ax3 = fig.add_subplot(gs[1, 0])
    active = c360[c360["is_active"] == 1] if "is_active" in c360.columns else c360
    plan_counts = (
        active.groupby("plan")["customer_id"].count()
        .reindex(["Free", "Starter", "Pro", "Business", "Enterprise"])
        .fillna(0)
    )
    ax3.pie(
        plan_counts.clip(lower=0.01), labels=plan_counts.index, autopct="%1.0f%%",
        colors=[PBI_LIGHT, PBI_ORANGE, PBI_NAVY, PBI_PURPLE, PBI_TEAL],
        textprops={"fontsize": 8}, startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax3.set_title("Active Customers by Plan", fontsize=11, fontweight="bold")

    ax4 = fig.add_subplot(gs[1, 1])
    g = active.groupby("region").agg(customers=("customer_id", "count")).sort_values("customers")
    ax4.barh(g.index, g["customers"], color=PBI_NAVY)
    ax4.set_title("Active Customers by Region", fontsize=11, fontweight="bold", loc="left")
    ax4.set_xlabel("Customers")
    ax4.grid(axis="x", alpha=0.25)

    fig.savefig(out / "retention_03_growth.png")
    plt.close(fig)
    print("  wrote retention_03_growth.png")


# ── Report B: Support & SLA Performance ─────────────────────────────────────

def _load_support(marts: Path) -> pd.DataFrame:
    path = marts / "support_sla.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Rebuild marts after regenerating support extracts.")
    return pd.read_csv(path)


def support_01_overview(marts: Path, out: Path) -> None:
    svc = _load_support(marts)
    svc["opened_at"] = pd.to_datetime(svc["opened_at"])
    total = len(svc)
    open_n = int(svc["is_open"].sum()) if "is_open" in svc.columns else 0
    avg_csat = float(svc["csat"].dropna().mean()) if "csat" in svc.columns and svc["csat"].notna().any() else 0.0
    within = int((svc["sla_status"] == "within_sla").sum()) if "sla_status" in svc.columns else 0
    resolved_n = int((svc["is_open"] == 0).sum()) if "is_open" in svc.columns else total
    within_pct = within / max(resolved_n, 1) * 100

    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Support & SLA Performance", SUPPORT_TABS, 0,
            "Ticket Volume & Satisfaction",
            "As-of: latest  ·  Segment: All  ·  Channel: All  ·  Priority: All",
            dept="Customer Insights · Support")
    gs = fig.add_gridspec(3, 4, left=0.05, right=0.97, top=0.83, bottom=0.07,
                          hspace=0.42, wspace=0.32)
    kpis = [
        (f"{total:,}", "Tickets Opened", PBI_NAVY),
        (f"{avg_csat:.2f}", "Avg CSAT (1–5)", PBI_TEAL),
        (f"{within_pct:.0f}%", "Resolved Within SLA", PBI_TEAL),
        (f"{open_n:,}", "Still Pending", PBI_ORANGE),
    ]
    for i, (v, lab, c) in enumerate(kpis):
        _kpi_card(fig.add_subplot(gs[0, i]), v, lab, c)

    ax1 = fig.add_subplot(gs[1, :2])
    daily = svc.groupby(svc["opened_at"].dt.to_period("M").astype(str)).size()
    ax1.bar(range(len(daily)), daily.values, color=PBI_NAVY, alpha=0.85)
    ax1.set_title("Tickets Opened by Month", fontsize=11, fontweight="bold", loc="left")
    step = max(len(daily) // 8, 1)
    ax1.set_xticks(range(0, len(daily), step))
    ax1.set_xticklabels(daily.index[::step], rotation=30, ha="right", fontsize=7)
    ax1.grid(axis="y", alpha=0.25)

    ax2 = fig.add_subplot(gs[1, 2:])
    reason_col = "reason" if "reason" in svc.columns else "category"
    by_reason = svc[reason_col].value_counts().sort_values(ascending=True)
    ax2.barh(by_reason.index, by_reason.values, color=PBI_PURPLE)
    ax2.set_title("Tickets by Reason", fontsize=11, fontweight="bold", loc="left")
    ax2.grid(axis="x", alpha=0.25)

    ax3 = fig.add_subplot(gs[2, :2])
    if "channel" in svc.columns:
        by_ch = svc["channel"].value_counts()
        ax3.pie(by_ch, labels=by_ch.index, autopct="%1.0f%%",
                colors=[PBI_TEAL, PBI_NAVY, PBI_ORANGE, PBI_PURPLE][: len(by_ch)],
                textprops={"fontsize": 9}, startangle=90,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax3.set_title("Tickets by Channel", fontsize=11, fontweight="bold")

    ax4 = fig.add_subplot(gs[2, 2:])
    if "csat" in svc.columns and svc["csat"].notna().any():
        csat = svc["csat"].dropna().astype(int)
        counts = csat.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        ax4.bar(counts.index.astype(str), counts.values,
                color=[PBI_RED, PBI_ORANGE, PBI_YELLOW, PBI_TEAL, "#107C10"])
    ax4.set_title("CSAT Score Distribution", fontsize=11, fontweight="bold", loc="left")
    ax4.set_xlabel("CSAT")
    ax4.grid(axis="y", alpha=0.25)

    fig.savefig(out / "support_01_overview.png")
    plt.close(fig)
    print("  wrote support_01_overview.png")


def support_02_sla(marts: Path, out: Path) -> None:
    svc = _load_support(marts)
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Support & SLA Performance", SUPPORT_TABS, 1,
            "SLA Attainment & Resolution Times",
            "Within SLA · Breached · By priority & segment",
            dept="Customer Insights · Support")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    status_order = ["within_sla", "beyond_sla", "pending_within_sla", "pending_beyond_sla"]
    labels = {
        "within_sla": "Resolved · Within SLA",
        "beyond_sla": "Resolved · Beyond SLA",
        "pending_within_sla": "Pending · Within SLA",
        "pending_beyond_sla": "Pending · Beyond SLA",
    }
    counts = svc["sla_status"].value_counts().reindex(status_order).fillna(0)
    ax1.pie(counts, labels=[labels.get(i, i) for i in counts.index], autopct="%1.0f%%",
            colors=[PBI_TEAL, PBI_RED, PBI_NAVY, PBI_ORANGE],
            textprops={"fontsize": 8}, startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax1.set_title("SLA Status Mix", fontsize=11, fontweight="bold")

    ax2 = fig.add_subplot(gs[0, 1])
    resolved = svc[svc["resolved_hours"].notna()].copy()
    by_pri = resolved.groupby("priority")["resolved_hours"].mean().reindex(
        ["critical", "high", "medium", "low"]
    ).dropna()
    ax2.bar([p.title() for p in by_pri.index], by_pri.values,
            color=[PBI_RED, PBI_ORANGE, PBI_NAVY, PBI_TEAL][: len(by_pri)])
    ax2.set_title("Avg Resolve Hours by Priority", fontsize=11, fontweight="bold", loc="left")
    ax2.set_ylabel("Hours")
    ax2.grid(axis="y", alpha=0.25)

    ax3 = fig.add_subplot(gs[1, 0])
    if "channel" in svc.columns:
        breach = svc.groupby("channel").agg(total=("event_id", "count"), breached=("sla_breach", "sum"))
        breach["breach_pct"] = breach["breached"] / breach["total"] * 100
        breach = breach.sort_values("breach_pct")
        ax3.barh(breach.index, breach["breach_pct"], color=PBI_RED)
    ax3.set_title("SLA Breach Rate by Channel (%)", fontsize=11, fontweight="bold", loc="left")
    ax3.set_xlabel("Breach %")
    ax3.grid(axis="x", alpha=0.25)

    ax4 = fig.add_subplot(gs[1, 1])
    if "segment" in svc.columns:
        by_seg = svc.groupby("segment").agg(
            total=("event_id", "count"),
            within=("sla_status", lambda s: (s == "within_sla").sum()),
        )
        by_seg["within_pct"] = by_seg["within"] / by_seg["total"] * 100
        by_seg = by_seg.sort_values("within_pct")
        ax4.barh(by_seg.index, by_seg["within_pct"], color=PBI_TEAL)
    ax4.set_title("Within-SLA Rate by Segment (%)", fontsize=11, fontweight="bold", loc="left")
    ax4.set_xlabel("Within SLA %")
    ax4.grid(axis="x", alpha=0.25)

    fig.savefig(out / "support_02_sla.png")
    plt.close(fig)
    print("  wrote support_02_sla.png")


def support_03_pending(marts: Path, out: Path) -> None:
    svc = _load_support(marts)
    open_tix = svc[svc["is_open"] == 1].copy() if "is_open" in svc.columns else svc.iloc[0:0].copy()

    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Support & SLA Performance", SUPPORT_TABS, 2,
            "Pending Queue & Ticket Aging",
            "Open tickets  ·  Age buckets  ·  Priority backlog",
            dept="Customer Insights · Support")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    if len(open_tix):
        bins = [0, 24, 72, 168, 336, 10_000]
        labels = ["<1d", "1–3d", "3–7d", "7–14d", "14d+"]
        open_tix = open_tix.copy()
        open_tix["age_bucket"] = pd.cut(open_tix["age_hours"], bins=bins, labels=labels, right=False)
        age_counts = open_tix["age_bucket"].value_counts().reindex(labels).fillna(0)
        ax1.bar(age_counts.index.astype(str), age_counts.values, color=PBI_ORANGE)
    ax1.set_title("Open Ticket Aging", fontsize=11, fontweight="bold", loc="left")
    ax1.set_ylabel("Tickets")
    ax1.grid(axis="y", alpha=0.25)

    ax2 = fig.add_subplot(gs[0, 1])
    if len(open_tix):
        by_pri = open_tix["priority"].value_counts().reindex(
            ["critical", "high", "medium", "low"]
        ).fillna(0)
        ax2.bar([p.title() for p in by_pri.index], by_pri.values,
                color=[PBI_RED, PBI_ORANGE, PBI_NAVY, PBI_TEAL])
    ax2.set_title("Open Backlog by Priority", fontsize=11, fontweight="bold", loc="left")
    ax2.grid(axis="y", alpha=0.25)

    ax3 = fig.add_subplot(gs[1, 0])
    if len(open_tix):
        reason_col = "reason" if "reason" in open_tix.columns else "category"
        by_reason = open_tix[reason_col].value_counts().sort_values(ascending=True)
        ax3.barh(by_reason.index, by_reason.values, color=PBI_PURPLE)
    ax3.set_title("Open Tickets by Reason", fontsize=11, fontweight="bold", loc="left")
    ax3.grid(axis="x", alpha=0.25)

    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis("off")
    oldest = open_tix.nlargest(8, "age_hours") if len(open_tix) else open_tix
    ax4.text(0.0, 1.0, "Oldest Open Tickets", fontsize=12, fontweight="bold",
             color=PBI_DARK, transform=ax4.transAxes, va="top")
    header = f"{'Ticket':<10} {'Pri':<8} {'Age(h)':>7} {'Reason'}"
    ax4.text(0.0, 0.88, header, fontsize=9, family="monospace", color=PBI_GRAY,
             transform=ax4.transAxes, va="top")
    reason_col = "reason" if "reason" in oldest.columns else "category"
    lines = [
        f"{r['event_id']:<10} {str(r['priority'])[:7]:<8} {r['age_hours']:>7.0f} {str(r[reason_col])[:22]}"
        for _, r in oldest.iterrows()
    ]
    ax4.text(0.0, 0.78, "\n".join(lines) if lines else "No open tickets",
             fontsize=9, family="monospace", color=PBI_DARK,
             transform=ax4.transAxes, va="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor=PBI_WHITE,
                       edgecolor=PBI_ORANGE, linewidth=1.2))

    fig.savefig(out / "support_03_pending.png")
    plt.close(fig)
    print("  wrote support_03_pending.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Power BI–styled Customer Insights pages")
    parser.add_argument("--marts", type=Path, default=Path("data/marts"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/model"))
    parser.add_argument("--out", type=Path, default=Path("powerbi/screenshots"))
    parser.add_argument("--also-reports", action="store_true", default=True,
                        help="Also copy screenshots to reports/powerbi/screenshots/")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    for pattern in ["customer_health_*.png", "revenue_segments_*.png"]:
        for obsolete in args.out.glob(pattern):
            obsolete.unlink()
            print(f"  removed {obsolete.name}")
        mirror = Path("reports/powerbi/screenshots")
        if mirror.exists():
            for obsolete in mirror.glob(pattern):
                obsolete.unlink()

    print("Generating Power BI–styled report pages (2 reports)…")
    retention_01_overview(args.marts, args.out)
    retention_02_cohorts(args.marts, args.out)
    retention_03_growth(args.marts, args.out)
    support_01_overview(args.marts, args.out)
    support_02_sla(args.marts, args.out)
    support_03_pending(args.marts, args.out)

    if args.also_reports:
        mirror = Path("reports/powerbi/screenshots")
        mirror.mkdir(parents=True, exist_ok=True)
        for png in args.out.glob("*.png"):
            shutil.copy2(png, mirror / png.name)
        print(f"  mirrored → {mirror}")

    print(f"Done → {args.out.resolve()}")


if __name__ == "__main__":
    main()
