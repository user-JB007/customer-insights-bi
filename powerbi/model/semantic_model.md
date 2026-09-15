# Semantic model — Customer Insights BI (Power BI)

Star-ish layout over curated marts. Two reports share the same model.

## Tables

| Table | Grain | Key columns |
|-------|-------|-------------|
| `fact_customer_360` | 1 row / customer | `customer_id`, segment, region, plan, mrr, health, `is_churned` |
| `fact_mrr_movement` | 1 row / month | `month`, mrr, arr, new/churned mrr & logos |
| `fact_retention_monthly` | cohort × tenure month | `cohort_month`, `months_since_signup`, `retention_rate` |
| `fact_revenue_cohorts` | cohort × tenure month | revenue, `revenue_per_customer` |
| `fact_product_revenue` | month × product | `txn_month`, `product`, `revenue` |
| `dim_segment_perf` | segment × region × plan | aggregated KPIs (optional) |

## Relationships (conceptual)

- `fact_customer_360[segment|region|plan]` → filters on `dim_segment_perf`
- Date: use `fact_mrr_movement[month]` as calendar bridge for time intelligence where needed
- Cohorts are self-contained (no customer-level join required for heatmaps)

## Report binding

| Report | Primary tables |
|--------|----------------|
| Customer Health | customer_360, mrr_movement, retention_monthly |
| Revenue & Segments | mrr_movement, customer_360, product_revenue, revenue_cohorts |
