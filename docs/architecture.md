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


## API source and sink

**Source:** [JSONPlaceholder](https://jsonplaceholder.typicode.com/) — `GET /users`, `/posts`, `/comments` land under `data/raw/api/` and feed `data/marts/engagement_events.csv` as an engagement enrichment mart. Config: `config/pipeline.yaml` / env `API_SOURCE_BASE_URL`.

**Sink:** POST retention/support KPI snapshot JSON to local FastAPI (`SINK_API_URL`, default `http://127.0.0.1:8089/ingest`) and optional JSONPlaceholder (`EXTERNAL_SINK_URL`).

CLI stages via `run_pipeline.py --source api|both --sink api`, or `python -m src.integrations.api_source` / `python -m src.integrations.api_sink`.

Power BI generators continue to use existing marts; engagement_events is additive enrichment.
