# Manufacturing-Downtime-Root-Cause-Analysis

A data analytics project diagnosing efficiency loss on a soda bottling
production line — quantifying overall line efficiency, identifying
underperforming operators, ranking the leading causes of downtime, and
pinpointing which operators struggle with which specific error types.

---

## Project Structure

```
manufacturing-line-productivity/
├── README.md                          <- you are here
├── requirements.txt
├── data/
│   └── raw/
│       ├── Manufacturing_Line_Productivity.xlsx
│       └── data_dictionary.csv
├── src/
│   ├── load_data.py                   <- load, clean, join the 4 raw tables
│   └── analysis.py                    <- all metrics, tables, and charts
└── outputs/
    ├── tables/                        <- CSV outputs of every analysis table
    │   ├── batch_level_detail.csv
    │   ├── operator_performance.csv
    │   ├── downtime_by_factor.csv
    │   ├── operator_error_breakdown.csv
    │   └── overall_efficiency.txt
    └── figures/                       <- PNG charts referenced above
        ├── operator_efficiency.png
        ├── downtime_by_factor.png
        ├── operator_error_heatmap.png
        └── downtime_error_share.png
```

## How to Run

```bash
git clone <your-repo-url>
cd manufacturing-line-productivity
pip install -r requirements.txt
cd src
python analysis.py
```

This regenerates every table in `outputs/tables/` and every chart in
`outputs/figures/` from the raw workbook in `data/raw/`.
