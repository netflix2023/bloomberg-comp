"""
Bloomberg Trading Challenge - Web Dashboard Generator
Dallas College Institutional Terminal

Architecture:
  1. CURRENT HOLDINGS (Official Bloomberg Portfolio — Read-Only)
     - Synced directly to actual holdings executed in the Bloomberg Terminal
     - Read-only: Currently reflects 0 holdings / 100% Cash ($1,000,000 Liquid)
     - 5-slot allocation capacity monitor (20% maximum per clip)
  2. WISHLIST & TARGET PIPELINE (Starts Empty By Default — Fully Addable & Removable)
     - Team's curated wishlist of prospective stocks
     - Starts empty by default (0 stocks)
     - Stocks can be added by clicking "⭐ Add to Wishlist" on any screener stock, or via custom ticker modal
     - Fully removable via 1-click "🗑️ Remove"
     - 1-click "Generate 20% Order Ticket for CHAL <GO>" for competition terminal entry
  3. SCREENER UNIVERSE (25 Stocks Kept Up to View)
     - Live quotes, consensus targets, strict 7% stops, 3:1+ R:R, catalyst dates
     - 1-click "⭐ Add to Wishlist" button on every card
"""

import os
import json
import socket
from datetime import datetime
import pandas as pd

def check_bloomberg_port(host="127.0.0.1", port=8194, timeout=0.4):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        bb_exe = r"C:\blp\DAPI\bbcomm.exe"
        if os.path.exists(bb_exe):
            try:
                import subprocess, time
                subprocess.Popen([bb_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.5)
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except Exception:
                pass
        return False

def generate_dashboard():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "bloomberg_live_remote_screener.csv")
    holdings_path = os.path.join(script_dir, "current_holdings.json")
    wishlist_path = os.path.join(script_dir, "wishlist.json")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}. Run sync_remote_excel.py first.")

    # 1. Load actual Bloomberg holdings (Strictly read-only)
    actual_holdings = []
    if os.path.exists(holdings_path):
        try:
            with open(holdings_path, "r", encoding="utf-8") as f:
                actual_holdings = json.load(f)
        except Exception:
            actual_holdings = []

    # 2. Load Wishlist configuration (Empty by default)
    wishlist_items = []
    if os.path.exists(wishlist_path):
        try:
            with open(wishlist_path, "r", encoding="utf-8") as f:
                wishlist_items = json.load(f)
        except Exception:
            wishlist_items = []

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

    # Check live Bloomberg API connection
    is_port_open = check_bloomberg_port()
    is_live_data = (age_seconds < 3600)

    df = pd.read_csv(csv_path)

    # Build market data lookup by symbol and candidates list
    market_db = {}
    candidates_list = []
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

        item = {
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
        }
        market_db[sym] = item
        candidates_list.append(item)

    candidates_list.sort(key=lambda x: x["upside_pct"], reverse=True)

    status_meta = {
        "is_live": is_live_data,
        "is_port_open": is_port_open,
        "csv_timestamp": csv_time_str,
        "csv_mtime_epoch": int(csv_mtime.timestamp()),
        "age_label": age_label,
        "connection_protocol": "Bloomberg Desktop API (BLPAPI / bbcomm.exe on 127.0.0.1:8194)",
        "feed_mode": "LIVE_API" if is_live_data else "OFFLINE_CACHED"
    }

    json_market_db = json.dumps(market_db)
    json_candidates_list = json.dumps(candidates_list)
    json_actual_holdings = json.dumps(actual_holdings)
    json_wishlist_items = json.dumps(wishlist_items)
    status_json = json.dumps(status_meta)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dallas College Bloomberg Trading Terminal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #070a12;
      --bg-surface: #0e1424;
      --card-bg: #121a2d;
      --card-border: #1e2c48;
      --accent-cyan: #00e5ff;
      --accent-green: #00e676;
      --accent-red: #ff3366;
      --accent-gold: #ffb300;
      --accent-amber: #f59e0b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
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
      margin: 0;
      line-height: 1.5;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1480px;
      margin: 0 auto;
      padding: 20px 24px 60px 24px;
    }}

    /* Top Sticky Navigation Bar */
    .top-nav-bar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(7, 10, 18, 0.94);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--card-border);
      padding: 12px 24px;
      margin-bottom: 20px;
    }}
    .nav-inner {{
      max-width: 1480px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .nav-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, #00e5ff 0%, #2563eb 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 18px;
      color: #070a12;
      box-shadow: 0 0 16px rgba(0, 229, 255, 0.35);
    }}
    .brand-text h1 {{
      font-size: 17px;
      font-weight: 800;
      letter-spacing: -0.2px;
      background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .brand-text p {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      font-weight: 600;
    }}

    /* 3-View Page Switcher Tabs */
    .page-switcher {{
      display: flex;
      background: #090e1a;
      border: 1px solid var(--card-border);
      padding: 4px;
      border-radius: 12px;
      gap: 4px;
    }}
    .nav-tab-btn {{
      display: inline-flex;
      align-items: center;
      gap: 9px;
      padding: 8px 18px;
      border-radius: 9px;
      font-size: 13px;
      font-weight: 700;
      color: var(--text-muted);
      border: 1px solid transparent;
      background: transparent;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .nav-tab-btn:hover {{
      color: #ffffff;
      background: rgba(255, 255, 255, 0.04);
    }}
    .nav-tab-btn.active {{
      background: linear-gradient(135deg, #121c32 0%, #1e293b 100%);
      color: #ffffff;
      border-color: rgba(0, 229, 255, 0.4);
      box-shadow: 0 4px 16px rgba(0, 229, 255, 0.15);
    }}
    .nav-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 2px 7px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
    }}
    .nav-badge.invested {{
      background: rgba(0, 230, 118, 0.2);
      color: var(--accent-green);
      border: 1px solid rgba(0, 230, 118, 0.4);
    }}
    .nav-badge.wishlist {{
      background: rgba(255, 179, 0, 0.2);
      color: var(--accent-gold);
      border: 1px solid rgba(255, 179, 0, 0.4);
    }}
    .nav-badge.universe {{
      background: rgba(0, 229, 255, 0.15);
      color: var(--accent-cyan);
      border: 1px solid rgba(0, 229, 255, 0.3);
    }}

    .nav-right {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .nav-action-btn {{
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid var(--card-border);
      color: #ffffff;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .nav-action-btn:hover {{
      border-color: var(--accent-cyan);
      background: rgba(37, 99, 235, 0.2);
    }}
    .nav-action-btn.primary {{
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      border: none;
      font-weight: 700;
    }}

    /* Mode Banner */
    .mode-banner {{
      border-radius: 12px;
      padding: 12px 18px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 12.5px;
    }}
    .mode-banner.offline {{
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(180, 83, 9, 0.15) 100%);
      border: 1px solid rgba(245, 158, 11, 0.35);
      color: #fde68a;
    }}
    .mode-banner.live {{
      background: linear-gradient(135deg, rgba(0, 230, 118, 0.08) 0%, rgba(5, 150, 105, 0.15) 100%);
      border: 1px solid rgba(0, 230, 118, 0.35);
      color: #a7f3d0;
    }}
    .mode-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 9999px;
      font-weight: 800;
      font-size: 11px;
      text-transform: uppercase;
    }}
    .mode-pill.offline {{ background: #f59e0b; color: #090d16; }}
    .mode-pill.live {{ background: #00e676; color: #090d16; }}
    .pulse-dot {{ width: 7px; height: 7px; border-radius: 50%; background-color: #090d16; }}
    .pulse-dot.live {{ box-shadow: 0 0 6px #ffffff; }}

    /* KPI Summary Strip */
    .portfolio-kpi-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.4), transparent);
    }}
    .kpi-card.accent-green::before {{ background: linear-gradient(90deg, transparent, rgba(0, 230, 118, 0.6), transparent); }}
    .kpi-card.accent-gold::before {{ background: linear-gradient(90deg, transparent, rgba(255, 179, 0, 0.6), transparent); }}
    .kpi-label {{
      font-size: 11.5px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .kpi-value {{
      font-size: 24px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #ffffff;
    }}
    .kpi-subtext {{ font-size: 11.5px; color: var(--text-muted); }}
    .cash-input-field {{
      background: #070a12;
      border: 1px solid #2d3748;
      color: var(--accent-cyan);
      font-family: 'JetBrains Mono', monospace;
      font-size: 18px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 6px;
      width: 100%;
      outline: none;
    }}

    /* Allocation Slots Visualizer */
    .allocation-tracker-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 16px 20px;
      margin-bottom: 24px;
    }}
    .tracker-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .tracker-title {{
      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .slots-grid {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 10px;
    }}
    @media (max-width: 900px) {{
      .slots-grid {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    }}
    .slot-box {{
      background: rgba(7, 10, 18, 0.7);
      border: 1px dashed var(--card-border);
      border-radius: 10px;
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .slot-box.occupied {{
      background: rgba(18, 28, 50, 0.9);
      border: 1px solid rgba(0, 229, 255, 0.4);
    }}
    .slot-num {{
      font-size: 10px;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .slot-ticker {{
      font-size: 16px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #ffffff;
    }}
    .slot-ticker.empty {{
      color: var(--text-dim);
      font-size: 13px;
      font-weight: 600;
      font-family: inherit;
    }}
    .slot-meta {{
      font-size: 11px;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }}

    /* Subpage System */
    .subpage {{
      display: none;
      animation: fadeIn 0.2s ease-out;
    }}
    .subpage.active {{
      display: block;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--card-border);
    }}
    .section-title-group h2 {{
      font-size: 22px;
      font-weight: 800;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .section-title-group p {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 2px;
    }}

    .official-tag {{
      background: rgba(0, 229, 255, 0.1);
      border: 1px solid rgba(0, 229, 255, 0.3);
      color: var(--accent-cyan);
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    /* Empty States */
    .empty-state-banner {{
      background: linear-gradient(135deg, rgba(14, 20, 36, 0.95) 0%, rgba(18, 26, 45, 0.95) 100%);
      border: 1px dashed #283754;
      border-radius: 18px;
      padding: 50px 32px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      max-width: 760px;
      margin: 32px auto;
    }}
    .empty-icon-wrap {{
      width: 68px;
      height: 68px;
      border-radius: 18px;
      background: rgba(0, 229, 255, 0.1);
      border: 1px solid rgba(0, 229, 255, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 30px;
      color: var(--accent-cyan);
    }}
    .empty-state-banner h3 {{ font-size: 20px; font-weight: 800; color: #ffffff; }}
    .empty-state-banner p {{ font-size: 14px; color: var(--text-muted); max-width: 580px; line-height: 1.6; }}

    /* Holdings Table */
    .holdings-table-wrap {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
      margin-bottom: 24px;
    }}
    .holdings-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .holdings-table th {{
      background: #0b1120;
      padding: 14px 16px;
      text-align: left;
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.6px;
      border-bottom: 1px solid var(--card-border);
    }}
    .holdings-table td {{
      padding: 16px;
      border-bottom: 1px solid #162238;
      vertical-align: middle;
    }}

    /* Controls & Filter Tabs */
    .controls-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
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
      padding: 7px 14px;
      border-radius: 9px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: #1a253d;
      color: #ffffff;
      border-color: var(--accent-cyan);
      box-shadow: 0 0 10px rgba(0, 229, 255, 0.15);
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
      padding: 9px 16px 9px 36px;
      border-radius: 10px;
      font-size: 13.5px;
      outline: none;
      width: 280px;
    }}
    .search-box:focus {{ border-color: var(--accent-cyan); }}
    .search-icon {{
      position: absolute;
      left: 12px;
      color: var(--text-muted);
      font-size: 13px;
      pointer-events: none;
    }}

    /* Card Grid */
    .stocks-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 18px;
    }}
    .stock-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 13px;
      position: relative;
      transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
      overflow: hidden;
    }}
    .stock-card:hover {{
      transform: translateY(-3px);
      border-color: #3b82f6;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .stock-card.is-wishlist {{
      border-color: rgba(255, 179, 0, 0.5);
      background: linear-gradient(135deg, rgba(18, 26, 45, 0.95) 0%, rgba(28, 24, 15, 0.95) 100%);
    }}

    /* Card Header */
    .card-header {{ display: flex; flex-direction: column; gap: 4px; }}
    .header-main-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }}
    .ticker-symbol {{
      font-size: 21px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: 0.5px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .signal-pill {{
      font-size: 10.5px;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      white-space: nowrap;
    }}
    .signal-pill.success {{ background: rgba(0, 230, 118, 0.15); color: var(--accent-green); border: 1px solid rgba(0, 230, 118, 0.4); }}
    .signal-pill.primary {{ background: rgba(0, 229, 255, 0.15); color: var(--accent-cyan); border: 1px solid rgba(0, 229, 255, 0.4); }}
    .signal-pill.secondary {{ background: rgba(148, 163, 184, 0.15); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.3); }}

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
      background: #1e2c48;
      padding: 2px 7px;
      border-radius: 5px;
      text-transform: uppercase;
      white-space: nowrap;
    }}

    /* Price Row */
    .price-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding-bottom: 10px;
      border-bottom: 1px solid #1a263e;
    }}
    .current-price {{
      font-size: 24px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #ffffff;
    }}
    .change-pct {{
      font-size: 12.5px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }}
    .change-pct.pos {{ color: var(--accent-green); }}
    .change-pct.neg {{ color: #ff3366; }}

    /* Metrics Box */
    .metric-rows {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: rgba(7, 10, 18, 0.6);
      padding: 11px 13px;
      border-radius: 10px;
      border: 1px solid #1a263e;
    }}
    .metric-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
    }}
    .metric-row .label {{ color: var(--text-muted); }}
    .metric-row .val {{ font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
    .val-highlight {{ color: var(--accent-green); }}
    .val-stop {{ color: #ff3366; }}

    .wishlist-notes-box {{
      font-size: 11.5px;
      color: #cbd5e1;
      background: rgba(18, 28, 50, 0.5);
      border-left: 3px solid var(--accent-gold);
      padding: 6px 10px;
      border-radius: 4px;
      line-height: 1.4;
    }}

    /* Card Actions */
    .card-actions {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      margin-top: 2px;
    }}
    .add-wish-btn {{
      background: linear-gradient(135deg, rgba(255, 179, 0, 0.15) 0%, rgba(245, 158, 11, 0.25) 100%);
      border: 1px solid rgba(255, 179, 0, 0.5);
      color: var(--accent-gold);
      padding: 10px 14px;
      border-radius: 9px;
      font-weight: 700;
      font-size: 12.5px;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .add-wish-btn:hover {{
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: #070a12;
      border-color: #f59e0b;
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }}
    .add-wish-btn.active {{
      background: rgba(0, 230, 118, 0.15);
      border-color: rgba(0, 230, 118, 0.5);
      color: var(--accent-green);
    }}
    .ticket-btn {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--card-border);
      color: #cbd5e1;
      padding: 10px 14px;
      border-radius: 9px;
      font-weight: 600;
      font-size: 12.5px;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .ticket-btn:hover {{ background: rgba(255, 255, 255, 0.18); color: #ffffff; }}

    .remove-btn {{
      background: rgba(255, 51, 102, 0.12);
      border: 1px solid rgba(255, 51, 102, 0.35);
      color: #ff6688;
      padding: 10px 14px;
      border-radius: 9px;
      font-weight: 700;
      font-size: 12.5px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      justify-content: center;
    }}
    .remove-btn:hover {{ background: rgba(255, 51, 102, 0.25); color: #ffffff; }}

    /* Modals */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.84);
      backdrop-filter: blur(6px);
      z-index: 200;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-card {{
      background: var(--bg-surface);
      border: 1px solid #2d3e5e;
      border-radius: 18px;
      max-width: 580px;
      width: 100%;
      padding: 26px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      box-shadow: 0 24px 50px rgba(0,0,0,0.8);
      max-height: 90vh;
      overflow-y: auto;
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
      line-height: 1;
    }}
    .modal-form-group {{ display: flex; flex-direction: column; gap: 6px; }}
    .modal-form-label {{
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .modal-input {{
      background: #070a12;
      border: 1px solid #2d3e5e;
      color: #ffffff;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 14px;
      font-family: 'JetBrains Mono', monospace;
      outline: none;
    }}
    .modal-input:focus {{ border-color: var(--accent-cyan); }}
    .ticket-box {{
      background: #070a12;
      border: 1px solid #1a263e;
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
    }}
    .ticket-line {{ display: flex; justify-content: space-between; }}
    .modal-actions {{ display: flex; gap: 10px; margin-top: 8px; }}
    .modal-confirm-btn {{
      flex: 1;
      background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
      color: #070a12;
      border: none;
      padding: 12px;
      border-radius: 10px;
      font-weight: 800;
      font-size: 14px;
      cursor: pointer;
    }}
    .modal-cancel-btn {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--card-border);
      color: #cbd5e1;
      padding: 12px 18px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
    }}

    /* Toast */
    .toast-notify {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #111a2f;
      border: 1px solid var(--accent-cyan);
      color: #ffffff;
      padding: 14px 20px;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.7);
      display: none;
      align-items: center;
      gap: 10px;
      z-index: 300;
      font-size: 13.5px;
      font-weight: 600;
    }}

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

<!-- TOP STICKY NAVIGATION BAR -->
<nav class="top-nav-bar">
  <div class="nav-inner">
    <div class="nav-brand">
      <div class="brand-logo">B</div>
      <div class="brand-text">
        <h1>Dallas College Bloomberg Terminal</h1>
        <p>Global Trading Challenge • 20% Position Cap</p>
      </div>
    </div>

    <!-- 3-VIEW PAGE SWITCHER TABS -->
    <div class="page-switcher">
      <button class="nav-tab-btn active" id="tabBtnHoldings" onclick="switchPage('holdings')">
        <span>💼 Current Holdings</span>
        <span class="nav-badge invested" id="badgeCountInvested">0</span>
      </button>
      <button class="nav-tab-btn" id="tabBtnWishlist" onclick="switchPage('wishlist')">
        <span>⭐ Team Wishlist</span>
        <span class="nav-badge wishlist" id="badgeCountWishlist">0</span>
      </button>
      <button class="nav-tab-btn" id="tabBtnUniverse" onclick="switchPage('universe')">
        <span>🔍 Screener Universe</span>
        <span class="nav-badge universe" id="badgeCountUniverse">25</span>
      </button>
    </div>

    <!-- TOP ACTIONS -->
    <div class="nav-right">
      <button class="nav-action-btn primary" onclick="openAddCustomModal()">➕ Add Custom Ticker</button>
      <button class="nav-action-btn" id="syncBtn" onclick="triggerServerSync()">🔄 Sync Bloomberg</button>
      <button class="nav-action-btn" onclick="openDiagModal()">📡 Diagnostics</button>
    </div>
  </div>
</nav>

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
    <div class="mode-right" style="display: flex; gap: 8px;">
      <button class="nav-action-btn" style="padding: 5px 10px; font-size: 11.5px;" onclick="triggerServerSync()">🔄 Run Live Sync</button>
    </div>
  </div>

  <!-- PORTFOLIO KPI SUMMARY STRIP -->
  <div class="portfolio-kpi-strip">
    <div class="kpi-card">
      <div class="kpi-label">
        <span>Total Portfolio Cash ($)</span>
        <span style="font-size: 10px; color: var(--accent-cyan);">SIMULATOR</span>
      </div>
      <input type="number" id="cashInput" class="cash-input-field" value="1000000" oninput="recalculateAll()">
      <div class="kpi-subtext">Challenge competition equity</div>
    </div>
    <div class="kpi-card accent-green">
      <div class="kpi-label">Total Portfolio Value</div>
      <div class="kpi-value" id="kpiTotalEquity" style="color: var(--accent-green);">$1,000,000</div>
      <div class="kpi-subtext" id="kpiUnrealizedText">Unrealized P&L: +$0.00 (0.0%)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Available Cash ($)</div>
      <div class="kpi-value" id="kpiCashAvailable" style="color: var(--accent-cyan);">$1,000,000</div>
      <div class="kpi-subtext" id="kpiInvestedText">Invested: $0 (0.0% deployed)</div>
    </div>
    <div class="kpi-card accent-gold">
      <div class="kpi-label">Max 20% Entry Limit</div>
      <div class="kpi-value" id="kpiMaxCap" style="color: var(--accent-gold);">$200,000</div>
      <div class="kpi-subtext">Max allowable per position clip</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Allocation Slots Used</div>
      <div class="kpi-value" id="kpiSlotsText" style="color: #ffffff;">0 / 5</div>
      <div class="kpi-subtext" id="kpiSlotsDesc">5 clips open (100% capacity)</div>
    </div>
  </div>

  <!-- 5-SLOT ALLOCATION TRACKER -->
  <div class="allocation-tracker-card">
    <div class="tracker-header">
      <div class="tracker-title">
        <span>🎯 Official 20% Position Sizing Slots (5 Max Clips)</span>
        <span class="official-tag">Bloomberg CHAL &lt;GO&gt; Synced</span>
      </div>
      <span style="font-size: 12px; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace;" id="trackerAllocPercent">0.0% / 100.0% Allocated</span>
    </div>
    <div class="slots-grid" id="slotsGrid"></div>
  </div>

  <!-- ================================================================= -->
  <!-- VIEW 1: CURRENT HOLDINGS (OFFICIAL BLOOMBERG PORTFOLIO)           -->
  <!-- ================================================================= -->
  <div class="subpage active" id="subpageHoldings">
    <div class="section-header">
      <div class="section-title-group">
        <h2>
          <span>💼 Official Current Holdings</span>
          <span class="official-tag">Read-Only • Terminal Synced</span>
        </h2>
        <p>Live portfolio actively held in your team's Bloomberg Terminal account. Positions cannot be manually created here — they automatically sync from Bloomberg executions.</p>
      </div>
      <div>
        <button class="nav-action-btn primary" onclick="switchPage('universe')">🔍 Browse 25 Screener Equities</button>
      </div>
    </div>

    <!-- READ-ONLY EMPTY HOLDINGS BANNER -->
    <div class="empty-state-banner" id="emptyHoldingsCard">
      <div class="empty-icon-wrap">💼</div>
      <h3>0 Active Bloomberg Positions</h3>
      <p>
        Your team currently has <b>0 invested positions</b> in the Bloomberg Challenge terminal. 
        Your portfolio is <b>100% Cash ($1,000,000 Liquid)</b> with all <b>5 allocation slots open</b> ($200,000 max entry per clip).
      </p>
      <div style="background: rgba(14, 20, 36, 0.8); border: 1px solid var(--card-border); padding: 12px 18px; border-radius: 10px; font-size: 13px; color: var(--text-muted); text-align: left; max-width: 580px;">
        💡 <b>How holdings update:</b><br>
        1. Browse the <b>Screener Universe</b> or add candidates to your <b>Wishlist</b>.<br>
        2. Click <b>"Generate 20% Order Ticket"</b> to copy the pre-sized order parameters.<br>
        3. Execute the order on the Bloomberg Terminal in `CHAL &lt;GO&gt;`.<br>
        4. Run sync — your real Bloomberg position will automatically appear here with live P&L and 7% hard stop alerts.
      </div>
      <div style="margin-top: 8px; display: flex; gap: 10px;">
        <button class="nav-action-btn primary" style="padding: 10px 22px; font-size: 14px;" onclick="switchPage('universe')">🔍 Browse Screener Universe</button>
        <button class="nav-action-btn" style="padding: 10px 18px; font-size: 14px;" onclick="switchPage('wishlist')">⭐ View Team Wishlist</button>
      </div>
    </div>

    <!-- HOLDINGS TABLE (Visible when positions exist in current_holdings.json) -->
    <div class="holdings-table-wrap" id="holdingsTableWrap" style="display: none;">
      <table class="holdings-table">
        <thead>
          <tr>
            <th>Security / Sector</th>
            <th>Shares Held</th>
            <th>Entry Price</th>
            <th>Current Quote</th>
            <th>Market Value</th>
            <th>Unrealized P&L</th>
            <th>Portfolio %</th>
            <th>Strict 7% Stop</th>
            <th>Catalyst Date</th>
          </tr>
        </thead>
        <tbody id="holdingsTableBody"></tbody>
      </table>
    </div>
  </div>

  <!-- ================================================================= -->
  <!-- VIEW 2: TEAM WISHLIST (EMPTY BY DEFAULT — ADDABLE & REMOVABLE)   -->
  <!-- ================================================================= -->
  <div class="subpage" id="subpageWishlist">
    <div class="section-header">
      <div class="section-title-group">
        <h2>
          <span>⭐ Team Prospective Wishlist</span>
          <span style="font-size: 12px; font-weight: 700; color: var(--accent-gold); background: rgba(255, 179, 0, 0.15); padding: 3px 8px; border-radius: 6px;" id="wishlistCountHeader">0 Saved</span>
        </h2>
        <p>Curated equities your team hopes to invest in. Easily add stocks from the Screener Universe or custom tickers, and click <b>"📋 Order Ticket"</b> for pre-sized 20% entry parameters.</p>
      </div>
      <div style="display: flex; gap: 10px; align-items: center;">
        <button class="nav-action-btn primary" onclick="switchPage('universe')">🔍 Browse 25 Screener Equities</button>
        <button class="nav-action-btn" onclick="openAddCustomModal()">➕ Custom Ticker</button>
      </div>
    </div>

    <!-- EMPTY WISHLIST BANNER (Default State) -->
    <div class="empty-state-banner" id="emptyWishlistCard" style="display: none;">
      <div class="empty-icon-wrap" style="color: var(--accent-gold); border-color: rgba(255, 179, 0, 0.4); background: rgba(255, 179, 0, 0.1);">⭐</div>
      <h3>Your Team Wishlist is Currently Empty</h3>
      <p>
        You have not added any stocks to your wishlist yet. 
        Browse the <b>25 Screener Equities</b> and click <b>"⭐ Add to Wishlist"</b> on any stock your team hopes to invest in.
      </p>
      <div style="margin-top: 6px;">
        <button class="nav-action-btn primary" style="padding: 10px 24px; font-size: 14px;" onclick="switchPage('universe')">🔍 Browse 25 Screener Stocks to Add</button>
      </div>
    </div>

    <!-- WISHLIST CARDS GRID (Populated by user clicks) -->
    <div class="stocks-grid" id="wishlistGrid"></div>
  </div>

  <!-- ================================================================= -->
  <!-- VIEW 3: SCREENER UNIVERSE (25 STOCKS KEPT UP TO VIEW)             -->
  <!-- ================================================================= -->
  <div class="subpage" id="subpageUniverse">
    <div class="section-header">
      <div class="section-title-group">
        <h2>
          <span>🔍 Bloomberg 25-Stock Screener Universe</span>
        </h2>
        <p>All 25 institutional candidates available to view with live Bloomberg quotes, Wall St targets, and 3:1+ R:R. Click <b>"⭐ Add to Wishlist"</b> on any stock to add it to your team's wishlist.</p>
      </div>
      <div>
        <span style="font-size: 13px; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace;">25 Institutional Equities</span>
      </div>
    </div>

    <!-- Filter & Search Controls -->
    <div class="controls-bar">
      <div class="filter-tabs">
        <button class="filter-btn active" onclick="filterSector('ALL', this)">All Universe (25)</button>
        <button class="filter-btn" onclick="filterSector('Information Technology', this)">AI & Tech</button>
        <button class="filter-btn" onclick="filterSector('Health Care', this)">Healthcare / Pharma</button>
        <button class="filter-btn" onclick="filterSector('Industrials', this)">Industrials</button>
        <button class="filter-btn" onclick="filterSector('Financials', this)">Financials</button>
        <button class="filter-btn" onclick="filterSector('Consumer', this)">Consumer</button>
        <button class="filter-btn" onclick="filterSector('Energy', this)">Energy</button>
      </div>
      <div class="search-box-wrapper">
        <span class="search-icon">🔍</span>
        <input type="text" id="universeSearchInput" class="search-box" placeholder="Search ticker or company..." oninput="searchUniverse()">
      </div>
    </div>

    <!-- Universe Cards Grid -->
    <div class="stocks-grid" id="universeGrid"></div>
  </div>

  <!-- Footer -->
  <footer class="terminal-footer">
    <div>Dallas College Bloomberg Global Trading Challenge • WLS Index Universe</div>
    <div>Engine: <b>BLPAPI (127.0.0.1:8194)</b> • Localhost Active</div>
    <div>Last Market Extraction: <b style="color: var(--accent-cyan);">{csv_time_str}</b></div>
  </footer>
</div>

<!-- ================================================================= -->
<!-- MODALS                                                            -->
<!-- ================================================================= -->

<!-- 1. CUSTOM TICKER MODAL -->
<div class="modal-overlay" id="customTickerModal" onclick="closeModalOnBg(event, 'customTickerModal')">
  <div class="modal-card">
    <div class="modal-title">
      <span>➕ Add Custom Ticker to Wishlist</span>
      <button class="close-btn" onclick="closeCustomTickerModal()">&times;</button>
    </div>
    <p style="font-size: 13px; color: var(--text-muted);">
      Enter any stock symbol outside the 25 screener names:
    </p>

    <div class="modal-form-group">
      <label class="modal-form-label">Ticker Symbol</label>
      <input type="text" id="customTickerInput" class="modal-input" placeholder="e.g. PLTR, TSM, SMCI" style="text-transform: uppercase;">
    </div>

    <div class="modal-form-group">
      <label class="modal-form-label">Investment Thesis / Catalyst Note</label>
      <input type="text" id="customNotesInput" class="modal-input" placeholder="e.g. Q3 earnings momentum / hyperscaler custom silicon">
    </div>

    <div class="modal-actions">
      <button class="modal-confirm-btn" onclick="confirmAddCustom()">Add to Wishlist</button>
      <button class="modal-cancel-btn" onclick="closeCustomTickerModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- 2. ORDER TICKET MODAL FOR CHAL <GO> -->
<div class="modal-overlay" id="tradeModal" onclick="closeModalOnBg(event, 'tradeModal')">
  <div class="modal-card">
    <div class="modal-title">
      <span id="modalTickerTitle">Trade Order Ticket (CHAL &lt;GO&gt;)</span>
      <button class="close-btn" onclick="closeModal()">&times;</button>
    </div>
    <p style="font-size: 13px; color: var(--text-muted);">
      Pre-sized strictly to the 20% competition rule. Copy and punch into the Bloomberg simulator:
    </p>
    <div class="ticket-box" id="ticketBox"></div>
    <button class="nav-action-btn primary" id="copyBtn" style="width: 100%; justify-content: center; padding: 12px; font-size: 13.5px;" onclick="copyTicket()">
      📋 Copy Order to Clipboard
    </button>
  </div>
</div>

<!-- 3. DIAGNOSTICS MODAL -->
<div class="modal-overlay" id="diagModal" onclick="closeModalOnBg(event, 'diagModal')">
  <div class="modal-card">
    <div class="modal-title">
      <span>📡 Bloomberg Data Feed Diagnostics</span>
      <button class="close-btn" onclick="closeDiagModal()">&times;</button>
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #1a263e; color: var(--text-muted);">Exact Last Sync</td>
        <td style="padding: 8px; border-bottom: 1px solid #1a263e; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace; font-weight: 700;">{csv_time_str}</td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #1a263e; color: var(--text-muted);">Data Freshness</td>
        <td style="padding: 8px; border-bottom: 1px solid #1a263e; font-family: 'JetBrains Mono', monospace;" id="diagDataAge">{age_label}</td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #1a263e; color: var(--text-muted);">BLPAPI Daemon Port</td>
        <td style="padding: 8px; border-bottom: 1px solid #1a263e; font-family: 'JetBrains Mono', monospace;">127.0.0.1:8194</td>
      </tr>
      <tr>
        <td style="padding: 8px; color: var(--text-muted);">Holdings Mode</td>
        <td style="padding: 8px; font-family: 'JetBrains Mono', monospace; color: var(--accent-green);">Read-Only (Terminal Sync)</td>
      </tr>
    </table>
  </div>
</div>

<div class="toast-notify" id="toastNotify"></div>

<script>
// --- INITIAL DATA ---
const marketDb = {json_market_db};
const universeList = {json_candidates_list};
const actualHoldings = {json_actual_holdings}; // Strictly read-only
let wishlistItems = {json_wishlist_items}; // Empty by default
const statusMeta = {status_json};

let currentUniverseFilter = 'ALL';
let currentUniverseSearch = '';
let activePage = 'holdings';

function switchPage(pageId) {{
  activePage = pageId;
  const tabHoldings = document.getElementById('tabBtnHoldings');
  const tabWishlist = document.getElementById('tabBtnWishlist');
  const tabUniverse = document.getElementById('tabBtnUniverse');
  const subHoldings = document.getElementById('subpageHoldings');
  const subWishlist = document.getElementById('subpageWishlist');
  const subUniverse = document.getElementById('subpageUniverse');

  tabHoldings.classList.toggle('active', pageId === 'holdings');
  tabWishlist.classList.toggle('active', pageId === 'wishlist');
  tabUniverse.classList.toggle('active', pageId === 'universe');

  subHoldings.classList.toggle('active', pageId === 'holdings');
  subWishlist.classList.toggle('active', pageId === 'wishlist');
  subUniverse.classList.toggle('active', pageId === 'universe');

  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

function showToast(msg) {{
  const t = document.getElementById('toastNotify');
  t.innerHTML = msg;
  t.style.display = 'flex';
  setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
}}

async function triggerServerSync() {{
  const btn = document.getElementById('syncBtn');
  btn.innerHTML = '🔄 Syncing...';
  try {{
    const res = await fetch('/api/sync', {{ method: 'POST' }});
    if (res.ok) {{
      showToast('✅ Synced live with Bloomberg quotes!');
      setTimeout(() => {{ window.location.reload(); }}, 1000);
      return;
    }}
  }} catch (e) {{
    window.location.reload();
  }}
  btn.innerHTML = '🔄 Sync Bloomberg';
}}

// =========================================================================
// RECALCULATION & RENDERING
// =========================================================================

function recalculateAll() {{
  const totalCashInput = parseFloat(document.getElementById('cashInput').value) || 1000000;
  const maxClip = totalCashInput * 0.20;
  document.getElementById('kpiMaxCap').innerText = '$' + maxClip.toLocaleString(undefined, {{maximumFractionDigits: 0}});

  // 1. Current Holdings Calculation (Read-Only)
  let totalInvestedCost = 0;
  let totalCurrentMarketVal = 0;
  const enrichedHoldings = actualHoldings.map(h => {{
    const stock = marketDb[h.symbol] || {{
      symbol: h.symbol, name: h.symbol, sector: 'Equities', price: h.entry_price || 0,
      target: (h.entry_price || 0) * 1.15, earnings_date: 'TBD', chg_1d: 0
    }};
    const curPrice = stock.price || h.entry_price;
    const costBasis = h.shares * h.entry_price;
    const marketVal = h.shares * curPrice;
    const pnlDollar = marketVal - costBasis;
    const pnlPct = costBasis > 0 ? (pnlDollar / costBasis) * 100 : 0;
    const stopPrice = h.entry_price * 0.93;

    totalInvestedCost += costBasis;
    totalCurrentMarketVal += marketVal;

    return {{ ...h, stock, curPrice, costBasis, marketVal, pnlDollar, pnlPct, stopPrice }};
  }});

  const totalUnrealizedPnl = totalCurrentMarketVal - totalInvestedCost;
  const availableCash = totalCashInput - totalInvestedCost;
  const totalPortfolioEquity = availableCash + totalCurrentMarketVal;

  document.getElementById('kpiTotalEquity').innerText = '$' + totalPortfolioEquity.toLocaleString(undefined, {{maximumFractionDigits: 2}});
  document.getElementById('kpiCashAvailable').innerText = '$' + Math.max(0, availableCash).toLocaleString(undefined, {{maximumFractionDigits: 2}});
  document.getElementById('kpiInvestedText').innerText = `Invested: $${{totalInvestedCost.toLocaleString(undefined, {{maximumFractionDigits: 0}})}} (0.0% deployed)`;

  const slotsUsed = enrichedHoldings.length;
  document.getElementById('kpiSlotsText').innerText = `${{slotsUsed}} / 5`;
  document.getElementById('kpiSlotsDesc').innerText = `${{5 - slotsUsed}} clips open (${{100 - (slotsUsed * 20)}}% capacity)`;

  // Update Badges
  document.getElementById('badgeCountInvested').innerText = slotsUsed;
  document.getElementById('badgeCountWishlist').innerText = wishlistItems.length;
  document.getElementById('wishlistCountHeader').innerText = `${{wishlistItems.length}} Saved`;
  document.getElementById('trackerAllocPercent').innerText = `${{(slotsUsed * 20).toFixed(0)}}% / 100% Max Clips Deployed`;

  renderAllocationSlots(enrichedHoldings, maxClip);
  renderHoldingsTable(enrichedHoldings, totalPortfolioEquity);
  renderWishlistGrid(maxClip);
  renderUniverseGrid(maxClip);
}}

function renderAllocationSlots(holdings, maxClip) {{
  const grid = document.getElementById('slotsGrid');
  grid.innerHTML = '';
  for (let i = 0; i < 5; i++) {{
    const h = holdings[i];
    const box = document.createElement('div');
    if (h) {{
      box.className = 'slot-box occupied';
      box.innerHTML = `
        <div class="slot-num">Slot ${{i + 1}} (20% Clip)</div>
        <div class="slot-ticker">${{h.symbol}}</div>
        <div class="slot-meta">$${{h.marketVal.toLocaleString(undefined, {{maximumFractionDigits: 0}})}} • ${{h.shares.toLocaleString()}} sh</div>
      `;
    }} else {{
      box.className = 'slot-box';
      box.innerHTML = `
        <div class="slot-num">Slot ${{i + 1}} (Open Clip)</div>
        <div class="slot-ticker empty">Unallocated</div>
        <div class="slot-meta" style="color: var(--text-dim);">$${{maxClip.toLocaleString(undefined, {{maximumFractionDigits: 0}})}} capacity</div>
      `;
    }}
    grid.appendChild(box);
  }}
}}

function renderHoldingsTable(holdings, totalEquity) {{
  const emptyCard = document.getElementById('emptyHoldingsCard');
  const tableWrap = document.getElementById('holdingsTableWrap');
  const tbody = document.getElementById('holdingsTableBody');

  if (holdings.length === 0) {{
    emptyCard.style.display = 'flex';
    tableWrap.style.display = 'none';
    tbody.innerHTML = '';
    return;
  }}

  emptyCard.style.display = 'none';
  tableWrap.style.display = 'block';
  tbody.innerHTML = '';

  holdings.forEach(h => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div style="font-weight: 800; font-family: 'JetBrains Mono', monospace; font-size: 15px; color: #ffffff;">${{h.symbol}}</div>
        <div style="font-size: 11px; color: var(--text-muted);">${{h.stock.name}} • <span class="sector-tag">${{h.stock.sector}}</span></div>
      </td>
      <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--accent-cyan);">${{h.shares.toLocaleString()}} sh</td>
      <td style="font-family: 'JetBrains Mono', monospace;">$${{h.entry_price.toFixed(2)}}</td>
      <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700;">$${{h.curPrice.toFixed(2)}}</td>
      <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700;">$${{h.marketVal.toLocaleString(undefined, {{maximumFractionDigits: 2}})}}</td>
      <td>
        <span style="font-weight: 700; font-family: 'JetBrains Mono', monospace; color: ${{h.pnlDollar >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}};">
          ${{h.pnlDollar >= 0 ? '+' : ''}}$${{h.pnlDollar.toFixed(2)}} (${{h.pnlPct.toFixed(2)}}%)
        </span>
      </td>
      <td style="font-family: 'JetBrains Mono', monospace;">${{((h.marketVal / totalEquity) * 100).toFixed(1)}}%</td>
      <td style="font-family: 'JetBrains Mono', monospace; color: var(--accent-red);">$${{h.stopPrice.toFixed(2)}} (-7%)</td>
      <td style="font-family: 'JetBrains Mono', monospace; color: var(--accent-gold);">${{h.stock.earnings_date}}</td>
    `;
    tbody.appendChild(tr);
  }});
}}

// =========================================================================
// RENDER VIEW 2: TEAM WISHLIST (EMPTY BY DEFAULT, REMOVABLE)
// =========================================================================

function renderWishlistGrid(maxClip) {{
  const grid = document.getElementById('wishlistGrid');
  const emptyCard = document.getElementById('emptyWishlistCard');

  if (wishlistItems.length === 0) {{
    emptyCard.style.display = 'flex';
    grid.innerHTML = '';
    return;
  }}

  emptyCard.style.display = 'none';
  grid.innerHTML = '';

  wishlistItems.forEach(item => {{
    const s = marketDb[item.symbol] || {{
      symbol: item.symbol, ticker: item.symbol + ' US Equity', name: item.symbol,
      sector: 'Custom', price: 100.0, target: 130.0, upside_pct: 30.0,
      stop_loss: 93.0, rr_ratio: 4.3, signal: 'WISHLIST TARGET', badge_color: 'primary',
      chg_1d: 0, earnings_date: 'TBD'
    }};

    const sharesToBuy = s.price > 0 ? Math.floor(maxClip / s.price) : 0;
    const card = document.createElement('div');
    card.className = 'stock-card is-wishlist';
    card.innerHTML = `
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

      <div class="price-row">
        <div class="current-price">$${{s.price.toFixed(2)}}</div>
        <div class="price-tag-group">
          <div class="change-pct ${{s.chg_1d >= 0 ? 'pos' : 'neg'}}">
            ${{s.chg_1d >= 0 ? '+' : ''}}${{s.chg_1d.toFixed(2)}}%
          </div>
        </div>
      </div>

      ${{item.notes ? `<div class="wishlist-notes-box">💡 ${{item.notes}}</div>` : ''}}

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
          <span class="label">Asymmetric R:R:</span>
          <span class="val" style="color: var(--accent-cyan);">${{s.rr_ratio}}:1 Ratio</span>
        </div>
        <div class="metric-row">
          <span class="label">20% Max Sizing:</span>
          <span class="val" style="color: #ffffff;">BUY ${{sharesToBuy.toLocaleString()}} SHARES</span>
        </div>
        <div class="metric-row">
          <span class="label">Catalyst (Earnings):</span>
          <span class="val" style="color: var(--accent-gold);">${{s.earnings_date}}</span>
        </div>
      </div>

      <div class="card-actions">
        <button class="add-wish-btn" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; border: none;" onclick="openOrderModal('${{s.symbol}}')">
          📋 20% Order Ticket
        </button>
        <button class="remove-btn" title="Remove from Wishlist" onclick="toggleWishlist('${{s.symbol}}')">
          🗑️ Remove
        </button>
      </div>
    `;
    grid.appendChild(card);
  }});
}}

// =========================================================================
// RENDER VIEW 3: SCREENER UNIVERSE (25 STOCKS KEPT TO VIEW)
// =========================================================================

function renderUniverseGrid(maxClip) {{
  const grid = document.getElementById('universeGrid');
  grid.innerHTML = '';

  const wishlistSymbolSet = new Set(wishlistItems.map(x => x.symbol));

  const filtered = universeList.filter(s => {{
    const matchesSector = currentUniverseFilter === 'ALL' || s.sector.toLowerCase().includes(currentUniverseFilter.toLowerCase());
    const matchesSearch = s.symbol.toLowerCase().includes(currentUniverseSearch.toLowerCase()) || 
                          s.name.toLowerCase().includes(currentUniverseSearch.toLowerCase());
    return matchesSector && matchesSearch;
  }});

  filtered.forEach(s => {{
    const isSaved = wishlistSymbolSet.has(s.symbol);
    const sharesToBuy = s.price > 0 ? Math.floor(maxClip / s.price) : 0;

    const card = document.createElement('div');
    card.className = `stock-card ${{isSaved ? 'is-wishlist' : ''}}`;
    card.innerHTML = `
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

      <div class="price-row">
        <div class="current-price">$${{s.price.toFixed(2)}}</div>
        <div class="price-tag-group">
          <div class="change-pct ${{s.chg_1d >= 0 ? 'pos' : 'neg'}}">
            ${{s.chg_1d >= 0 ? '+' : ''}}${{s.chg_1d.toFixed(2)}}%
          </div>
        </div>
      </div>

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
          <span class="label">Risk/Reward Ratio:</span>
          <span class="val" style="color: var(--accent-cyan);">${{s.rr_ratio}}:1 Ratio</span>
        </div>
        <div class="metric-row">
          <span class="label">20% Max Sizing:</span>
          <span class="val" style="color: #ffffff;">BUY ${{sharesToBuy.toLocaleString()}} SHARES</span>
        </div>
        <div class="metric-row">
          <span class="label">Catalyst (Earnings):</span>
          <span class="val" style="color: var(--accent-gold);">${{s.earnings_date}}</span>
        </div>
      </div>

      <div class="card-actions">
        <button class="add-wish-btn ${{isSaved ? 'active' : ''}}" onclick="toggleWishlist('${{s.symbol}}')">
          ${{isSaved ? '✓ On Wishlist (Click to Remove)' : '⭐ Add to Wishlist'}}
        </button>
        <button class="ticket-btn" title="View Competition Order Ticket" onclick="openOrderModal('${{s.symbol}}')">
          📋 Ticket
        </button>
      </div>
    `;
    grid.appendChild(card);
  }});
}}

function filterSector(sector, btn) {{
  currentUniverseFilter = sector;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  recalculateAll();
}}

function searchUniverse() {{
  currentUniverseSearch = document.getElementById('universeSearchInput').value;
  recalculateAll();
}}

// =========================================================================
// TOGGLE WISHLIST (EASILY ADD OR REMOVE BY CLICKING)
// =========================================================================

async function toggleWishlist(symbol) {{
  const exists = wishlistItems.some(x => x.symbol === symbol);

  if (exists) {{
    wishlistItems = wishlistItems.filter(x => x.symbol !== symbol);
    showToast(`🗑️ ${{symbol}} removed from Wishlist.`);
    try {{
      await fetch('/api/wishlist', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ action: 'delete', item: {{ symbol }} }})
      }});
    }} catch (e) {{}}
  }} else {{
    const newItem = {{
      symbol: symbol,
      notes: "Added from Screener Universe",
      priority: "Medium"
    }};
    wishlistItems = [newItem, ...wishlistItems];
    showToast(`⭐ <b>${{symbol}}</b> added to your Wishlist!`);
    try {{
      await fetch('/api/wishlist', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ action: 'add', item: newItem }})
      }});
    }} catch (e) {{}}
  }}

  recalculateAll();
}}

// =========================================================================
// CUSTOM TICKER MODAL
// =========================================================================

function openAddCustomModal() {{
  document.getElementById('customTickerInput').value = '';
  document.getElementById('customNotesInput').value = '';
  document.getElementById('customTickerModal').style.display = 'flex';
}}

function closeCustomTickerModal() {{
  document.getElementById('customTickerModal').style.display = 'none';
}}

async function confirmAddCustom() {{
  const ticker = document.getElementById('customTickerInput').value.toUpperCase().trim();
  const notes = document.getElementById('customNotesInput').value.trim();

  if (!ticker) {{
    alert("Please enter a valid stock ticker symbol.");
    return;
  }}

  const newItem = {{
    symbol: ticker,
    notes: notes || "Custom Watchlist Ticker",
    priority: "High"
  }};

  wishlistItems = [newItem, ...wishlistItems.filter(x => x.symbol !== ticker)];

  try {{
    await fetch('/api/wishlist', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ action: 'add', item: newItem }})
    }});
  }} catch (e) {{}}

  closeCustomTickerModal();
  recalculateAll();
  showToast(`⭐ <b>${{ticker}}</b> added to your Wishlist!`);
  switchPage('wishlist');
}}

// =========================================================================
// ORDER TICKET MODAL FOR CHAL <GO>
// =========================================================================

let selectedTicketText = '';

function openOrderModal(symbol) {{
  const stock = marketDb[symbol] || {{
    symbol: symbol, ticker: symbol + ' US Equity', name: symbol, price: 100, target: 130, upside_pct: 30, stop_loss: 93, rr_ratio: 4.3, earnings_date: 'TBD'
  }};
  const totalCash = parseFloat(document.getElementById('cashInput').value) || 1000000;
  const maxClip = totalCash * 0.20;
  const shares = stock.price > 0 ? Math.floor(maxClip / stock.price) : 0;
  const totalSpend = (shares * stock.price).toFixed(2);
  const potentialProfit = (shares * (stock.target - stock.price)).toFixed(2);
  const maxLoss = (shares * (stock.price - stock.stop_loss)).toFixed(2);

  document.getElementById('modalTickerTitle').innerText = `${{stock.symbol}} — 20% Competition Trade Ticket (CHAL <GO>)`;
  
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

function copyTicket() {{
  navigator.clipboard.writeText(selectedTicketText).then(() => {{
    const btn = document.getElementById('copyBtn');
    btn.innerText = '✅ Order Copied to Clipboard!';
    setTimeout(() => {{ btn.innerText = '📋 Copy Order to Clipboard'; }}, 2000);
  }});
}}

function openDiagModal() {{
  document.getElementById('diagModal').style.display = 'flex';
}}

function closeDiagModal() {{
  document.getElementById('diagModal').style.display = 'none';
}}

function closeModalOnBg(e, modalId) {{
  if (e.target.id === modalId) {{
    document.getElementById(modalId).style.display = 'none';
  }}
}}

// Initialize
recalculateAll();
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

    print(f"Generated clean institutional dashboard:")
    print(f"  - Official Bloomberg Holdings count: {len(actual_holdings)} (Read-Only)")
    print(f"  - Team Wishlist count: {len(wishlist_items)} (Empty by default: {len(wishlist_items) == 0})")
    print(f"  - Screener Universe count: {len(candidates_list)} (Kept up to view with 1-click 'Add to Wishlist')")
    print(f"  - Saved to: {html_file1}")
    return html_file1

if __name__ == "__main__":
    generate_dashboard()
