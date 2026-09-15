-- Snowflake-flavored setup for Customer Insights BI marts
-- Adapt database/schema names to your account. No secrets required.

CREATE DATABASE IF NOT EXISTS CUSTOMER_INSIGHTS;
CREATE SCHEMA IF NOT EXISTS CUSTOMER_INSIGHTS.RAW;
CREATE SCHEMA IF NOT EXISTS CUSTOMER_INSIGHTS.MARTS;

-- Example stage + file format for CSV landing (local run uses Python instead)
CREATE OR REPLACE FILE FORMAT CUSTOMER_INSIGHTS.RAW.CSV_FF
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL', 'NaT');

-- Raw tables (load via COPY INTO or Snowpipe in production)
CREATE OR REPLACE TABLE CUSTOMER_INSIGHTS.RAW.CUSTOMERS (
  customer_id             VARCHAR,
  signup_date             DATE,
  segment                 VARCHAR,
  region                  VARCHAR,
  plan                    VARCHAR,
  acquisition_channel     VARCHAR,
  seats                   NUMBER,
  mrr                     FLOAT,
  tenure_days             NUMBER,
  monthly_active_days     FLOAT,
  support_tickets_90d     NUMBER,
  nps_score               FLOAT,
  feature_adoption_score  FLOAT,
  payment_failures_90d    NUMBER,
  is_churned              NUMBER(1),
  churn_date              DATE,
  as_of_date              DATE
);

CREATE OR REPLACE TABLE CUSTOMER_INSIGHTS.RAW.TRANSACTIONS (
  transaction_id  VARCHAR,
  customer_id     VARCHAR,
  txn_date        DATE,
  product         VARCHAR,
  amount          FLOAT,
  currency        VARCHAR,
  status          VARCHAR,
  billing_period  VARCHAR
);

CREATE OR REPLACE TABLE CUSTOMER_INSIGHTS.RAW.SUPPORT_EVENTS (
  event_id        VARCHAR,
  customer_id     VARCHAR,
  created_at      DATE,
  category        VARCHAR,
  priority        VARCHAR,
  resolved_hours  FLOAT
);
