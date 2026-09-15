"""Generate Power BI–styled report page PNGs for GitHub visitors.

Exactly TWO reports (multi-page each):
  A) Customer Health — retention, cohorts, churn risk
  B) Revenue & Segments — MRR, segments, product & risk

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

HEALTH_TABS = ["Overview", "Retention", "Churn Risk"]
REVENUE_TABS = ["MRR & Movement", "Segments", "Product & Risk"]


def _chrome(
    fig: plt.Figure,
    report: str,
    tabs: list[str],
    page_idx: int,
    title: str,
    filters: str,
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
    fig.text(0.98, 0.935, "Power BI · Portfolio Demo", fontsize=8, color="#A19F9D",
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


# ── Report A: Customer Health ───────────────────────────────────────────────

def health_01_overview(marts: Path, out: Path) -> None:
    mrr = pd.read_csv(marts / "mrr_movement.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Customer Health Report", HEALTH_TABS, 0,
            "Retention & Churn Overview",
            "As-of: latest month  ·  Segment: All  ·  Region: All  ·  Plan: All")
    gs = fig.add_gridspec(3, 4, left=0.05, right=0.97, top=0.83, bottom=0.07,
                          hspace=0.42, wspace=0.32)

    latest = mrr.iloc[-1]
    prev = mrr.iloc[-2] if len(mrr) > 1 else latest
    mom = (latest["mrr"] - prev["mrr"]) / prev["mrr"] * 100 if prev["mrr"] else 0
    active = int(c360["is_active"].sum()) if "is_active" in c360.columns else int(latest["active_customers"])
    churned = int(c360["is_churned"].sum())
    kpis = [
        (f"{active:,}", "Active Customers", PBI_TEAL),
        (f"{latest['logo_churn_rate']*100:.1f}%", "Logo Churn (mo)", PBI_RED),
        (f"{churned:,}", "Churned (lifetime)", PBI_ORANGE),
        (f"{mom:+.1f}%", "MRR MoM", PBI_NAVY),
    ]
    for i, (v, lab, c) in enumerate(kpis):
        _kpi_card(fig.add_subplot(gs[0, i]), v, lab, c)

    ax1 = fig.add_subplot(gs[1, :2])
    ax1.plot(range(len(mrr)), mrr["logo_churn_rate"] * 100, color=PBI_RED, linewidth=2.2)
    ax1.fill_between(range(len(mrr)), mrr["logo_churn_rate"] * 100, color=PBI_RED, alpha=0.15)
    ax1.set_title("Monthly Logo Churn Rate (%)", fontsize=11, fontweight="bold", loc="left")
    step = max(len(mrr) // 8, 1)
    ax1.set_xticks(range(0, len(mrr), step))
    ax1.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax1.set_ylabel("Churn %", fontsize=8)
    ax1.grid(axis="y", alpha=0.25)

    ax2 = fig.add_subplot(gs[1, 2:])
    by_seg = c360.groupby("segment").agg(churn=("is_churned", "mean")).reindex(
        ["Enterprise", "Mid-Market", "SMB", "Startup"]
    ).dropna(how="all")
    if by_seg.empty:
        by_seg = c360.groupby("segment").agg(churn=("is_churned", "mean"))
    colors = [PBI_TEAL, PBI_NAVY, PBI_ORANGE, PBI_RED][: len(by_seg)]
    bars = ax2.barh(by_seg.index, by_seg["churn"] * 100, color=colors)
    ax2.set_xlabel("Churn Rate (%)", fontsize=8)
    ax2.set_title("Churn Rate by Segment", fontsize=11, fontweight="bold", loc="left")
    for bar, v in zip(bars, by_seg["churn"] * 100):
        ax2.text(v + 0.3, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", fontsize=8)
    ax2.set_xlim(0, max(by_seg["churn"] * 100) * 1.35 if len(by_seg) else 1)
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
    health = c360["customer_health_score"].dropna()
    ax4.hist(health, bins=30, color=PBI_NAVY, alpha=0.85, edgecolor="white")
    ax4.axvline(45, color=PBI_RED, linestyle="--", linewidth=1.2, label="At-risk < 45")
    ax4.set_title("Customer Health Score Distribution", fontsize=11, fontweight="bold", loc="left")
    ax4.set_xlabel("Health Score")
    ax4.legend(fontsize=7, frameon=False)
    ax4.grid(axis="y", alpha=0.25)

    fig.savefig(out / "customer_health_01_overview.png")
    plt.close(fig)
    print("  wrote customer_health_01_overview.png")


def health_02_retention(marts: Path, out: Path) -> None:
    ret = pd.read_csv(marts / "retention_monthly.csv")
    pivot = ret.pivot_table(
        index="cohort_month", columns="months_since_signup",
        values="retention_rate", aggfunc="mean",
    ).tail(18).iloc[:, :13]
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Customer Health Report", HEALTH_TABS, 1,
            "Retention Cohorts",
            "Cohort window: last 18 months  ·  Months since signup: 0–12")
    ax = fig.add_axes([0.10, 0.10, 0.80, 0.70])
    sns.heatmap(pivot * 100, ax=ax, cmap="RdYlGn", vmin=40, vmax=100, annot=True, fmt=".0f",
                annot_kws={"size": 7}, linewidths=0.4, linecolor="white",
                cbar_kws={"label": "Retention %", "shrink": 0.8})
    ax.set_xlabel("Months Since Signup")
    ax.set_ylabel("Signup Cohort")
    ax.set_title("Logo Retention Heatmap", fontsize=12, fontweight="bold", loc="left", pad=10)
    fig.savefig(out / "customer_health_02_retention.png")
    plt.close(fig)
    print("  wrote customer_health_02_retention.png")


def health_03_churn_risk(marts: Path, artifacts: Path, out: Path) -> None:
    c360 = pd.read_csv(marts / "customer_360.csv")
    metrics_path = artifacts / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else None
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    filt = "Active book risk flags  ·  Health / payment / engagement"
    if metrics:
        filt += f"  ·  Model ROC-AUC {metrics.get('roc_auc', 0):.3f}"
    _chrome(fig, "Customer Health Report", HEALTH_TABS, 2,
            "Churn Risk Overview", filt)
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    risk = c360[(c360["is_churned"] == 0) & (c360["mrr"] > 0)].copy()
    risk["risk_flag"] = (
        (risk["customer_health_score"] < 45)
        | (risk["payment_failures_90d"] >= 2)
        | (risk["monthly_active_days"] < 5)
    )

    ax1 = fig.add_subplot(gs[0, 0])
    counts = risk["risk_flag"].value_counts()
    ax1.pie(
        [counts.get(False, 0), counts.get(True, 0)],
        labels=["Healthy Active", "At-Risk Active"], autopct="%1.1f%%",
        colors=[PBI_TEAL, PBI_RED], startangle=90, textprops={"fontsize": 9},
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    ax1.set_title("Active Book — Risk Split", fontsize=11, fontweight="bold")

    ax2 = fig.add_subplot(gs[0, 1])
    channel = c360.groupby("acquisition_channel").agg(churn=("is_churned", "mean")).sort_values("churn")
    ax2.bar(channel.index, channel["churn"] * 100,
            color=[PBI_TEAL if v < 0.25 else PBI_RED for v in channel["churn"]])
    ax2.set_title("Churn Rate by Acquisition Channel", fontsize=11, fontweight="bold", loc="left")
    ax2.set_ylabel("Churn %")
    ax2.tick_params(axis="x", rotation=25)
    ax2.grid(axis="y", alpha=0.25)

    ax3 = fig.add_subplot(gs[1, :])
    ax3.axis("off")
    top_risk = risk[risk["risk_flag"]].nlargest(10, "mrr")[
        ["customer_id", "segment", "plan", "mrr", "customer_health_score", "region"]
    ]
    ax3.text(0.0, 1.0, "Priority Outreach (highest MRR at-risk)", fontsize=12, fontweight="bold",
             color=PBI_DARK, transform=ax3.transAxes, va="top")
    header = f"{'ID':<10} {'Segment':<12} {'Plan':<10} {'MRR':>8} {'Health':>7} {'Region'}"
    ax3.text(0.0, 0.88, header, fontsize=9, family="monospace", color=PBI_GRAY,
             transform=ax3.transAxes, va="top")
    lines = [
        f"{r['customer_id']:<10} {r['segment']:<12} {r['plan']:<10} ${r['mrr']:>7.0f} "
        f"{r['customer_health_score']:>7.0f} {r['region']}"
        for _, r in top_risk.iterrows()
    ]
    ax3.text(0.0, 0.78, "\n".join(lines), fontsize=9, family="monospace", color=PBI_DARK,
             transform=ax3.transAxes, va="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor=PBI_WHITE, edgecolor=PBI_RED, linewidth=1.2))

    fig.savefig(out / "customer_health_03_churn_risk.png")
    plt.close(fig)
    print("  wrote customer_health_03_churn_risk.png")


# ── Report B: Revenue & Segments ────────────────────────────────────────────

def revenue_01_mrr(marts: Path, out: Path) -> None:
    mrr = pd.read_csv(marts / "mrr_movement.csv")
    rev = pd.read_csv(marts / "revenue_cohorts.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Revenue & Segments Report", REVENUE_TABS, 0,
            "MRR, ARR & Revenue Cohorts",
            "As-of: latest month  ·  Metric: MRR / revenue per customer")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    latest = mrr.iloc[-1]
    prev = mrr.iloc[-2] if len(mrr) > 1 else latest
    mom = (latest["mrr"] - prev["mrr"]) / prev["mrr"] * 100 if prev["mrr"] else 0

    # KPI strip via text cards in top row — use nested gridspec mentally
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.axis("off")
    cards = [
        (f"${latest['arr']/1e6:.2f}M", "ARR", PBI_TEAL),
        (f"${latest['mrr']/1e3:.0f}K", "MRR", PBI_NAVY),
        (f"{mom:+.1f}%", "MRR MoM", PBI_ORANGE),
        (f"${latest['net_new_mrr']/1e3:.0f}K", "Net New MRR", PBI_PURPLE),
    ]
    for i, (val, lab, accent) in enumerate(cards):
        x0 = 0.02 + i * 0.245
        ax_kpi.add_patch(plt.Rectangle(
            (x0, 0.15), 0.22, 0.7, transform=ax_kpi.transAxes,
            facecolor=PBI_WHITE, edgecolor=PBI_BORDER, linewidth=1.2,
        ))
        ax_kpi.add_patch(plt.Rectangle(
            (x0, 0.15), 0.012, 0.7, transform=ax_kpi.transAxes,
            facecolor=accent, edgecolor="none",
        ))
        ax_kpi.text(x0 + 0.11, 0.58, val, ha="center", va="center", fontsize=16,
                    fontweight="bold", transform=ax_kpi.transAxes)
        ax_kpi.text(x0 + 0.11, 0.30, lab, ha="center", va="center", fontsize=8,
                    color=PBI_GRAY, transform=ax_kpi.transAxes)

    ax1 = fig.add_subplot(gs[1, 0])
    ax1.fill_between(range(len(mrr)), mrr["mrr"] / 1000, color=PBI_TEAL, alpha=0.25)
    ax1.plot(range(len(mrr)), mrr["mrr"] / 1000, color=PBI_TEAL, linewidth=2.2)
    ax1.set_title("Monthly Recurring Revenue ($K)", fontsize=11, fontweight="bold", loc="left")
    step = max(len(mrr) // 8, 1)
    ax1.set_xticks(range(0, len(mrr), step))
    ax1.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax1.set_ylabel("MRR ($K)", fontsize=8)
    ax1.grid(axis="y", alpha=0.25)

    ax2 = fig.add_subplot(gs[1, 1])
    ax2.bar(range(len(mrr)), mrr["new_mrr"] / 1000, color=PBI_TEAL, alpha=0.9, label="New MRR")
    ax2.bar(range(len(mrr)), -mrr["churned_mrr"] / 1000, color=PBI_RED, alpha=0.9, label="Churned MRR")
    ax2.axhline(0, color=PBI_GRAY, linewidth=0.8)
    ax2.set_title("MRR Movement: New vs Churned ($K)", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xticks(range(0, len(mrr), step))
    ax2.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax2.legend(fontsize=7, frameon=False)
    ax2.grid(axis="y", alpha=0.25)

    # Add cohort curve as inset? Keep 2x2 clean — already used both bottom cells.
    # Re-layout: put cohort tip in KPI area already filled. Fine for page 01.

    fig.savefig(out / "revenue_segments_01_mrr.png")
    plt.close(fig)
    print("  wrote revenue_segments_01_mrr.png")

    # Extra small cohort visual is on page 02/03; optionally enhance page 01 with cohort curve
    # by regenerating with 3-row layout — keep as is for clarity.


def revenue_02_segments(marts: Path, out: Path) -> None:
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Revenue & Segments Report", REVENUE_TABS, 1,
            "Segment Performance",
            "Book of business  ·  Active + churned  ·  Health vs MRR")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    g = c360.groupby("region").agg(mrr=("mrr", "sum")).sort_values("mrr", ascending=True)
    ax1.barh(g.index, g["mrr"] / 1000, color=PBI_NAVY)
    ax1.set_title("MRR by Region ($K)", fontsize=11, fontweight="bold", loc="left")
    ax1.set_xlabel("MRR ($K)")
    ax1.grid(axis="x", alpha=0.25)

    ax2 = fig.add_subplot(gs[0, 1])
    sample = c360.sample(min(1500, len(c360)), random_state=42)
    sc = ax2.scatter(
        sample["customer_health_score"], sample["mrr"], c=sample["is_churned"],
        cmap="coolwarm", alpha=0.45, s=16, edgecolors="none",
    )
    ax2.set_title("Health Score vs MRR (color = churned)", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xlabel("Customer Health Score")
    ax2.set_ylabel("MRR ($)")
    fig.colorbar(sc, ax=ax2, fraction=0.046).set_label("Churned")
    ax2.grid(alpha=0.25)

    ax3 = fig.add_subplot(gs[1, 0])
    plan_mrr = (
        c360.groupby("plan")["mrr"].sum()
        .reindex(["Free", "Starter", "Pro", "Business", "Enterprise"])
        .fillna(0)
    )
    ax3.pie(
        plan_mrr.clip(lower=0.01), labels=plan_mrr.index, autopct="%1.0f%%",
        colors=[PBI_LIGHT, PBI_ORANGE, PBI_NAVY, PBI_PURPLE, PBI_TEAL],
        textprops={"fontsize": 8}, startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax3.set_title("MRR Mix by Plan", fontsize=11, fontweight="bold")

    ax4 = fig.add_subplot(gs[1, 1])
    plans = ["Free", "Starter", "Pro", "Business", "Enterprise"]
    box_data = [c360.loc[c360["plan"] == p, "customer_health_score"].dropna() for p in plans]
    bp = ax4.boxplot(box_data, tick_labels=plans, patch_artist=True)
    for patch, c in zip(bp["boxes"], [PBI_LIGHT, PBI_ORANGE, PBI_NAVY, PBI_PURPLE, PBI_TEAL]):
        patch.set_facecolor(c)
        patch.set_alpha(0.9)
    ax4.set_title("Health Score by Plan", fontsize=11, fontweight="bold", loc="left")
    ax4.set_ylabel("Health Score")
    ax4.grid(axis="y", alpha=0.25)

    fig.savefig(out / "revenue_segments_02_segments.png")
    plt.close(fig)
    print("  wrote revenue_segments_02_segments.png")


def revenue_03_product_risk(marts: Path, out: Path) -> None:
    prod = pd.read_csv(marts / "product_revenue.csv")
    rev = pd.read_csv(marts / "revenue_cohorts.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, "Revenue & Segments Report", REVENUE_TABS, 2,
            "Product Revenue & Cohort Yield",
            "Product mix · Revenue per customer by tenure")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08,
                          hspace=0.38, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, :])
    pivot = (
        prod.pivot_table(index="txn_month", columns="product", values="revenue", aggfunc="sum")
        .fillna(0).tail(24)
    )
    pivot.plot.area(
        ax=ax1, stacked=True, alpha=0.85,
        color=[PBI_TEAL, PBI_NAVY, PBI_ORANGE, PBI_PURPLE, PBI_RED],
    )
    ax1.set_title("Product Revenue Trend (trailing 24 months)", fontsize=11, fontweight="bold", loc="left")
    ax1.set_ylabel("Revenue ($)")
    ax1.set_xlabel("")
    ax1.legend(loc="upper left", fontsize=7, frameon=False, ncol=3)
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(axis="y", alpha=0.25)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))

    ax2 = fig.add_subplot(gs[1, 0])
    curve = rev.groupby("months_since_signup")["revenue_per_customer"].mean().reset_index()
    curve = curve[curve["months_since_signup"] <= 18]
    ax2.plot(curve["months_since_signup"], curve["revenue_per_customer"], color=PBI_TEAL,
             linewidth=2.5, marker="o", markersize=4)
    ax2.fill_between(curve["months_since_signup"], curve["revenue_per_customer"],
                     alpha=0.2, color=PBI_TEAL)
    ax2.set_title("Avg Revenue / Customer by Tenure", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xlabel("Months Since Signup")
    ax2.set_ylabel("Revenue per Customer ($)")
    ax2.grid(alpha=0.25)

    ax3 = fig.add_subplot(gs[1, 1])
    top = rev.groupby("cohort_month")["revenue"].sum().nlargest(8).index
    heat = rev[rev["cohort_month"].isin(top)].pivot_table(
        index="cohort_month", columns="months_since_signup", values="revenue", aggfunc="sum"
    ).iloc[:, :12]
    sns.heatmap(heat / 1000, ax=ax3, cmap="YlGnBu", annot=False, cbar_kws={"label": "Revenue ($K)"})
    ax3.set_title("Top Cohorts — Revenue by Tenure ($K)", fontsize=11, fontweight="bold", loc="left")
    ax3.set_xlabel("Months Since Signup")
    ax3.set_ylabel("Cohort")

    fig.savefig(out / "revenue_segments_03_product.png")
    plt.close(fig)
    print("  wrote revenue_segments_03_product.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Power BI–styled Customer Insights pages")
    parser.add_argument("--marts", type=Path, default=Path("data/marts"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/model"))
    parser.add_argument("--out", type=Path, default=Path("powerbi/screenshots"))
    parser.add_argument("--also-reports", action="store_true", default=True,
                        help="Also copy screenshots to reports/powerbi/screenshots/")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print("Generating Power BI–styled report pages (2 reports)…")
    health_01_overview(args.marts, args.out)
    health_02_retention(args.marts, args.out)
    health_03_churn_risk(args.marts, args.artifacts, args.out)
    revenue_01_mrr(args.marts, args.out)
    revenue_02_segments(args.marts, args.out)
    revenue_03_product_risk(args.marts, args.out)

    if args.also_reports:
        mirror = Path("reports/powerbi/screenshots")
        mirror.mkdir(parents=True, exist_ok=True)
        for png in args.out.glob("*.png"):
            shutil.copy2(png, mirror / png.name)
        print(f"  mirrored → {mirror}")

    print(f"Done → {args.out.resolve()}")


if __name__ == "__main__":
    main()
