"""
Bloomberg Market Data Automation Script
Connects to local bbcomm daemon (127.0.0.1:8194), verifies blpapi & xbbg,
fetches live reference and fundamental data for a basket of US Equities,
and exports the dataset to CSV.
"""

import sys
import os
import logging
from datetime import datetime
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("BloombergAutomation")

def test_blpapi_direct():
    """Verify raw Bloomberg BLPAPI session connection to localhost:8194."""
    logger.info("Step 1: Testing direct blpapi connection to 127.0.0.1:8194...")
    import blpapi

    session_options = blpapi.SessionOptions()
    session_options.setServerHost("127.0.0.1")
    session_options.setServerPort(8194)

    session = blpapi.Session(session_options)
    if not session.start():
        raise ConnectionError("Failed to start Bloomberg blpapi session. Check bbcomm.exe status.")

    if not session.openService("//blp/refdata"):
        session.stop()
        raise ConnectionError("Failed to open Bloomberg service //blp/refdata.")

    logger.info("blpapi session established and //blp/refdata service successfully opened.")

    # Send a quick probe request
    ref_service = session.getService("//blp/refdata")
    request = ref_service.createRequest("ReferenceDataRequest")
    request.append("securities", "SPY US Equity")
    request.append("fields", "PX_LAST")
    request.append("fields", "NAME")

    session.sendRequest(request)
    
    spy_probe = {}
    end_of_stream = False
    while not end_of_stream:
        event = session.nextEvent(5000)
        for msg in event:
            if msg.hasElement("securityData"):
                sec_data_array = msg.getElement("securityData")
                for i in range(sec_data_array.numValues()):
                    sec_data = sec_data_array.getValueAsElement(i)
                    field_data = sec_data.getElement("fieldData")
                    for f in range(field_data.numElements()):
                        elem = field_data.getElement(f)
                        spy_probe[str(elem.name())] = elem.getValue()
        if event.eventType() == blpapi.Event.RESPONSE:
            end_of_stream = True

    session.stop()
    logger.info(f"Direct blpapi probe result: SPY US Equity -> {spy_probe}")
    return spy_probe


def fetch_equity_basket():
    """Fetch live market and fundamental data for a basket of US Equities via xbbg/pandas."""
    logger.info("Step 2: Fetching live equity basket via xbbg...")
    from xbbg import blp

    tickers = [
        "AAPL US Equity",
        "MSFT US Equity",
        "NVDA US Equity",
        "GOOGL US Equity",
        "AMZN US Equity",
        "META US Equity",
        "TSLA US Equity",
        "JPM US Equity",
    ]

    fields = [
        "NAME",
        "PX_LAST",
        "CHG_PCT_1D",
        "VOLUME",
        "HIGH",
        "LOW",
        "CUR_MKT_CAP",
        "PE_RATIO",
        "TRAIL_12M_EPS",
        "DIVIDEND_INDICATED_YIELD",
    ]

    logger.info(f"Requesting {len(fields)} fields for {len(tickers)} securities...")
    res = blp.bdp(tickers=tickers, flds=fields)

    # Convert to pandas DataFrame (supports both narwhals/polars and native pandas)
    if hasattr(res, "to_pandas"):
        raw_df = res.to_pandas()
    else:
        raw_df = pd.DataFrame(res)

    logger.info(f"Received raw data shape: {raw_df.shape}")

    # If xbbg returns long format (ticker, field, value), pivot to wide matrix
    if set(["ticker", "field", "value"]).issubset(raw_df.columns):
        wide_df = raw_df.pivot(index="ticker", columns="field", values="value").reset_index()
    else:
        wide_df = raw_df.reset_index()

    # Reorder columns logically if present
    desired_order = ["ticker", "NAME", "PX_LAST", "CHG_PCT_1D", "HIGH", "LOW", "VOLUME", "CUR_MKT_CAP", "PE_RATIO", "TRAIL_12M_EPS", "DIVIDEND_INDICATED_YIELD"]
    available_cols = [c for c in desired_order if c in wide_df.columns] + [c for c in wide_df.columns if c not in desired_order]
    wide_df = wide_df[available_cols]

    return wide_df, raw_df


def main():
    logger.info("=" * 70)
    logger.info("BLOOMBERG TERMINAL AUTOMATION & QUANT PIPELINE")
    logger.info("=" * 70)

    # 1. Native API verification
    test_blpapi_direct()

    # 2. Market & Fundamental data fetch
    wide_df, raw_df = fetch_equity_basket()

    # 3. Formatted display
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    print("\n" + "=" * 90)
    print("LIVE US EQUITIES MARKET & FUNDAMENTAL MATRIX")
    print("=" * 90)
    print(wide_df.to_string(index=False))
    print("=" * 90 + "\n")

    # 4. Export to CSV files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wide_csv_ts = os.path.join(script_dir, f"us_equities_market_data_{ts}.csv")
    wide_csv_latest = os.path.join(script_dir, "us_equities_market_data_latest.csv")
    raw_csv_latest = os.path.join(script_dir, "us_equities_raw_tidy_latest.csv")

    wide_df.to_csv(wide_csv_ts, index=False)
    wide_df.to_csv(wide_csv_latest, index=False)
    raw_df.to_csv(raw_csv_latest, index=False)

    logger.info("Data export completed successfully:")
    logger.info(f"  [Matrix CSV] -> {wide_csv_latest}")
    logger.info(f"  [Tidy CSV]   -> {raw_csv_latest}")
    logger.info(f"  [Snapshot]   -> {wide_csv_ts}")

    return wide_df

if __name__ == "__main__":
    main()
