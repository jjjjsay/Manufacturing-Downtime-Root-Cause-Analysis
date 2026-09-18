# Executive Summary

The bottling line is running at **64.0% efficiency** — for every hour the
line is scheduled, only about 38 minutes are truly productive. Across 38
batches analyzed, operators lost a combined **1,388 minutes (~23 hours)**
to downtime, and **56% of that downtime (776 minutes) was attributable to
operator error** rather than equipment or supply issues.

Efficiency is not uniform across the team: **Mac (60.9%) and Dennis
(63.2%)** run below the line average, while **Charlie (66.8%) and Dee
(64.1%)** run at or above it. The gap is concentrated, not diffuse — Mac
alone accounts for **130 of the 160 minutes (81%)** of all "batch change"
error downtime on the line, while Charlie and Dennis together account for
**238 of the 332 minutes (72%)** of all "machine adjustment" downtime.
"Machine adjustment" is also the single largest downtime factor overall
(332 minutes across 12 occurrences), followed by machine failure (254
minutes, not operator-driven) and inventory shortages (225 minutes, not
operator-driven).

## Business Problem

The production line's throughput has felt inconsistent, but there has
been no structured way to answer basic operational questions:

- What is the line actually running at, efficiency-wise, versus its
  theoretical maximum?
- Is underperformance a people problem, an equipment problem, or both?
- Which downtime factors are costing the most time and are worth fixing
  first?
- Are downtime issues spread evenly across operators, or concentrated —
  and if concentrated, is it a training gap that can be closed cheaply?

This project uses one week of batch-level production data (38 batches,
4 operators, 6 products, 12 downtime factors) to answer these questions
and turn them into concrete, prioritized recommendations.

---

## Methodology

**Data.** Four related tables sourced from
`Manufacturing_Line_Productivity.xlsx`:
| Table | Grain | Key fields |
|---|---|---|
| Line productivity | 1 row per batch | Date, Product, Batch, Operator, Start/End Time |
| Products | 1 row per product | Flavor, Size, Min batch time (ideal, zero-downtime minutes) |
| Line downtime | 1 row per batch, 1 column per factor | Minutes lost, by downtime factor ID |
| Downtime factors | 1 row per factor | Description, whether it's an Operator Error |

**Approach.**
1. **Clean & engineer.** Computed each batch's actual duration from
   Start/End Time (handling the one batch that runs past midnight).
   Melted the wide downtime table into long form (`Batch, Factor,
   Minutes`) and joined it to the factor descriptions and the
   operator-error flag.
2. **Merge into one batch-level fact table** joining productivity,
   product minimum times, and total/operator-error downtime per batch.
3. **Efficiency metric.** `Efficiency = Minimum batch time / Actual duration`,
   computed per batch and aggregated (sum of minimums / sum of actuals,
   not an average of ratios, to avoid short-batch bias) at the line and
   operator level.
4. **Operator rollups.** Grouped by operator: batch count, total ideal vs.
   actual time, efficiency, average downtime per batch, and the share of
   that downtime caused by operator error.
5. **Downtime factor ranking.** Grouped by factor: total minutes lost,
   number of occurrences, and average minutes per occurrence — sorted to
   surface the leading causes.
6. **Operator × error-type cross-tab.** Pivoted operator-error-only
   downtime by Operator (rows) and error Description (columns) to find
   operator-specific patterns, visualized as a heatmap.
7. **Validate & visualize.** Sanity-checked totals (e.g., downtime +
   min batch time ≈ actual duration) and generated four charts
   (`outputs/figures/`) supporting the findings above.

---

The business problem is therefore two-fold: a **process/training issue**
(batch changeovers, machine adjustments) concentrated in specific
operators, and a **systemic issue** (equipment reliability, inventory
planning) affecting everyone equally. Closing the gap between the
lowest- and highest-performing operator alone would recover roughly
**5–6 percentage points of line efficiency** with no capital investment.

## Skills

- **Python data wrangling** — `pandas` (merge, melt, groupby, pivot_table)
  to reshape a small multi-table Excel workbook into an analysis-ready
  fact table
- **Data cleaning** — handling an edge case where a shift crosses
  midnight and Excel serializes the time as a full datetime instead of a
  time-of-day
- **Metric design** — building an efficiency measure appropriate for
  aggregation across batches of different sizes, instead of a naive
  average of ratios
- **Exploratory & diagnostic analysis** — operator rollups, Pareto-style
  ranking of downtime causes, and a cross-tab to isolate operator-specific
  patterns
- **Data visualization** — `matplotlib` (bar, horizontal bar, heatmap,
  pie) built for a business audience: labeled thresholds, color-coded
  categories, and annotated values
- **Analytics storytelling** — translating table output into a written
  executive summary and prioritized business recommendations

---

## Results & Business Recommendation

### 1. Current line efficiency: 64.0%
`Efficiency = Σ(Minimum batch time) / Σ(Actual batch duration)` across all
38 batches. The line is running at roughly two-thirds of its
theoretical maximum throughput.

### 2. Operator performance — two operators below average

| Operator | Batches | Efficiency | Avg. downtime / batch | % of downtime from operator error |
|---|---|---|---|---|
| **Mac** | 8 | **60.9%** | 41.5 min | 57.8% |
| **Dennis** | 8 | **63.2%** | 37.8 min | 54.3% |
| Dee | 11 | 64.1% | 33.6 min | 51.9% |
| Charlie | 11 | 66.8% | 34.9 min | 59.4% |
| **Line average** | 38 | **64.0%** | 36.4 min | 56.0% |

Mac and Dennis run below the line average; Charlie has the highest
efficiency despite also having the highest *proportion* of downtime tied
to operator error — meaning Charlie's total downtime volume is simply
lower, not the error mix.

<img width="840" height="540" alt="operator_efficiency" src="https://github.com/user-attachments/assets/66a3b4c9-21e9-41e8-a2de-5e46aa7ef07a" />


### 3. Leading downtime factors

| Rank | Factor | Operator error? | Total minutes | Occurrences |
|---|---|---|---|---|
| 1 | Machine adjustment | Yes | 332 | 12 |
| 2 | Machine failure | No | 254 | 11 |
| 3 | Inventory shortage | No | 225 | 9 |
| 4 | Batch change | Yes | 160 | 5 |
| 5 | Batch coding error | Yes | 145 | 6 |

The top 5 factors account for **1,116 of 1,388 total downtime minutes
(80%)**. Overall, **56% of all downtime is operator-error-related**, and
44% is equipment/supply-related (machine failure + inventory shortage
alone are 35% of all downtime and are not operator-fixable through

<img width="960" height="600" alt="downtime_by_factor" src="https://github.com/user-attachments/assets/4c26098e-cde7-45ca-b03a-13ac5424c382" />
<img width="600" height="600" alt="downtime_error_share" src="https://github.com/user-attachments/assets/0aea0b89-7c67-4c74-b179-f8d11ca5f271" />



### 4. Operator-specific error patterns

| Operator | Batch change | Batch coding error | Machine adjustment | Total operator-error min |
|---|---|---|---|---|
| **Mac** | **130** | 47 | 15 | 192 |
| Charlie | 10 | 44 | **118** | 228 |
| Dennis | 0 | 24 | **120** | 164 |
| Dee | 20 | 30 | 79 | 192 |

Two clear, specific patterns emerge:
- **Mac drives 81% of all batch-change downtime** on the line (130 of 160
  minutes) — a strong signal of a specific skill gap in changeover
  procedure, not a general performance problem.
- **Charlie and Dennis together drive 72% of all machine-adjustment
  downtime** (238 of 332 minutes) — the single largest downtime factor
  line-wide.

<img width="960" height="540" alt="operator_error_heatmap" src="https://github.com/user-attachments/assets/9a84814f-abc6-45e8-add9-acfe066ffb31" />


---

## Business Recommendations

1. **Retrain Mac on batch-changeover procedure.** This single, targeted
   fix addresses 130 minutes of downtime (~9% of all downtime observed)
   concentrated in one operator and one task — likely the highest
   ROI action available since it needs no capital investment.
2. **Standardize and retrain machine-adjustment procedure for Charlie and
   Dennis**, since together they drive 72% of the line's single largest
   downtime category. Consider pairing them with Dee or Mac (who have
   little-to-no adjustment downtime) to shadow and document what those
   operators do differently.
3. **Escalate machine failure and inventory shortage to maintenance and
   supply chain**, not the line team — these two factors are 35% of all
   downtime (479 minutes) and are not operator-error-driven, so training
   will not fix them. Investigate a preventive-maintenance schedule and
   safety-stock levels for input materials.
4. **Set an efficiency floor and monitor going forward.** Use 64.0% as
   the current baseline and 66.8% (Charlie, the top performer) as a
   near-term target for every operator; closing that gap for Mac and
   Dennis alone would lift line-wide efficiency by an estimated 5–6
   points with no new equipment.
5. **Reduce Batch coding error line-wide** (145 minutes, spread fairly
   evenly across all four operators) — since no single operator drives
   it, this points to a process or labeling-system issue worth a
   root-cause review rather than individual coaching.

---

## Next Steps

- **Expand the data window.** This analysis covers one week (38 batches).
  Re-run the same pipeline over a full month or quarter to confirm these
  patterns hold and aren't a short-term blip.
- **Add shift/time-of-day as a dimension** — several batches run
  overnight; test whether downtime or efficiency varies by shift, which
  could point to fatigue or staffing-level issues rather than pure skill.
- **Track efficiency post-intervention.** After the Mac and
  Charlie/Dennis retraining, re-run `src/analysis.py` on the following
  weeks' data to measure whether the targeted downtime factors actually
  drop.
- **Build a lightweight recurring dashboard** (e.g., a scheduled version
  of this script feeding a BI tool) so line efficiency and top downtime
  factors are visible weekly instead of analyzed ad hoc.
- **Investigate root cause of "Batch coding error"** with the line's
  labeling/coding system vendor or process owner, since it's evenly
  distributed across operators rather than concentrated in one person.

---
