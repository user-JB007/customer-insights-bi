# Power BI Report Pack — Customer Insights BI

**Primary BI deliverable: Power BI Project (PBIP)** — not screenshots.  
Two reports share one semantic model. Native `.pbix` binary authoring needs Windows Power BI Desktop; open the PBIP here, refresh, then Save As `.pbix`.

## Open in Power BI Desktop

1. Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (Windows).
2. Enable **File → Options and settings → Options → Preview features → Power BI Project (.pbip) save option** if prompted on older builds.
3. Double-click either:
   - [`Customer_Retention_Growth.pbip`](Customer_Retention_Growth.pbip)
   - [`Support_SLA_Performance.pbip`](Support_SLA_Performance.pbip)
   
   Or open `*/definition.pbir` inside each `.Report` folder.
4. On first open the model loads **without cached data** (no `.abf` on Linux CI). Click **Refresh** / Apply changes.
5. If Desktop asks for the CSV folder, set parameter **MartsFolder** to this folder’s `data/` path (absolute), e.g. `C:\...\customer-insights-bi\powerbi\data\` (trailing slash). Default relative value is `./../data/`.
6. File → **Save As** → Power BI `.pbix` when you want a single packaged workbook.

## Layout

```
powerbi/
├── Customer_Retention_Growth.pbip
├── Support_SLA_Performance.pbip
├── CustomerInsights.SemanticModel/
│   ├── definition.pbism
│   ├── model.bim              # TMSL tables, relationships, M partitions, DAX
│   └── diagramLayout.json
├── Customer_Retention_Growth.Report/
│   ├── definition.pbir        # → ../CustomerInsights.SemanticModel
│   └── report.json            # pages: Overview, Cohorts, Growth
├── Support_SLA_Performance.Report/
│   ├── definition.pbir
│   └── report.json            # pages: Overview, SLA Performance, Pending
├── data/                      # mart CSV copies for Desktop refresh
├── model/measures.dax         # DAX source matching the model
├── pages/                     # page briefs
└── screenshots/               # secondary GitHub preview only
```

## Reports

| Report | Pages | Primary tables |
|--------|-------|----------------|
| **Customer Retention & Growth** | Overview, Cohorts, Growth | fact_customer_360, fact_mrr_movement, fact_retention_monthly, fact_revenue_cohorts, fact_product_revenue |
| **Support & SLA Performance** | Overview, SLA Performance, Pending | fact_support_sla (+ relationship to fact_customer_360) |

## Rebuild

```bash
python scripts/build_powerbi_project.py
```

Copies `data/marts/*.csv` → `powerbi/data/`, regenerates `model.bim`, both reports, `.pbip` shortcuts, and `model/measures.dax`.

## Limitations

- **Linux / this repo CI cannot author a guaranteed-open binary `.pbix`** (Desktop is Windows-only). PBIP + TMSL + DAX is the portable definition; Desktop Save As produces `.pbix`.
- First open requires **Refresh** against `powerbi/data/` (or `data/marts/`).
- Report `report.json` visuals are PBIR-legacy definitions bound to model measures; after refresh, tweak layout in Desktop if a visual needs rebinding.
- Do not treat PNGs under `screenshots/` as the workbook.

## DAX

See [`model/measures.dax`](model/measures.dax) — Active Customers, Logo Churn Rate, MRR MoM %, Within SLA %, Beyond Aging Threshold, etc.
