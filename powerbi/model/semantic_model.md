# Semantic Model — Customer Insights (Star Schema)

## Grain

| Table | Grain |
|-------|-------|
| `fact_customer_360` | One row per **customer** (as-of snapshot) |
| `fact_mrr_movement` | One row per **calendar month** |
| `fact_retention_monthly` | One row per **signup cohort × months_since_signup** |
| `fact_revenue_cohorts` | One row per **signup cohort × months_since_signup** |
| `fact_product_revenue` | One row per **txn_month × product** |
| `dim_segment_perf` | One row per **segment × region × plan** (pre-agg helper) |
| `fact_churn_scores` | One row per **holdout customer** (ML scores) |

## Dimensions (logical)

| Dimension | Key / attributes |
|-----------|------------------|
| `dim_customer` | `customer_id`, segment, region, plan, acquisition_channel, seats |
| `dim_date` / month | `month` (YYYY-MM), year, quarter |
| `dim_cohort` | `cohort_month` |
| `dim_product` | `product` |
| `dim_plan` | Free, Starter, Pro, Business, Enterprise |
| `dim_segment` | Enterprise, Mid-Market, SMB, Startup |
| `dim_region` | region labels |

`fact_customer_360` is a wide customer fact that already carries dimensional attributes — acceptable for Desktop demos. In Fabric/Snowflake, normalize to dims and keep measures on the fact.

## Relationships

```
dim_date[month]          1—*  fact_mrr_movement[month]
dim_date[month]          1—*  fact_product_revenue[txn_month]
dim_cohort[cohort_month] 1—*  fact_retention_monthly[cohort_month]
dim_cohort[cohort_month] 1—*  fact_revenue_cohorts[cohort_month]
dim_customer[customer_id] 1—* fact_churn_scores[customer_id]   (optional)
dim_customer[customer_id] 1—1 fact_customer_360[customer_id]
```

Filter direction: single (dims → facts). Cohort pages typically do **not** cross-filter the MRR movement page.

## Notable columns — fact_customer_360

`customer_id`, `signup_date`, `segment`, `region`, `plan`, `acquisition_channel`, `seats`, `mrr`, `tenure_days`, `monthly_active_days`, `support_tickets_90d`, `nps_score`, `feature_adoption_score`, `payment_failures_90d`, `is_churned`, `lifetime_revenue`, `customer_health_score`, `is_active`, …
