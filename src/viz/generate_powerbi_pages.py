"""Generate Power BI–styled executive report page PNGs for GitHub visitors.

Writes 6 polished screenshots under reports/powerbi/screenshots/.
Uses curated marts + churn model artifacts. Re-run:

    python src/viz/generate_powerbi_pages.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

# Power BI–inspired palette
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
PBI_CARD = "#FFFFFF"
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

PAGES = [
    "Executive Overview",
    "Retention Cohorts",
    "Revenue Cohorts",
    "Segment Performance",
    "Churn Model",
    "Product & Risk",
]


def _chrome(fig: plt.Figure, page_idx: int, title: str, filters: str) -> None:
    """Draw Power BI–like header, filter bar, and page tabs."""
    # Top yellow accent strip
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0, 0.965), 1, 0.035, transform=fig.transFigure,
            boxstyle="square,pad=0", facecolor=PBI_YELLOW, edgecolor="none",
            clip_on=False, zorder=0,
        )
    )
    # Dark title bar
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0, 0.905), 1, 0.06, transform=fig.transFigure,
            boxstyle="square,pad=0", facecolor=PBI_DARK, edgecolor="none",
            clip_on=False, zorder=0,
        )
    )
    fig.text(0.02, 0.935, "Customer Insights BI", fontsize=9, color=PBI_YELLOW,
             fontweight="bold", va="center", transform=fig.transFigure)
    fig.text(0.02, 0.918, title, fontsize=14, color=PBI_WHITE, fontweight="bold",
             va="center", transform=fig.transFigure)
    fig.text(0.98, 0.935, "Power BI · Portfolio Demo", fontsize=8, color="#A19F9D",
             ha="right", va="center", transform=fig.transFigure)

    # Filter bar cue
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (0.02, 0.855), 0.96, 0.038, transform=fig.transFigure,
            boxstyle="round,pad=0.002,rounding_size=0.008", facecolor=PBI_WHITE,
            edgecolor=PBI_BORDER, linewidth=1, clip_on=False, zorder=1,
        )
    )
    fig.text(0.035, 0.874, f"Filters  |  {filters}", fontsize=8, color=PBI_GRAY,
             va="center", transform=fig.transFigure)

    # Page tabs at bottom
    n = len(PAGES)
    tab_w = 0.96 / n
    for i, name in enumerate(PAGES):
        x = 0.02 + i * tab_w
        active = i == page_idx
        color = PBI_YELLOW if active else PBI_WHITE
        fig.patches.append(
            mpatches.FancyBboxPatch(
                (x, 0.008), tab_w - 0.004, 0.032, transform=fig.transFigure,
                boxstyle="round,pad=0.001,rounding_size=0.004", facecolor=color,
                edgecolor=PBI_BORDER, linewidth=0.8, clip_on=False, zorder=1,
            )
        )
        fig.text(x + (tab_w - 0.004) / 2, 0.024, name, fontsize=6.5,
                 ha="center", va="center", color=PBI_DARK if active else PBI_GRAY,
                 fontweight="bold" if active else "normal", transform=fig.transFigure)


def _kpi_card(ax, value: str, label: str, accent: str) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.02, 0.08), 0.96, 0.84, transform=ax.transAxes,
                               facecolor=PBI_WHITE, edgecolor=PBI_BORDER, linewidth=1.2, zorder=0))
    ax.add_patch(plt.Rectangle((0.02, 0.08), 0.04, 0.84, transform=ax.transAxes,
                               facecolor=accent, edgecolor="none", zorder=1))
    ax.text(0.55, 0.58, value, ha="center", va="center", fontsize=18, fontweight="bold",
            color=PBI_DARK, transform=ax.transAxes)
    ax.text(0.55, 0.28, label, ha="center", va="center", fontsize=8, color=PBI_GRAY,
            transform=ax.transAxes)


def page_01(marts: Path, out: Path) -> None:
    mrr = pd.read_csv(marts / "mrr_movement.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, 0, "01 — Executive Overview", "As-of: latest month  ·  Segment: All  ·  Region: All  ·  Plan: All")
    gs = fig.add_gridspec(3, 4, left=0.05, right=0.97, top=0.83, bottom=0.07, hspace=0.42, wspace=0.32)

    latest = mrr.iloc[-1]
    prev = mrr.iloc[-2] if len(mrr) > 1 else latest
    mom = (latest["mrr"] - prev["mrr"]) / prev["mrr"] * 100 if prev["mrr"] else 0
    kpis = [
        (f"${latest['arr']/1e6:.2f}M", "ARR", PBI_TEAL),
        (f"{int(latest['active_customers']):,}", "Active Customers", PBI_NAVY),
        (f"{latest['logo_churn_rate']*100:.1f}%", "Logo Churn (mo)", PBI_RED),
        (f"{mom:+.1f}%", "MRR MoM", PBI_ORANGE),
    ]
    for i, (v, lab, c) in enumerate(kpis):
        _kpi_card(fig.add_subplot(gs[0, i]), v, lab, c)

    ax1 = fig.add_subplot(gs[1, :2])
    ax1.fill_between(range(len(mrr)), mrr["mrr"] / 1000, color=PBI_TEAL, alpha=0.25)
    ax1.plot(range(len(mrr)), mrr["mrr"] / 1000, color=PBI_TEAL, linewidth=2.2)
    ax1.set_title("Monthly Recurring Revenue ($K)", fontsize=11, fontweight="bold", loc="left")
    step = max(len(mrr) // 8, 1)
    ax1.set_xticks(range(0, len(mrr), step))
    ax1.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax1.set_ylabel("MRR ($K)", fontsize=8)
    ax1.grid(axis="y", alpha=0.25)
    ax1.set_facecolor(PBI_WHITE)

    ax2 = fig.add_subplot(gs[1, 2:])
    ax2.bar(range(len(mrr)), mrr["new_mrr"] / 1000, color=PBI_TEAL, alpha=0.9, label="New MRR")
    ax2.bar(range(len(mrr)), -mrr["churned_mrr"] / 1000, color=PBI_RED, alpha=0.9, label="Churned MRR")
    ax2.axhline(0, color=PBI_GRAY, linewidth=0.8)
    ax2.set_title("MRR Movement: New vs Churned ($K)", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xticks(range(0, len(mrr), step))
    ax2.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=7)
    ax2.legend(fontsize=7, frameon=False)
    ax2.grid(axis="y", alpha=0.25)

    ax3 = fig.add_subplot(gs[2, :2])
    by_seg = c360.groupby("segment").agg(churn=("is_churned", "mean")).reindex(
        ["Enterprise", "Mid-Market", "SMB", "Startup"]
    )
    colors = [PBI_TEAL, PBI_NAVY, PBI_ORANGE, PBI_RED]
    bars = ax3.barh(by_seg.index, by_seg["churn"] * 100, color=colors)
    ax3.set_xlabel("Churn Rate (%)", fontsize=8)
    ax3.set_title("Churn Rate by Segment", fontsize=11, fontweight="bold", loc="left")
    for bar, v in zip(bars, by_seg["churn"] * 100):
        ax3.text(v + 0.3, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", fontsize=8)
    ax3.set_xlim(0, max(by_seg["churn"] * 100) * 1.3)
    ax3.grid(axis="x", alpha=0.25)

    ax4 = fig.add_subplot(gs[2, 2:])
    plan_mrr = c360.groupby("plan")["mrr"].sum().reindex(["Free", "Starter", "Pro", "Business", "Enterprise"]).fillna(0)
    ax4.pie(plan_mrr.clip(lower=0.01), labels=plan_mrr.index, autopct="%1.0f%%",
            colors=[PBI_LIGHT, PBI_ORANGE, PBI_NAVY, PBI_PURPLE, PBI_TEAL],
            textprops={"fontsize": 8}, startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax4.set_title("MRR Mix by Plan", fontsize=11, fontweight="bold")

    fig.savefig(out / "01_executive_overview.png")
    plt.close(fig)
    print("  wrote 01_executive_overview.png")


def page_02(marts: Path, out: Path) -> None:
    ret = pd.read_csv(marts / "retention_monthly.csv")
    pivot = ret.pivot_table(index="cohort_month", columns="months_since_signup",
                            values="retention_rate", aggfunc="mean").tail(18).iloc[:, :13]
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, 1, "02 — Retention Cohorts", "Cohort window: last 18 months  ·  Months since signup: 0–12")
    ax = fig.add_axes([0.10, 0.10, 0.80, 0.70])
    sns.heatmap(pivot * 100, ax=ax, cmap="RdYlGn", vmin=40, vmax=100, annot=True, fmt=".0f",
                annot_kws={"size": 7}, linewidths=0.4, linecolor="white",
                cbar_kws={"label": "Retention %", "shrink": 0.8})
    ax.set_xlabel("Months Since Signup")
    ax.set_ylabel("Signup Cohort")
    ax.set_title("Logo Retention Heatmap", fontsize=12, fontweight="bold", loc="left", pad=10)
    fig.savefig(out / "02_retention_heatmap.png")
    plt.close(fig)
    print("  wrote 02_retention_heatmap.png")


def page_03(marts: Path, out: Path) -> None:
    rev = pd.read_csv(marts / "revenue_cohorts.csv")
    curve = rev.groupby("months_since_signup")["revenue_per_customer"].mean().reset_index()
    curve = curve[curve["months_since_signup"] <= 18]
    top = rev.groupby("cohort_month")["revenue"].sum().nlargest(8).index
    heat = rev[rev["cohort_month"].isin(top)].pivot_table(
        index="cohort_month", columns="months_since_signup", values="revenue", aggfunc="sum"
    ).iloc[:, :12]
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, 2, "03 — Revenue Cohorts", "Metric: revenue per customer  ·  Top cohorts by lifetime revenue")
    gs = fig.add_gridspec(1, 2, left=0.07, right=0.96, top=0.82, bottom=0.10, wspace=0.28)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(curve["months_since_signup"], curve["revenue_per_customer"], color=PBI_TEAL,
             linewidth=2.5, marker="o", markersize=4)
    ax1.fill_between(curve["months_since_signup"], curve["revenue_per_customer"], alpha=0.2, color=PBI_TEAL)
    ax1.set_title("Avg Revenue / Customer by Tenure", fontsize=11, fontweight="bold", loc="left")
    ax1.set_xlabel("Months Since Signup")
    ax1.set_ylabel("Revenue per Customer ($)")
    ax1.grid(alpha=0.25)
    ax2 = fig.add_subplot(gs[0, 1])
    sns.heatmap(heat / 1000, ax=ax2, cmap="YlGnBu", annot=False, cbar_kws={"label": "Revenue ($K)"})
    ax2.set_title("Top Cohorts — Revenue by Tenure ($K)", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xlabel("Months Since Signup")
    ax2.set_ylabel("Cohort")
    fig.savefig(out / "03_revenue_cohorts.png")
    plt.close(fig)
    print("  wrote 03_revenue_cohorts.png")


def page_04(marts: Path, out: Path) -> None:
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, 3, "04 — Segment Performance", "Book of business  ·  Active + churned  ·  Health vs MRR")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08, hspace=0.38, wspace=0.28)
    ax1 = fig.add_subplot(gs[0, 0])
    g = c360.groupby("region").agg(mrr=("mrr", "sum")).sort_values("mrr", ascending=True)
    ax1.barh(g.index, g["mrr"] / 1000, color=PBI_NAVY)
    ax1.set_title("MRR by Region ($K)", fontsize=11, fontweight="bold", loc="left")
    ax1.set_xlabel("MRR ($K)")
    ax1.grid(axis="x", alpha=0.25)
    ax2 = fig.add_subplot(gs[0, 1])
    sample = c360.sample(min(1500, len(c360)), random_state=42)
    sc = ax2.scatter(sample["customer_health_score"], sample["mrr"], c=sample["is_churned"],
                     cmap="coolwarm", alpha=0.45, s=16, edgecolors="none")
    ax2.set_title("Health Score vs MRR (color = churned)", fontsize=11, fontweight="bold", loc="left")
    ax2.set_xlabel("Customer Health Score")
    ax2.set_ylabel("MRR ($)")
    fig.colorbar(sc, ax=ax2, fraction=0.046).set_label("Churned")
    ax2.grid(alpha=0.25)
    ax3 = fig.add_subplot(gs[1, 0])
    channel = c360.groupby("acquisition_channel").agg(churn=("is_churned", "mean")).sort_values("churn")
    ax3.bar(channel.index, channel["churn"] * 100,
            color=[PBI_TEAL if v < 0.25 else PBI_RED for v in channel["churn"]])
    ax3.set_title("Churn Rate by Acquisition Channel", fontsize=11, fontweight="bold", loc="left")
    ax3.set_ylabel("Churn %")
    ax3.tick_params(axis="x", rotation=25)
    ax3.grid(axis="y", alpha=0.25)
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
    fig.savefig(out / "04_segment_performance.png")
    plt.close(fig)
    print("  wrote 04_segment_performance.png")


def page_05(artifacts: Path, out: Path) -> None:
    metrics = json.loads((artifacts / "metrics.json").read_text())
    imp = pd.read_csv(artifacts / "feature_importance.csv").head(12)
    roc = pd.read_csv(artifacts / "roc_curve.csv")
    preds = pd.read_csv(artifacts / "holdout_predictions.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, 4, "05 — Churn Model Performance",
            f"Model: {metrics['model']}  ·  Holdout ROC-AUC {metrics['roc_auc']:.3f}")
    gs = fig.add_gridspec(2, 3, left=0.06, right=0.97, top=0.82, bottom=0.08, hspace=0.38, wspace=0.32)
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.axis("off")
    lines = [
        f"Accuracy   {metrics['accuracy']:.3f}",
        f"Precision  {metrics['precision']:.3f}",
        f"Recall     {metrics['recall']:.3f}",
        f"F1         {metrics['f1']:.3f}",
        f"ROC-AUC    {metrics['roc_auc']:.3f}",
        f"CV AUC     {metrics['cv_roc_auc_mean']:.3f} ± {metrics['cv_roc_auc_std']:.3f}",
    ]
    ax0.text(0.05, 0.95, "Holdout Metrics", fontsize=12, fontweight="bold", color=PBI_DARK,
             transform=ax0.transAxes, va="top")
    ax0.text(0.05, 0.78, "\n".join(lines), fontsize=11, family="monospace", color=PBI_GRAY,
             transform=ax0.transAxes, va="top",
             bbox=dict(boxstyle="round,pad=0.6", facecolor=PBI_WHITE, edgecolor=PBI_TEAL, linewidth=1.5))
    ax1 = fig.add_subplot(gs[0, 1])
    cm = np.array(metrics["confusion_matrix"])
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax1, cbar=False,
                xticklabels=["Active", "Churned"], yticklabels=["Active", "Churned"])
    ax1.set_xlabel("Predicted")
    ax1.set_ylabel("Actual")
    ax1.set_title("Confusion Matrix", fontsize=11, fontweight="bold")
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.plot(roc["fpr"], roc["tpr"], color=PBI_TEAL, linewidth=2.5, label=f"AUC = {metrics['roc_auc']:.3f}")
    ax2.plot([0, 1], [0, 1], "--", color=PBI_GRAY, alpha=0.5)
    ax2.set_xlabel("False Positive Rate")
    ax2.set_ylabel("True Positive Rate")
    ax2.set_title("ROC Curve", fontsize=11, fontweight="bold")
    ax2.legend(frameon=False)
    ax2.grid(alpha=0.25)
    ax3 = fig.add_subplot(gs[1, :2])
    ax3.barh(imp["feature"][::-1], imp["importance"][::-1], color=PBI_TEAL)
    ax3.set_title("Top Feature Importances", fontsize=11, fontweight="bold", loc="left")
    ax3.set_xlabel("Importance")
    ax3.grid(axis="x", alpha=0.25)
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.hist(preds.loc[preds["y_true"] == 0, "churn_probability"], bins=25, alpha=0.65,
             color=PBI_NAVY, label="Active", density=True)
    ax4.hist(preds.loc[preds["y_true"] == 1, "churn_probability"], bins=25, alpha=0.65,
             color=PBI_RED, label="Churned", density=True)
    ax4.axvline(0.5, color=PBI_GRAY, linestyle="--", linewidth=1)
    ax4.set_title("Score Distribution", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Churn Probability")
    ax4.legend(frameon=False, fontsize=8)
    ax4.grid(alpha=0.25)
    fig.savefig(out / "05_churn_model_performance.png")
    plt.close(fig)
    print("  wrote 05_churn_model_performance.png")


def page_06(marts: Path, artifacts: Path, out: Path) -> None:
    prod = pd.read_csv(marts / "product_revenue.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14.5, 9.2), facecolor=PBI_LIGHT)
    _chrome(fig, 5, "06 — Product Revenue & At-Risk", "Product mix · Priority outreach by MRR at risk")
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.96, top=0.82, bottom=0.08, hspace=0.38, wspace=0.28)
    ax1 = fig.add_subplot(gs[0, :])
    pivot = prod.pivot_table(index="txn_month", columns="product", values="revenue", aggfunc="sum").fillna(0).tail(24)
    pivot.plot.area(ax=ax1, stacked=True, alpha=0.85,
                    color=[PBI_TEAL, PBI_NAVY, PBI_ORANGE, PBI_PURPLE, PBI_RED])
    ax1.set_title("Product Revenue Trend (trailing 24 months)", fontsize=11, fontweight="bold", loc="left")
    ax1.set_ylabel("Revenue ($)")
    ax1.set_xlabel("")
    ax1.legend(loc="upper left", fontsize=7, frameon=False, ncol=3)
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(axis="y", alpha=0.25)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))
    ax2 = fig.add_subplot(gs[1, 0])
    risk = c360[(c360["is_churned"] == 0) & (c360["mrr"] > 0)].copy()
    risk["risk_flag"] = (
        (risk["customer_health_score"] < 45)
        | (risk["payment_failures_90d"] >= 2)
        | (risk["monthly_active_days"] < 5)
    )
    counts = risk["risk_flag"].value_counts()
    ax2.pie([counts.get(False, 0), counts.get(True, 0)],
            labels=["Healthy Active", "At-Risk Active"], autopct="%1.1f%%",
            colors=[PBI_TEAL, PBI_RED], startangle=90, textprops={"fontsize": 9},
            wedgeprops={"edgecolor": "white", "linewidth": 2})
    ax2.set_title("Active Book — Risk Split", fontsize=11, fontweight="bold")
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis("off")
    top_risk = risk[risk["risk_flag"]].nlargest(8, "mrr")[
        ["customer_id", "segment", "plan", "mrr", "customer_health_score", "region"]
    ]
    ax3.text(0.0, 1.0, "Priority Outreach (highest MRR at-risk)", fontsize=11, fontweight="bold",
             color=PBI_DARK, transform=ax3.transAxes, va="top")
    header = f"{'ID':<10} {'Segment':<12} {'Plan':<10} {'MRR':>8} {'Health':>7} {'Region'}"
    ax3.text(0.0, 0.88, header, fontsize=8, family="monospace", color=PBI_GRAY, transform=ax3.transAxes, va="top")
    lines = [
        f"{r['customer_id']:<10} {r['segment']:<12} {r['plan']:<10} ${r['mrr']:>7.0f} {r['customer_health_score']:>7.0f} {r['region']}"
        for _, r in top_risk.iterrows()
    ]
    ax3.text(0.0, 0.80, "\n".join(lines), fontsize=8, family="monospace", color=PBI_DARK,
             transform=ax3.transAxes, va="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor=PBI_WHITE, edgecolor=PBI_RED, linewidth=1.2))
    fig.savefig(out / "06_product_and_risk.png")
    plt.close(fig)
    print("  wrote 06_product_and_risk.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Power BI–styled report page PNGs")
    parser.add_argument("--marts", type=Path, default=Path("data/marts"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/model"))
    parser.add_argument("--out", type=Path, default=Path("reports/powerbi/screenshots"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print("Generating Power BI–styled report pages…")
    page_01(args.marts, args.out)
    page_02(args.marts, args.out)
    page_03(args.marts, args.out)
    page_04(args.marts, args.out)
    page_05(args.artifacts, args.out)
    page_06(args.marts, args.artifacts, args.out)
    print(f"Done → {args.out.resolve()}")


if __name__ == "__main__":
    main()
