# SQL Marts (Snowflake-flavored)

Run in order:

1. `marts/00_setup.sql` — database, schemas, raw tables, file format  
2. `marts/01_customer_360.sql` … `06_product_revenue.sql` — curated views  

Load CSVs from `data/raw/` via `COPY INTO` (or use the local Python builder in `src/data/build_marts.py` which mirrors these grains as Parquet/CSV under `data/marts/`).

Dialect notes for Databricks SQL / Fabric are in `docs/bi_tool_mapping.md`.
