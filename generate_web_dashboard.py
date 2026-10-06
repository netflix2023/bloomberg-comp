"""
Bloomberg Trading Challenge - Web Dashboard Generator
Generates an interactive, beautiful HTML dashboard (index.html / dashboard.html)
using live data from the Bloomberg Terminal. Designed to be ultra-intuitive for students
who don't know how to navigate the complex Bloomberg Terminal interface.
"""

import os
import json
from datetime import datetime
import pandas as pd

def generate_dashboard():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "bloomberg_live_remote_screener.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}. Run sync_remote_excel.py first.")

    df = pd.read_csv(csv_path)

    # Calculate computed fields
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

    # Sort by upside_pct descending
    candidates.sort(key=lambda x: x["upside_pct"], reverse=True)
    json_data = json.dumps(candidates)
    sync_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dallas College Bloomberg Trading Challenge — Live Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #090d16;
      --card-bg: #111726;
      --card-border: #1e293b;
      --accent-cyan: #00e5ff;
      --accent-green: #00e676;
      --accent-red: #ff3d71;
      --accent-gold: #ffb300;
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
      max-width: 1400px;
      margin: 0 auto;
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
    .sync-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(0, 230, 118, 0.1);
      border: 1px solid rgba(0, 230, 118, 0.3);
      color: var(--accent-green);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
    }}
    .pulse-dot {{
      width: 8px;
      height: 8px;
      background-color: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--accent-green);
    }}

    /* Top Stats Grid */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
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

    /* Beginner Alert Box */
    .guide-banner {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(17, 23, 38, 0.9) 100%);
      border: 1px solid #334155;
      border-left: 4px solid var(--accent-cyan);
      border-radius: 12px;
      padding: 18px 24px;
      margin-bottom: 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .guide-banner h3 {{
      font-size: 16px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 4px;
    }}
    .guide-banner p {{
      font-size: 14px;
      color: var(--text-muted);
      max-width: 900px;
    }}
    .guide-badge {{
      background: rgba(0, 229, 255, 0.15);
      color: var(--accent-cyan);
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 13px;
    }}

    /* Controls: Filter & Search */
    .controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
      margin-bottom: 20px;
    }}
    .filter-tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .filter-btn {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: #1e293b;
      color: #ffffff;
      border-color: var(--accent-cyan);
    }}
    .search-box {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: #ffffff;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 14px;
      outline: none;
      min-width: 260px;
    }}
    .search-box:focus {{
      border-color: var(--accent-cyan);
    }}

    /* Stock Cards Grid */
    .stocks-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 18px;
    }}
    .stock-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      position: relative;
      transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    }}
    .stock-card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
      border-color: #3b82f6;
    }}
    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .ticker-name h2 {{
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .company-title {{
      font-size: 13px;
      color: var(--text-muted);
      font-weight: 500;
    }}
    .sector-tag {{
      display: inline-block;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 6px;
      background: rgba(148, 163, 184, 0.1);
      color: #cbd5e1;
      margin-top: 4px;
    }}
    .signal-pill {{
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .signal-pill.success {{
      background: rgba(0, 230, 118, 0.15);
      color: var(--accent-green);
      border: 1px solid rgba(0, 230, 118, 0.3);
    }}
    .signal-pill.primary {{
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }}
    .signal-pill.secondary {{
      background: rgba(148, 163, 184, 0.15);
      color: #94a3b8;
    }}

    .price-row {{
      display: flex;
      align-items: baseline;
      gap: 12px;
      padding: 10px 0;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .current-price {{
      font-size: 28px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
    }}
    .change-pct {{
      font-size: 14px;
      font-weight: 700;
    }}
    .change-pct.pos {{ color: var(--accent-green); }}
    .change-pct.neg {{ color: var(--accent-red); }}

    /* Key Target & Sizing Metrics */
    .metric-rows {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .metric-row {{
      display: flex;
      justify-content: space-between;
      font-size: 13px;
    }}
    .metric-row .label {{
      color: var(--text-muted);
    }}
    .metric-row .val {{
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }}
    .val-highlight {{
      color: var(--accent-green);
    }}
    .val-stop {{
      color: var(--accent-red);
    }}

    /* Action Button */
    .trade-btn {{
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      color: #ffffff;
      border: none;
      padding: 12px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      transition: filter 0.2s;
    }}
    .trade-btn:hover {{
      filter: brightness(1.15);
    }}

    /* Trade Modal */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-card {{
      background: #111726;
      border: 1px solid #334155;
      border-radius: 16px;
      max-width: 520px;
      width: 100%;
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.75);
    }}
    .modal-title {{
      font-size: 20px;
      font-weight: 800;
      color: #ffffff;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .close-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 24px;
      cursor: pointer;
    }}
    .ticket-box {{
      background: #090d16;
      border: 1px solid #1e293b;
      border-radius: 10px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
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
    }}
  </style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <div class="header">
    <div class="title-group">
      <h1>Bloomberg Global Trading Challenge — Dallas College</h1>
      <p>Simplified Live Decision & Position-Sizing Terminal • Synced from local Bloomberg daemon (127.0.0.1:8194)</p>
    </div>
    <div class="sync-badge">
      <div class="pulse-dot"></div>
      <span>Data Synced: {sync_time}</span>
    </div>
  </div>

  <!-- Top Stats Grid -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Total Portfolio Cash ($)</div>
      <input type="number" id="cashInput" class="input-box" value="1000000" oninput="updateSizing()">
      <div class="stat-desc">Edit this number to recompute all position clips</div>
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
      <div class="stat-label">Winning Math Edge</div>
      <div class="stat-value" style="color: var(--accent-green);">3:1 Ratio</div>
      <div class="stat-desc">40% win rate yields positive net compounding</div>
    </div>
  </div>

  <!-- Beginner Guide Banner -->
  <div class="guide-banner">
    <div>
      <h3>🚀 How To Use This Dashboard (No Bloomberg Experience Needed)</h3>
      <p>
        You do not need to memorize complex Bloomberg commands! 
        1) Pick a stock with high <b>Wall St Upside</b> and <b>3:1+ R:R</b>.
        2) Click <b>"Generate Trade Ticket"</b> below to see the exact number of shares to buy.
        3) In the lab terminal, type <code>CHAL &lt;GO&gt;</code>, type the symbol and exact share count, and hit Enter. That's it!
      </p>
    </div>
    <div class="guide-badge">20% Cap Auto-Calculated</div>
  </div>

  <!-- Controls -->
  <div class="controls">
    <div class="filter-tabs">
      <button class="filter-btn active" onclick="filterSector('ALL', this)">All Stocks (25)</button>
      <button class="filter-btn" onclick="filterSector('Information Technology', this)">AI & Tech</button>
      <button class="filter-btn" onclick="filterSector('Health Care', this)">Healthcare / Pharma</button>
      <button class="filter-btn" onclick="filterSector('Industrials', this)">Industrials</button>
      <button class="filter-btn" onclick="filterSector('Financials', this)">Financials</button>
      <button class="filter-btn" onclick="filterSector('Consumer Discretionary', this)">Consumer</button>
    </div>
    <input type="text" id="searchInput" class="search-box" placeholder="Search ticker or name..." oninput="searchStocks()">
  </div>

  <!-- Stock Cards Grid -->
  <div class="stocks-grid" id="stocksGrid"></div>
</div>

<!-- Modal -->
<div class="modal-overlay" id="tradeModal" onclick="closeModalOnBg(event)">
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
let currentFilter = 'ALL';
let currentSearch = '';

function renderStocks() {{
  const grid = document.getElementById('stocksGrid');
  grid.innerHTML = '';
  const totalCash = parseFloat(document.getElementById('cashInput').value) || 1000000;
  const maxClip = totalCash * 0.20;

  const filtered = stocksData.filter(s => {{
    const matchesSector = currentFilter === 'ALL' || s.sector.toLowerCase().includes(currentFilter.toLowerCase());
    const matchesSearch = s.symbol.toLowerCase().includes(currentSearch.toLowerCase()) || 
                          s.name.toLowerCase().includes(currentSearch.toLowerCase());
    return matchesSector && matchesSearch;
  }});

  filtered.forEach(s => {{
    const sharesToBuy = s.price > 0 ? Math.floor(maxClip / s.price) : 0;
    const actualInvested = sharesToBuy * s.price;
    const targetGain = sharesToBuy * (s.target - s.price);
    const stopLossRisk = sharesToBuy * (s.price - s.stop_loss);

    const card = document.createElement('div');
    card.className = 'stock-card';
    card.innerHTML = `
      <div class="card-top">
        <div class="ticker-name">
          <h2>${{s.symbol}} <span class="sector-tag">${{s.sector}}</span></h2>
          <div class="company-title">${{s.name}}</div>
        </div>
        <span class="signal-pill ${{s.badge_color}}">${{s.signal}}</span>
      </div>

      <div class="price-row">
        <div class="current-price">$${{s.price.toFixed(2)}}</div>
        <div class="change-pct ${{s.chg_1d >= 0 ? 'pos' : 'neg'}}">
          ${{s.chg_1d >= 0 ? '+' : ''}}${{s.chg_1d.toFixed(2)}}% (1D)
        </div>
      </div>

      <div class="metric-rows">
        <div class="metric-row">
          <span class="label">Wall St Target Price:</span>
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
          <span class="label">Analyst Consensus:</span>
          <span class="val">${{s.buy_pct}}% Buy (${{s.buy_rec}} Buy / ${{s.sell_rec}} Sell)</span>
        </div>
        <div class="metric-row">
          <span class="label">Catalyst (Earnings Date):</span>
          <span class="val" style="color: var(--accent-gold);">${{s.earnings_date}}</span>
        </div>
      </div>

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
    <div class="ticket-line"><span>Strict 7% Stop-Loss:</span><span style="color: var(--accent-red);">$${{stock.stop_loss.toFixed(2)}}</span></div>
    <div class="ticket-line"><span>Upside Payoff:</span><span style="color: var(--accent-green);">+$${{Number(potentialProfit).toLocaleString()}}</span></div>
    <div class="ticket-line"><span>Downside Risk:</span><span style="color: var(--accent-red);">-$${{Number(maxLoss).toLocaleString()}}</span></div>
    <div class="ticket-line"><span>Upcoming Catalyst:</span><span style="color: var(--accent-gold);">${{stock.earnings_date}}</span></div>
  `;

  document.getElementById('tradeModal').style.display = 'flex';
}}

function closeModal() {{
  document.getElementById('tradeModal').style.display = 'none';
}}

function closeModalOnBg(e) {{
  if (e.target.id === 'tradeModal') closeModal();
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

    print(f"Generated web dashboard:\n  - {html_file1}\n  - {html_file2}")
    return html_file1

if __name__ == "__main__":
    generate_dashboard()
