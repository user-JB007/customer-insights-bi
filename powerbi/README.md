# Power BI Report Pack — Customer Insights BI

**Primary BI tool for this repo: Power BI.**  
Semantic model, DAX, page briefs, and GitHub screenshots. Recreate in Power BI Desktop from mart CSVs under `data/marts/`.

## Exactly two reports (different business subjects)

| Report | Purpose | Screenshots |
|--------|---------|-------------|
| **Customer Retention & Growth** | Retention, cohorts, active customers, growth | `retention_01_overview.png`, `retention_02_cohorts.png`, `retention_03_growth.png` |
| **Support & SLA Performance** | Tickets, CSAT, within/beyond SLA, pending & aging | `support_01_overview.png`, `support_02_sla.png`, `support_03_pending.png` |

## View on GitHub (no Desktop required)

See the root README **Power BI Reports** section, or browse:

- `powerbi/screenshots/`
- `reports/powerbi/screenshots/` (mirror)

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
| `support_sla.csv` | `fact_support_sla` |

2. Relationships & grain: [`model/semantic_model.md`](model/semantic_model.md)
3. Measures: [`model/measures.dax`](model/measures.dax)
4. Page layout: [`pages/`](pages/)

## Design intent

Marts are the warehouse contract (Snowflake SQL under `sql/marts/` + Python parity). Screenshots render on github.com; DAX supports Desktop/Fabric recreation without shipping a non-portable `.pbix`.
