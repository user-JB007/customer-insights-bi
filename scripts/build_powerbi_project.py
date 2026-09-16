#!/usr/bin/env python3
"""Assemble a Power BI Project (PBIP) from curated mart CSVs.

Creates openable artifacts under powerbi/:
  - CustomerInsights.SemanticModel/   (TMSL model.bim + definition.pbism)
  - Customer_Retention_Growth.Report/
  - Support_SLA_Performance.Report/
  - *.pbip shortcuts
  - data/ copies of mart CSVs for Desktop refresh
  - model/measures.dax (synced)

Native .pbix authoring requires Windows Power BI Desktop. Opening either
.pbip (or definition.pbir) in Desktop loads the model + report; Save As
produces .pbix after refresh.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"
PBI = ROOT / "powerbi"
PBI_DATA = PBI / "data"
SM = PBI / "CustomerInsights.SemanticModel"
RET_RPT = PBI / "Customer_Retention_Growth.Report"
SUP_RPT = PBI / "Support_SLA_Performance.Report"

MART_FILES = [
    "customer_360.csv",
    "mrr_movement.csv",
    "retention_monthly.csv",
    "revenue_cohorts.csv",
    "product_revenue.csv",
    "segment_performance.csv",
    "support_sla.csv",
]


def m_csv(relative: str, columns: list[tuple[str, str]], year_month_cols: list[str] | None = None) -> str:
    """Build Power Query M that loads a CSV via MartsFolder parameter."""
    year_month_cols = year_month_cols or []
    transform_cols = ", ".join(f'{{"{n}", {t}}}' for n, t in columns)
    lines = [
        "let",
        "    Source = Csv.Document(",
        f'        File.Contents(MartsFolder & "{relative}"),',
        f'        [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]',
        "    ),",
        '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
        f'    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{transform_cols}}})',
    ]
    prev = '#"Changed Type"'
    for c in year_month_cols:
        lines[-1] = lines[-1] + ","
        step = f"{c} as date"
        lines.append(
            f'    #"{step}" = Table.TransformColumns({prev}, {{{{"{c}", each try Date.From(Text.From(_) & "-01") otherwise null, type date}}}})'
        )
        prev = f'#"{step}"'
    lines.append("in")
    lines.append(f"    {prev}")
    return "\n".join(lines)


def partition(name: str, m_expr: str) -> dict:
    return {
        "name": name,
        "mode": "import",
        "source": [
            {
                "type": "m",
                "expression": m_expr.split("\n"),
            }
        ],
    }


def col(name: str, data_type: str, fmt: str | None = None, summarize: str | None = "none") -> dict:
    c: dict = {
        "name": name,
        "dataType": data_type,
        "sourceColumn": name,
        "summarizeBy": summarize if summarize else "none",
    }
    if fmt:
        c["formatString"] = fmt
    if data_type in ("string", "dateTime", "date", "boolean"):
        # dimensions typically don't summarize
        c["summarizeBy"] = "none"
    return c


def measure(name: str, expr: str, fmt: str | None = None) -> dict:
    m: dict = {
        "name": name,
        "expression": expr if isinstance(expr, list) else expr.split("\n"),
    }
    if fmt:
        m["formatString"] = fmt
    return m


def build_model_bim() -> dict:
    # Shared folder parameter — default points at powerbi/data next to reports
    # User can change MartsFolder in Desktop Transform Data → Parameters
    expressions = [
        {
            "name": "MartsFolder",
            "kind": "m",
            "expression": [
                '"../../data/marts/" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
            ],
        }
    ]

    # --- fact_customer_360 ---
    c360_cols_m = [
        ("customer_id", "type text"),
        ("signup_date", "type date"),
        ("segment", "type text"),
        ("region", "type text"),
        ("plan", "type text"),
        ("acquisition_channel", "type text"),
        ("seats", "Int64.Type"),
        ("mrr", "type number"),
        ("tenure_days", "Int64.Type"),
        ("monthly_active_days", "type number"),
        ("support_tickets_90d", "Int64.Type"),
        ("nps_score", "type number"),
        ("feature_adoption_score", "type number"),
        ("payment_failures_90d", "Int64.Type"),
        ("is_churned", "Int64.Type"),
        ("churn_date", "type date"),
        ("as_of_date", "type date"),
        ("lifetime_revenue", "type number"),
        ("txn_count", "Int64.Type"),
        ("last_txn_date", "type date"),
        ("first_txn_date", "type date"),
        ("avg_txn_amount", "type number"),
        ("total_tickets", "Int64.Type"),
        ("avg_resolve_hours", "type number"),
        ("critical_tickets", "Int64.Type"),
        ("days_since_last_txn", "type number"),
        ("is_active", "Int64.Type"),
        ("customer_health_score", "type number"),
    ]
    c360_table = {
        "name": "fact_customer_360",
        "columns": [
            col("customer_id", "string"),
            col("signup_date", "dateTime", "yyyy-mm-dd"),
            col("segment", "string"),
            col("region", "string"),
            col("plan", "string"),
            col("acquisition_channel", "string"),
            col("seats", "int64", "0", "sum"),
            col("mrr", "double", "#,##0.00", "sum"),
            col("tenure_days", "int64", "0", "sum"),
            col("monthly_active_days", "double", "0.0", "average"),
            col("support_tickets_90d", "int64", "0", "sum"),
            col("nps_score", "double", "0.0", "average"),
            col("feature_adoption_score", "double", "0.00", "average"),
            col("payment_failures_90d", "int64", "0", "sum"),
            col("is_churned", "int64", "0", "sum"),
            col("churn_date", "dateTime", "yyyy-mm-dd"),
            col("as_of_date", "dateTime", "yyyy-mm-dd"),
            col("lifetime_revenue", "double", "#,##0.00", "sum"),
            col("txn_count", "int64", "0", "sum"),
            col("last_txn_date", "dateTime", "yyyy-mm-dd"),
            col("first_txn_date", "dateTime", "yyyy-mm-dd"),
            col("avg_txn_amount", "double", "#,##0.00", "average"),
            col("total_tickets", "int64", "0", "sum"),
            col("avg_resolve_hours", "double", "0.0", "average"),
            col("critical_tickets", "int64", "0", "sum"),
            col("days_since_last_txn", "double", "0.0", "average"),
            col("is_active", "int64", "0", "sum"),
            col("customer_health_score", "double", "0.0", "average"),
        ],
        "measures": [
            measure(
                "Active Customers",
                "CALCULATE ( COUNTROWS ( fact_customer_360 ), fact_customer_360[is_active] = 1 )",
                "#,##0",
            ),
            measure(
                "Churned Customers",
                "CALCULATE ( COUNTROWS ( fact_customer_360 ), fact_customer_360[is_churned] = 1 )",
                "#,##0",
            ),
            measure(
                "Avg Health Score",
                "AVERAGE ( fact_customer_360[customer_health_score] )",
                "0.0",
            ),
            measure(
                "At Risk Customers",
                """CALCULATE (
    COUNTROWS ( fact_customer_360 ),
    fact_customer_360[is_churned] = 0,
    fact_customer_360[mrr] > 0,
    OR (
        fact_customer_360[customer_health_score] < 45,
        OR (
            fact_customer_360[payment_failures_90d] >= 2,
            fact_customer_360[monthly_active_days] < 5
        )
    )
)""",
                "#,##0",
            ),
            measure(
                "Customer Count",
                "COUNTROWS ( fact_customer_360 )",
                "#,##0",
            ),
            measure(
                "Active Rate",
                "DIVIDE ( [Active Customers], [Customer Count] )",
                "0.0%",
            ),
        ],
        "partitions": [
            partition(
                "fact_customer_360",
                m_csv("customer_360.csv", c360_cols_m).replace("../../data/marts/", "").replace(
                    'MartsFolder & "customer_360.csv"',
                    'MartsFolder & "customer_360.csv"',
                ),
            )
        ],
    }
    # Fix M to use relative file via MartsFolder parameter
    c360_table["partitions"][0] = partition("fact_customer_360", m_csv("customer_360.csv", c360_cols_m))

    mrr_cols_m = [
        ("month", "type text"),
        ("active_customers", "Int64.Type"),
        ("mrr", "type number"),
        ("arr", "type number"),
        ("new_customers", "Int64.Type"),
        ("new_mrr", "type number"),
        ("churned_customers", "Int64.Type"),
        ("churned_mrr", "type number"),
        ("logo_churn_rate", "type number"),
        ("net_new_mrr", "type number"),
        ("mrr_growth_pct", "type number"),
    ]
    mrr_table = {
        "name": "fact_mrr_movement",
        "columns": [
            col("month", "dateTime", "yyyy-mm"),
            col("active_customers", "int64", "0", "sum"),
            col("mrr", "double", "#,##0.00", "sum"),
            col("arr", "double", "#,##0.00", "sum"),
            col("new_customers", "int64", "0", "sum"),
            col("new_mrr", "double", "#,##0.00", "sum"),
            col("churned_customers", "int64", "0", "sum"),
            col("churned_mrr", "double", "#,##0.00", "sum"),
            col("logo_churn_rate", "double", "0.0%", "average"),
            col("net_new_mrr", "double", "#,##0.00", "sum"),
            col("mrr_growth_pct", "double", "0.0%", "average"),
        ],
        "measures": [
            measure("Total MRR", "SUM ( fact_mrr_movement[mrr] )", "#,##0.00"),
            measure("Total ARR", "SUM ( fact_mrr_movement[arr] )", "#,##0.00"),
            measure("Net New MRR", "SUM ( fact_mrr_movement[net_new_mrr] )", "#,##0.00"),
            measure(
                "Logo Churn Rate",
                """DIVIDE (
    SUM ( fact_mrr_movement[churned_customers] ),
    SUM ( fact_mrr_movement[active_customers] ) + SUM ( fact_mrr_movement[churned_customers] )
)""",
                "0.0%",
            ),
            measure(
                "MRR MoM %",
                """VAR Curr = [Total MRR]
VAR Prev =
    CALCULATE ( [Total MRR], DATEADD ( fact_mrr_movement[month], -1, MONTH ) )
RETURN
    DIVIDE ( Curr - Prev, Prev )""",
                "0.0%",
            ),
            measure("New Logos", "SUM ( fact_mrr_movement[new_customers] )", "#,##0"),
            measure("Churned Logos", "SUM ( fact_mrr_movement[churned_customers] )", "#,##0"),
        ],
        "partitions": [partition("fact_mrr_movement", m_csv("mrr_movement.csv", mrr_cols_m, year_month_cols=["month"]))],
    }

    ret_cols_m = [
        ("cohort_month", "type text"),
        ("months_since_signup", "Int64.Type"),
        ("cohort_size", "Int64.Type"),
        ("customers_retained", "Int64.Type"),
        ("retention_rate", "type number"),
    ]
    ret_table = {
        "name": "fact_retention_monthly",
        "columns": [
            col("cohort_month", "dateTime", "yyyy-mm"),
            col("months_since_signup", "int64", "0", "sum"),
            col("cohort_size", "int64", "0", "sum"),
            col("customers_retained", "int64", "0", "sum"),
            col("retention_rate", "double", "0.0%", "average"),
        ],
        "measures": [
            measure(
                "Avg Retention Rate",
                "AVERAGE ( fact_retention_monthly[retention_rate] )",
                "0.0%",
            ),
        ],
        "partitions": [partition("fact_retention_monthly", m_csv("retention_monthly.csv", ret_cols_m, year_month_cols=["cohort_month"]))],
    }

    rev_cols_m = [
        ("cohort_month", "type text"),
        ("months_since_signup", "Int64.Type"),
        ("revenue", "type number"),
        ("paying_customers", "Int64.Type"),
        ("txn_count", "Int64.Type"),
        ("cohort_size", "Int64.Type"),
        ("revenue_per_customer", "type number"),
    ]
    rev_table = {
        "name": "fact_revenue_cohorts",
        "columns": [
            col("cohort_month", "dateTime", "yyyy-mm"),
            col("months_since_signup", "int64", "0", "sum"),
            col("revenue", "double", "#,##0.00", "sum"),
            col("paying_customers", "int64", "0", "sum"),
            col("txn_count", "int64", "0", "sum"),
            col("cohort_size", "int64", "0", "sum"),
            col("revenue_per_customer", "double", "#,##0.00", "average"),
        ],
        "measures": [
            measure(
                "Revenue Per Customer",
                "AVERAGE ( fact_revenue_cohorts[revenue_per_customer] )",
                "#,##0.00",
            ),
            measure(
                "Cohort Revenue",
                "SUM ( fact_revenue_cohorts[revenue] )",
                "#,##0.00",
            ),
        ],
        "partitions": [partition("fact_revenue_cohorts", m_csv("revenue_cohorts.csv", rev_cols_m, year_month_cols=["cohort_month"]))],
    }

    prod_cols_m = [
        ("txn_month", "type text"),
        ("product", "type text"),
        ("revenue", "type number"),
        ("txn_count", "Int64.Type"),
        ("customers", "Int64.Type"),
    ]
    prod_table = {
        "name": "fact_product_revenue",
        "columns": [
            col("txn_month", "dateTime", "yyyy-mm"),
            col("product", "string"),
            col("revenue", "double", "#,##0.00", "sum"),
            col("txn_count", "int64", "0", "sum"),
            col("customers", "int64", "0", "sum"),
        ],
        "measures": [
            measure("Product Revenue", "SUM ( fact_product_revenue[revenue] )", "#,##0.00"),
        ],
        "partitions": [partition("fact_product_revenue", m_csv("product_revenue.csv", prod_cols_m, year_month_cols=["txn_month"]))],
    }

    seg_cols_m = [
        ("segment", "type text"),
        ("region", "type text"),
        ("plan", "type text"),
        ("customers", "Int64.Type"),
        ("active_customers", "Int64.Type"),
        ("churned", "Int64.Type"),
        ("total_mrr", "type number"),
        ("avg_mrr", "type number"),
        ("avg_health", "type number"),
        ("avg_nps", "type number"),
        ("lifetime_revenue", "type number"),
        ("churn_rate", "type number"),
    ]
    seg_table = {
        "name": "dim_segment_perf",
        "columns": [
            col("segment", "string"),
            col("region", "string"),
            col("plan", "string"),
            col("customers", "int64", "0", "sum"),
            col("active_customers", "int64", "0", "sum"),
            col("churned", "int64", "0", "sum"),
            col("total_mrr", "double", "#,##0.00", "sum"),
            col("avg_mrr", "double", "#,##0.00", "average"),
            col("avg_health", "double", "0.0", "average"),
            col("avg_nps", "double", "0.0", "average"),
            col("lifetime_revenue", "double", "#,##0.00", "sum"),
            col("churn_rate", "double", "0.0%", "average"),
        ],
        "partitions": [partition("dim_segment_perf", m_csv("segment_performance.csv", seg_cols_m))],
    }

    sla_cols_m = [
        ("event_id", "type text"),
        ("customer_id", "type text"),
        ("opened_at", "type datetime"),
        ("resolved_at", "type datetime"),
        ("sla_due_at", "type datetime"),
        ("opened_date", "type date"),
        ("status", "type text"),
        ("priority", "type text"),
        ("reason", "type text"),
        ("category", "type text"),
        ("channel", "type text"),
        ("csat", "type number"),
        ("resolved_hours", "type number"),
        ("age_hours", "type number"),
        ("is_open", "Int64.Type"),
        ("sla_breach", "type logical"),
        ("sla_status", "type text"),
        ("segment", "type text"),
        ("region", "type text"),
        ("plan", "type text"),
    ]
    sla_table = {
        "name": "fact_support_sla",
        "columns": [
            col("event_id", "string"),
            col("customer_id", "string"),
            col("opened_at", "dateTime", "General Date"),
            col("resolved_at", "dateTime", "General Date"),
            col("sla_due_at", "dateTime", "General Date"),
            col("opened_date", "dateTime", "yyyy-mm-dd"),
            col("status", "string"),
            col("priority", "string"),
            col("reason", "string"),
            col("category", "string"),
            col("channel", "string"),
            col("csat", "double", "0.0", "average"),
            col("resolved_hours", "double", "0.0", "average"),
            col("age_hours", "double", "0.0", "average"),
            col("is_open", "int64", "0", "sum"),
            col("sla_breach", "boolean"),
            col("sla_status", "string"),
            col("segment", "string"),
            col("region", "string"),
            col("plan", "string"),
        ],
        "measures": [
            measure("Ticket Volume", "COUNTROWS ( fact_support_sla )", "#,##0"),
            measure("Avg CSAT", "AVERAGE ( fact_support_sla[csat] )", "0.00"),
            measure(
                "Within SLA %",
                """DIVIDE (
    CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[sla_status] = "within_sla" ),
    CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[is_open] = 0 )
)""",
                "0.0%",
            ),
            measure(
                "Pending Tickets",
                """CALCULATE (
    COUNTROWS ( fact_support_sla ),
    fact_support_sla[status] IN { "pending", "escalated" }
)""",
                "#,##0",
            ),
            measure(
                "Open Tickets",
                "CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[is_open] = 1 )",
                "#,##0",
            ),
            measure(
                "Avg Resolve Hours",
                "AVERAGE ( fact_support_sla[resolved_hours] )",
                "0.0",
            ),
            measure(
                "Breach Count",
                "CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[sla_breach] = TRUE () )",
                "#,##0",
            ),
            measure(
                "Beyond Aging Threshold",
                """VAR Threshold = [Aging Threshold Hours]
RETURN
    CALCULATE (
        COUNTROWS ( fact_support_sla ),
        fact_support_sla[is_open] = 1,
        fact_support_sla[age_hours] >= Threshold
    )""",
                "#,##0",
            ),
        ],
        "partitions": [partition("fact_support_sla", m_csv("support_sla.csv", sla_cols_m))],
    }

    # Parameter table for aging threshold (what-if style single-value)
    param_table = {
        "name": "Aging Threshold",
        "columns": [
            {
                "name": "Aging Threshold Hours",
                "dataType": "int64",
                "isNameInferred": False,
                "isDataTypeInferred": False,
                "formatString": "0",
                "summarizeBy": "none",
                "isHidden": False,
            }
        ],
        "partitions": [
            {
                "name": "Aging Threshold",
                "mode": "import",
                "source": [
                    {
                        "type": "calculated",
                        "expression": ["DATATABLE ( \"Aging Threshold Hours\", INTEGER, {{72}} )"],
                    }
                ],
            }
        ],
        "measures": [
            measure(
                "Aging Threshold Hours",
                'SELECTEDVALUE ( \'Aging Threshold\'[Aging Threshold Hours], 72 )',
                "0",
            )
        ],
    }

    relationships = [
        {
            "name": "rel_support_to_customer",
            "fromTable": "fact_support_sla",
            "fromColumn": "customer_id",
            "toTable": "fact_customer_360",
            "toColumn": "customer_id",
            "crossFilteringBehavior": "oneDirection",
        }
    ]

    model = {
        "name": "CustomerInsights",
        "compatibilityLevel": 1550,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True,
            },
            "tables": [
                c360_table,
                mrr_table,
                ret_table,
                rev_table,
                prod_table,
                seg_table,
                sla_table,
                param_table,
            ],
            "relationships": relationships,
            "expressions": expressions,
            "annotations": [
                {"name": "PBI_QueryOrder", "value": json.dumps([
                    "MartsFolder",
                    "fact_customer_360",
                    "fact_mrr_movement",
                    "fact_retention_monthly",
                    "fact_revenue_cohorts",
                    "fact_product_revenue",
                    "dim_segment_perf",
                    "fact_support_sla",
                ])},
            ],
        },
    }
    return model


def _visual(x, y, w, h, title: str, visual_type: str, query_state: dict) -> dict:
    """Minimal PBIR-legacy visualContainer."""
    config = {
        "name": title.replace(" ", "")[:20] + str(abs(hash(title)) % 10000),
        "layouts": [
            {
                "id": 0,
                "position": {
                    "x": x,
                    "y": y,
                    "z": 0,
                    "width": w,
                    "height": h,
                    "tabOrder": 0,
                },
            }
        ],
        "singleVisual": {
            "visualType": visual_type,
            "projections": query_state.get("projections", {}),
            "prototypeQuery": query_state.get("prototypeQuery", {"Version": 2, "From": [], "Select": [], "Where": []}),
            "vcObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                        }
                    }
                ]
            },
        },
    }
    return {
        "x": x,
        "y": y,
        "z": 0,
        "width": w,
        "height": h,
        "config": json.dumps(config),
        "filters": "[]",
    }


def _card_query(table: str, measure: str) -> dict:
    return {
        "projections": {"Values": [{"queryRef": f"{table}.{measure}"}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": table[:1], "Entity": table, "Type": 0}],
            "Select": [
                {
                    "Measure": {"Expression": {"SourceRef": {"Source": table[:1]}}, "Property": measure},
                    "Name": f"{table}.{measure}",
                    "NativeReferenceName": measure,
                }
            ],
        },
    }


def _bar_query(table: str, category: str, measure: str) -> dict:
    alias = "t"
    return {
        "projections": {
            "Category": [{"queryRef": f"{table}.{category}"}],
            "Y": [{"queryRef": f"{table}.{measure}"}],
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": table, "Type": 0}],
            "Select": [
                {
                    "Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": category},
                    "Name": f"{table}.{category}",
                    "NativeReferenceName": category,
                },
                {
                    "Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": measure},
                    "Name": f"{table}.{measure}",
                    "NativeReferenceName": measure,
                },
            ],
        },
    }


def _line_query(table: str, date_col: str, measure: str) -> dict:
    alias = "t"
    return {
        "projections": {
            "Category": [{"queryRef": f"{table}.{date_col}"}],
            "Y": [{"queryRef": f"{table}.{measure}"}],
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": table, "Type": 0}],
            "Select": [
                {
                    "Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": date_col},
                    "Name": f"{table}.{date_col}",
                    "NativeReferenceName": date_col,
                },
                {
                    "Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": measure},
                    "Name": f"{table}.{measure}",
                    "NativeReferenceName": measure,
                },
            ],
        },
    }


def build_retention_report() -> dict:
    pages = []
    # Overview
    visuals = [
        _visual(20, 20, 200, 100, "Active Customers", "card", _card_query("fact_customer_360", "Active Customers")),
        _visual(240, 20, 200, 100, "Logo Churn Rate", "card", _card_query("fact_mrr_movement", "Logo Churn Rate")),
        _visual(460, 20, 200, 100, "Total MRR", "card", _card_query("fact_mrr_movement", "Total MRR")),
        _visual(680, 20, 200, 100, "MRR MoM %", "card", _card_query("fact_mrr_movement", "MRR MoM %")),
        _visual(900, 20, 200, 100, "Avg Health Score", "card", _card_query("fact_customer_360", "Avg Health Score")),
        _visual(20, 140, 540, 320, "Active Customers Over Time", "lineChart", _line_query("fact_mrr_movement", "month", "Total MRR")),
        _visual(580, 140, 540, 320, "Active Rate by Segment", "clusteredBarChart", _bar_query("fact_customer_360", "segment", "Active Rate")),
        _visual(20, 480, 540, 280, "Logo Movement", "clusteredColumnChart", _bar_query("fact_mrr_movement", "month", "New Logos")),
        _visual(580, 480, 540, 280, "At Risk Customers", "card", _card_query("fact_customer_360", "At Risk Customers")),
    ]
    pages.append({
        "name": "ReportSectionOverview",
        "displayName": "Overview",
        "filters": "[]",
        "ordinal": 0,
        "visualContainers": visuals,
        "width": 1280,
        "height": 800,
        "config": json.dumps({"objects": {"section": [{"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}]}}),
    })
    # Cohorts
    visuals2 = [
        _visual(
            20, 20, 1100, 700,
            "Logo Retention Heatmap",
            "pivotTable",
            {
                "projections": {
                    "Rows": [{"queryRef": "fact_retention_monthly.cohort_month"}],
                    "Columns": [{"queryRef": "fact_retention_monthly.months_since_signup"}],
                    "Values": [{"queryRef": "fact_retention_monthly.Avg Retention Rate"}],
                },
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": "r", "Entity": "fact_retention_monthly", "Type": 0}],
                    "Select": [
                        {"Column": {"Expression": {"SourceRef": {"Source": "r"}}, "Property": "cohort_month"}, "Name": "fact_retention_monthly.cohort_month"},
                        {"Column": {"Expression": {"SourceRef": {"Source": "r"}}, "Property": "months_since_signup"}, "Name": "fact_retention_monthly.months_since_signup"},
                        {"Measure": {"Expression": {"SourceRef": {"Source": "r"}}, "Property": "Avg Retention Rate"}, "Name": "fact_retention_monthly.Avg Retention Rate"},
                    ],
                },
            },
        )
    ]
    pages.append({
        "name": "ReportSectionCohorts",
        "displayName": "Cohorts",
        "filters": "[]",
        "ordinal": 1,
        "visualContainers": visuals2,
        "width": 1280,
        "height": 800,
        "config": "{}",
    })
    # Growth
    visuals3 = [
        _visual(20, 20, 200, 100, "Net New MRR", "card", _card_query("fact_mrr_movement", "Net New MRR")),
        _visual(240, 20, 200, 100, "New Logos", "card", _card_query("fact_mrr_movement", "New Logos")),
        _visual(460, 20, 200, 100, "Total ARR", "card", _card_query("fact_mrr_movement", "Total ARR")),
        _visual(20, 140, 540, 400, "MRR Growth", "lineChart", _line_query("fact_mrr_movement", "month", "Net New MRR")),
        _visual(580, 140, 540, 400, "Active Mix by Plan", "clusteredBarChart", _bar_query("fact_customer_360", "plan", "Active Customers")),
        _visual(20, 560, 1100, 200, "Active Mix by Region", "clusteredBarChart", _bar_query("fact_customer_360", "region", "Active Customers")),
    ]
    pages.append({
        "name": "ReportSectionGrowth",
        "displayName": "Growth",
        "filters": "[]",
        "ordinal": 2,
        "visualContainers": visuals3,
        "width": 1280,
        "height": 800,
        "config": "{}",
    })

    return {
        "config": json.dumps({
            "version": "5.43",
            "themeCollection": {"baseTheme": {"name": "CY23SU08", "version": "5.43", "type": 2}},
            "activeSectionIndex": 0,
            "defaultDrillFilterOtherVisuals": True,
            "linguisticSchemaSyncVersion": 2,
            "settings": {"useNewFilterPaneExperience": True, "allowChangeFilterTypes": True},
        }),
        "filters": "[]",
        "sections": pages,
        "layoutOptimization": 0,
    }


def build_support_report() -> dict:
    pages = []
    visuals = [
        _visual(20, 20, 200, 100, "Ticket Volume", "card", _card_query("fact_support_sla", "Ticket Volume")),
        _visual(240, 20, 200, 100, "Avg CSAT", "card", _card_query("fact_support_sla", "Avg CSAT")),
        _visual(460, 20, 200, 100, "Within SLA %", "card", _card_query("fact_support_sla", "Within SLA %")),
        _visual(680, 20, 200, 100, "Pending Tickets", "card", _card_query("fact_support_sla", "Pending Tickets")),
        _visual(20, 140, 540, 320, "Monthly Ticket Volume", "lineChart", _line_query("fact_support_sla", "opened_date", "Ticket Volume")),
        _visual(580, 140, 540, 320, "Reason Mix", "clusteredBarChart", _bar_query("fact_support_sla", "reason", "Ticket Volume")),
        _visual(20, 480, 540, 280, "Channel Mix", "clusteredBarChart", _bar_query("fact_support_sla", "channel", "Ticket Volume")),
        _visual(580, 480, 540, 280, "CSAT by Channel", "clusteredBarChart", _bar_query("fact_support_sla", "channel", "Avg CSAT")),
    ]
    pages.append({
        "name": "ReportSectionOverview",
        "displayName": "Overview",
        "filters": "[]",
        "ordinal": 0,
        "visualContainers": visuals,
        "width": 1280,
        "height": 800,
        "config": "{}",
    })
    visuals2 = [
        _visual(20, 20, 400, 360, "SLA Status Mix", "clusteredBarChart", _bar_query("fact_support_sla", "sla_status", "Ticket Volume")),
        _visual(440, 20, 400, 360, "Resolve Hours by Priority", "clusteredBarChart", _bar_query("fact_support_sla", "priority", "Avg Resolve Hours")),
        _visual(860, 20, 300, 160, "Breach Count", "card", _card_query("fact_support_sla", "Breach Count")),
        _visual(860, 200, 300, 160, "Avg Resolve Hours", "card", _card_query("fact_support_sla", "Avg Resolve Hours")),
        _visual(20, 400, 540, 360, "Breach by Channel", "clusteredBarChart", _bar_query("fact_support_sla", "channel", "Breach Count")),
        _visual(580, 400, 540, 360, "Within SLA by Segment", "clusteredBarChart", _bar_query("fact_support_sla", "segment", "Within SLA %")),
    ]
    pages.append({
        "name": "ReportSectionSLA",
        "displayName": "SLA Performance",
        "filters": "[]",
        "ordinal": 1,
        "visualContainers": visuals2,
        "width": 1280,
        "height": 800,
        "config": "{}",
    })
    visuals3 = [
        _visual(20, 20, 200, 100, "Open Tickets", "card", _card_query("fact_support_sla", "Open Tickets")),
        _visual(240, 20, 280, 100, "Beyond Aging Threshold", "card", _card_query("fact_support_sla", "Beyond Aging Threshold")),
        _visual(20, 140, 540, 400, "Open by Priority", "clusteredBarChart", _bar_query("fact_support_sla", "priority", "Open Tickets")),
        _visual(580, 140, 540, 400, "Open by Reason", "clusteredBarChart", _bar_query("fact_support_sla", "reason", "Open Tickets")),
        _visual(20, 560, 1100, 200, "Aging (age_hours)", "clusteredBarChart", _bar_query("fact_support_sla", "priority", "Beyond Aging Threshold")),
    ]
    pages.append({
        "name": "ReportSectionPending",
        "displayName": "Pending",
        "filters": "[]",
        "ordinal": 2,
        "visualContainers": visuals3,
        "width": 1280,
        "height": 800,
        "config": "{}",
    })
    return {
        "config": json.dumps({
            "version": "5.43",
            "themeCollection": {"baseTheme": {"name": "CY23SU08", "version": "5.43", "type": 2}},
            "activeSectionIndex": 0,
            "defaultDrillFilterOtherVisuals": True,
            "settings": {"useNewFilterPaneExperience": True},
        }),
        "filters": "[]",
        "sections": pages,
        "layoutOptimization": 0,
    }


DAX_FILE = '''-- Customer Insights BI — DAX measures (matches CustomerInsights.SemanticModel)

-- fact_customer_360
Active Customers =
CALCULATE ( COUNTROWS ( fact_customer_360 ), fact_customer_360[is_active] = 1 )

Churned Customers =
CALCULATE ( COUNTROWS ( fact_customer_360 ), fact_customer_360[is_churned] = 1 )

Customer Count = COUNTROWS ( fact_customer_360 )

Active Rate = DIVIDE ( [Active Customers], [Customer Count] )

Avg Health Score = AVERAGE ( fact_customer_360[customer_health_score] )

At Risk Customers =
CALCULATE (
    COUNTROWS ( fact_customer_360 ),
    fact_customer_360[is_churned] = 0,
    fact_customer_360[mrr] > 0,
    OR (
        fact_customer_360[customer_health_score] < 45,
        OR (
            fact_customer_360[payment_failures_90d] >= 2,
            fact_customer_360[monthly_active_days] < 5
        )
    )
)

-- fact_mrr_movement
Total MRR = SUM ( fact_mrr_movement[mrr] )

Total ARR = SUM ( fact_mrr_movement[arr] )

Net New MRR = SUM ( fact_mrr_movement[net_new_mrr] )

New Logos = SUM ( fact_mrr_movement[new_customers] )

Churned Logos = SUM ( fact_mrr_movement[churned_customers] )

Logo Churn Rate =
DIVIDE (
    SUM ( fact_mrr_movement[churned_customers] ),
    SUM ( fact_mrr_movement[active_customers] ) + SUM ( fact_mrr_movement[churned_customers] )
)

MRR MoM % =
VAR Curr = [Total MRR]
VAR Prev = CALCULATE ( [Total MRR], DATEADD ( fact_mrr_movement[month], -1, MONTH ) )
RETURN DIVIDE ( Curr - Prev, Prev )

-- fact_retention_monthly / cohorts
Avg Retention Rate = AVERAGE ( fact_retention_monthly[retention_rate] )

Revenue Per Customer = AVERAGE ( fact_revenue_cohorts[revenue_per_customer] )

Cohort Revenue = SUM ( fact_revenue_cohorts[revenue] )

Product Revenue = SUM ( fact_product_revenue[revenue] )

-- fact_support_sla
Ticket Volume = COUNTROWS ( fact_support_sla )

Avg CSAT = AVERAGE ( fact_support_sla[csat] )

Within SLA % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[sla_status] = "within_sla" ),
    CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[is_open] = 0 )
)

Pending Tickets =
CALCULATE (
    COUNTROWS ( fact_support_sla ),
    fact_support_sla[status] IN { "pending", "escalated" }
)

Open Tickets =
CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[is_open] = 1 )

Avg Resolve Hours = AVERAGE ( fact_support_sla[resolved_hours] )

Breach Count =
CALCULATE ( COUNTROWS ( fact_support_sla ), fact_support_sla[sla_breach] = TRUE () )

Aging Threshold Hours =
SELECTEDVALUE ( 'Aging Threshold'[Aging Threshold Hours], 72 )

Beyond Aging Threshold =
VAR Threshold = [Aging Threshold Hours]
RETURN
    CALCULATE (
        COUNTROWS ( fact_support_sla ),
        fact_support_sla[is_open] = 1,
        fact_support_sla[age_hours] >= Threshold
    )
'''


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    PBI.mkdir(parents=True, exist_ok=True)
    PBI_DATA.mkdir(parents=True, exist_ok=True)

    # Copy marts into powerbi/data for Desktop-relative refresh
    for name in MART_FILES:
        src = MARTS / name
        if not src.exists():
            raise SystemExit(f"Missing mart: {src}")
        shutil.copy2(src, PBI_DATA / name)
        print(f"Copied {name}")

    # Also keep MartsFolder default as ../../data/marts/ (repo root marts)
    # AND powerbi/data as convenience — README documents both.

    # Semantic model
    SM.mkdir(parents=True, exist_ok=True)
    (SM / ".pbi").mkdir(exist_ok=True)
    write_json(
        SM / "definition.pbism",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "1.0",
            "settings": {},
        },
    )
    model = build_model_bim()
    # Point MartsFolder default at packaged powerbi/data (relative from SemanticModel)
    model["model"]["expressions"][0]["expression"] = [
        '"./../data/" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    ]
    write_json(SM / "model.bim", model)
    write_json(
        SM / "diagramLayout.json",
        {
            "version": "1.1.0",
            "diagrams": [
                {
                    "ordinal": 0,
                    "scrollPosition": {"x": 0, "y": 0},
                    "nodes": [
                        {"location": {"x": 0, "y": 0}, "nodeIndex": "fact_customer_360", "size": {"height": 300, "width": 220}},
                        {"location": {"x": 300, "y": 0}, "nodeIndex": "fact_mrr_movement", "size": {"height": 260, "width": 200}},
                        {"location": {"x": 600, "y": 0}, "nodeIndex": "fact_retention_monthly", "size": {"height": 200, "width": 200}},
                        {"location": {"x": 0, "y": 360}, "nodeIndex": "fact_support_sla", "size": {"height": 300, "width": 220}},
                        {"location": {"x": 300, "y": 360}, "nodeIndex": "fact_product_revenue", "size": {"height": 180, "width": 180}},
                        {"location": {"x": 600, "y": 360}, "nodeIndex": "dim_segment_perf", "size": {"height": 200, "width": 180}},
                    ],
                    "name": "All tables",
                    "zoomValue": 100,
                    "pinKeyFieldsToTop": False,
                    "showExtraHeaderInfo": False,
                    "hideKeyFieldsWhenCollapsed": False,
                    "tablesLocked": False,
                }
            ],
            "selectedDiagram": "All tables",
            "defaultDiagram": "All tables",
        },
    )
    write_json(
        SM / ".pbi" / "editorSettings.json",
        {"version": "1.0", "showHiddenFields": True, "autodetectRelationships": False},
    )

    # Reports
    for rpt_dir, builder, title in [
        (RET_RPT, build_retention_report, "Customer Retention & Growth"),
        (SUP_RPT, build_support_report, "Support & SLA Performance"),
    ]:
        rpt_dir.mkdir(parents=True, exist_ok=True)
        write_json(
            rpt_dir / "definition.pbir",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
                "version": "1.0",
                "datasetReference": {"byPath": {"path": "../CustomerInsights.SemanticModel"}},
            },
        )
        write_json(rpt_dir / "report.json", builder())
        print(f"Wrote report: {title} → {rpt_dir.name}")

    # PBIP shortcuts
    for pbip_name, report_folder in [
        ("Customer_Retention_Growth.pbip", "Customer_Retention_Growth.Report"),
        ("Support_SLA_Performance.pbip", "Support_SLA_Performance.Report"),
    ]:
        write_json(
            PBI / pbip_name,
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
                "version": "1.0",
                "artifacts": [{"report": {"path": report_folder}}],
                "settings": {"enableAutoRecovery": True},
            },
        )

    # DAX sync
    model_dir = PBI / "model"
    model_dir.mkdir(exist_ok=True)
    (model_dir / "measures.dax").write_text(DAX_FILE, encoding="utf-8")
    print(f"Wrote {model_dir / 'measures.dax'}")

    # .gitignore for local Desktop cache
    gitignore = PBI / ".gitignore"
    gi = """# Power BI Desktop local caches (machine-specific)
**/.pbi/localSettings.json
**/.pbi/cache.abf
**/Cache/
*.pbix.bak
"""
    gitignore.write_text(gi, encoding="utf-8")

    print("\nPBIP layout:")
    for p in sorted(PBI.rglob("*")):
        if p.is_file() and "screenshots" not in p.parts:
            rel = p.relative_to(PBI)
            print(f"  {rel}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
