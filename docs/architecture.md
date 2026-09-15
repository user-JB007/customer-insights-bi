# Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Customer Insights BI                        │
├─────────────────────────────────────────────────────────────────┤
│  RAW LAYER                                                      │
│  customers · transactions · support_events   (source CSV)    │
├─────────────────────────────────────────────────────────────────┤
│  CURATED MARTS (Snowflake SQL + local Python parity)            │
│  customer_360 · retention_monthly · revenue_cohorts             │
│  mrr_movement · segment_performance · product_revenue           │
│  support_sla                                                   │
├──────────────────────────┬──────────────────────────────────────┤
│  ML LAYER                │  BI / REPORTING LAYER                │
│  Feature table           │  Matplotlib/Seaborn executive PNGs   │
│  Gradient Boosting churn │  Ready for Power BI / Tableau /      │
│  metrics + joblib        │  Fabric / Databricks SQL             │
└──────────────────────────┴──────────────────────────────────────┘
```

**Design choices**

- **Learnable churn signal** — churn labels correlate with tenure, usage, NPS, payment failures, and plan so the model is genuinely predictive (not random).
- **SQL as source of truth for warehouses** — `sql/marts/*.sql` is Snowflake-flavored; `src/data/build_marts.py` reproduces the same grains offline.
- **Reproducible pipeline** — `python run_pipeline.py` regenerates raw → marts → model → screenshots end-to-end.
- **No secrets / no cloud dependency** — the stack runs fully offline.
