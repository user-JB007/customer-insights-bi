# Semantic model — Customer Insights BI (Power BI)

Star-ish layout over curated marts. Two reports share `CustomerInsights.SemanticModel` (`model.bim`).

## Tables

| Table | Grain | Key columns |
|-------|-------|-------------|
| `fact_customer_360` | 1 row / customer | `customer_id`, segment, region, plan, mrr, health, `is_churned` |
| `fact_mrr_movement` | 1 row / month | `month`, mrr, arr, new/churned mrr & logos |
| `fact_retention_monthly` | cohort × tenure month | `cohort_month`, `months_since_signup`, `retention_rate` |
| `fact_revenue_cohorts` | cohort × tenure month | revenue, `revenue_per_customer` |
| `fact_product_revenue` | month × product | `txn_month`, `product`, `revenue` |
| `dim_segment_perf` | segment × region × plan | aggregated KPIs |
| `fact_support_sla` | ticket | event_id, SLA clocks, csat, sla_status, is_open |
| `Aging Threshold` | parameter | `Aging Threshold Hours` (default 72) |

## Relationships

- `fact_support_sla[customer_id]` → `fact_customer_360[customer_id]` (many-to-one)

## Report binding

| Report | Primary tables |
|--------|----------------|
| Customer Retention & Growth | customer_360, mrr_movement, retention_monthly, revenue_cohorts, product_revenue |
| Support & SLA Performance | support_sla (+ customer_360) |

M partitions load CSVs via **MartsFolder** parameter (default `./../data/` under `powerbi/`).
