# How Marts Feed Power BI / Tableau / Fabric / Databricks SQL

This project ships **curated analytics marts** (CSV + Parquet locally; Snowflake SQL views for warehouse deployment). No live cloud connection is required for the demo — point your BI tool at the files or deploy the SQL to Snowflake / Databricks SQL.

## Mart catalog

| Mart | Grain | Primary use |
|------|-------|-------------|
| `customer_360` | 1 row / customer | Account health, churn labels, lifetime value |
| `retention_monthly` | cohort × tenure month | Logo retention curves / heatmaps |
| `revenue_cohorts` | cohort × tenure month | Revenue retention / LTV curves |
| `mrr_movement` | 1 row / calendar month | ARR/MRR trend, new vs churned MRR |
| `segment_performance` | segment × region × plan | Slice-and-dice scorecards |
| `product_revenue` | month × product | Product mix & growth |

## Power BI

1. **Get data** → Text/CSV or Parquet folder → select `data/marts/`.
2. Prefer **Parquet** for typed columns; enable **Combine files** if using a folder.
3. Relationships (star-ish):
   - `customer_360[customer_id]` is the account dimension (also usable as fact for KPIs).
   - `mrr_movement[month]`, `product_revenue[txn_month]` as date keys — create a shared Date table if desired.
4. Suggested measures:
   - `Active Customers = SUM(customer_360[is_active])`
   - `Churn Rate = AVERAGE(customer_360[is_churned])`
   - `ARR = SUM(mrr_movement[arr])` (latest month filter)
5. Publish to Power BI Service; refresh from OneDrive/SharePoint or a gateway if CSVs live on-prem.

## Tableau

1. Connect to **Text file** / **Statistical file** (Parquet via Hyper extract) pointing at `data/marts/`.
2. Or connect Tableau to **Snowflake** and select `CUSTOMER_INSIGHTS.MARTS.*` views from `sql/marts/`.
3. Build:
   - Executive board from `mrr_movement` + `customer_360`
   - Retention heatmap: `retention_monthly` with `months_since_signup` on Columns, `cohort_month` on Rows, `retention_rate` on Color
4. Extract + scheduled refresh for portfolio demos offline.

## Microsoft Fabric

1. Upload `data/marts/*.parquet` into a **Lakehouse** Files or Tables folder.
2. Or run the Snowflake-flavored SQL (minor dialect tweaks: `IFF` → `IIF` / `CASE`, `DATE_TRUNC` compatible) against a Fabric Warehouse.
3. Build a **Semantic model** on top of Lakehouse tables; create reports in Power BI within Fabric.
4. Optional: notebook in Fabric mirrors `src/models/train_churn.py` for churn scoring written back to a Lakehouse table.

## Databricks SQL

1. `CREATE SCHEMA customer_insights;` then `CREATE TABLE … USING PARQUET LOCATION '…'` or `read_files` on the mart paths.
2. Translate views in `sql/marts/` (Snowflake `IFF` → `IF`, `DATE_TRUNC` / `ADD_MONTHS` are largely portable; replace `GENERATOR`/`FLATTEN` patterns with `EXPLODE(SEQUENCE(…))`).
3. Serve dashboards via **Dashboards** in Databricks SQL or partner BI on the SQL warehouse endpoint.
4. MLflow can track the churn model from `src/models/train_churn.py` if you promote this beyond the local joblib artifact.

## Local → cloud promotion path

```
data/raw (CSV)
    ↓  sql/marts/00_setup.sql + COPY INTO   OR   src/data/build_marts.py
data/marts / CUSTOMER_INSIGHTS.MARTS.*
    ↓
Power BI · Tableau · Fabric · Databricks SQL
    ↓
src/models/train_churn.py  →  artifacts/model/  →  scored at-risk lists in BI
```
