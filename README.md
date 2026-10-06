# Bloomberg Market Data & Quantitative Automation Pipeline

This workspace provides an automated Python environment configured to interface with the local Bloomberg Desktop API (`bbcomm.exe`) without requiring administrative rights.

## System & Infrastructure Overview

- **Bloomberg Daemon (`bbcomm.exe`)**: `c:\blp\DAPI\bbcomm.exe` listening on `127.0.0.1:8194`
- **Core C/C++ BLPAPI Libraries**: `C:\blp\DAPI\blpapi3_64.dll`
- **Python Environment**: Standalone CPython 3.11.17 installed in user space:
  - Interpreter: `C:\Users\e3402020\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe`
  - Shims: `pip.cmd` & `pip.ps1` configured in `C:\Users\e3402020\.local\bin`
  - User PATH: Updated to prioritize standalone Python ahead of Windows Store app execution aliases.

## Installed Packages
- `blpapi` (3.26.9.1) - Official Bloomberg Python SDK from `https://blpapi.bloomberg.com/repository/releases/python/simple/`
- `xbbg` (1.5.0) - Fast Bloomberg API wrapper for pandas/dataframes
- `pandas` (3.0.6) & `numpy` (2.4.6) - Data manipulation and analysis

## Project Files
- `bloomberg_fetch.py`: Main quantitative pipeline script. Verifies low-level `blpapi` session handshake, queries live market/fundamental data for US Equities basket via `xbbg`, structures output into a pandas DataFrame, and exports to CSV.
- `trading_challenge_screener.py`: Bloomberg Global Trading Challenge multi-factor equity screener. Connects to `127.0.0.1:8194`, screens a 21-stock institutional universe across sectors, calculates ROE quality, momentum, valuation Z-scores, and distance from 52-week extremes. Exports to Excel workbook (`bloomberg_challenge_screener.xlsx`) and CSV.
- `run_fetch.bat`: Windows batch runner to launch the script directly.
- `us_equities_market_data_latest.csv`: Pivoted matrix of live market prices, volumes, market caps, P/E ratios, and dividend yields.
- `us_equities_raw_tidy_latest.csv`: Tidy long-format export (`ticker`, `field`, `value`).
- `bloomberg_challenge_screener.xlsx`: Multi-tab Excel report (Top Picks, Full Universe, Sector Breakdown).

## Execution
Run from PowerShell or Command Prompt:
```powershell
python bloomberg_fetch.py
```
Or execute the batch file:
```cmd
run_fetch.bat
```
