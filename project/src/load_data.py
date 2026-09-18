"""
load_data.py
------------
Loads the four raw tables out of Manufacturing_Line_Productivity.xlsx,
cleans them, and returns tidy pandas DataFrames.

Raw tables (per data_dictionary.csv):
    1. "Line productivity" -> one row per batch: Date, Product, Batch,
       Operator, Start Time, End Time
    2. "Products"          -> one row per product: Product, Flavor, Size,
       Min batch time (minutes, with zero downtime)
    3. "Downtime factors"  -> one row per downtime factor: Factor (ID),
       Description, Operator Error (Yes/No)
    4. "Line downtime"     -> wide table: one row per batch, one column per
       downtime factor ID, value = minutes lost to that factor on that batch
"""

import os
import datetime as dt
import pandas as pd

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(_PROJECT_ROOT, "data", "raw", "Manufacturing_Line_Productivity.xlsx")


def load_raw_tables(path: str = RAW_PATH):
    """Read all four sheets from the workbook."""
    xls = pd.ExcelFile(path)

    line_productivity = xls.parse("Line productivity")
    products = xls.parse("Products")
    downtime_factors = xls.parse("Downtime factors")
    # Row 0 of this sheet is a merged "Downtime factor" header spanning the
    # factor-ID columns, so the real column headers are on row index 1.
    line_downtime = xls.parse("Line downtime", header=1)

    return line_productivity, products, downtime_factors, line_downtime


def _time_to_minutes(value) -> float:
    """
    Normalize an Excel time-of-day cell to "minutes since local midnight".

    Excel (and openpyxl) represents most times as a plain datetime.time,
    but a time that crosses midnight when combined with the date serial
    (e.g. a batch that starts at 22:55 and ends at 01:05 the next day)
    comes back as a full datetime.datetime object one day past the epoch.
    We detect that case and add the extra day back in as +1440 minutes.
    """
    if isinstance(value, dt.datetime):
        epoch = dt.datetime(1899, 12, 31)  # Excel's day-0 reference date
        return (value - epoch).total_seconds() / 60.0
    # plain time-of-day
    return value.hour * 60 + value.minute + value.second / 60.0


def _batch_duration_minutes(row) -> float:
    """
    Compute batch duration in minutes from Start Time / End Time.

    One batch (422148) runs past midnight, 22:55 -> 01:05, which makes the
    naive End - Start negative. We normalize both timestamps to minutes
    since midnight first (see _time_to_minutes), then add a day (1440 min)
    to the end time whenever it is earlier than the start time.
    """
    start_min = _time_to_minutes(row["Start Time"])
    end_min = _time_to_minutes(row["End Time"])

    if end_min < start_min:
        end_min += 24 * 60

    return end_min - start_min


def build_batch_table(line_productivity: pd.DataFrame,
                       products: pd.DataFrame,
                       line_downtime: pd.DataFrame,
                       downtime_factors: pd.DataFrame) -> pd.DataFrame:
    """
    Build one clean, analysis-ready row-per-batch table containing:
      - actual duration (minutes)
      - the product's minimum (ideal) batch time
      - total downtime minutes (sum across all factors)
      - total operator-error downtime minutes
      - line efficiency for that batch (min time / actual time)
    """
    df = line_productivity.copy()
    df["Duration (min)"] = df.apply(_batch_duration_minutes, axis=1)

    # Attach each product's minimum batch time
    df = df.merge(products[["Product", "Flavor", "Size", "Min batch time"]],
                   on="Product", how="left")

    # Melt the wide downtime table (one column per factor ID) into long form:
    # Batch, Factor, Minutes
    factor_cols = [c for c in line_downtime.columns if c != "Batch"]
    downtime_long = line_downtime.melt(
        id_vars="Batch", value_vars=factor_cols,
        var_name="Factor", value_name="Minutes"
    ).dropna(subset=["Minutes"])
    downtime_long["Factor"] = downtime_long["Factor"].astype(int)

    # Tag each downtime row with its factor description + operator-error flag
    downtime_long = downtime_long.merge(downtime_factors, on="Factor", how="left")

    # Total downtime minutes per batch
    total_downtime = downtime_long.groupby("Batch")["Minutes"].sum().rename("Downtime (min)")
    df = df.merge(total_downtime, on="Batch", how="left")
    df["Downtime (min)"] = df["Downtime (min)"].fillna(0.0)

    # Operator-error-only downtime minutes per batch
    error_downtime = (
        downtime_long[downtime_long["Operator Error"] == "Yes"]
        .groupby("Batch")["Minutes"].sum()
        .rename("Operator Error Downtime (min)")
    )
    df = df.merge(error_downtime, on="Batch", how="left")
    df["Operator Error Downtime (min)"] = df["Operator Error Downtime (min)"].fillna(0.0)

    # Per-batch efficiency
    df["Efficiency"] = df["Min batch time"] / df["Duration (min)"]

    return df, downtime_long


if __name__ == "__main__":
    lp, prod, factors, dtown = load_raw_tables()
    batch_df, downtime_long = build_batch_table(lp, prod, dtown, factors)
    print(batch_df.head())
    print("\nRows:", len(batch_df))
