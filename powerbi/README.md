# Power BI Report Pack — Customer Insights BI

**Primary BI tool for this repo: Power BI.**  
Honest portfolio design: **semantic model + DAX + page briefs + GitHub screenshots**.  
No opaque `.pbix` binaries — visitors view dashboards on GitHub and recreate them in Power BI Desktop from mart CSVs.

## Exactly two reports (same SaaS domain, different questions)

| Report | Purpose | Screenshots |
|--------|---------|-------------|
| **Customer Health** | Retention, cohorts, churn risk overview | `customer_health_01_overview.png`, `customer_health_02_retention.png`, `customer_health_03_churn_risk.png` |
| **Revenue & Segments** | MRR/revenue, segment performance, product & cohort yield | `revenue_segments_01_mrr.png`, `revenue_segments_02_segments.png`, `revenue_segments_03_product.png` |

## View on GitHub (no Desktop required)

See the root README **Power BI Reports** section, or browse:

- `powerbi/screenshots/`
- `reports/powerbi/screenshots/` (mirror for README embeds)

Regenerate:

```bash
python src/viz/generate_powerbi_pages.py
# or full pipeline
python run_pipeline.py
```

## Recreate in Power BI Desktop

1. **Get data** from committed marts in `data/marts/`:

| File | Model table |
|------|-------------|
| `customer_360.csv` | `fact_customer_360` |
| `mrr_movement.csv` | `fact_mrr_movement` |
| `retention_monthly.csv` | `fact_retention_monthly` |
| `revenue_cohorts.csv` | `fact_revenue_cohorts` |
| `segment_performance.csv` | `dim_segment_perf` |
| `product_revenue.csv` | `fact_product_revenue` |

2. Relationships & grain: [`model/semantic_model.md`](model/semantic_model.md)
3. Measures: [`model/measures.dax`](model/measures.dax)
4. Page layout: [`pages/`](pages/)

## Design intent

Marts are the warehouse contract (Snowflake SQL under `sql/marts/` + Python parity). Screenshots render on github.com; DAX proves Desktop/Fabric readiness without shipping a non-portable `.pbix`.
