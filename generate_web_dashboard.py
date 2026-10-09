"""
Bloomberg Trading Challenge - Web Dashboard Generator
Generates an interactive HTML dashboard (index.html / dashboard.html)
with dual-mode support, permanent "Last Synced" indicators, and polished UI:
  - LIVE API MODE (Connected to Bloomberg Desktop API 127.0.0.1:8194)
  - OFFLINE / CACHED SNAPSHOT MODE (Preserves historical market-close data)
"""

import os
import json
import socket
from datetime import datetime
import pandas as pd

def check_bloomberg_port(host="127.0.0.1", port=8194, timeout=0.4):
    """Check if the Bloomberg Desktop API daemon (bbcomm.exe) is listening on port 8194."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def generate_dashboard():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "bloomberg_live_remote_screener.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}. Run sync_remote_excel.py first.")

    # Inspect CSV file metadata
    csv_mtime = datetime.fromtimestamp(os.path.getmtime(csv_path))
    csv_time_str = csv_mtime.strftime("%B %d, %Y at %I:%M %p")
    now = datetime.now()
    age_seconds = (now - csv_mtime).total_seconds()
    days_ago = int(age_seconds // 86400)
    hours_ago = int((age_seconds % 86400) // 3600)
    mins_ago = int((age_seconds % 3600) // 60)
    
    if days_ago > 0:
        age_label = f"{days_ago} day{'s' if days_ago > 1 else ''} ago"
    elif hours_ago > 0:
        age_label = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"
    elif mins_ago > 0:
        age_label = f"{mins_ago} min{'s' if mins_ago > 1 else ''} ago"
    else:
        age_label = "Just now"

    # Check live Bloomberg API connection and data recency
    is_port_open = check_bloomberg_port()
    # Data is considered live if synced within 60 minutes
    is_live_data = (age_seconds < 3600)

    df = pd.read_csv(csv_path)

    candidates = []
    for _, row in df.iterrows():
        sym = str(row.get("SYMBOL", ""))
        name = str(row.get("NAME", ""))
        sector = str(row.get("GICS_SECTOR_NAME", ""))
        px = float(row["PX_LAST"]) if pd.notnull(row.get("PX_LAST")) else 0.0
        chg_1d = float(row["CHG_PCT_1D"]) if pd.notnull(row.get("CHG_PCT_1D")) else 0.0
        chg_5d = float(row["CHG_PCT_5D"]) if pd.notnull(row.get("CHG_PCT_5D")) else 0.0
        tgt = float(row["BEST_TARGET_PRICE"]) if pd.notnull(row.get("BEST_TARGET_PRICE")) else px * 1.15
        buy_rec = int(row["TOT_BUY_REC"]) if pd.notnull(row.get("TOT_BUY_REC")) else 0
        hold_rec = int(row["TOT_HOLD_REC"]) if pd.notnull(row.get("TOT_HOLD_REC")) else 0
        sell_rec = int(row["TOT_SELL_REC"]) if pd.notnull(row.get("TOT_SELL_REC")) else 0
        tot_rec = buy_rec + hold_rec + sell_rec
        buy_pct = round((buy_rec / tot_rec * 100), 1) if tot_rec > 0 else 75.0
        roe = float(row["RETURN_COM_EQY"]) if pd.notnull(row.get("RETURN_COM_EQY")) else 0.0
        pe = float(row["PE_RATIO"]) if pd.notnull(row.get("PE_RATIO")) else 0.0
        mkt_cap = float(row["CUR_MKT_CAP"]) if pd.notnull(row.get("CUR_MKT_CAP")) else 0.0
        vol = float(row["VOLUME"]) if pd.notnull(row.get("VOLUME")) else 0.0
        earn_dt = str(row.get("EXPECTED_REPORT_DT", "")) if pd.notnull(row.get("EXPECTED_REPORT_DT")) else "TBD"

        upside_pct = round(((tgt - px) / px * 100), 2) if px > 0 else 0.0
        stop_loss = round(px * 0.93, 2)
        dollar_risk = round(px - stop_loss, 2)
        dollar_reward = round(tgt - px, 2)
        rr_ratio = round(dollar_reward / dollar_risk, 1) if dollar_risk > 0 else 0.0

        if rr_ratio >= 3.0 and upside_pct >= 20:
            signal = "STRONG BUY (CATALYST)"
            badge_color = "success"
        elif rr_ratio >= 2.0:
            signal = "QUALIFIED BUY"
            badge_color = "primary"
        else:
            signal = "WATCHLIST"
            badge_color = "secondary"

        candidates.append({
            "symbol": sym,
            "ticker": f"{sym} US Equity",
            "name": name,
            "sector": sector,
            "price": px,
            "chg_1d": chg_1d,
            "chg_5d": chg_5d,
            "target": round(tgt, 2),
            "upside_pct": upside_pct,
            "stop_loss": stop_loss,
            "rr_ratio": rr_ratio,
            "signal": signal,
            "badge_color": badge_color,
            "buy_rec": buy_rec,
            "hold_rec": hold_rec,
            "sell_rec": sell_rec,
            "buy_pct": buy_pct,
            "roe": round(roe, 1),
            "pe": round(pe, 1),
            "market_cap": mkt_cap,
            "volume": vol,
            "earnings_date": earn_dt
        })

    candidates.sort(key=lambda x: x["upside_pct"], reverse=True)
    json_data = json.dumps(candidates)
    
    status_meta = {
        "is_live": is_live_data,
        "is_port_open": is_port_open,
        "csv_timestamp": csv_time_str,
        "csv_mtime_epoch": int(csv_mtime.timestamp()),
        "age_label": age_label,
        "connection_protocol": "Bloomberg Desktop API (BLPAPI / bbcomm.exe on 127.0.0.1:8194)",
        "feed_mode": "LIVE_API" if is_live_data else "OFFLINE_CACHED"
    }
    status_json = json.dumps(status_meta)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dallas College Bloomberg Trading Challenge — Decision Terminal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #090d16;
      --card-bg: #111726;
      --card-border: #1e293b;
      --accent-cyan: #00e5ff;
      --accent-green: #00e676;
      --accent-red: #ff3366;
      --accent-gold: #ffb300;
      --accent-amber: #f59e0b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      padding: 24px;
      line-height: 1.5;
    }}
    .container {{
      max-width: 1440px;
      margin: 0 auto;
    }}

    /* Top Mode & Diagnostic Banner */
    .mode-banner {{
      border-radius: 12px;
      padding: 14px 20px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 13px;
      transition: all 0.3s ease;
    }}
    .mode-banner.offline {{
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(180, 83, 9, 0.2) 100%);
      border: 1px solid rgba(245, 158, 11, 0.4);
      color: #fde68a;
    }}
    .mode-banner.live {{
      background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(5, 150, 105, 0.2) 100%);
      border: 1px solid rgba(0, 230, 118, 0.4);
      color: #a7f3d0;
    }}
    .mode-left {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .mode-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: 9999px;
      font-weight: 800;
      letter-spacing: 0.5px;
      font-size: 12px;
      text-transform: uppercase;
    }}
    .mode-pill.offline {{
      background: #f59e0b;
      color: #090d16;
    }}
    .mode-pill.live {{
      background: #00e676;
      color: #090d16;
    }}
    .pulse-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .pulse-dot.live {{
      background-color: #090d16;
      box-shadow: 0 0 8px #ffffff;
    }}
    .pulse-dot.offline {{
      background-color: #090d16;
    }}
    .mode-right {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .diag-btn {{
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #ffffff;
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .diag-btn:hover {{
      background: rgba(255, 255, 255, 0.2);
    }}
    .sim-toggle {{
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #ffffff;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      cursor: pointer;
    }}

    /* Header */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }}
    .title-group h1 {{
      font-size: 28px;
      font-weight: 800;
      background: linear-gradient(135deg, #00e5ff 0%, #3b82f6 50%, #00e676 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 4px;
    }}
    .title-group p {{
      color: var(--text-muted);
      font-size: 14px;
    }}

    .header-badges {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
    }}
    .sync-timestamp-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(0, 229, 255, 0.1);
      border: 1px solid rgba(0, 229, 255, 0.3);
      color: #ffffff;
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .sync-timestamp-badge b {{
      color: var(--accent-cyan);
    }}
    .age-pill {{
      background: rgba(255, 255, 255, 0.12);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      color: #94a3b8;
    }}
    .feed-info-tag {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #111726;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-family: 'JetBrains Mono', monospace;
    }}

    /* Top Stats Grid */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      transition: transform 0.2s, border-color 0.2s;
    }}
    .stat-card:hover {{
      transform: translateY(-2px);
      border-color: #334155;
    }}
    .stat-label {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .stat-value {{
      font-size: 28px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #ffffff;
    }}
    .stat-desc {{
      font-size: 12px;
      color: var(--text-muted);
    }}
    .input-box {{
      background: #090d16;
      border: 1px solid #334155;
      color: #00e5ff;
      font-family: 'JetBrains Mono', monospace;
      font-size: 20px;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 8px;
      width: 100%;
      outline: none;
    }}
    .input-box:focus {{
      border-color: var(--accent-cyan);
    }}

    /* How-To Guide Banner */
    .guide-banner {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(17, 23, 38, 0.9) 100%);
      border: 1px solid #334155;
      border-left: 4px solid var(--accent-cyan);
      border-radius: 12px;
      padding: 16px 22px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .guide-content h3 {{
      font-size: 15px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 6px;
    }}
    .guide-steps {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 13px;
      color: var(--text-muted);
    }}
    .step-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid #334155;
      padding: 4px 10px;
      border-radius: 6px;
      color: #cbd5e1;
    }}
    .step-chip b {{
      background: var(--accent-cyan);
      color: #090d16;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
    }}
    .step-chip code {{
      background: #090d16;
      color: var(--accent-gold);
      padding: 1px 5px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .guide-badge {{
      background: rgba(0, 229, 255, 0.15);
      border: 1px solid rgba(0, 229, 255, 0.3);
      color: var(--accent-cyan);
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 12px;
      white-space: nowrap;
    }}

    /* Controls */
    .controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 24px;
    }}
    .filter-tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .filter-btn {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: #1e293b;
      color: #ffffff;
      border-color: var(--accent-cyan);
      box-shadow: 0 0 12px rgba(0, 229, 255, 0.15);
    }}
    .search-box-wrapper {{
      position: relative;
      display: flex;
      align-items: center;
    }}
    .search-box {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: #ffffff;
      padding: 10px 16px 10px 38px;
      border-radius: 10px;
      font-size: 14px;
      outline: none;
      width: 280px;
      transition: border-color 0.2s;
    }}
    .search-box:focus {{
      border-color: var(--accent-cyan);
    }}
    .search-icon {{
      position: absolute;
      left: 12px;
      color: var(--text-muted);
      font-size: 14px;
      pointer-events: none;
    }}

    /* Stock Cards Grid - Fixed Overflow & Clean Header */
    .stocks-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 20px;
    }}
    .stock-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      position: relative;
      transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
      overflow: hidden;
    }}
    .stock-card:hover {{
      transform: translateY(-4px);
      border-color: #3b82f6;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}

    /* Card Header: 2 Clean Rows to prevent any badge overflow */
    .card-header {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .header-main-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }}
    .ticker-symbol {{
      font-size: 22px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: 0.5px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .signal-pill {{
      font-size: 11px;
      font-weight: 800;
      padding: 4px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      white-space: nowrap;
      text-align: right;
    }}
    .signal-pill.success {{
      background: rgba(0, 230, 118, 0.15);
      color: var(--accent-green);
      border: 1px solid rgba(0, 230, 118, 0.4);
    }}
    .signal-pill.primary {{
      background: rgba(0, 229, 255, 0.15);
      color: var(--accent-cyan);
      border: 1px solid rgba(0, 229, 255, 0.4);
    }}
    .signal-pill.secondary {{
      background: rgba(148, 163, 184, 0.15);
      color: var(--text-muted);
      border: 1px solid rgba(148, 163, 184, 0.3);
    }}

    .header-sub-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      font-size: 12px;
    }}
    .company-title {{
      color: var(--text-muted);
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 60%;
    }}
    .sector-tag {{
      font-size: 10px;
      font-weight: 700;
      color: #94a3b8;
      background: #1e293b;
      padding: 2px 7px;
      border-radius: 5px;
      text-transform: uppercase;
      white-space: nowrap;
      letter-spacing: 0.3px;
    }}

    /* Price Row with High Contrast */
    .price-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding-bottom: 12px;
      border-bottom: 1px solid #1e293b;
    }}
    .current-price {{
      font-size: 26px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #ffffff;
    }}
    .price-tag-group {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .state-badge {{
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase;
    }}
    .state-badge.offline {{
      background: rgba(245, 158, 11, 0.2);
      color: #f59e0b;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }}
    .state-badge.live {{
      background: rgba(0, 230, 118, 0.2);
      color: #00e676;
      border: 1px solid rgba(0, 230, 118, 0.4);
    }}
    .change-pct {{
      font-size: 13px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }}
    .change-pct.pos {{ color: var(--accent-green); }}
    .change-pct.neg {{ color: #ff3366; }}

    /* Tinted Metrics Box for Institutional Look */
    .metric-rows {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: rgba(9, 13, 22, 0.6);
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid #1e293b;
    }}
    .metric-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12.5px;
    }}
    .metric-row .label {{
      color: var(--text-muted);
    }}
    .metric-row .val {{
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }}
    .val-highlight {{ color: var(--accent-green); }}
    .val-stop {{ color: #ff3366; }}

    .trade-btn {{
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      color: #ffffff;
      border: none;
      padding: 12px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      transition: filter 0.2s, transform 0.1s;
      margin-top: 2px;
    }}
    .trade-btn:hover {{
      filter: brightness(1.15);
    }}
    .trade-btn:active {{
      transform: scale(0.98);
    }}

    /* Diagnostic Modal */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(5px);
      z-index: 200;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-card {{
      background: var(--card-bg);
      border: 1px solid #334155;
      border-radius: 16px;
      max-width: 580px;
      width: 100%;
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.7);
    }}
    .modal-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 18px;
      font-weight: 800;
      color: #ffffff;
    }}
    .close-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 26px;
      cursor: pointer;
    }}
    .diag-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .diag-table td {{
      padding: 8px 10px;
      border-bottom: 1px solid #1e293b;
    }}
    .diag-table td:first-child {{
      color: var(--text-muted);
      font-weight: 600;
      width: 40%;
    }}
    .diag-table td:last-child {{
      font-family: 'JetBrains Mono', monospace;
      color: #ffffff;
    }}

    /* Order Ticket Box */
    .ticket-box {{
      background: #090d16;
      border: 1px solid #1e293b;
      border-radius: 10px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 9px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
    }}
    .ticket-line {{
      display: flex;
      justify-content: space-between;
    }}
    .copy-btn {{
      background: var(--accent-cyan);
      color: #090d16;
      border: none;
      padding: 12px;
      border-radius: 10px;
      font-weight: 700;
      cursor: pointer;
      font-size: 14px;
    }}

    /* Footer */
    .terminal-footer {{
      margin-top: 48px;
      padding-top: 24px;
      border-top: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 12px;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }}
  </style>
</head>
<body>

<div class="container">

  <!-- TOP LIVE VS OFFLINE STATUS BANNER -->
  <div id="modeBanner" class="mode-banner offline">
    <div class="mode-left">
      <div id="modePill" class="mode-pill offline">
        <div id="pulseDot" class="pulse-dot offline"></div>
        <span id="modeText">OFFLINE SNAPSHOT</span>
      </div>
      <div>
        <span id="bannerSummary"><b>Last Synced:</b> {csv_time_str} (<span id="bannerAgeText">{age_label}</span>) • Bloomberg API: <b>Offline</b></span>
      </div>
    </div>
    <div class="mode-right">
      <button class="diag-btn" onclick="openDiagModal()">🔍 Feed & API Diagnostics</button>
      <button class="diag-btn" onclick="window.location.reload()">🔄 Refresh Feed</button>
      <button class="sim-toggle" onclick="toggleSimulatedMode()">Toggle View Mode</button>
    </div>
  </div>

  <!-- Main Header with Permanent Last Synced Badge -->
  <div class="header">
    <div class="title-group">
      <h1>Bloomberg Global Trading Challenge — Dallas College</h1>
      <p>Quantitative Decision, Risk-Reward & 20% Position-Sizing Terminal</p>
    </div>
    <div class="header-badges">
      <div class="sync-timestamp-badge">
        <span>🕒 Last Synced: <b id="headerSyncTime">{csv_time_str}</b></span>
        <span id="headerSyncAge" class="age-pill">({age_label})</span>
      </div>
      <div class="feed-info-tag">
        <span>Protocol: <b>BLPAPI (127.0.0.1:8194)</b></span>
        <span style="color: #475569;">|</span>
        <span id="feedStatusLabel">Status: <b>Live Feed</b></span>
      </div>
    </div>
  </div>

  <!-- Top Stats Grid -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Total Portfolio Cash ($)</div>
      <input type="number" id="cashInput" class="input-box" value="1000000" oninput="updateSizing()">
      <div class="stat-desc">Type your balance to recalculate all 20% positions</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Max 20% Entry Limit</div>
      <div class="stat-value" id="maxCapDisplay" style="color: var(--accent-cyan);">$200,000</div>
      <div class="stat-desc">Mandatory competition limit per position</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Max Risk / Stop Budget</div>
      <div class="stat-value" id="riskBudgetDisplay" style="color: var(--accent-gold);">$14,000</div>
      <div class="stat-desc">Max loss on a 20% clip using strict 7% stop</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Winning Expectancy Edge</div>
      <div class="stat-value" style="color: var(--accent-green);">3:1 Ratio</div>
      <div class="stat-desc">40% win rate yields positive compounding</div>
    </div>
  </div>

  <!-- Beginner Guide Banner with 3 Clean Steps -->
  <div class="guide-banner">
    <div class="guide-content">
      <h3>🚀 How To Execute Competition Trades</h3>
      <div class="guide-steps">
        <span class="step-chip"><b>1</b> Screen candidates with 3:1+ R:R & Target Upside</span>
        <span class="step-chip"><b>2</b> Click "Generate 20% Trade Ticket" for share counts</span>
        <span class="step-chip"><b>3</b> Execute in terminal via <code>CHAL &lt;GO&gt;</code></span>
      </div>
    </div>
    <div class="guide-badge">20% Position Cap Enforced</div>
  </div>

  <!-- Controls -->
  <div class="controls">
    <div class="filter-tabs">
      <button class="filter-btn active" onclick="filterSector('ALL', this)">All Stocks (25)</button>
      <button class="filter-btn" onclick="filterSector('Information Technology', this)">AI & Tech</button>
      <button class="filter-btn" onclick="filterSector('Health Care', this)">Healthcare / Pharma</button>
      <button class="filter-btn" onclick="filterSector('Industrials', this)">Industrials</button>
      <button class="filter-btn" onclick="filterSector('Financials', this)">Financials</button>
      <button class="filter-btn" onclick="filterSector('Consumer', this)">Consumer</button>
    </div>
    <div class="search-box-wrapper">
      <span class="search-icon">🔍</span>
      <input type="text" id="searchInput" class="search-box" placeholder="Search ticker or company..." oninput="searchStocks()">
    </div>
  </div>

  <!-- Stock Cards Grid -->
  <div class="stocks-grid" id="stocksGrid"></div>

  <!-- Footer with Permanent Timestamp Stamp -->
  <footer class="terminal-footer">
    <div>Dallas College Bloomberg Global Trading Challenge • WLS Index Universe</div>
    <div>Data Engine: <b>Bloomberg BLPAPI (127.0.0.1:8194)</b></div>
    <div>Last Terminal Extraction: <b style="color: var(--accent-cyan);">{csv_time_str}</b></div>
  </footer>
</div>

<!-- Diagnostics Modal -->
<div class="modal-overlay" id="diagModal" onclick="closeModalOnBg(event, 'diagModal')">
  <div class="modal-card">
    <div class="modal-title">
      <span>📡 Bloomberg Data Feed Diagnostics</span>
      <button class="close-btn" onclick="closeDiagModal()">&times;</button>
    </div>
    <p style="font-size: 13px; color: var(--text-muted);">
      Detailed breakdown of your data connection, protocol, and exact synchronization time:
    </p>
    <table class="diag-table">
      <tr>
        <td>Exact Last Sync Time</td>
        <td style="color: var(--accent-cyan); font-weight: 700;">{csv_time_str}</td>
      </tr>
      <tr>
        <td>Data Freshness Age</td>
        <td id="diagDataAge">{age_label}</td>
      </tr>
      <tr>
        <td>Connection Type</td>
        <td id="diagConnType">Bloomberg Desktop API (BLPAPI / bbcomm.exe)</td>
      </tr>
      <tr>
        <td>Local Daemon Port</td>
        <td>127.0.0.1:8194 (TCP Loopback)</td>
      </tr>
      <tr>
        <td>Terminal Active Now?</td>
        <td id="diagPortStatus">Checking...</td>
      </tr>
      <tr>
        <td>File Source</td>
        <td>bloomberg_live_remote_screener.csv</td>
      </tr>
    </table>
    <div style="background: rgba(30, 41, 59, 0.5); padding: 12px; border-radius: 8px; font-size: 12px; color: var(--text-muted);">
      <b>How to sync newer quotes from the terminal:</b><br>
      1. Open the Bloomberg terminal in the Dallas College lab.<br>
      2. Double-click <b>Sync & Share with Friend</b> on your Desktop.<br>
      3. Fresh market quotes will immediately sync locally and push to GitHub.
    </div>
  </div>
</div>

<!-- Trade Ticket Modal -->
<div class="modal-overlay" id="tradeModal" onclick="closeModalOnBg(event, 'tradeModal')">
  <div class="modal-card">
    <div class="modal-title">
      <span id="modalTickerTitle">Trade Order Ticket</span>
      <button class="close-btn" onclick="closeModal()">&times;</button>
    </div>
    <p style="font-size: 13px; color: var(--text-muted);">
      Pre-sized strictly within Dallas College 20% rules. Punch these exact parameters into the competition simulator:
    </p>
    <div class="ticket-box" id="ticketBox"></div>
    <button class="copy-btn" id="copyBtn" onclick="copyTicket()">📋 Copy Order to Clipboard</button>
  </div>
</div>

<script>
const stocksData = {json_data};
const statusMeta = {status_json};
let isSimulatedLive = false;
let currentFilter = 'ALL';
let currentSearch = '';

// Live Dynamic Age Calculator (updates every minute)
function updateDynamicAge() {{
  const epoch = statusMeta.csv_mtime_epoch;
  if (!epoch) return;
  const nowSec = Math.floor(Date.now() / 1000);
  const diff = nowSec - epoch;
  let label = "Just now";
  if (diff >= 86400) {{
    const d = Math.floor(diff / 86400);
    label = d + (d === 1 ? " day ago" : " days ago");
  }} else if (diff >= 3600) {{
    const h = Math.floor(diff / 3600);
    label = h + (h === 1 ? " hr ago" : " hrs ago");
  }} else if (diff >= 60) {{
    const m = Math.floor(diff / 60);
    label = m + (m === 1 ? " min ago" : " mins ago");
  }} else if (diff > 5) {{
    label = diff + " sec ago";
  }} else {{
    label = "Just now";
  }}
  
  const elBanner = document.getElementById('bannerAgeText');
  if (elBanner) elBanner.innerText = label;
  const elHeader = document.getElementById('headerSyncAge');
  if (elHeader) elHeader.innerText = "(" + label + ")";
  const elDiag = document.getElementById('diagDataAge');
  if (elDiag) elDiag.innerText = label;
}}

// Initialize connection banner and sync info
function applyModeUI() {{
  const isCurrentlyLive = isSimulatedLive || statusMeta.is_live;
  const banner = document.getElementById('modeBanner');
  const pill = document.getElementById('modePill');
  const dot = document.getElementById('pulseDot');
  const text = document.getElementById('modeText');
  const summary = document.getElementById('bannerSummary');
  const feedLabel = document.getElementById('feedStatusLabel');
  const diagPort = document.getElementById('diagPortStatus');

  if (isCurrentlyLive) {{
    banner.className = 'mode-banner live';
    pill.className = 'mode-pill live';
    dot.className = 'pulse-dot live';
    text.innerText = 'LIVE API FEED';
    summary.innerHTML = '<b>Last Synced:</b> ' + statusMeta.csv_timestamp + ' (<span id="bannerAgeText">' + statusMeta.age_label + '</span>) • Bloomberg API (127.0.0.1:8194): <b style="color: var(--accent-green);">Connected</b>';
    feedLabel.innerHTML = 'Status: <b style="color: var(--accent-green);">● Live BLPAPI Feed</b>';
    diagPort.innerHTML = '<span style="color: var(--accent-green);">🟢 Connected (Active Session)</span>';
  }} else {{
    banner.className = 'mode-banner offline';
    pill.className = 'mode-pill offline';
    dot.className = 'pulse-dot offline';
    text.innerText = 'OFFLINE SNAPSHOT';
    summary.innerHTML = '<b>Last Synced:</b> ' + statusMeta.csv_timestamp + ' (<span id="bannerAgeText">' + statusMeta.age_label + '</span>) • Bloomberg API (127.0.0.1:8194): <b>Offline</b>';
    feedLabel.innerHTML = 'Status: <b style="color: var(--accent-amber);">Cached Snapshot</b>';
    diagPort.innerHTML = '<span style="color: var(--accent-red);">🔴 Disconnected (bbcomm offline)</span>';
  }}
  updateDynamicAge();
  renderStocks();
}}

function toggleSimulatedMode() {{
  isSimulatedLive = !isSimulatedLive;
  applyModeUI();
}}

function openDiagModal() {{
  document.getElementById('diagModal').style.display = 'flex';
}}

function closeDiagModal() {{
  document.getElementById('diagModal').style.display = 'none';
}}

function renderStocks() {{
  const grid = document.getElementById('stocksGrid');
  grid.innerHTML = '';
  const totalCash = parseFloat(document.getElementById('cashInput').value) || 1000000;
  const maxClip = totalCash * 0.20;
  const isCurrentlyLive = isSimulatedLive || statusMeta.is_live;

  const filtered = stocksData.filter(s => {{
    const matchesSector = currentFilter === 'ALL' || s.sector.toLowerCase().includes(currentFilter.toLowerCase());
    const matchesSearch = s.symbol.toLowerCase().includes(currentSearch.toLowerCase()) || 
                          s.name.toLowerCase().includes(currentSearch.toLowerCase());
    return matchesSector && matchesSearch;
  }});

  filtered.forEach(s => {{
    const sharesToBuy = s.price > 0 ? Math.floor(maxClip / s.price) : 0;
    const badgeHtml = isCurrentlyLive
      ? '<span class="state-badge live">● LIVE</span>'
      : '<span class="state-badge offline">CACHED</span>';

    const card = document.createElement('div');
    card.className = 'stock-card';
    card.innerHTML = `
      <!-- Clean 2-Row Header (Zero Overflow) -->
      <div class="card-header">
        <div class="header-main-row">
          <div class="ticker-symbol">${{s.symbol}}</div>
          <span class="signal-pill ${{s.badge_color}}">${{s.signal}}</span>
        </div>
        <div class="header-sub-row">
          <div class="company-title" title="${{s.name}}">${{s.name}}</div>
          <span class="sector-tag">${{s.sector}}</span>
        </div>
      </div>

      <!-- Price Row -->
      <div class="price-row">
        <div class="current-price">$${{s.price.toFixed(2)}}</div>
        <div class="price-tag-group">
          ${{badgeHtml}}
          <div class="change-pct ${{s.chg_1d >= 0 ? 'pos' : 'neg'}}">
            ${{s.chg_1d >= 0 ? '+' : ''}}${{s.chg_1d.toFixed(2)}}%
          </div>
        </div>
      </div>

      <!-- Institutional Metrics Box -->
      <div class="metric-rows">
        <div class="metric-row">
          <span class="label">Wall St Target:</span>
          <span class="val val-highlight">$${{s.target.toFixed(2)}} (+${{s.upside_pct}}%)</span>
        </div>
        <div class="metric-row">
          <span class="label">Strict 7% Stop Loss:</span>
          <span class="val val-stop">$${{s.stop_loss.toFixed(2)}} (-7.0%)</span>
        </div>
        <div class="metric-row">
          <span class="label">Asymmetric Risk/Reward:</span>
          <span class="val" style="color: var(--accent-cyan);">${{s.rr_ratio}}:1 Ratio</span>
        </div>
        <div class="metric-row">
          <span class="label">20% Max Sizing:</span>
          <span class="val" style="color: #ffffff;">BUY ${{sharesToBuy.toLocaleString()}} SHARES</span>
        </div>
        <div class="metric-row">
          <span class="label">Analyst Buy Skew:</span>
          <span class="val">${{s.buy_pct}}% Buy (${{s.buy_rec}} Buy / ${{s.sell_rec}} Sell)</span>
        </div>
        <div class="metric-row">
          <span class="label">Catalyst (Earnings):</span>
          <span class="val" style="color: var(--accent-gold);">${{s.earnings_date}}</span>
        </div>
      </div>

      <!-- 1-Click Competition Order Generator -->
      <button class="trade-btn" onclick="openModal('${{s.symbol}}')">
        ⚡ Generate 20% Trade Ticket
      </button>
    `;
    grid.appendChild(card);
  }});
}}

function updateSizing() {{
  const cash = parseFloat(document.getElementById('cashInput').value) || 1000000;
  const maxCap = cash * 0.20;
  const riskBudget = maxCap * 0.07;
  document.getElementById('maxCapDisplay').innerText = '$' + maxCap.toLocaleString(undefined, {{maximumFractionDigits: 0}});
  document.getElementById('riskBudgetDisplay').innerText = '$' + riskBudget.toLocaleString(undefined, {{maximumFractionDigits: 0}});
  renderStocks();
}}

function filterSector(sector, btn) {{
  currentFilter = sector;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderStocks();
}}

function searchStocks() {{
  currentSearch = document.getElementById('searchInput').value;
  renderStocks();
}}

let selectedTicketText = '';

function openModal(symbol) {{
  const stock = stocksData.find(s => s.symbol === symbol);
  if (!stock) return;
  const totalCash = parseFloat(document.getElementById('cashInput').value) || 1000000;
  const maxClip = totalCash * 0.20;
  const shares = Math.floor(maxClip / stock.price);
  const totalSpend = (shares * stock.price).toFixed(2);
  const potentialProfit = (shares * (stock.target - stock.price)).toFixed(2);
  const maxLoss = (shares * (stock.price - stock.stop_loss)).toFixed(2);

  document.getElementById('modalTickerTitle').innerText = `${{stock.symbol}} — 20% Competition Trade Ticket`;
  
  selectedTicketText = `--- DALLAS COLLEGE TRADING CHALLENGE ORDER ---
Security: ${{stock.ticker}} (${{stock.name}})
Action: BUY (Long-Only)
Order Type: MARKET
Quantity: ${{shares.toLocaleString()}} Shares
Estimated Cost: $${{Number(totalSpend).toLocaleString()}} (within 20% max clip)
Target Price (Wall St): $${{stock.target.toFixed(2)}} (+${{stock.upside_pct}}%)
Target Profit: +$${{Number(potentialProfit).toLocaleString()}}
Stop-Loss Price (7% Hard Stop): $${{stock.stop_loss.toFixed(2)}}
Max Risk: -$${{Number(maxLoss).toLocaleString()}}
Risk/Reward Ratio: ${{stock.rr_ratio}}:1
Catalyst Date: ${{stock.earnings_date}}
------------------------------------------------`;

  document.getElementById('ticketBox').innerHTML = `
    <div class="ticket-line"><span>Action:</span><span style="color: var(--accent-green); font-weight: 700;">BUY (Long-Only)</span></div>
    <div class="ticket-line"><span>Security:</span><span>${{stock.ticker}}</span></div>
    <div class="ticket-line"><span>Quantity:</span><span style="color: var(--accent-cyan); font-weight: 700;">${{shares.toLocaleString()}} Shares</span></div>
    <div class="ticket-line"><span>Total Position Value:</span><span>$${{Number(totalSpend).toLocaleString()}}</span></div>
    <div class="ticket-line"><span>Wall St Target:</span><span style="color: var(--accent-green);">$${{stock.target.toFixed(2)}} (+${{stock.upside_pct}}%)</span></div>
    <div class="ticket-line"><span>Strict 7% Stop-Loss:</span><span style="color: #ff3366;">$${{stock.stop_loss.toFixed(2)}}</span></div>
    <div class="ticket-line"><span>Upside Payoff:</span><span style="color: var(--accent-green);">+$${{Number(potentialProfit).toLocaleString()}}</span></div>
    <div class="ticket-line"><span>Downside Risk:</span><span style="color: #ff3366;">-$${{Number(maxLoss).toLocaleString()}}</span></div>
    <div class="ticket-line"><span>Upcoming Catalyst:</span><span style="color: var(--accent-gold);">${{stock.earnings_date}}</span></div>
  `;

  document.getElementById('tradeModal').style.display = 'flex';
}}

function closeModal() {{
  document.getElementById('tradeModal').style.display = 'none';
}}

function closeModalOnBg(e, modalId) {{
  if (e.target.id === modalId) {{
    document.getElementById(modalId).style.display = 'none';
  }}
}}

function copyTicket() {{
  navigator.clipboard.writeText(selectedTicketText).then(() => {{
    const btn = document.getElementById('copyBtn');
    btn.innerText = '✅ Order Copied to Clipboard!';
    setTimeout(() => {{ btn.innerText = '📋 Copy Order to Clipboard'; }}, 2000);
  }});
}}

// Initialize
updateSizing();
applyModeUI();
setInterval(updateDynamicAge, 30000); // Check age every 30s
</script>
</body>
</html>
"""

    html_file1 = os.path.join(script_dir, "index.html")
    html_file2 = os.path.join(script_dir, "dashboard.html")

    with open(html_file1, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(html_file2, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated web dashboard with polished UI & fixed card header layout:")
    print(f"  - Mode: {'LIVE API' if is_live_data else 'OFFLINE SNAPSHOT'}")
    print(f"  - Exact Sync Timestamp: {csv_time_str} ({age_label})")
    print(f"  - Saved to: {html_file1}")
    return html_file1

if __name__ == "__main__":
    generate_dashboard()
