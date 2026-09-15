"""Generate polished executive-style dashboard PNG screenshots for the project.

Produces 6 labeled report images under reports/screenshots/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

# Executive palette
NAVY = "#0B1F3A"
TEAL = "#1ABC9C"
CORAL = "#E74C3C"
GOLD = "#F39C12"
SLATE = "#34495E"
LIGHT = "#ECF0F1"
BLUE = "#3498DB"
PURPLE = "#9B59B6"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": SLATE,
        "axes.labelcolor": NAVY,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "text.color": NAVY,
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "figure.dpi": 150,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)


def _banner(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(0.02, 0.97, title, fontsize=18, fontweight="bold", color=NAVY, va="top")
    fig.text(0.02, 0.935, subtitle, fontsize=10, color=SLATE, va="top")
    fig.add_artist(plt.Line2D([0.02, 0.98], [0.90, 0.90], transform=fig.transFigure, color=TEAL, linewidth=2.5, solid_capstyle="round"))


def _footer(fig: plt.Figure, label: str) -> None:
    fig.text(0.02, 0.015, f"Customer Insights BI  ·  {label}", fontsize=8, color=SLATE)
    fig.text(0.98, 0.015, "INTERNAL", fontsize=8, color=CORAL, ha="right", fontweight="bold")


def dash_01_executive_overview(marts: Path, out: Path) -> None:
    mrr = pd.read_csv(marts / "mrr_movement.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    seg = pd.read_csv(marts / "segment_performance.csv")

    fig = plt.figure(figsize=(14, 9))
    _banner(fig, "01 — Executive Overview", "SaaS customer health, MRR trajectory, and churn at a glance")
    gs = fig.add_gridspec(3, 4, left=0.06, right=0.97, top=0.86, bottom=0.08, hspace=0.45, wspace=0.35)

    # KPI cards
    latest = mrr.iloc[-1]
    kpis = [
        ("ARR", f"${latest['arr']/1e6:.2f}M", TEAL),
        ("Active Customers", f"{int(latest['active_customers']):,}", BLUE),
        ("Logo Churn (mo)", f"{latest['logo_churn_rate']*100:.1f}%", CORAL),
        ("Avg Health Score", f"{c360['customer_health_score'].mean():.0f}", GOLD),
    ]
    for i, (label, value, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[0, i])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0.05, 0.15), 0.9, 0.7, transform=ax.transAxes, facecolor=LIGHT, edgecolor=color, linewidth=2, clip_on=False))
        ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=20, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(0.5, 0.32, label, ha="center", va="center", fontsize=9, color=SLATE, transform=ax.transAxes)

    ax1 = fig.add_subplot(gs[1, :2])
    ax1.fill_between(range(len(mrr)), mrr["mrr"] / 1000, color=TEAL, alpha=0.25)
    ax1.plot(range(len(mrr)), mrr["mrr"] / 1000, color=TEAL, linewidth=2.2)
    ax1.set_title("Monthly Recurring Revenue ($K)")
    step = max(len(mrr) // 8, 1)
    ax1.set_xticks(range(0, len(mrr), step))
    ax1.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=8)
    ax1.set_ylabel("MRR ($K)")
    ax1.grid(axis="y", alpha=0.3)

    ax2 = fig.add_subplot(gs[1, 2:])
    ax2.bar(range(len(mrr)), mrr["new_mrr"] / 1000, color=TEAL, alpha=0.85, label="New MRR")
    ax2.bar(range(len(mrr)), -mrr["churned_mrr"] / 1000, color=CORAL, alpha=0.85, label="Churned MRR")
    ax2.axhline(0, color=SLATE, linewidth=0.8)
    ax2.set_title("MRR Movement: New vs Churned ($K)")
    ax2.set_xticks(range(0, len(mrr), step))
    ax2.set_xticklabels(mrr["month"].iloc[::step], rotation=30, ha="right", fontsize=8)
    ax2.legend(fontsize=8, frameon=False)
    ax2.grid(axis="y", alpha=0.3)

    ax3 = fig.add_subplot(gs[2, :2])
    by_seg = c360.groupby("segment").agg(churn=("is_churned", "mean"), n=("customer_id", "count")).reindex(
        ["Enterprise", "Mid-Market", "SMB", "Startup"]
    )
    colors = [TEAL, BLUE, GOLD, CORAL]
    bars = ax3.barh(by_seg.index, by_seg["churn"] * 100, color=colors)
    ax3.set_xlabel("Churn Rate (%)")
    ax3.set_title("Churn Rate by Segment")
    for bar, v in zip(bars, by_seg["churn"] * 100):
        ax3.text(v + 0.4, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", fontsize=9)
    ax3.set_xlim(0, max(by_seg["churn"] * 100) * 1.25)
    ax3.grid(axis="x", alpha=0.3)

    ax4 = fig.add_subplot(gs[2, 2:])
    plan_mrr = c360.groupby("plan")["mrr"].sum().reindex(["Free", "Starter", "Pro", "Business", "Enterprise"])
    ax4.pie(plan_mrr.clip(lower=0.01), labels=plan_mrr.index, autopct="%1.0f%%", colors=[LIGHT, GOLD, BLUE, PURPLE, TEAL],
            textprops={"fontsize": 8}, startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax4.set_title("MRR Mix by Plan")

    _footer(fig, "Executive Overview")
    fig.savefig(out / "01_executive_overview.png")
    plt.close(fig)
    print("  wrote 01_executive_overview.png")


def dash_02_retention_heatmap(marts: Path, out: Path) -> None:
    ret = pd.read_csv(marts / "retention_monthly.csv")
    # Focus on recent cohorts with enough history
    pivot = ret.pivot_table(index="cohort_month", columns="months_since_signup", values="retention_rate", aggfunc="mean")
    # Keep last 18 cohorts, first 13 months
    pivot = pivot.tail(18).iloc[:, :13]

    fig = plt.figure(figsize=(14, 8.5))
    _banner(fig, "02 — Cohort Retention Heatmap", "Logo retention by signup cohort (month 0 = signup month)")
    ax = fig.add_axes([0.12, 0.12, 0.78, 0.72])
    sns.heatmap(
        pivot * 100,
        ax=ax,
        cmap="RdYlGn",
        vmin=40,
        vmax=100,
        annot=True,
        fmt=".0f",
        annot_kws={"size": 7},
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"label": "Retention %", "shrink": 0.8},
    )
    ax.set_xlabel("Months Since Signup")
    ax.set_ylabel("Signup Cohort")
    ax.set_title("")
    _footer(fig, "Retention Cohorts")
    fig.savefig(out / "02_retention_heatmap.png")
    plt.close(fig)
    print("  wrote 02_retention_heatmap.png")


def dash_03_revenue_cohorts(marts: Path, out: Path) -> None:
    rev = pd.read_csv(marts / "revenue_cohorts.csv")
    # Average revenue_per_customer by months_since across cohorts
    curve = rev.groupby("months_since_signup")["revenue_per_customer"].mean().reset_index()
    curve = curve[curve["months_since_signup"] <= 18]

    # Top cohorts by total revenue
    top = rev.groupby("cohort_month")["revenue"].sum().nlargest(8).index
    heat = rev[rev["cohort_month"].isin(top)].pivot_table(
        index="cohort_month", columns="months_since_signup", values="revenue", aggfunc="sum"
    ).iloc[:, :12]

    fig = plt.figure(figsize=(14, 8.5))
    _banner(fig, "03 — Revenue Cohort Analysis", "How customer cohorts monetize over their lifetime")
    gs = fig.add_gridspec(1, 2, left=0.07, right=0.97, top=0.84, bottom=0.1, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(curve["months_since_signup"], curve["revenue_per_customer"], color=TEAL, linewidth=2.5, marker="o", markersize=4)
    ax1.fill_between(curve["months_since_signup"], curve["revenue_per_customer"], alpha=0.2, color=TEAL)
    ax1.set_title("Avg Revenue / Customer by Tenure Month")
    ax1.set_xlabel("Months Since Signup")
    ax1.set_ylabel("Revenue per Customer ($)")
    ax1.grid(alpha=0.3)

    ax2 = fig.add_subplot(gs[0, 1])
    sns.heatmap(heat / 1000, ax=ax2, cmap="YlGnBu", annot=False, cbar_kws={"label": "Revenue ($K)"})
    ax2.set_title("Top Cohorts — Revenue by Tenure ($K)")
    ax2.set_xlabel("Months Since Signup")
    ax2.set_ylabel("Cohort")

    _footer(fig, "Revenue Cohorts")
    fig.savefig(out / "03_revenue_cohorts.png")
    plt.close(fig)
    print("  wrote 03_revenue_cohorts.png")


def dash_04_segment_performance(marts: Path, out: Path) -> None:
    c360 = pd.read_csv(marts / "customer_360.csv")
    fig = plt.figure(figsize=(14, 8.5))
    _banner(fig, "04 — Segment & Plan Performance", "Where revenue and risk concentrate across the book of business")
    gs = fig.add_gridspec(2, 2, left=0.08, right=0.96, top=0.84, bottom=0.08, hspace=0.4, wspace=0.3)

    ax1 = fig.add_subplot(gs[0, 0])
    g = c360.groupby("region").agg(mrr=("mrr", "sum"), customers=("customer_id", "count")).sort_values("mrr", ascending=True)
    ax1.barh(g.index, g["mrr"] / 1000, color=BLUE)
    ax1.set_title("MRR by Region ($K)")
    ax1.set_xlabel("MRR ($K)")
    ax1.grid(axis="x", alpha=0.3)

    ax2 = fig.add_subplot(gs[0, 1])
    scatter_df = c360.sample(min(1500, len(c360)), random_state=42)
    sc = ax2.scatter(
        scatter_df["customer_health_score"],
        scatter_df["mrr"],
        c=scatter_df["is_churned"],
        cmap="coolwarm",
        alpha=0.45,
        s=18,
        edgecolors="none",
    )
    ax2.set_title("Health Score vs MRR (color = churned)")
    ax2.set_xlabel("Customer Health Score")
    ax2.set_ylabel("MRR ($)")
    cbar = fig.colorbar(sc, ax=ax2, fraction=0.046)
    cbar.set_label("Churned")
    ax2.grid(alpha=0.3)

    ax3 = fig.add_subplot(gs[1, 0])
    channel = c360.groupby("acquisition_channel").agg(churn=("is_churned", "mean"), n=("customer_id", "count"))
    channel = channel.sort_values("churn")
    ax3.bar(channel.index, channel["churn"] * 100, color=[TEAL if v < 0.25 else CORAL for v in channel["churn"]])
    ax3.set_title("Churn Rate by Acquisition Channel")
    ax3.set_ylabel("Churn %")
    ax3.tick_params(axis="x", rotation=25)
    ax3.grid(axis="y", alpha=0.3)

    ax4 = fig.add_subplot(gs[1, 1])
    box_data = [c360.loc[c360["plan"] == p, "customer_health_score"].dropna() for p in ["Free", "Starter", "Pro", "Business", "Enterprise"]]
    bp = ax4.boxplot(box_data, tick_labels=["Free", "Starter", "Pro", "Business", "Enterprise"], patch_artist=True)
    colors = [LIGHT, GOLD, BLUE, PURPLE, TEAL]
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.85)
    ax4.set_title("Health Score Distribution by Plan")
    ax4.set_ylabel("Health Score")
    ax4.grid(axis="y", alpha=0.3)

    _footer(fig, "Segment Performance")
    fig.savefig(out / "04_segment_performance.png")
    plt.close(fig)
    print("  wrote 04_segment_performance.png")


def dash_05_churn_model(artifacts: Path, out: Path) -> None:
    metrics = json.loads((artifacts / "metrics.json").read_text())
    imp = pd.read_csv(artifacts / "feature_importance.csv").head(12)
    roc = pd.read_csv(artifacts / "roc_curve.csv")
    preds = pd.read_csv(artifacts / "holdout_predictions.csv")

    fig = plt.figure(figsize=(14, 8.5))
    _banner(fig, "05 — Churn Model Performance", f"{metrics['model']}  ·  Holdout ROC-AUC {metrics['roc_auc']:.3f}")
    gs = fig.add_gridspec(2, 3, left=0.07, right=0.97, top=0.84, bottom=0.08, hspace=0.4, wspace=0.35)

    # Metric cards
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
    ax0.text(0.05, 0.95, "Holdout Metrics", fontsize=12, fontweight="bold", color=NAVY, transform=ax0.transAxes, va="top")
    ax0.text(0.05, 0.78, "\n".join(lines), fontsize=11, family="monospace", color=SLATE, transform=ax0.transAxes, va="top",
             bbox=dict(boxstyle="round,pad=0.6", facecolor=LIGHT, edgecolor=TEAL, linewidth=1.5))

    ax1 = fig.add_subplot(gs[0, 1])
    cm = np.array(metrics["confusion_matrix"])
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax1, cbar=False,
                xticklabels=["Active", "Churned"], yticklabels=["Active", "Churned"])
    ax1.set_xlabel("Predicted")
    ax1.set_ylabel("Actual")
    ax1.set_title("Confusion Matrix")

    ax2 = fig.add_subplot(gs[0, 2])
    ax2.plot(roc["fpr"], roc["tpr"], color=TEAL, linewidth=2.5, label=f"AUC = {metrics['roc_auc']:.3f}")
    ax2.plot([0, 1], [0, 1], "--", color=SLATE, alpha=0.5)
    ax2.set_xlabel("False Positive Rate")
    ax2.set_ylabel("True Positive Rate")
    ax2.set_title("ROC Curve")
    ax2.legend(frameon=False)
    ax2.grid(alpha=0.3)

    ax3 = fig.add_subplot(gs[1, :2])
    ax3.barh(imp["feature"][::-1], imp["importance"][::-1], color=TEAL)
    ax3.set_title("Top Feature Importances")
    ax3.set_xlabel("Importance")
    ax3.grid(axis="x", alpha=0.3)

    ax4 = fig.add_subplot(gs[1, 2])
    ax4.hist(preds.loc[preds["y_true"] == 0, "churn_probability"], bins=25, alpha=0.65, color=BLUE, label="Active", density=True)
    ax4.hist(preds.loc[preds["y_true"] == 1, "churn_probability"], bins=25, alpha=0.65, color=CORAL, label="Churned", density=True)
    ax4.axvline(0.5, color=SLATE, linestyle="--", linewidth=1)
    ax4.set_title("Score Distribution")
    ax4.set_xlabel("Churn Probability")
    ax4.legend(frameon=False, fontsize=8)
    ax4.grid(alpha=0.3)

    _footer(fig, "ML Churn Model")
    fig.savefig(out / "05_churn_model_performance.png")
    plt.close(fig)
    print("  wrote 05_churn_model_performance.png")


def dash_06_product_and_risk(marts: Path, artifacts: Path, out: Path) -> None:
    prod = pd.read_csv(marts / "product_revenue.csv")
    c360 = pd.read_csv(marts / "customer_360.csv")
    preds_path = artifacts / "holdout_predictions.csv"
    preds = pd.read_csv(preds_path) if preds_path.exists() else None

    fig = plt.figure(figsize=(14, 8.5))
    _banner(fig, "06 — Product Revenue & At-Risk Customers", "Product mix trends and prioritized churn intervention list")
    gs = fig.add_gridspec(2, 2, left=0.08, right=0.96, top=0.84, bottom=0.08, hspace=0.4, wspace=0.3)

    ax1 = fig.add_subplot(gs[0, :])
    pivot = prod.pivot_table(index="txn_month", columns="product", values="revenue", aggfunc="sum").fillna(0)
    pivot = pivot.tail(24)
    pivot.plot.area(ax=ax1, stacked=True, alpha=0.85, color=[TEAL, BLUE, GOLD, PURPLE, CORAL])
    ax1.set_title("Product Revenue Trend (trailing 24 months)")
    ax1.set_ylabel("Revenue ($)")
    ax1.set_xlabel("")
    ax1.legend(loc="upper left", fontsize=8, frameon=False, ncol=3)
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(axis="y", alpha=0.3)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))

    ax2 = fig.add_subplot(gs[1, 0])
    risk = c360[(c360["is_churned"] == 0) & (c360["mrr"] > 0)].copy()
    risk["risk_flag"] = (
        (risk["customer_health_score"] < 45)
        | (risk["payment_failures_90d"] >= 2)
        | (risk["monthly_active_days"] < 5)
    )
    counts = risk["risk_flag"].value_counts()
    ax2.pie(
        [counts.get(False, 0), counts.get(True, 0)],
        labels=["Healthy Active", "At-Risk Active"],
        autopct="%1.1f%%",
        colors=[TEAL, CORAL],
        startangle=90,
        textprops={"fontsize": 9},
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    ax2.set_title("Active Book — Risk Split")

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis("off")
    top_risk = risk[risk["risk_flag"]].nlargest(8, "mrr")[
        ["customer_id", "segment", "plan", "mrr", "customer_health_score", "region"]
    ]
    ax3.text(0.0, 1.0, "Priority Outreach (highest MRR at-risk)", fontsize=11, fontweight="bold", color=NAVY, transform=ax3.transAxes, va="top")
    header = f"{'ID':<10} {'Segment':<12} {'Plan':<10} {'MRR':>8} {'Health':>7} {'Region'}"
    ax3.text(0.0, 0.88, header, fontsize=8, family="monospace", color=SLATE, transform=ax3.transAxes, va="top")
    lines = []
    for _, r in top_risk.iterrows():
        lines.append(
            f"{r['customer_id']:<10} {r['segment']:<12} {r['plan']:<10} ${r['mrr']:>7.0f} {r['customer_health_score']:>7.0f} {r['region']}"
        )
    ax3.text(0.0, 0.80, "\n".join(lines), fontsize=8, family="monospace", color=NAVY, transform=ax3.transAxes, va="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor=LIGHT, edgecolor=CORAL, linewidth=1.2))

    _footer(fig, "Product & Risk")
    fig.savefig(out / "06_product_and_risk.png")
    plt.close(fig)
    print("  wrote 06_product_and_risk.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--marts", type=Path, default=Path("data/marts"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/model"))
    parser.add_argument("--out", type=Path, default=Path("reports/screenshots"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print("Generating dashboard screenshots…")
    dash_01_executive_overview(args.marts, args.out)
    dash_02_retention_heatmap(args.marts, args.out)
    dash_03_revenue_cohorts(args.marts, args.out)
    dash_04_segment_performance(args.marts, args.out)
    dash_05_churn_model(args.artifacts, args.out)
    dash_06_product_and_risk(args.marts, args.artifacts, args.out)
    print(f"Done → {args.out}")


if __name__ == "__main__":
    main()
