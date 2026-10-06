"""
Bloomberg Global Trading Challenge Quantitative Screener
Pulls live market, momentum, liquidity, and fundamental data from the local
Bloomberg Desktop API daemon (localhost:8194) and screens top candidates.
Exports results to Excel (.xlsx) and CSV.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("TradingChallengeScreener")

def get_universe_tickers():
    """Returns a diversified universe of highly liquid US Equities for the Trading Challenge."""
    return [
        # Mega-cap Tech & Communication
        "AAPL US Equity",
        "MSFT US Equity",
        "GOOGL US Equity",
        "AMZN US Equity",
        "META US Equity",
        # Semiconductors & AI Hardware
        "NVDA US Equity",
        "AVGO US Equity",
        "AMD US Equity",
        # Financials
        "JPM US Equity",
        "GS US Equity",
        "V US Equity",
        # Healthcare & Pharmaceuticals
        "LLY US Equity",
        "UNH US Equity",
        "JNJ US Equity",
        # Energy
        "XOM US Equity",
        "CVX US Equity",
        # Industrials & Aerospace
        "CAT US Equity",
        "GE US Equity",
        # Consumer & Retail
        "TSLA US Equity",
        "WMT US Equity",
        "COST US Equity",
    ]

def fetch_screener_data(tickers):
    """Fetch live market and fundamental data via xbbg."""
    from xbbg import blp

    fields = [
        "NAME",
        "GICS_SECTOR_NAME",
        "PX_LAST",
        "CHG_PCT_1D",
        "HIGH_52WEEK",
        "LOW_52WEEK",
        "VOLUME",
        "CUR_MKT_CAP",
        "PE_RATIO",
        "TRAIL_12M_EPS",
        "RETURN_COM_EQY",
        "DIVIDEND_INDICATED_YIELD",
    ]

    logger.info(f"Connecting to Bloomberg Desktop API (127.0.0.1:8194)...")
    logger.info(f"Requesting {len(fields)} fields for {len(tickers)} securities...")

    res = blp.bdp(tickers=tickers, flds=fields)

    # Convert to pandas
    if hasattr(res, "to_pandas"):
        raw_df = res.to_pandas()
    else:
        raw_df = pd.DataFrame(res)

    if set(["ticker", "field", "value"]).issubset(raw_df.columns):
        wide_df = raw_df.pivot(index="ticker", columns="field", values="value").reset_index()
    else:
        wide_df = raw_df.reset_index()

    return wide_df

def process_and_rank(df):
    """Calculate quantitative factors, screen eligibility, and rank candidates."""
    logger.info("Processing quantitative signals and challenge ranking...")

    # Convert numeric columns
    numeric_cols = [
        "PX_LAST", "CHG_PCT_1D", "HIGH_52WEEK", "LOW_52WEEK",
        "VOLUME", "CUR_MKT_CAP", "PE_RATIO", "TRAIL_12M_EPS",
        "RETURN_COM_EQY", "DIVIDEND_INDICATED_YIELD"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clean ticker symbol for display (e.g. 'AAPL US Equity' -> 'AAPL')
    df["SYMBOL"] = df["ticker"].apply(lambda x: x.split()[0] if isinstance(x, str) else x)

    # Calculate Distance from 52-Week High (%)
    # 0% = at 52-week high, -10% = 10% pullback
    if "HIGH_52WEEK" in df.columns and "PX_LAST" in df.columns:
        df["PCT_OFF_52W_HIGH"] = ((df["PX_LAST"] - df["HIGH_52WEEK"]) / df["HIGH_52WEEK"]) * 100

    # Calculate Distance from 52-Week Low (%)
    if "LOW_52WEEK" in df.columns and "PX_LAST" in df.columns:
        df["PCT_ABOVE_52W_LOW"] = ((df["PX_LAST"] - df["LOW_52WEEK"]) / df["LOW_52WEEK"]) * 100

    # Challenge Eligibility Filter:
    # 1. Price >= $10.00
    # 2. Market Cap >= $10 Billion ($1e10)
    # 3. Volume >= 500,000 shares
    df["ELIGIBLE"] = (
        (df["PX_LAST"] >= 10.0) &
        (df["CUR_MKT_CAP"] >= 10e9) &
        (df["VOLUME"] >= 500_000)
    )

    # Quantitative Composite Score (Z-Score approach):
    # Higher ROE is good (+)
    # Lower P/E ratio is favorable for valuation (+) [inverted]
    # Strong momentum (CHG_PCT_1D, proximity to high) (+)
    roe_z = (df["RETURN_COM_EQY"] - df["RETURN_COM_EQY"].mean()) / (df["RETURN_COM_EQY"].std() + 1e-6)
    mom_z = (df["CHG_PCT_1D"] - df["CHG_PCT_1D"].mean()) / (df["CHG_PCT_1D"].std() + 1e-6)
    pe_z = -((df["PE_RATIO"] - df["PE_RATIO"].median()) / (df["PE_RATIO"].std() + 1e-6))
    
    # Composite score
    df["SCORE"] = (0.45 * roe_z.fillna(0)) + (0.35 * mom_z.fillna(0)) + (0.20 * pe_z.fillna(0))
    df["RANK"] = df["SCORE"].rank(ascending=False, method="min").astype(int)

    # Sort by Rank
    df = df.sort_values(by="RANK").reset_index(drop=True)
    return df

def export_reports(df):
    """Export formatted results to Excel workbook and CSV."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "bloomberg_challenge_screener.xlsx")
    csv_path = os.path.join(script_dir, "bloomberg_challenge_screener.csv")

    # Column arrangement
    cols_order = [
        "RANK", "SYMBOL", "NAME", "GICS_SECTOR_NAME", "PX_LAST", "CHG_PCT_1D",
        "RETURN_COM_EQY", "PE_RATIO", "TRAIL_12M_EPS", "CUR_MKT_CAP", "VOLUME",
        "HIGH_52WEEK", "LOW_52WEEK", "PCT_OFF_52W_HIGH", "DIVIDEND_INDICATED_YIELD", "SCORE"
    ]
    present_cols = [c for c in cols_order if c in df.columns] + [c for c in df.columns if c not in cols_order]
    out_df = df[present_cols]

    # 1. Export CSV
    out_df.to_csv(csv_path, index=False)
    logger.info(f"Exported screener CSV: {csv_path}")

    # 2. Sector summary
    sector_summary = df.groupby("GICS_SECTOR_NAME").agg(
        Count=("SYMBOL", "count"),
        Avg_PX_LAST=("PX_LAST", "mean"),
        Avg_1D_Chg=("CHG_PCT_1D", "mean"),
        Avg_ROE=("RETURN_COM_EQY", "mean"),
        Avg_PE=("PE_RATIO", "mean"),
        Total_MktCap=("CUR_MKT_CAP", "sum"),
    ).reset_index().sort_values(by="Avg_ROE", ascending=False)

    # 3. Export Excel with OpenPyXL
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        out_df.to_excel(writer, sheet_name="Challenge Screener", index=False)
        out_df.head(10).to_excel(writer, sheet_name="Top 10 Picks", index=False)
        sector_summary.to_excel(writer, sheet_name="Sector Breakdown", index=False)

    logger.info(f"Exported screener Excel workbook: {excel_path}")
    return out_df, excel_path, csv_path

def main():
    logger.info("=" * 80)
    logger.info("BLOOMBERG GLOBAL TRADING CHALLENGE - CANDIDATE SCREENER")
    logger.info("=" * 80)

    universe = get_universe_tickers()
    raw_wide = fetch_screener_data(universe)
    screened_df = process_and_rank(raw_wide)
    final_df, excel_path, csv_path = export_reports(screened_df)

    # Display Top 10 Picks
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    display_cols = ["RANK", "SYMBOL", "NAME", "GICS_SECTOR_NAME", "PX_LAST", "CHG_PCT_1D", "RETURN_COM_EQY", "PE_RATIO", "CUR_MKT_CAP"]
    preview = final_df[[c for c in display_cols if c in final_df.columns]].head(10)

    print("\n" + "=" * 90)
    print("TOP 10 SCREENED CANDIDATES FOR BLOOMBERG GLOBAL TRADING CHALLENGE")
    print("=" * 90)
    print(preview.to_string(index=False))
    print("=" * 90 + "\n")

    logger.info("Screener pipeline finished successfully.")
    return final_df

if __name__ == "__main__":
    main()
