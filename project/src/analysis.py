"""
analysis.py
-----------
Runs the full analysis for the soda bottling line productivity project and
writes result tables (CSV) and charts (PNG) to outputs/.

Business questions answered here:
    1. What is the current line efficiency? (sum of min time / sum of actual time)
    2. Are any operators underperforming?
    3. What are the leading factors for downtime?
    4. Do any operators struggle with particular types of operator error?

Run from the project root:
    python src/analysis.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

from load_data import load_raw_tables, build_batch_table

# Resolve paths relative to the project root (parent of this src/ folder) so
# the script works whether it's run as `python src/analysis.py` from the
# project root or `python analysis.py` from inside src/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(PROJECT_ROOT, "outputs", "figures")
TABLE_DIR = os.path.join(PROJECT_ROOT, "outputs", "tables")
RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "Manufacturing_Line_Productivity.xlsx")

plt.rcParams["figure.dpi"] = 120
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False


def ensure_dirs():
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(TABLE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Q1. Overall line efficiency
# ---------------------------------------------------------------------------
def overall_efficiency(batch_df: pd.DataFrame) -> float:
    """
    Line efficiency = total minimum (ideal) time / total actual time,
    aggregated across every batch. This is the standard OEE-style
    "performance efficiency" measure: it answers "of all the time the line
    ran, what share was truly productive?"
    """
    total_min_time = batch_df["Min batch time"].sum()
    total_actual_time = batch_df["Duration (min)"].sum()
    return total_min_time / total_actual_time


# ---------------------------------------------------------------------------
# Q2. Operator performance
# ---------------------------------------------------------------------------
def operator_performance(batch_df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-operator rollup: batches run, total ideal time, total actual time,
    overall efficiency, and average downtime minutes per batch.
    """
    grp = batch_df.groupby("Operator").agg(
        Batches=("Batch", "count"),
        Total_Min_Time=("Min batch time", "sum"),
        Total_Actual_Time=("Duration (min)", "sum"),
        Total_Downtime=("Downtime (min)", "sum"),
        Total_Operator_Error_Downtime=("Operator Error Downtime (min)", "sum"),
    )
    grp["Efficiency"] = grp["Total_Min_Time"] / grp["Total_Actual_Time"]
    grp["Avg_Downtime_per_Batch"] = grp["Total_Downtime"] / grp["Batches"]
    grp["Pct_Downtime_from_Operator_Error"] = (
        grp["Total_Operator_Error_Downtime"] / grp["Total_Downtime"]
    )
    return grp.sort_values("Efficiency").reset_index()


# ---------------------------------------------------------------------------
# Q3. Leading downtime factors
# ---------------------------------------------------------------------------
def downtime_by_factor(downtime_long: pd.DataFrame) -> pd.DataFrame:
    """
    Total minutes lost and number of occurrences per downtime factor,
    sorted by total minutes lost (descending).
    """
    grp = downtime_long.groupby(["Factor", "Description", "Operator Error"]).agg(
        Total_Minutes=("Minutes", "sum"),
        Occurrences=("Minutes", "count"),
    )
    grp["Avg_Minutes_per_Occurrence"] = grp["Total_Minutes"] / grp["Occurrences"]
    return grp.sort_values("Total_Minutes", ascending=False).reset_index()


# ---------------------------------------------------------------------------
# Q4. Operator x error-type breakdown (operator-error factors only)
# ---------------------------------------------------------------------------
def operator_error_breakdown(batch_df: pd.DataFrame,
                              downtime_long: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot table of total downtime minutes, restricted to factors flagged
    as Operator Error = Yes, broken out by Operator (rows) and factor
    Description (columns). Highlights which operators struggle with which
    specific error types.
    """
    error_rows = downtime_long[downtime_long["Operator Error"] == "Yes"].copy()
    error_rows = error_rows.merge(
        batch_df[["Batch", "Operator"]], on="Batch", how="left"
    )
    pivot = pd.pivot_table(
        error_rows, index="Operator", columns="Description",
        values="Minutes", aggfunc="sum", fill_value=0, margins=True,
        margins_name="Total"
    )
    return pivot


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def make_charts(batch_df, op_perf, factor_df, error_pivot, overall_eff):
    # 1. Operator efficiency bar chart with the line average
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#d62728" if e < overall_eff else "#2ca02c" for e in op_perf["Efficiency"]]
    ax.bar(op_perf["Operator"], op_perf["Efficiency"] * 100, color=colors)
    ax.axhline(overall_eff * 100, color="black", linestyle="--", linewidth=1,
               label=f"Line average ({overall_eff * 100:.1f}%)")
    ax.set_ylabel("Efficiency (%)")
    ax.set_title("Operator Efficiency vs. Line Average")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/operator_efficiency.png")
    plt.close(fig)

    # 2. Leading downtime factors (Pareto-style)
    fig, ax = plt.subplots(figsize=(8, 5))
    factor_sorted = factor_df.sort_values("Total_Minutes", ascending=True)
    bar_colors = ["#d62728" if oe == "Yes" else "#1f77b4"
                  for oe in factor_sorted["Operator Error"]]
    ax.barh(factor_sorted["Description"], factor_sorted["Total_Minutes"], color=bar_colors)
    ax.set_xlabel("Total downtime minutes")
    ax.set_title("Downtime Minutes by Factor\n(red = operator-error factor)")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/downtime_by_factor.png")
    plt.close(fig)

    # 3. Operator error-type heatmap
    heat_data = error_pivot.drop(index="Total", errors="ignore").drop(columns="Total", errors="ignore")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.imshow(heat_data.values, cmap="Reds", aspect="auto")
    ax.set_xticks(range(len(heat_data.columns)))
    ax.set_xticklabels(heat_data.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(heat_data.index)))
    ax.set_yticklabels(heat_data.index)
    for i in range(heat_data.shape[0]):
        for j in range(heat_data.shape[1]):
            val = heat_data.values[i, j]
            if val > 0:
                ax.text(j, i, int(val), ha="center", va="center",
                        color="white" if val > heat_data.values.max() / 2 else "black",
                        fontsize=9)
    ax.set_title("Operator-Error Downtime Minutes by Operator & Error Type")
    fig.colorbar(im, ax=ax, label="Minutes")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/operator_error_heatmap.png")
    plt.close(fig)

    # 4. Downtime cause split: operator error vs other
    fig, ax = plt.subplots(figsize=(5, 5))
    error_total = factor_df.loc[factor_df["Operator Error"] == "Yes", "Total_Minutes"].sum()
    other_total = factor_df.loc[factor_df["Operator Error"] == "No", "Total_Minutes"].sum()
    ax.pie([error_total, other_total], labels=["Operator error", "Other causes"],
           autopct="%1.0f%%", colors=["#d62728", "#1f77b4"], startangle=90)
    ax.set_title("Share of Downtime: Operator Error vs. Other Causes")
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/downtime_error_share.png")
    plt.close(fig)


def main():
    ensure_dirs()

    line_productivity, products, downtime_factors, line_downtime = load_raw_tables(RAW_PATH)
    batch_df, downtime_long = build_batch_table(
        line_productivity, products, line_downtime, downtime_factors
    )

    overall_eff = overall_efficiency(batch_df)
    op_perf = operator_performance(batch_df)
    factor_df = downtime_by_factor(downtime_long)
    error_pivot = operator_error_breakdown(batch_df, downtime_long)

    # ---- Console summary ----
    print(f"Overall line efficiency: {overall_eff:.1%}")
    print("\nOperator performance:\n", op_perf)
    print("\nDowntime by factor:\n", factor_df)
    print("\nOperator error breakdown:\n", error_pivot)

    # ---- Save tables ----
    batch_df.to_csv(f"{TABLE_DIR}/batch_level_detail.csv", index=False)
    op_perf.to_csv(f"{TABLE_DIR}/operator_performance.csv", index=False)
    factor_df.to_csv(f"{TABLE_DIR}/downtime_by_factor.csv", index=False)
    error_pivot.to_csv(f"{TABLE_DIR}/operator_error_breakdown.csv")

    with open(f"{TABLE_DIR}/overall_efficiency.txt", "w") as f:
        f.write(f"Overall line efficiency: {overall_eff:.4f} ({overall_eff:.1%})\n")

    # ---- Save charts ----
    make_charts(batch_df, op_perf, factor_df, error_pivot, overall_eff)

    print(f"\nAll tables written to {TABLE_DIR}/, all charts written to {FIG_DIR}/")


if __name__ == "__main__":
    main()
