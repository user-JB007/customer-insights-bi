# Power BI Report Pack — Customer Insights BI

Honest portfolio approach: **semantic model + DAX + page briefs + GitHub screenshots** so visitors see the BI story without Power BI Desktop. Existing executive PNGs under `reports/screenshots/` remain; this pack adds Power BI–chrome pages under `reports/powerbi/screenshots/`.

## View on GitHub (no Desktop required)

See the root README **Power BI Reports** section, or open:

`reports/powerbi/screenshots/`

| # | Screenshot | Page |
|---|------------|------|
| 01 | `01_executive_overview.png` | ARR, customers, churn, MRR MoM, movement |
| 02 | `02_retention_heatmap.png` | Logo retention cohort heatmap |
| 03 | `03_revenue_cohorts.png` | Revenue per customer by tenure |
| 04 | `04_segment_performance.png` | Region, channel, plan, health vs MRR |
| 05 | `05_churn_model_performance.png` | ROC, confusion matrix, importances |
| 06 | `06_product_and_risk.png` | Product mix + at-risk outreach |

Regenerate:

```bash
python src/viz/generate_powerbi_pages.py
# optional: also refresh classic screenshots
python src/viz/generate_dashboards.py
```

## Recreate in Power BI Desktop

1. **Get data** from committed marts in `data/marts/`:

| File | Model table |
|------|-------------|
| `customer_360.csv` / `.parquet` | `fact_customer_360` |
| `mrr_movement.csv` | `fact_mrr_movement` |
| `retention_monthly.csv` | `fact_retention_monthly` |
| `revenue_cohorts.csv` | `fact_revenue_cohorts` |
| `segment_performance.csv` | `dim_segment_perf` (agg) |
| `product_revenue.csv` | `fact_product_revenue` |
| `artifacts/model/holdout_predictions.csv` | `fact_churn_scores` (optional) |

2. Relationships & grain: [`model/semantic_model.md`](model/semantic_model.md)
3. Measures: [`model/measures.dax`](model/measures.dax)
4. Page layout: [`pages/`](pages/)
5. Broader tool mapping (Tableau / Fabric / Databricks SQL): [`docs/bi_tool_mapping.md`](../docs/bi_tool_mapping.md)

## Design intent

Marts are the warehouse contract (Snowflake SQL under `sql/marts/` + Python parity). Screenshots render on github.com for profile traffic; DAX proves Desktop/Fabric readiness without shipping a non-portable `.pbix`.
