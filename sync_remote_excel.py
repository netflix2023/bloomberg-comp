"""
Bloomberg Live Remote Excel Dashboard & Sync Engine
Pulls live market, catalyst, and fundamental data from local Bloomberg daemon (localhost:8194)
and generates a standalone, institutional-grade Excel workbook (bloomberg_live_remote_dashboard.xlsx)
that team members can open and use on any machine without needing Bloomberg installed.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("RemoteExcelSync")

def get_screener_tickers():
    """Curated universe of 24 large/mid-cap equities across uncorrelated sectors."""
    return [
        # AI Infrastructure & Mega Tech
        "NVDA US Equity",
        "AVGO US Equity",
        "AAPL US Equity",
        "MSFT US Equity",
        "GOOGL US Equity",
        "AMZN US Equity",
        "META US Equity",
        "AMD US Equity",
        # Healthcare & Pharmaceuticals
        "LLY US Equity",
        "UNH US Equity",
        "JNJ US Equity",
        "ABBV US Equity",
        # Financials & Payment Infrastructure
        "JPM US Equity",
        "GS US Equity",
        "V US Equity",
        "MA US Equity",
        # Industrials & Defense
        "CAT US Equity",
        "GE US Equity",
        "LMT US Equity",
        "RTX US Equity",
        # Energy & Materials
        "XOM US Equity",
        "CVX US Equity",
        # Consumer & Cyclicals
        "TSLA US Equity",
        "WMT US Equity",
        "COST US Equity",
    ]

def fetch_bloomberg_data(tickers):
    """Fetch live market, analyst estimates, earnings, and fundamentals via xbbg."""
    logger.info("Connecting to Bloomberg Desktop API at 127.0.0.1:8194...")
    from xbbg import blp

    fields = [
        "NAME",
        "GICS_SECTOR_NAME",
        "PX_LAST",
        "CHG_PCT_1D",
        "CHG_PCT_5D",
        "BEST_TARGET_PRICE",
        "TOT_BUY_REC",
        "TOT_HOLD_REC",
        "TOT_SELL_REC",
        "RETURN_COM_EQY",
        "PE_RATIO",
        "CUR_MKT_CAP",
        "VOLUME",
        "HIGH_52WEEK",
        "LOW_52WEEK",
        "EXPECTED_REPORT_DT",
    ]

    res = blp.bdp(tickers=tickers, flds=fields)
    raw_df = res.to_pandas() if hasattr(res, "to_pandas") else pd.DataFrame(res)

    if set(["ticker", "field", "value"]).issubset(raw_df.columns):
        wide_df = raw_df.pivot(index="ticker", columns="field", values="value").reset_index()
    else:
        wide_df = raw_df.reset_index()

    # Convert numeric fields
    numeric_flds = [
        "PX_LAST", "CHG_PCT_1D", "CHG_PCT_5D", "BEST_TARGET_PRICE",
        "TOT_BUY_REC", "TOT_HOLD_REC", "TOT_SELL_REC",
        "RETURN_COM_EQY", "PE_RATIO", "CUR_MKT_CAP", "VOLUME",
        "HIGH_52WEEK", "LOW_52WEEK"
    ]
    for col in numeric_flds:
        if col in wide_df.columns:
            wide_df[col] = pd.to_numeric(wide_df[col], errors="coerce")

    # Format ticker and symbol
    wide_df["SYMBOL"] = wide_df["ticker"].apply(lambda x: x.split()[0] if isinstance(x, str) else x)

    return wide_df

def build_excel_workbook(df, output_path):
    """Build a styled, multi-tab Excel workbook with formulas and baked terminal values."""
    logger.info(f"Generating institutional Excel workbook at {output_path}...")
    wb = openpyxl.Workbook()

    # Define Styles
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1B365D")
    subtitle_font = Font(name="Calibri", size=10, italic=True, color="555555")
    bold_font = Font(name="Calibri", size=10, bold=True)
    regular_font = Font(name="Calibri", size=10)
    
    navy_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    accent_blue_fill = PatternFill(start_color="2A52BE", end_color="2A52BE", fill_type="solid")
    light_blue_fill = PatternFill(start_color="E6F0FA", end_color="E6F0FA", fill_type="solid")
    light_gray_fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
    green_fill = PatternFill(start_color="E2F0D9", end_color="E2F0D9", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC")
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # =========================================================================
    # SHEET 1: Executive Summary & Rules (Dallas College Playbook)
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Competition Rules & Strategy"
    ws1.views.sheetView[0].showGridLines = True

    ws1["A1"] = "BLOOMBERG GLOBAL TRADING CHALLENGE — DALLAS COLLEGE"
    ws1["A1"].font = title_font
    ws1["A2"] = f"Strategy Playbook & Mathematical Risk Framework | Synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws1["A2"].font = subtitle_font

    ws1["A4"] = "1. OFFICIAL COMPETITION RULES & CONSTRAINTS"
    ws1["A4"].font = Font(name="Calibri", size=11, bold=True, color="1B365D")

    rules = [
        ("Asset Class", "Long-Only Equities", "Strictly no options, no shorting, no leverage."),
        ("Benchmark Universe", "World Large/Mid Cap Index (WLS Index)", "Must be index constituents; no penny stocks."),
        ("Position Sizing Limit", "Maximum 20% of Portfolio Value at Entry", "Limits catastrophic drawdown from single earnings miss."),
        ("Minimum Security Price", "> $5.00 per share", "Guarantees liquidity and realistic fill simulation."),
        ("Capital Recycling", "Active Rebalancing Allowed", "Take profits on catalyst peaks and redeploy into next 20% clip."),
    ]
    
    ws1.append(["Rule Name", "Constraint", "Strategic Playbook Directive"])
    rule_hdr_row = 5
    for col_idx in range(1, 4):
        cell = ws1.cell(row=rule_hdr_row, column=col_idx)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = align_left

    current_row = 6
    for r in rules:
        ws1.append(list(r))
        for col_idx in range(1, 4):
            cell = ws1.cell(row=current_row, column=col_idx)
            cell.font = regular_font
            cell.border = thin_border
            if current_row % 2 == 0:
                cell.fill = light_blue_fill
        current_row += 1

    current_row += 1
    ws1.cell(row=current_row, column=1, value="2. MATHEMATICAL REALITY: STOCK PREDICTION VS. RISK/REWARD RATIO").font = Font(name="Calibri", size=11, bold=True, color="1B365D")
    current_row += 1

    math_headers = ["Strategy Scenario", "Win Rate", "Wins (of 10)", "Avg Win ($)", "Losses (of 10)", "Avg Loss ($)", "Total Wins ($)", "Total Losses ($)", "Net Profit/Loss ($)"]
    ws1.append(math_headers)
    math_hdr_row = current_row
    for col_idx in range(1, len(math_headers) + 1):
        cell = ws1.cell(row=math_hdr_row, column=col_idx)
        cell.font = header_font
        cell.fill = accent_blue_fill
        cell.alignment = align_center

    current_row += 1
    # Scenario A
    ws1.append(["Scenario A: High Prediction, Poor Risk", 0.80, 8, 100, 2, 600, "=C14*D14", "=E14*F14", "=G14-H14"])
    # Scenario B
    ws1.append(["Scenario B: Low Prediction, Asymmetric 3:1 R/R", 0.40, 4, 300, 6, 100, "=C15*D15", "=E15*F15", "=G15-H15"])

    for r_idx in [current_row, current_row + 1]:
        for c_idx in range(1, len(math_headers) + 1):
            cell = ws1.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            cell.font = regular_font
            if c_idx == 2:
                cell.number_format = "0.0%"
            elif c_idx in [4, 6, 7, 8, 9]:
                cell.number_format = "$#,##0"
            if c_idx == 9:
                cell.font = bold_font
                if r_idx == current_row:
                    cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid") # Red tint
                else:
                    cell.fill = green_fill # Green tint
        current_row += 1

    # =========================================================================
    # SHEET 2: Live Remote Screener (Baked Bloomberg Values + Live Formulas)
    # =========================================================================
    ws2 = wb.create_sheet(title="Remote Live Screener")
    ws2.views.sheetView[0].showGridLines = True

    ws2["A1"] = "LIVE CANDIDATE SCREENER — REMOTE ACCESSIBLE"
    ws2["A1"].font = title_font
    ws2["A2"] = "Terminal data baked as values; dynamic Excel formulas compute Target Upside, Stop Losses, and Asymmetric Risk/Reward."
    ws2["A2"].font = subtitle_font

    headers_ws2 = [
        "SYMBOL", "NAME", "SECTOR", "LAST PRICE", "1D CHG %", "5D CHG %",
        "WALL ST TARGET", "TARGET UPSIDE %", "7% STOP LOSS", "$ RISK/SH", "$ REWARD/SH",
        "RISK/REWARD RATIO", "SIGNAL", "BUY RECS", "HOLD RECS", "SELL RECS", "BUY %",
        "ROE %", "P/E RATIO", "MARKET CAP", "VOLUME", "EARNINGS DATE"
    ]
    
    start_row = 4
    for col_idx, h in enumerate(headers_ws2, 1):
        cell = ws2.cell(row=start_row, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = align_center

    # Sort DataFrame by market cap or target upside if possible
    df_sorted = df.copy()
    if "BEST_TARGET_PRICE" in df_sorted.columns and "PX_LAST" in df_sorted.columns:
        df_sorted["PRELIM_UPSIDE"] = (df_sorted["BEST_TARGET_PRICE"] - df_sorted["PX_LAST"]) / df_sorted["PX_LAST"]
        df_sorted = df_sorted.sort_values(by="PRELIM_UPSIDE", ascending=False).reset_index(drop=True)

    row_cursor = start_row + 1
    for _, row in df_sorted.iterrows():
        symbol = str(row.get("SYMBOL", ""))
        name = str(row.get("NAME", ""))
        sector = str(row.get("GICS_SECTOR_NAME", ""))
        px_last = float(row["PX_LAST"]) if pd.notnull(row.get("PX_LAST")) else 0.0
        chg_1d = (float(row["CHG_PCT_1D"]) / 100.0) if pd.notnull(row.get("CHG_PCT_1D")) else 0.0
        chg_5d = (float(row["CHG_PCT_5D"]) / 100.0) if pd.notnull(row.get("CHG_PCT_5D")) else 0.0
        target = float(row["BEST_TARGET_PRICE"]) if pd.notnull(row.get("BEST_TARGET_PRICE")) else px_last * 1.15
        buy_rec = int(row["TOT_BUY_REC"]) if pd.notnull(row.get("TOT_BUY_REC")) else 0
        hold_rec = int(row["TOT_HOLD_REC"]) if pd.notnull(row.get("TOT_HOLD_REC")) else 0
        sell_rec = int(row["TOT_SELL_REC"]) if pd.notnull(row.get("TOT_SELL_REC")) else 0
        roe = float(row["RETURN_COM_EQY"]) if pd.notnull(row.get("RETURN_COM_EQY")) else 0.0
        pe = float(row["PE_RATIO"]) if pd.notnull(row.get("PE_RATIO")) else 0.0
        mkt_cap = float(row["CUR_MKT_CAP"]) if pd.notnull(row.get("CUR_MKT_CAP")) else 0.0
        vol = float(row["VOLUME"]) if pd.notnull(row.get("VOLUME")) else 0.0
        earn_dt = str(row.get("EXPECTED_REPORT_DT", "")) if pd.notnull(row.get("EXPECTED_REPORT_DT")) else "TBD"

        # Formulated cells:
        # Col D = Last Price, Col G = Target Price
        # Col H (Upside %) = (G - D) / D
        upside_formula = f"=(G{row_cursor}-D{row_cursor})/D{row_cursor}"
        # Col I (7% Stop Loss) = D * 0.93
        stop_formula = f"=D{row_cursor}*0.93"
        # Col J ($ Risk) = D - I
        risk_formula = f"=D{row_cursor}-I{row_cursor}"
        # Col K ($ Reward) = G - D
        reward_formula = f"=G{row_cursor}-D{row_cursor}"
        # Col L (R:R Ratio) = K / J
        rr_formula = f"=IF(J{row_cursor}>0, K{row_cursor}/J{row_cursor}, 0)"
        # Col M (Signal) = IF(L >= 3.0, "STRONG BUY (3:1+)", IF(L >= 2.0, "QUALIFIED (2:1+)", "MONITOR"))
        signal_formula = f'=IF(L{row_cursor}>=3.0, "STRONG BUY (3:1+)", IF(L{row_cursor}>=2.0, "QUALIFIED (2:1+)", "MONITOR"))'
        # Col Q (Buy %) = N / (N + O + P)
        buy_pct_formula = f"=IF((N{row_cursor}+O{row_cursor}+P{row_cursor})>0, N{row_cursor}/(N{row_cursor}+O{row_cursor}+P{row_cursor}), 0)"

        data_row = [
            symbol, name, sector, px_last, chg_1d, chg_5d,
            target, upside_formula, stop_formula, risk_formula, reward_formula,
            rr_formula, signal_formula, buy_rec, hold_rec, sell_rec, buy_pct_formula,
            roe, pe, mkt_cap, vol, earn_dt
        ]
        ws2.append(data_row)

        # Apply formatting
        for col_idx in range(1, len(headers_ws2) + 1):
            cell = ws2.cell(row=row_cursor, column=col_idx)
            cell.border = thin_border
            cell.font = regular_font

            # Alignments & Formats
            if col_idx in [1, 2, 3]:
                cell.alignment = align_left
            elif col_idx in [4, 7, 9, 10, 11]:
                cell.alignment = align_right
                cell.number_format = "$#,##0.00"
            elif col_idx in [5, 6, 8, 17]:
                cell.alignment = align_right
                cell.number_format = "0.0%"
            elif col_idx in [12]:
                cell.alignment = align_right
                cell.number_format = '0.0":1"'
                cell.font = bold_font
            elif col_idx in [13]:
                cell.alignment = align_center
                cell.font = bold_font
            elif col_idx in [14, 15, 16]:
                cell.alignment = align_right
                cell.number_format = "#,##0"
            elif col_idx in [18]: # ROE
                cell.alignment = align_right
                cell.number_format = '0.0"%"'
            elif col_idx in [19]: # PE
                cell.alignment = align_right
                cell.number_format = "0.0"
            elif col_idx in [20]: # Market Cap
                cell.alignment = align_right
                cell.number_format = "$#,##0"
            elif col_idx in [21]: # Volume
                cell.alignment = align_right
                cell.number_format = "#,##0"
            elif col_idx in [22]: # Earnings Date
                cell.alignment = align_center

        row_cursor += 1

    # =========================================================================
    # SHEET 3: 20% Portfolio Calculator & Position Sizer
    # =========================================================================
    ws3 = wb.create_sheet(title="20pct Portfolio Sizer")
    ws3.views.sheetView[0].showGridLines = True

    ws3["A1"] = "DALLAS COLLEGE 20% POSITION SIZING & COMPOUNDING CALCULATOR"
    ws3["A1"].font = title_font
    ws3["A2"] = "Enforces the mandatory 20% portfolio entry limit. Change the Total Portfolio Cash below to recalculate all sizing clips."
    ws3["A2"].font = subtitle_font

    ws3["A4"] = "TOTAL PORTFOLIO CASH ($):"
    ws3["A4"].font = bold_font
    ws3["B4"] = 1000000.0  # Starting competition cash
    ws3["B4"].font = Font(name="Calibri", size=12, bold=True, color="1B365D")
    ws3["B4"].number_format = "$#,##0.00"
    ws3["B4"].fill = yellow_fill

    ws3["A5"] = "MAX 20% ALLOCATION CEILING:"
    ws3["A5"].font = bold_font
    ws3["B5"] = "=B4*0.20"
    ws3["B5"].font = Font(name="Calibri", size=12, bold=True, color="C00000")
    ws3["B5"].number_format = "$#,##0.00"

    ws3["A6"] = "PORTFOLIO RISK BUDGET (2% MAX):"
    ws3["A6"].font = bold_font
    ws3["B6"] = "=B4*0.02"
    ws3["B6"].number_format = "$#,##0.00"

    # Position Table
    pos_headers = [
        "SLOT #", "TICKER", "ENTRY PRICE", "TARGET PRICE", "STOP LOSS PRICE",
        "ALLOCATED $ (20% MAX)", "SHARES TO BUY", "ACTUAL POSITION $",
        "PORTFOLIO WEIGHT %", "MAX RISK $ (7% STOP)", "TARGET PROFIT $",
        "REBALANCED CASH BALANCE"
    ]
    pos_start_row = 8
    for col_idx, h in enumerate(pos_headers, 1):
        cell = ws3.cell(row=pos_start_row, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = align_center

    # 5 Allocation Slots (5 x 20% = 100% capacity)
    default_candidates = [
        ("NVDA", "='Remote Live Screener'!D5", "='Remote Live Screener'!G5", "='Remote Live Screener'!I5"),
        ("AVGO", "='Remote Live Screener'!D6", "='Remote Live Screener'!G6", "='Remote Live Screener'!I6"),
        ("LLY",  "='Remote Live Screener'!D7", "='Remote Live Screener'!G7", "='Remote Live Screener'!I7"),
        ("CAT",  "='Remote Live Screener'!D8", "='Remote Live Screener'!G8", "='Remote Live Screener'!I8"),
        ("AMZN", "='Remote Live Screener'!D9", "='Remote Live Screener'!G9", "='Remote Live Screener'!I9"),
    ]

    p_row = pos_start_row + 1
    for slot_idx, (sym, p_entry, p_tgt, p_stop) in enumerate(default_candidates, 1):
        # Col F: Allocated $ = $B$5
        # Col G: Shares = INT(F / Entry Price)
        # Col H: Actual Position $ = Shares * Entry Price
        # Col I: Weight % = Actual $ / Total Cash
        # Col J: Max Risk $ = Shares * (Entry - Stop)
        # Col K: Target Profit $ = Shares * (Target - Entry)
        # Col L: Rebalanced Balance = Previous + Profit
        ws3.cell(row=p_row, column=1, value=f"Position {slot_idx}").alignment = align_center
        ws3.cell(row=p_row, column=2, value=sym).alignment = align_center
        ws3.cell(row=p_row, column=3, value=p_entry).number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=4, value=p_tgt).number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=5, value=p_stop).number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=6, value="=$B$5").number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=7, value=f"=INT(F{p_row}/C{p_row})").number_format = "#,##0"
        ws3.cell(row=p_row, column=8, value=f"=G{p_row}*C{p_row}").number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=9, value=f"=H{p_row}/$B$4").number_format = "0.0%"
        ws3.cell(row=p_row, column=10, value=f"=G{p_row}*(C{p_row}-E{p_row})").number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=11, value=f"=G{p_row}*(D{p_row}-C{p_row})").number_format = "$#,##0.00"
        ws3.cell(row=p_row, column=12, value=f"=$B$4+K{p_row}").number_format = "$#,##0.00"

        for c_idx in range(1, len(pos_headers) + 1):
            cell = ws3.cell(row=p_row, column=c_idx)
            cell.border = thin_border
            cell.font = regular_font
        p_row += 1

    # Totals Row
    ws3.cell(row=p_row, column=1, value="TOTAL ALLOCATED").font = bold_font
    ws3.cell(row=p_row, column=8, value=f"=SUM(H{pos_start_row+1}:H{p_row-1})").number_format = "$#,##0.00"
    ws3.cell(row=p_row, column=9, value=f"=SUM(I{pos_start_row+1}:I{p_row-1})").number_format = "0.0%"
    ws3.cell(row=p_row, column=10, value=f"=SUM(J{pos_start_row+1}:J{p_row-1})").number_format = "$#,##0.00"
    ws3.cell(row=p_row, column=11, value=f"=SUM(K{pos_start_row+1}:K{p_row-1})").number_format = "$#,##0.00"
    for c_idx in range(1, len(pos_headers) + 1):
        cell = ws3.cell(row=p_row, column=c_idx)
        cell.font = bold_font
        cell.fill = light_gray_fill

    # =========================================================================
    # SHEET 4: Catalyst & Earnings Calendar
    # =========================================================================
    ws4 = wb.create_sheet(title="Earnings Catalyst Calendar")
    ws4.views.sheetView[0].showGridLines = True

    ws4["A1"] = "UPCOMING EARNINGS & CATALYST PIPELINE"
    ws4["A1"].font = title_font
    ws4["A2"] = "Tracks stocks approaching earnings catalyst windows for rapid pre-announcement momentum and post-catalyst compounding."
    ws4["A2"].font = subtitle_font

    cat_headers = ["SYMBOL", "COMPANY NAME", "SECTOR", "LAST PRICE", "EXPECTED EARNINGS DATE", "CONSENSUS TARGET", "UPSIDE %", "WALL ST BUY %", "PLAYBOOK CATALYST STATUS"]
    cat_start = 4
    for c_idx, h in enumerate(cat_headers, 1):
        cell = ws4.cell(row=cat_start, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = align_center

    # Sort by earnings date
    df_earn = df.copy()
    if "EXPECTED_REPORT_DT" in df_earn.columns:
        df_earn = df_earn.sort_values(by="EXPECTED_REPORT_DT").reset_index(drop=True)

    c_row = cat_start + 1
    for _, r in df_earn.iterrows():
        sym = str(r.get("SYMBOL", ""))
        nm = str(r.get("NAME", ""))
        sec = str(r.get("GICS_SECTOR_NAME", ""))
        px = float(r["PX_LAST"]) if pd.notnull(r.get("PX_LAST")) else 0.0
        tgt = float(r["BEST_TARGET_PRICE"]) if pd.notnull(r.get("BEST_TARGET_PRICE")) else px * 1.15
        dt = str(r.get("EXPECTED_REPORT_DT", "")) if pd.notnull(r.get("EXPECTED_REPORT_DT")) else "TBD"
        b_rec = int(r["TOT_BUY_REC"]) if pd.notnull(r.get("TOT_BUY_REC")) else 0
        h_rec = int(r["TOT_HOLD_REC"]) if pd.notnull(r.get("TOT_HOLD_REC")) else 0
        s_rec = int(r["TOT_SELL_REC"]) if pd.notnull(r.get("TOT_SELL_REC")) else 0
        tot_rec = b_rec + h_rec + s_rec
        b_pct = (b_rec / tot_rec) if tot_rec > 0 else 0.0

        up_formula = f"=(F{c_row}-D{c_row})/D{c_row}"
        status_formula = f'=IF(G{c_row}>=0.25, "HIGH CONVICTION CATALYST", IF(G{c_row}>=0.10, "MONITORING CATALYST", "SECONDARY"))'

        ws4.append([sym, nm, sec, px, dt, tgt, up_formula, b_pct, status_formula])
        for c_idx in range(1, len(cat_headers) + 1):
            cell = ws4.cell(row=c_row, column=c_idx)
            cell.border = thin_border
            cell.font = regular_font
            if c_idx in [1, 2, 3]:
                cell.alignment = align_left
            elif c_idx in [4, 6]:
                cell.alignment = align_right
                cell.number_format = "$#,##0.00"
            elif c_idx == 5:
                cell.alignment = align_center
            elif c_idx in [7, 8]:
                cell.alignment = align_right
                cell.number_format = "0.0%"
            elif c_idx == 9:
                cell.alignment = align_center
                cell.font = bold_font
        c_row += 1

    # Auto-adjust column widths across all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if val.startswith("="):
                    val = "FormulaValue"
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output_path)
    logger.info(f"Successfully saved remote Excel workbook: {output_path}")

def main():
    logger.info("=" * 80)
    logger.info("STARTING BLOOMBERG LIVE REMOTE EXCEL SYNC ENGINE")
    logger.info("=" * 80)

    tickers = get_screener_tickers()
    df = fetch_bloomberg_data(tickers)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    xlsx_path = os.path.join(script_dir, "bloomberg_live_remote_dashboard.xlsx")
    csv_path = os.path.join(script_dir, "bloomberg_live_remote_screener.csv")

    # Export CSV backup
    df.to_csv(csv_path, index=False)
    logger.info(f"Exported raw screener data to CSV: {csv_path}")

    # Build Excel Workbook
    build_excel_workbook(df, xlsx_path)

    print("\n" + "=" * 90)
    print("BLOOMBERG REMOTE EXCEL DASHBOARD READY!")
    print(f"File location: {xlsx_path}")
    print("=" * 90 + "\n")
    return xlsx_path

if __name__ == "__main__":
    main()
