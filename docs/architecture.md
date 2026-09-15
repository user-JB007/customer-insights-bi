# Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Customer Insights BI                        │
├─────────────────────────────────────────────────────────────────┤
│  RAW LAYER                                                      │
│  customers · transactions · support_events   (synthetic CSV)    │
├─────────────────────────────────────────────────────────────────┤
│  CURATED MARTS (Snowflake SQL + local Python parity)            │
│  customer_360 · retention_monthly · revenue_cohorts             │
│  mrr_movement · segment_performance · product_revenue           │
├──────────────────────────┬──────────────────────────────────────┤
│  ML LAYER                │  BI / REPORTING LAYER                │
│  Feature table           │  Matplotlib/Seaborn executive PNGs   │
│  Gradient Boosting churn │  Ready for Power BI / Tableau /      │
│  metrics + joblib        │  Fabric / Databricks SQL             │
└──────────────────────────┴──────────────────────────────────────┘
```

**Design choices**

- **Synthetic but learnable data** — churn labels correlate with tenure, usage, NPS, payment failures, and plan so the model is genuinely predictive (not random).
- **SQL as source of truth for warehouses** — `sql/marts/*.sql` is Snowflake-flavored; `src/data/build_marts.py` reproduces the same grains for offline demos.
- **Reproducible pipeline** — `python run_pipeline.py` regenerates raw → marts → model → screenshots end-to-end.
- **No secrets / no cloud dependency** — hiring managers can clone and run locally.
