"""
╔══════════════════════════════════════════════════════════════════════╗
║           AI STACK BENCHMARK DASHBOARD                               ║
║           Powered by yfinance + Anthropic API                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  SETUP:                                                              ║
║    pip install yfinance pandas plotly dash anthropic                 ║
║    export ANTHROPIC_API_KEY="your-key-here"                          ║
║    python ai_stack_dashboard.py                                      ║
║  Then open: http://127.0.0.1:8050                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import anthropic

from dash import Dash, dcc, html, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc

# ──────────────────────────────────────────────────────────────────────────────
# API KEY SETUP — checks env var, then .env file, then prompts user
# ──────────────────────────────────────────────────────────────────────────────

def load_api_key():
    """Load Anthropic API key from env, .env file, or prompt the user."""
    # 1. Check environment variable first
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key and key.startswith("sk-"):
        print(f"✓ Anthropic API key loaded from environment variable.")
        return key

    # 2. Check for a .env file in the same directory as this script
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key.startswith("sk-"):
                    os.environ["ANTHROPIC_API_KEY"] = key
                    print(f"✓ Anthropic API key loaded from .env file.")
                    return key

    # 3. Prompt the user and save to .env for next time
    print("\n" + "="*60)
    print("  ANTHROPIC API KEY NOT FOUND")
    print("  Get your key at: https://console.anthropic.com/")
    print("="*60)
    key = input("  Paste your Anthropic API key (or press Enter to skip): ").strip()
    if key.startswith("sk-"):
        os.environ["ANTHROPIC_API_KEY"] = key
        # Save to .env file so it's remembered next time
        env_file.write_text(f'ANTHROPIC_API_KEY="{key}"\n')
        print(f"  ✓ Key saved to {env_file} — won't ask again next time.")
        return key
    else:
        print("  ⚠ No valid key entered. AI Analysis will be disabled.")
        print("    (Dashboard will still run with full market data.)")
        return ""

ANTHROPIC_API_KEY = load_api_key()

# ──────────────────────────────────────────────────────────────────────────────
# AI STACK UNIVERSE
# ──────────────────────────────────────────────────────────────────────────────

AI_STACK = {
    "L1 – Raw Materials": {
        "color": "#8B4513",
        "light": "#D4956B",
        "description": "Silicon, copper, rare earth metals, lithium — physical inputs for every chip",
        "companies": {
            "BHP":   {"name": "BHP Group",             "cap": "Large"},
            "RIO":   {"name": "Rio Tinto",              "cap": "Large"},
            "FCX":   {"name": "Freeport-McMoRan",       "cap": "Large"},
            "SCCO":  {"name": "Southern Copper",        "cap": "Large"},
            "VALE":  {"name": "Vale",                   "cap": "Large"},
            "MP":    {"name": "MP Materials",           "cap": "Mid"},
            "ALB":   {"name": "Albemarle",              "cap": "Mid"},
            "LYSDY": {"name": "Lynas Rare Earths",      "cap": "Mid"},
            "UUUU":  {"name": "Energy Fuels",           "cap": "Small"},
            "PPTA":  {"name": "Perpetua Resources",     "cap": "Small"},
            "COPX":  {"name": "Global X Copper ETF",    "cap": "ETF"},
            "REMX":  {"name": "VanEck Rare Earth ETF",  "cap": "ETF"},
        }
    },
    "L2 – Semiconductors": {
        "color": "#1A3A8C",
        "light": "#5B8DD9",
        "description": "GPU/TPU/ASIC designers, foundries, packaging houses, chip equipment",
        "companies": {
            "NVDA":  {"name": "NVIDIA",                 "cap": "Large"},
            "TSM":   {"name": "TSMC",                   "cap": "Large"},
            "AVGO":  {"name": "Broadcom",               "cap": "Large"},
            "AMD":   {"name": "AMD",                    "cap": "Large"},
            "INTC":  {"name": "Intel",                  "cap": "Large"},
            "QCOM":  {"name": "Qualcomm",               "cap": "Large"},
            "MU":    {"name": "Micron Technology",      "cap": "Large"},
            "AMAT":  {"name": "Applied Materials",      "cap": "Large"},
            "ASML":  {"name": "ASML Holding",           "cap": "Large"},
            "LRCX":  {"name": "Lam Research",           "cap": "Large"},
            "KLAC":  {"name": "KLA Corporation",        "cap": "Large"},
            "MRVL":  {"name": "Marvell Technology",     "cap": "Mid"},
            "MPWR":  {"name": "Monolithic Power",       "cap": "Mid"},
            "AMKR":  {"name": "Amkor Technology",       "cap": "Mid"},
            "ONTO":  {"name": "Onto Innovation",        "cap": "Mid"},
            "CAMT":  {"name": "Camtek",                 "cap": "Mid"},
        }
    },
    "L3 – Compute Infrastructure": {
        "color": "#0D6B5E",
        "light": "#3DB8A5",
        "description": "Data centers, networking, cooling, power delivery, cloud GPU providers",
        "companies": {
            "ANET":  {"name": "Arista Networks",        "cap": "Large"},
            "EQIX":  {"name": "Equinix",                "cap": "Large"},
            "DLR":   {"name": "Digital Realty",         "cap": "Large"},
            "VRT":   {"name": "Vertiv Holdings",        "cap": "Large"},
            "ETN":   {"name": "Eaton Corporation",      "cap": "Large"},
            "CSCO":  {"name": "Cisco Systems",          "cap": "Large"},
            "SBGSY": {"name": "Schneider Electric",     "cap": "Large"},
            "IRM":   {"name": "Iron Mountain",          "cap": "Large"},
            "ALAB":  {"name": "Astera Labs",            "cap": "Mid"},
            "CRDO":  {"name": "Credo Technology",       "cap": "Mid"},
            "COHR":  {"name": "Coherent Corp",          "cap": "Mid"},
            "LITE":  {"name": "Lumentum Holdings",      "cap": "Mid"},
            "SMCI":  {"name": "Super Micro Computer",   "cap": "Mid"},
            "CRWV":  {"name": "CoreWeave",              "cap": "Mid"},
            "FN":    {"name": "Fabrinet",               "cap": "Mid"},
            "MOD":   {"name": "Modine Manufacturing",   "cap": "Mid"},
            "NVT":   {"name": "nVent Electric",         "cap": "Mid"},
        }
    },
    "L4 – Foundation Models": {
        "color": "#6B1A8C",
        "light": "#B366E0",
        "description": "Hyperscalers and organizations training large-scale AI models",
        "companies": {
            "MSFT":  {"name": "Microsoft",              "cap": "Large"},
            "GOOGL": {"name": "Alphabet",               "cap": "Large"},
            "META":  {"name": "Meta Platforms",         "cap": "Large"},
            "AMZN":  {"name": "Amazon",                 "cap": "Large"},
            "NVDA":  {"name": "NVIDIA (also L2)",       "cap": "Large"},
        }
    },
    "L5 – Orchestration & Evaluation": {
        "color": "#B85C00",
        "light": "#F0A057",
        "description": "MLOps, observability, agent frameworks, evaluation platforms",
        "companies": {
            "PLTR":  {"name": "Palantir",               "cap": "Large"},
            "DDOG":  {"name": "Datadog",                "cap": "Large"},
            "DT":    {"name": "Dynatrace",              "cap": "Large"},
            "PATH":  {"name": "UiPath",                 "cap": "Mid"},
            "AI":    {"name": "C3.ai",                  "cap": "Small"},
        }
    },
    "L6 – Enterprise AI Platforms": {
        "color": "#1A5C2E",
        "light": "#4DB876",
        "description": "Vertical AI applications embedded into enterprise workflows",
        "companies": {
            "CRM":   {"name": "Salesforce",             "cap": "Large"},
            "NOW":   {"name": "ServiceNow",             "cap": "Large"},
            "SAP":   {"name": "SAP",                    "cap": "Large"},
            "ORCL":  {"name": "Oracle",                 "cap": "Large"},
            "IBM":   {"name": "IBM",                    "cap": "Large"},
            "WDAY":  {"name": "Workday",                "cap": "Large"},
            "ADBE":  {"name": "Adobe",                  "cap": "Large"},
            "VEEV":  {"name": "Veeva Systems",          "cap": "Mid"},
            "APPN":  {"name": "Appian",                 "cap": "Small"},
        }
    },
    "L7 – Governance & Identity": {
        "color": "#8C1A1A",
        "light": "#E05555",
        "description": "Identity management, deepfake detection, AI governance, compliance",
        "companies": {
            "OKTA":  {"name": "Okta",                   "cap": "Large"},
            "CYBR":  {"name": "CyberArk",               "cap": "Large"},
            "PANW":  {"name": "Palo Alto Networks",     "cap": "Large"},
            "CRWD":  {"name": "CrowdStrike",            "cap": "Large"},
            "SAIL":  {"name": "SailPoint",              "cap": "Mid"},
        }
    },
    "⚡ Power & Energy": {
        "color": "#7A6B00",
        "light": "#D4B800",
        "description": "Power generation, nuclear, grid infrastructure for AI data centers",
        "companies": {
            "NEE":   {"name": "NextEra Energy",         "cap": "Large"},
            "CEG":   {"name": "Constellation Energy",   "cap": "Large"},
            "DUK":   {"name": "Duke Energy",            "cap": "Large"},
            "GEV":   {"name": "GE Vernova",             "cap": "Large"},
            "VST":   {"name": "Vistra Energy",          "cap": "Mid"},
            "BE":    {"name": "Bloom Energy",           "cap": "Small"},
            "OKLO":  {"name": "Oklo",                   "cap": "Small"},
            "SMR":   {"name": "NuScale Power",          "cap": "Small"},
            "FLNC":  {"name": "Fluence Energy",         "cap": "Small"},
        }
    }
}

# Benchmark indices for comparison
BENCHMARKS = {
    "SPY":  "S&P 500",
    "QQQ":  "NASDAQ 100",
    "SOXX": "iShares Semiconductor ETF",
}

# ──────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ──────────────────────────────────────────────────────────────────────────────

def get_all_tickers():
    tickers = set()
    for layer_data in AI_STACK.values():
        tickers.update(layer_data["companies"].keys())
    tickers.update(BENCHMARKS.keys())
    return list(tickers)

def fetch_price_data(period="1y"):
    """Fetch historical price data for all tickers."""
    all_tickers = get_all_tickers()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching data for {len(all_tickers)} tickers...")
    
    end = datetime.today()
    period_map = {
        "3mo": 90, "6mo": 180, "1y": 365,
        "2y": 730, "3y": 1095, "5y": 1825
    }
    days = period_map.get(period, 365)
    start = end - timedelta(days=days)
    
    try:
        raw = yf.download(
            tickers=all_tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            threads=True
        )
        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw["Close"]
        else:
            prices = raw[["Close"]]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Data fetched: {prices.shape[1]} tickers, {len(prices)} days")
        return prices
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def compute_normalized_returns(prices):
    """Normalize prices to 100 at start for relative comparison."""
    return (prices / prices.iloc[0]) * 100

def compute_layer_index(prices, layer_key):
    """Equal-weighted index for a given layer."""
    tickers = [t for t in AI_STACK[layer_key]["companies"].keys() if t in prices.columns]
    if not tickers:
        return pd.Series(dtype=float)
    layer_prices = prices[tickers].dropna(how="all")
    normalized = compute_normalized_returns(layer_prices)
    return normalized.mean(axis=1)

def get_current_stats(prices, tickers):
    """Get current price stats for a list of tickers."""
    stats = []
    for ticker in tickers:
        if ticker not in prices.columns:
            continue
        series = prices[ticker].dropna()
        if len(series) < 2:
            continue
        current = series.iloc[-1]
        prev_close = series.iloc[-2]
        start = series.iloc[0]
        pct_1d = ((current - prev_close) / prev_close) * 100
        pct_period = ((current - start) / start) * 100

        # Get company name
        name = ticker
        for layer_data in AI_STACK.values():
            if ticker in layer_data["companies"]:
                name = layer_data["companies"][ticker]["name"]
                break
        if ticker in BENCHMARKS:
            name = BENCHMARKS[ticker]

        stats.append({
            "Ticker": ticker,
            "Name": name,
            "Price": round(current, 2),
            "1D %": round(pct_1d, 2),
            "Period %": round(pct_period, 2),
            "52W High": round(series.rolling(252).max().iloc[-1], 2) if len(series) >= 252 else round(series.max(), 2),
            "52W Low": round(series.rolling(252).min().iloc[-1], 2) if len(series) >= 252 else round(series.min(), 2),
        })
    return pd.DataFrame(stats).sort_values("Period %", ascending=False)

# ──────────────────────────────────────────────────────────────────────────────
# ANTHROPIC AI ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────

def get_ai_analysis(layer_stats_json: str, layer_name: str, period: str) -> str:
    """Use Claude to analyze layer performance data."""
    api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ No Anthropic API key found.\n\nRestart the dashboard and paste your key when prompted.\nGet one free at: https://console.anthropic.com/"
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a financial analyst specializing in AI sector equities. 
    
Analyze the following stock performance data for the **{layer_name}** layer of the AI technology stack over a **{period}** lookback period.

Performance Data (JSON):
{layer_stats_json}

Please provide:
1. **Key Outperformers**: Which 2-3 stocks stand out positively and why (connect to AI stack fundamentals)
2. **Laggards**: Which 1-2 stocks underperformed and the likely cause
3. **Layer Thesis**: Is this layer gaining or losing investment momentum? 
4. **Notable Signal**: One actionable observation for investors monitoring this layer
5. **Risk Factor**: The single biggest risk to this layer's continued performance

Keep your response concise (300 words max), data-driven, and focused on AI stack dynamics. Use the performance numbers in your analysis."""
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Analysis unavailable: {str(e)}"

def get_portfolio_analysis(all_layer_returns: str, period: str) -> str:
    """Claude analysis of the full AI stack cross-layer performance."""
    api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ No Anthropic API key found.\n\nRestart the dashboard and paste your key when prompted.\nGet one free at: https://console.anthropic.com/"
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a senior portfolio manager specializing in AI infrastructure and technology investments.

Below is the equal-weighted index performance for each layer of the AI technology stack over **{period}**:

{all_layer_returns}

Provide a strategic cross-layer analysis covering:
1. **Stack Flow**: Where is capital rotating within the AI stack right now?
2. **Leading vs. Lagging Layers**: Which layers are leading/lagging the S&P 500 benchmark?
3. **Investment Positioning**: For a new investor, which 2 layers offer the best risk/reward today?
4. **Macro Signal**: What does the relative performance of infrastructure (L2/L3) vs. applications (L5/L6) tell us about AI adoption maturity?
5. **Contrarian Opportunity**: Is there a layer being overlooked that deserves attention?

Be specific, cite the performance numbers, and keep it under 400 words."""
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Analysis unavailable: {str(e)}"

# ──────────────────────────────────────────────────────────────────────────────
# DASH APP
# ──────────────────────────────────────────────────────────────────────────────

# Try importing DBC, fall back gracefully
try:
    import dash_bootstrap_components as dbc
    HAS_DBC = True
except ImportError:
    HAS_DBC = False

app = Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap",
        dbc.themes.DARKLY if HAS_DBC else ""
    ] if HAS_DBC else [
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap"
    ],
    title="AI Stack Benchmark Dashboard",
    suppress_callback_exceptions=True
)

# Inject custom CSS via index_string (correct Dash method — html.Style is not supported)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { margin: 0; padding: 0; background: #090D1A; }
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #090D1A; }
            ::-webkit-scrollbar-thumb { background: #1E3A6E; border-radius: 3px; }

            /* ── Dash 2.x Dropdown dark theme ── */
            .dash-dropdown .Select-control,
            .Select-control {
                background-color: #0A1225 !important;
                border-color: #1E3A6E !important;
                color: #E8EDF5 !important;
            }
            .dash-dropdown .Select-control:hover,
            .Select-control:hover { border-color: #2E6DA4 !important; }

            /* The actual visible selected text */
            .dash-dropdown .Select-value-label,
            .Select-value-label,
            .dash-dropdown .Select--single .Select-value .Select-value-label,
            .Select--single .Select-value .Select-value-label,
            .dash-dropdown div[class*="singleValue"],
            div[class*="singleValue"] {
                color: #E8EDF5 !important;
            }

            /* Dropdown menu container */
            .dash-dropdown .Select-menu-outer,
            .Select-menu-outer,
            .dash-dropdown div[class*="menu"],
            div[class*="menu"] {
                background-color: #0A1225 !important;
                border-color: #1E3A6E !important;
                z-index: 9999 !important;
            }

            /* Menu items */
            .dash-dropdown .Select-option,
            .Select-option,
            .dash-dropdown div[class*="option"],
            div[class*="option"] {
                background-color: #0A1225 !important;
                color: #C8D8F0 !important;
            }
            .dash-dropdown .Select-option:hover,
            .Select-option:hover,
            .dash-dropdown .Select-option.is-focused,
            .Select-option.is-focused,
            .dash-dropdown div[class*="option"]:hover,
            div[class*="option"]:hover {
                background-color: #1E3A6E !important;
                color: #FFFFFF !important;
            }
            .dash-dropdown .Select-option.is-selected,
            .Select-option.is-selected {
                background-color: #1A3A8C !important;
                color: #FFFFFF !important;
            }

            /* Placeholder */
            .dash-dropdown .Select-placeholder,
            .Select-placeholder,
            .dash-dropdown div[class*="placeholder"],
            div[class*="placeholder"] { color: #8899CC !important; }

            /* Input text when searching */
            .dash-dropdown .Select-input > input,
            .Select-input > input { color: #E8EDF5 !important; background: transparent !important; }

            /* Arrow indicator */
            .Select-arrow { border-top-color: #5B8DD9 !important; }
            .is-open .Select-arrow { border-bottom-color: #5B8DD9 !important; }

            /* ── Data tables ── */
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                background-color: #0D1530 !important;
                color: #E8EDF5 !important;
                border-color: #1E3A6E !important;
                font-family: "Space Mono", monospace !important;
                font-size: 12px !important;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                background-color: #0A1225 !important;
                color: #5B8DD9 !important;
                border-color: #1E3A6E !important;
                font-family: "Syne", sans-serif !important;
                font-size: 11px !important;
                letter-spacing: 1px;
                text-transform: uppercase;
            }

            /* ── Tab bar ── */
            .dash-tab { transition: all 0.2s ease; }
            .dash-tab:hover { color: #8AABDD !important; }

            /* ── AI Analysis card animations ── */
            .ai-section-card { animation: fadeSlideIn 0.4s ease forwards; }
            @keyframes fadeSlideIn {
                from { opacity: 0; transform: translateY(12px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            .ai-metric-pill {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-family: "Space Mono", monospace;
                margin: 2px 4px 2px 0;
            }
            .ai-positive { background: #0D3320; color: #4DB876; border: 1px solid #1B6B3A; }
            .ai-negative { background: #2D0D0D; color: #E05555; border: 1px solid #8B1A1A; }
            .ai-neutral  { background: #0D1A3A; color: #5B8DD9; border: 1px solid #1E3A6E; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ── Styles ───────────────────────────────────────────────────────────────────

STYLE = {
    "page": {
        "background": "#090D1A",
        "minHeight": "100vh",
        "fontFamily": "'Syne', sans-serif",
        "color": "#E8EDF5",
        "padding": "0",
        "margin": "0",
    },
    "header": {
        "background": "linear-gradient(135deg, #0D1530 0%, #0A1A3A 50%, #0D1520 100%)",
        "borderBottom": "1px solid #1E3A6E",
        "padding": "20px 32px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
    },
    "title": {
        "fontFamily": "'Syne', sans-serif",
        "fontWeight": "800",
        "fontSize": "22px",
        "color": "#FFFFFF",
        "letterSpacing": "2px",
        "textTransform": "uppercase",
        "margin": "0",
    },
    "subtitle": {
        "fontFamily": "'Space Mono', monospace",
        "fontSize": "11px",
        "color": "#5B8DD9",
        "letterSpacing": "1px",
        "margin": "4px 0 0 0",
    },
    "body": {
        "padding": "24px 32px",
    },
    "card": {
        "background": "#0D1530",
        "border": "1px solid #1E3A6E",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "20px",
    },
    "card_title": {
        "fontFamily": "'Syne', sans-serif",
        "fontWeight": "700",
        "fontSize": "13px",
        "color": "#5B8DD9",
        "letterSpacing": "2px",
        "textTransform": "uppercase",
        "marginBottom": "16px",
    },
    "select": {
        "background": "#0A1225",
        "color": "#E8EDF5",
        "border": "1px solid #1E3A6E",
        "borderRadius": "4px",
        "padding": "8px 12px",
        "fontFamily": "'Space Mono', monospace",
        "fontSize": "12px",
        "cursor": "pointer",
        "marginRight": "12px",
    },
    "btn_primary": {
        "background": "linear-gradient(135deg, #1A3A8C, #2E6DA4)",
        "border": "none",
        "borderRadius": "4px",
        "color": "white",
        "padding": "8px 20px",
        "fontFamily": "'Syne', sans-serif",
        "fontWeight": "700",
        "fontSize": "12px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "cursor": "pointer",
    },
    "btn_ai": {
        "background": "linear-gradient(135deg, #4B1A8C, #7B3DB8)",
        "border": "none",
        "borderRadius": "4px",
        "color": "white",
        "padding": "8px 20px",
        "fontFamily": "'Syne', sans-serif",
        "fontWeight": "700",
        "fontSize": "12px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "cursor": "pointer",
        "marginLeft": "8px",
    },
    "ai_box": {
        "background": "#0A0D1E",
        "border": "1px solid #4B1A8C",
        "borderLeft": "3px solid #7B3DB8",
        "borderRadius": "4px",
        "padding": "16px",
        "fontFamily": "'Space Mono', monospace",
        "fontSize": "12px",
        "color": "#C8B8E8",
        "lineHeight": "1.7",
        "whiteSpace": "pre-wrap",
        "marginTop": "12px",
    },
    "metric_card": {
        "background": "#0A1225",
        "border": "1px solid #1E3A6E",
        "borderRadius": "6px",
        "padding": "16px",
        "textAlign": "center",
    },
    "metric_value": {
        "fontFamily": "'Space Mono', monospace",
        "fontSize": "24px",
        "fontWeight": "700",
        "color": "#FFFFFF",
        "margin": "0",
    },
    "metric_label": {
        "fontFamily": "'Syne', sans-serif",
        "fontSize": "10px",
        "color": "#5B8DD9",
        "letterSpacing": "1.5px",
        "textTransform": "uppercase",
        "margin": "4px 0 0 0",
    },
    "tab": {
        "background": "transparent",
        "border": "none",
        "color": "#8899CC",
        "padding": "10px 20px",
        "fontFamily": "'Syne', sans-serif",
        "fontWeight": "700",
        "fontSize": "11px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "cursor": "pointer",
        "borderBottom": "2px solid transparent",
    },
    "tab_selected": {
        "background": "transparent",
        "border": "none",
        "color": "#5B8DD9",
        "padding": "10px 20px",
        "fontFamily": "'Syne', sans-serif",
        "fontWeight": "700",
        "fontSize": "11px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "borderBottom": "2px solid #5B8DD9",
    }
}

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "#090D1A",
        "plot_bgcolor": "#0D1530",
        "font": {"family": "Space Mono, monospace", "color": "#C8D8F0"},
        "xaxis": {"gridcolor": "#1A2A4A", "linecolor": "#1E3A6E", "tickfont": {"size": 10}},
        "yaxis": {"gridcolor": "#1A2A4A", "linecolor": "#1E3A6E", "tickfont": {"size": 10}},
        "legend": {"bgcolor": "#0A1225", "bordercolor": "#1E3A6E", "borderwidth": 1},
        "margin": {"l": 50, "r": 30, "t": 40, "b": 40},
        "colorway": ["#5B8DD9", "#3DB8A5", "#B366E0", "#F0A057", "#4DB876", "#E05555", "#D4B800", "#D4956B"]
    }
}

# ── Layout ───────────────────────────────────────────────────────────────────

layer_options = [{"label": k, "value": k} for k in AI_STACK.keys()]
period_options = [
    {"label": "3 Months",  "value": "3mo"},
    {"label": "6 Months",  "value": "6mo"},
    {"label": "1 Year",    "value": "1y"},
    {"label": "2 Years",   "value": "2y"},
    {"label": "3 Years",   "value": "3y"},
    {"label": "5 Years",   "value": "5y"},
]

app.layout = html.Div(style=STYLE["page"], children=[

    # ── Header ──
    html.Div(style=STYLE["header"], children=[
        html.Div([
            html.H1("AI STACK BENCHMARK", style=STYLE["title"]),
            html.P("Real-time layer performance analysis • Powered by Claude", style=STYLE["subtitle"]),
        ]),
        html.Div([
            html.Span(id="last-updated", style={
                "fontFamily": "'Space Mono', monospace",
                "fontSize": "11px", "color": "#3DB8A5",
            }),
        ])
    ]),

    # ── Controls ──
    html.Div(style={**STYLE["body"], "paddingBottom": "0"}, children=[
        html.Div(style={**STYLE["card"], "padding": "16px", "marginBottom": "0"}, children=[
            html.Div(style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "12px"}, children=[
                html.Div([
                    html.Label("PERIOD", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    dcc.Dropdown(
                        id="period-select",
                        options=period_options,
                        value="1y",
                        clearable=False,
                        style={"width": "160px", "fontFamily": "Space Mono, monospace", "fontSize": "12px"},
                    )
                ]),
                html.Div([
                    html.Label("VIEW LAYER", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    dcc.Dropdown(
                        id="layer-select",
                        options=[{"label": "All Layers (Overview)", "value": "ALL"}] + layer_options,
                        value="ALL",
                        clearable=False,
                        style={"width": "280px", "fontFamily": "Space Mono, monospace", "fontSize": "12px"},
                    )
                ]),
                html.Div([
                    html.Label(" ", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    html.Button("↻ REFRESH DATA", id="refresh-btn", n_clicks=0, style=STYLE["btn_primary"]),
                    html.Button("✦ AI ANALYSIS", id="ai-analysis-btn", n_clicks=0, style=STYLE["btn_ai"]),
                ], style={"marginTop": "2px"}),
                html.Div([
                    html.Label("COMPARE TO", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    dcc.Checklist(
                        id="benchmark-select",
                        options=[{"label": f"  {v}", "value": k} for k, v in BENCHMARKS.items()],
                        value=["SPY"],
                        style={"fontFamily": "Space Mono, monospace", "fontSize": "11px", "color": "#8899CC"},
                        inputStyle={"marginRight": "4px"},
                        labelStyle={"marginRight": "16px", "display": "inline-block"},
                    )
                ]),
            ])
        ])
    ]),

    # ── Data store ──
    dcc.Store(id="price-data-store"),
    dcc.Store(id="ai-analysis-text-store"),
    dcc.Interval(id="auto-refresh", interval=300_000, n_intervals=0),  # 5-min auto refresh

    # ── Main Content ──
    html.Div(style=STYLE["body"], children=[

        # Summary metrics row
        html.Div(id="summary-metrics", style={"marginBottom": "20px"}),

        # Tabs
        dcc.Tabs(id="main-tabs", value="overview", style={"marginBottom": "4px"}, children=[
            dcc.Tab(label="LAYER OVERVIEW",      value="overview",    style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="PERFORMANCE CHART",   value="perf",        style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="HEAT MAP",            value="heat",        style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="COMPANY DRILL-DOWN",  value="drilldown",   style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="CROSS-LAYER SCATTER", value="scatter",     style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="TOP MOVERS",          value="movers",      style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="✦ AI ANALYSIS",       value="ai",
                style={**STYLE["tab"], "color": "#9B66E0"},
                selected_style={**STYLE["tab_selected"], "color": "#B388FF", "borderBottom": "2px solid #9B66E0"}),
        ]),

        html.Div(id="tab-content"),
    ]),

    # Invisible div — CSS injected via app.index_string below
])

# ── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    Output("price-data-store", "data"),
    Output("last-updated", "children"),
    Input("refresh-btn", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
    Input("period-select", "value"),
    prevent_initial_call=False
)
def refresh_data(n_clicks, n_intervals, period):
    prices = fetch_price_data(period)
    if prices.empty:
        return None, "⚠ Data fetch failed"
    data_json = prices.reset_index().to_json(date_format="iso")
    ts = datetime.now().strftime("Updated %b %d, %Y  %H:%M:%S")
    return data_json, f"● {ts}"

@app.callback(
    Output("summary-metrics", "children"),
    Input("price-data-store", "data"),
    Input("period-select", "value"),
    Input("layer-select", "value"),
)
def update_summary(data_json, period, selected_layer):
    if not data_json:
        return html.P("Loading data...", style={"color": "#5B8DD9", "fontFamily": "Space Mono"})
    
    df = pd.read_json(StringIO(data_json)).set_index("Date")
    df.index = pd.to_datetime(df.index)
    
    # Compute metrics
    metrics = []
    
    if selected_layer == "ALL":
        layers_to_show = list(AI_STACK.keys())
    else:
        layers_to_show = [selected_layer]
    
    for layer_key in layers_to_show[:8]:  # max 8 cards
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        perf = ((idx.iloc[-1] - idx.iloc[0]) / idx.iloc[0]) * 100
        color = AI_STACK[layer_key]["color"]
        light = AI_STACK[layer_key]["light"]
        sign = "+" if perf >= 0 else ""
        perf_color = "#4DB876" if perf >= 0 else "#E05555"
        
        short_name = layer_key.split("–")[0].strip() if "–" in layer_key else layer_key[:10]
        
        metrics.append(
            html.Div(style={
                **STYLE["metric_card"],
                "borderTop": f"3px solid {light}",
                "flex": "1",
                "minWidth": "120px",
            }, children=[
                html.P(f"{sign}{perf:.1f}%", style={**STYLE["metric_value"], "color": perf_color}),
                html.P(short_name, style={**STYLE["metric_label"], "color": light}),
            ])
        )
    
    # Add S&P 500 benchmark
    if "SPY" in df.columns:
        spy = df["SPY"].dropna()
        spy_perf = ((spy.iloc[-1] - spy.iloc[0]) / spy.iloc[0]) * 100
        sign = "+" if spy_perf >= 0 else ""
        metrics.append(
            html.Div(style={
                **STYLE["metric_card"],
                "borderTop": "3px solid #888",
                "flex": "1",
                "minWidth": "120px",
            }, children=[
                html.P(f"{sign}{spy_perf:.1f}%", style={**STYLE["metric_value"], "color": "#AABBCC"}),
                html.P("S&P 500", style={**STYLE["metric_label"], "color": "#888"}),
            ])
        )
    
    return html.Div(metrics, style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})

@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
    Input("price-data-store", "data"),
    Input("ai-analysis-text-store", "data"),
    Input("period-select", "value"),
    Input("layer-select", "value"),
    Input("benchmark-select", "value"),
)
def render_tab(tab, data_json, ai_text_data, period, selected_layer, benchmarks):
    if tab == "ai":
        return render_ai_tab(ai_text_data, selected_layer, period)

    if not data_json:
        return html.Div("Fetching market data...", style={
            "textAlign": "center", "padding": "60px",
            "color": "#5B8DD9", "fontFamily": "Space Mono, monospace"
        })

    df = pd.read_json(StringIO(data_json)).set_index("Date")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    if tab == "overview":
        return render_overview(df, period, benchmarks)
    elif tab == "perf":
        return render_performance_chart(df, period, selected_layer, benchmarks)
    elif tab == "heat":
        return render_heatmap(df)
    elif tab == "drilldown":
        return render_drilldown(df, selected_layer)
    elif tab == "scatter":
        return render_scatter(df)
    elif tab == "movers":
        return render_movers(df)
    return html.Div("Select a tab")

def make_fig(fig):
    """Apply consistent dark theme to figure."""
    fig.update_layout(
        paper_bgcolor="#090D1A",
        plot_bgcolor="#0D1530",
        font=dict(family="Space Mono, monospace", color="#C8D8F0", size=11),
        xaxis=dict(gridcolor="#1A2A4A", linecolor="#1E3A6E"),
        yaxis=dict(gridcolor="#1A2A4A", linecolor="#1E3A6E"),
        legend=dict(bgcolor="#0A1225", bordercolor="#1E3A6E", borderwidth=1),
        margin=dict(l=60, r=30, t=50, b=50),
        hoverlabel=dict(
            bgcolor="#0A1225",
            bordercolor="#1E3A6E",
            font=dict(family="Space Mono, monospace", size=11, color="#E8EDF5")
        )
    )
    return fig

def render_overview(df, period, benchmarks):
    """All layer indices on one chart."""
    fig = go.Figure()
    
    # Benchmark lines
    bench_colors = {"SPY": "#888888", "QQQ": "#AAAAAA", "SOXX": "#CCCCCC"}
    for bm in (benchmarks or []):
        if bm in df.columns:
            series = df[bm].dropna()
            norm = (series / series.iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm.values,
                name=BENCHMARKS[bm],
                line=dict(color=bench_colors.get(bm, "#999"), width=1, dash="dash"),
                opacity=0.6,
            ))
    
    # Layer indices
    for layer_key, layer_data in AI_STACK.items():
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        short = layer_key.split("–")[0].strip() if "–" in layer_key else layer_key
        fig.add_trace(go.Scatter(
            x=idx.index, y=idx.values,
            name=short,
            line=dict(color=layer_data["light"], width=2),
            hovertemplate=f"<b>{layer_key}</b><br>%{{x|%b %d, %Y}}<br>Index: %{{y:.1f}}<extra></extra>"
        ))
    
    fig.add_hline(y=100, line_color="#1E3A6E", line_dash="dot", line_width=1)
    fig.update_layout(
        title=dict(text=f"AI STACK LAYER INDICES — Equal-Weighted (Base=100)", font=dict(size=13, color="#5B8DD9")),
        yaxis_title="Normalized Return (Base=100)",
        height=500,
        hovermode="x unified",
    )
    make_fig(fig)
    
    # Layer performance table
    rows = []
    for layer_key, layer_data in AI_STACK.items():
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        perf = ((idx.iloc[-1] - idx.iloc[0]) / idx.iloc[0]) * 100
        n_stocks = len([t for t in layer_data["companies"] if t in df.columns])
        rows.append({
            "Layer": layer_key,
            "Return %": f"{'+' if perf >= 0 else ''}{perf:.1f}%",
            "Stocks": n_stocks,
            "Status": "↑ OUTPERFORM" if perf > 0 else "↓ UNDERPERFORM"
        })
    
    rows.sort(key=lambda x: float(x["Return %"].replace("%", "").replace("+", "")), reverse=True)
    
    table_rows = []
    for row in rows:
        perf_val = float(row["Return %"].replace("%", "").replace("+", ""))
        color = "#4DB876" if perf_val >= 0 else "#E05555"
        table_rows.append(
            html.Tr([
                html.Td(row["Layer"], style={"padding": "10px 14px", "borderBottom": "1px solid #1E3A6E", "color": "#C8D8F0"}),
                html.Td(row["Return %"], style={"padding": "10px 14px", "borderBottom": "1px solid #1E3A6E", "color": color, "fontFamily": "Space Mono, monospace", "fontWeight": "700", "textAlign": "right"}),
                html.Td(str(row["Stocks"]), style={"padding": "10px 14px", "borderBottom": "1px solid #1E3A6E", "color": "#8899CC", "textAlign": "center"}),
                html.Td(row["Status"], style={"padding": "10px 14px", "borderBottom": "1px solid #1E3A6E", "color": color, "fontSize": "11px"}),
            ])
        )
    
    table = html.Table([
        html.Thead(html.Tr([
            html.Th("LAYER", style={"padding": "10px 14px", "color": "#5B8DD9", "fontSize": "11px", "letterSpacing": "1px", "textAlign": "left", "fontFamily": "Syne, sans-serif", "borderBottom": "2px solid #1E3A6E"}),
            html.Th("PERIOD RETURN", style={"padding": "10px 14px", "color": "#5B8DD9", "fontSize": "11px", "letterSpacing": "1px", "textAlign": "right", "fontFamily": "Syne, sans-serif", "borderBottom": "2px solid #1E3A6E"}),
            html.Th("# STOCKS", style={"padding": "10px 14px", "color": "#5B8DD9", "fontSize": "11px", "letterSpacing": "1px", "textAlign": "center", "fontFamily": "Syne, sans-serif", "borderBottom": "2px solid #1E3A6E"}),
            html.Th("VS BASELINE", style={"padding": "10px 14px", "color": "#5B8DD9", "fontSize": "11px", "letterSpacing": "1px", "fontFamily": "Syne, sans-serif", "borderBottom": "2px solid #1E3A6E"}),
        ])),
        html.Tbody(table_rows)
    ], style={"width": "100%", "borderCollapse": "collapse", "fontFamily": "Space Mono, monospace", "fontSize": "12px"})
    
    return html.Div(style=STYLE["card"], children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.P("LAYER PERFORMANCE SUMMARY", style={**STYLE["card_title"], "marginTop": "20px"}),
        table
    ])

def render_performance_chart(df, period, selected_layer, benchmarks):
    """Detailed performance for a specific layer or all."""
    fig = go.Figure()
    
    bench_colors = {"SPY": "#888888", "QQQ": "#AAAAAA", "SOXX": "#CCCCCC"}
    for bm in (benchmarks or []):
        if bm in df.columns:
            series = df[bm].dropna()
            norm = (series / series.iloc[0]) * 100
            fig.add_trace(go.Scatter(x=norm.index, y=norm.values, name=BENCHMARKS[bm],
                line=dict(color=bench_colors.get(bm, "#999"), width=1.5, dash="dash"), opacity=0.7))
    
    if selected_layer == "ALL":
        layers = AI_STACK.items()
    else:
        layers = [(selected_layer, AI_STACK[selected_layer])]
    
    for layer_key, layer_data in layers:
        for ticker, info in layer_data["companies"].items():
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if series.empty:
                continue
            norm = (series / series.iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm.values,
                name=f"{ticker} – {info['name']}",
                line=dict(width=1.5),
                opacity=0.85,
                hovertemplate=f"<b>{ticker}</b><br>%{{x|%b %d, %Y}}<br>Normalized: %{{y:.1f}}<extra></extra>"
            ))
    
    fig.add_hline(y=100, line_color="#1E3A6E", line_dash="dot")
    fig.update_layout(
        title=dict(text=f"NORMALIZED PRICE PERFORMANCE (Base=100)", font=dict(size=13, color="#5B8DD9")),
        height=560,
        hovermode="x unified",
        yaxis_title="Normalized Price (Base = 100 at period start)",
    )
    make_fig(fig)
    return html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": True})])

def render_heatmap(df):
    """Heatmap of returns: layers vs time buckets."""
    # Compute monthly returns per layer
    monthly_returns = {}
    for layer_key in AI_STACK:
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        monthly = idx.resample("ME").last().pct_change().dropna() * 100
        monthly_returns[layer_key] = monthly
    
    if not monthly_returns:
        return html.Div("Insufficient data for heatmap.")
    
    combined = pd.DataFrame(monthly_returns).T
    combined.columns = [str(c)[:7] for c in combined.columns]
    
    # Short layer names
    short_names = [k.split("–")[0].strip() if "–" in k else k[:12] for k in combined.index]
    
    fig = go.Figure(data=go.Heatmap(
        z=combined.values,
        x=list(combined.columns),
        y=short_names,
        colorscale=[
            [0, "#8B0000"], [0.35, "#1A3A5C"], [0.5, "#0D1530"],
            [0.65, "#1A5C2E"], [1, "#00CC44"]
        ],
        zmid=0,
        text=[[f"{v:.1f}%" for v in row] for row in combined.values],
        texttemplate="%{text}",
        textfont={"size": 10, "family": "Space Mono, monospace"},
        colorbar=dict(
            title="Monthly %",
            tickfont=dict(color="#C8D8F0", size=10),
            title_font=dict(color="#5B8DD9", size=11),
        )
    ))
    fig.update_layout(
        title=dict(text="MONTHLY RETURN HEATMAP BY LAYER", font=dict(size=13, color="#5B8DD9")),
        height=380,
    )
    make_fig(fig)
    
    return html.Div(style=STYLE["card"], children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False})
    ])

def render_drilldown(df, selected_layer):
    """Detailed drilldown for selected layer with bar chart + table."""
    if selected_layer == "ALL":
        selected_layer = list(AI_STACK.keys())[0]
    
    layer_data = AI_STACK[selected_layer]
    tickers = [t for t in layer_data["companies"] if t in df.columns]
    
    stats = get_current_stats(df, tickers)
    if stats.empty:
        return html.Div("No data available.")
    
    # Bar chart
    colors = ["#4DB876" if v >= 0 else "#E05555" for v in stats["Period %"]]
    
    fig = go.Figure(go.Bar(
        x=stats["Ticker"],
        y=stats["Period %"],
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in stats["Period %"]],
        textposition="outside",
        textfont=dict(family="Space Mono, monospace", size=10),
        hovertemplate="<b>%{x}</b><br>Return: %{y:.2f}%<extra></extra>"
    ))
    fig.add_hline(y=0, line_color="#1E3A6E", line_width=1)
    fig.update_layout(
        title=dict(text=f"{selected_layer} — Individual Stock Performance", font=dict(size=13, color="#5B8DD9")),
        height=380,
        yaxis_title="Period Return %",
        showlegend=False,
    )
    make_fig(fig)
    
    # Table
    table_rows = []
    for _, row in stats.iterrows():
        color = "#4DB876" if row["Period %"] >= 0 else "#E05555"
        d_color = "#4DB876" if row["1D %"] >= 0 else "#E05555"
        table_rows.append(html.Tr([
            html.Td(row["Ticker"], style={"padding": "9px 14px", "color": "#5B8DD9", "fontWeight": "700", "borderBottom": "1px solid #1A2A4A"}),
            html.Td(row["Name"], style={"padding": "9px 14px", "color": "#C8D8F0", "borderBottom": "1px solid #1A2A4A"}),
            html.Td(f"${row['Price']:,.2f}", style={"padding": "9px 14px", "color": "#E8EDF5", "fontFamily": "Space Mono", "borderBottom": "1px solid #1A2A4A", "textAlign": "right"}),
            html.Td(f"{'+' if row['1D %'] >= 0 else ''}{row['1D %']:.2f}%", style={"padding": "9px 14px", "color": d_color, "fontFamily": "Space Mono", "borderBottom": "1px solid #1A2A4A", "textAlign": "right"}),
            html.Td(f"{'+' if row['Period %'] >= 0 else ''}{row['Period %']:.1f}%", style={"padding": "9px 14px", "color": color, "fontFamily": "Space Mono", "fontWeight": "700", "borderBottom": "1px solid #1A2A4A", "textAlign": "right"}),
            html.Td(f"${row['52W High']:,.2f}", style={"padding": "9px 14px", "color": "#8899CC", "fontFamily": "Space Mono", "borderBottom": "1px solid #1A2A4A", "textAlign": "right", "fontSize": "11px"}),
            html.Td(f"${row['52W Low']:,.2f}", style={"padding": "9px 14px", "color": "#8899CC", "fontFamily": "Space Mono", "borderBottom": "1px solid #1A2A4A", "textAlign": "right", "fontSize": "11px"}),
        ]))
    
    th_style = {"padding": "10px 14px", "color": "#5B8DD9", "fontSize": "10px", "letterSpacing": "1px", "textAlign": "left", "fontFamily": "Syne", "borderBottom": "2px solid #1E3A6E", "textTransform": "uppercase"}
    table = html.Table([
        html.Thead(html.Tr([
            html.Th("Ticker", style=th_style), html.Th("Name", style=th_style),
            html.Th("Price", style={**th_style, "textAlign": "right"}),
            html.Th("1D %", style={**th_style, "textAlign": "right"}),
            html.Th("Period %", style={**th_style, "textAlign": "right"}),
            html.Th("52W High", style={**th_style, "textAlign": "right"}),
            html.Th("52W Low", style={**th_style, "textAlign": "right"}),
        ])),
        html.Tbody(table_rows)
    ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "12px", "fontFamily": "Space Mono, monospace"})
    
    return html.Div(style=STYLE["card"], children=[
        html.P(layer_data["description"], style={"color": "#8899CC", "fontFamily": "Space Mono, monospace", "fontSize": "11px", "marginBottom": "16px"}),
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.P("DETAILED METRICS", style={**STYLE["card_title"], "marginTop": "20px"}),
        table
    ])

def render_scatter(df):
    """Scatter: 1D return vs period return for all stocks, colored by layer."""
    all_tickers = []
    for layer_key, layer_data in AI_STACK.items():
        for t in layer_data["companies"]:
            all_tickers.append((t, layer_key, layer_data["light"]))
    
    stats_data = []
    for ticker, layer, color in all_tickers:
        if ticker not in df.columns:
            continue
        series = df[ticker].dropna()
        if len(series) < 5:
            continue
        period_ret = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
        d_ret = ((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]) * 100
        stats_data.append({
            "ticker": ticker, "layer": layer.split("–")[0].strip() if "–" in layer else layer[:12],
            "1d": d_ret, "period": period_ret, "color": color
        })
    
    if not stats_data:
        return html.Div("No data.")
    
    sdf = pd.DataFrame(stats_data)
    
    fig = px.scatter(
        sdf, x="period", y="1d",
        color="layer",
        text="ticker",
        hover_data={"ticker": True, "layer": True, "1d": ":.2f", "period": ":.1f"},
        labels={"period": "Period Return %", "1d": "1-Day Return %", "layer": "Layer"},
        title="CROSS-LAYER SCATTER: Period Return vs. 1-Day Momentum",
    )
    fig.update_traces(textposition="top center", textfont=dict(size=8, family="Space Mono, monospace"))
    fig.add_vline(x=0, line_color="#1E3A6E", line_dash="dot")
    fig.add_hline(y=0, line_color="#1E3A6E", line_dash="dot")
    fig.update_layout(height=560)
    make_fig(fig)
    fig.update_layout(title=dict(font=dict(size=13, color="#5B8DD9")))
    
    return html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": True})])

def render_movers(df):
    """Top gainers and losers across all layers."""
    all_stats = []
    for layer_key, layer_data in AI_STACK.items():
        for ticker in layer_data["companies"]:
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if len(series) < 2:
                continue
            perf = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
            d_perf = ((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]) * 100
            all_stats.append({
                "Ticker": ticker,
                "Name": layer_data["companies"][ticker]["name"],
                "Layer": layer_key.split("–")[0].strip() if "–" in layer_key else layer_key[:12],
                "Period %": perf,
                "1D %": d_perf,
                "Color": layer_data["light"]
            })
    
    if not all_stats:
        return html.Div("No data.")
    
    sdf = pd.DataFrame(all_stats).sort_values("Period %", ascending=False)
    
    top10 = sdf.head(10)
    bot10 = sdf.tail(10).sort_values("Period %")
    
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=("TOP 10 GAINERS", "BOTTOM 10 LAGGARDS"),
        horizontal_spacing=0.12)
    
    fig.add_trace(go.Bar(
        x=top10["Period %"], y=top10["Ticker"], orientation="h",
        marker_color=top10["Color"].tolist(),
        text=[f"+{v:.1f}%" for v in top10["Period %"]],
        textposition="outside",
        textfont=dict(size=10, family="Space Mono"),
        name="Gainers",
        hovertemplate="<b>%{y}</b><br>Return: %{x:.1f}%<extra></extra>"
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        x=bot10["Period %"], y=bot10["Ticker"], orientation="h",
        marker_color="#E05555",
        text=[f"{v:.1f}%" for v in bot10["Period %"]],
        textposition="outside",
        textfont=dict(size=10, family="Space Mono"),
        name="Laggards",
        hovertemplate="<b>%{y}</b><br>Return: %{x:.1f}%<extra></extra>"
    ), row=1, col=2)
    
    fig.update_layout(height=460, showlegend=False)
    fig.update_xaxes(gridcolor="#1A2A4A", linecolor="#1E3A6E")
    fig.update_yaxes(gridcolor="#1A2A4A", linecolor="#1E3A6E")
    make_fig(fig)
    for ann in fig.layout.annotations:
        ann.font.color = "#5B8DD9"
        ann.font.size = 12
    
    # 1D movers table
    top5_1d = sdf.nlargest(5, "1D %")
    bot5_1d = sdf.nsmallest(5, "1D %")
    
    def mini_table(data, title, color):
        rows = []
        for _, r in data.iterrows():
            rows.append(html.Tr([
                html.Td(r["Ticker"], style={"padding": "8px 12px", "color": "#5B8DD9", "fontWeight": "700", "borderBottom": "1px solid #1A2A4A", "fontSize": "12px"}),
                html.Td(r["Name"][:22], style={"padding": "8px 12px", "color": "#C8D8F0", "borderBottom": "1px solid #1A2A4A", "fontSize": "11px"}),
                html.Td(f"{'+' if r['1D %'] >= 0 else ''}{r['1D %']:.2f}%", style={"padding": "8px 12px", "color": color, "fontFamily": "Space Mono", "fontWeight": "700", "borderBottom": "1px solid #1A2A4A", "fontSize": "12px", "textAlign": "right"}),
            ]))
        return html.Div([
            html.P(title, style={**STYLE["card_title"], "color": color}),
            html.Table([html.Tbody(rows)], style={"width": "100%", "borderCollapse": "collapse"})
        ])
    
    return html.Div([
        html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        html.Div(style={"display": "flex", "gap": "16px"}, children=[
            html.Div(style={**STYLE["card"], "flex": "1"}, children=[mini_table(top5_1d, "TODAY'S TOP MOVERS", "#4DB876")]),
            html.Div(style={**STYLE["card"], "flex": "1"}, children=[mini_table(bot5_1d, "TODAY'S BIGGEST DROPS", "#E05555")]),
        ])
    ])

# ── Modern AI Analysis Tab Renderer ─────────────────────────────────────────

def render_ai_tab(ai_text_data, selected_layer, period):
    """Render the dedicated AI Analysis tab with modern card UI."""

    # Empty state — not yet run
    if not ai_text_data:
        return html.Div(style={**STYLE["card"], "textAlign": "center", "padding": "60px 40px"}, children=[
            html.Div("✦", style={"fontSize": "48px", "color": "#3A1A6E", "marginBottom": "16px"}),
            html.P("NO ANALYSIS RUN YET", style={
                "fontFamily": "Syne, sans-serif", "fontWeight": "800",
                "fontSize": "16px", "color": "#5B3A8C", "letterSpacing": "3px", "margin": "0 0 12px 0"
            }),
            html.P("Select a time period and layer, then click the  ✦ AI ANALYSIS  button above to generate a Claude-powered report.",
                style={"color": "#556688", "fontFamily": "Space Mono, monospace", "fontSize": "12px", "lineHeight": "1.8", "maxWidth": "480px", "margin": "0 auto"}
            ),
        ])

    raw_text = ai_text_data.get("text", "")
    scope     = ai_text_data.get("scope", selected_layer)
    period_lbl = ai_text_data.get("period", period)
    timestamp  = ai_text_data.get("timestamp", "")

    # Parse the markdown-style sections Claude returns into styled cards
    def parse_sections(text):
        """Split Claude's numbered response into section cards."""
        import re
        # Match "1. **Title**: content" or "**Title**\ncontent"
        pattern = re.compile(r'\d+\.\s+\*\*(.*?)\*\*[:\s]*(.*?)(?=\n\d+\.\s+\*\*|\Z)', re.DOTALL)
        matches = pattern.findall(text)

        section_icons = {
            "Key Outperformers": ("▲", "#4DB876", "#0D3320", "#1B6B3A"),
            "Laggards":          ("▼", "#E05555", "#2D0D0D", "#8B1A1A"),
            "Layer Thesis":      ("◈", "#5B8DD9", "#0D1A3A", "#1E3A6E"),
            "Stack Flow":        ("⟳", "#5B8DD9", "#0D1A3A", "#1E3A6E"),
            "Notable Signal":    ("◆", "#F0A057", "#2A1800", "#7A3800"),
            "Investment Positioning": ("$", "#3DB8A5", "#0D2A28", "#1D7A8C"),
            "Risk Factor":       ("⚠", "#E05555", "#2D0D0D", "#8B1A1A"),
            "Macro Signal":      ("~", "#B366E0", "#1A0D2A", "#5B1A8C"),
            "Contrarian Opportunity": ("◎", "#D4B800", "#1A1600", "#7A6B00"),
            "Leading vs. Lagging Layers": ("↕", "#5B8DD9", "#0D1A3A", "#1E3A6E"),
        }
        default_icon = ("•", "#8899CC", "#0D1A3A", "#1E3A6E")

        cards = []
        if matches:
            for title, content in matches:
                title = title.strip()
                content = content.strip()
                icon, text_color, bg, border_color = section_icons.get(title, default_icon)

                # Highlight tickers (all-caps 2-5 char words) and percentages
                import re as re2
                def highlight(c):
                    c = re2.sub(r'\b([A-Z]{2,5})\b(?!\s*:)', lambda m:
                        f'<span style="color:#5B8DD9;font-weight:700;font-family:Space Mono,monospace">{m.group(1)}</span>', c)
                    c = re2.sub(r'([+-]?\d+\.?\d*%)', lambda m:
                        f'<span style="color:{"#4DB876" if not m.group(1).startswith("-") else "#E05555"};font-weight:700">{m.group(1)}</span>', c)
                    return c

                highlighted = highlight(content)

                cards.append(
                    html.Div(className="ai-section-card", style={
                        "background": bg,
                        "border": f"1px solid {border_color}",
                        "borderLeft": f"4px solid {text_color}",
                        "borderRadius": "6px",
                        "padding": "18px 20px",
                        "marginBottom": "12px",
                    }, children=[
                        html.Div(style={"display": "flex", "alignItems": "center", "marginBottom": "10px", "gap": "10px"}, children=[
                            html.Span(icon, style={"fontSize": "18px", "color": text_color}),
                            html.Span(title.upper(), style={
                                "fontFamily": "Syne, sans-serif", "fontWeight": "800",
                                "fontSize": "11px", "letterSpacing": "2px", "color": text_color
                            }),
                        ]),
                        html.Div(
                            dangerously_allow_html=True,
                            children=highlighted,
                            style={
                                "fontFamily": "Space Mono, monospace",
                                "fontSize": "12px", "lineHeight": "1.9",
                                "color": "#C8D8F0", "whiteSpace": "pre-wrap"
                            }
                        )
                    ])
                )
        else:
            # Fallback: render raw text nicely if no sections parsed
            cards.append(html.Div(style={
                "background": "#0A0D1E", "border": "1px solid #2A1A5E",
                "borderRadius": "6px", "padding": "20px",
                "fontFamily": "Space Mono, monospace", "fontSize": "12px",
                "lineHeight": "1.9", "color": "#C8D8F0", "whiteSpace": "pre-wrap"
            }, children=raw_text))
        return cards

    scope_label = scope if scope != "ALL" else "All Layers — Full Stack"
    period_map = {"3mo": "3 Months", "6mo": "6 Months", "1y": "1 Year",
                  "2y": "2 Years", "3y": "3 Years", "5y": "5 Years"}
    period_display = period_map.get(period_lbl, period_lbl)

    return html.Div([
        # Header card
        html.Div(style={
            "background": "linear-gradient(135deg, #0D0A1E 0%, #160D2E 50%, #0D0A1E 100%)",
            "border": "1px solid #2A1A5E",
            "borderRadius": "8px",
            "padding": "24px 28px",
            "marginBottom": "16px",
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "flexWrap": "wrap",
            "gap": "12px",
        }, children=[
            html.Div([
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "6px"}, children=[
                    html.Span("✦", style={"fontSize": "22px", "color": "#9B66E0"}),
                    html.Span("CLAUDE AI ANALYSIS", style={
                        "fontFamily": "Syne, sans-serif", "fontWeight": "800",
                        "fontSize": "18px", "letterSpacing": "3px", "color": "#FFFFFF"
                    }),
                ]),
                html.Div(style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginTop": "4px"}, children=[
                    html.Span(scope_label, className="ai-metric-pill ai-neutral"),
                    html.Span(period_display, className="ai-metric-pill ai-neutral"),
                    html.Span(f"Generated {timestamp}", className="ai-metric-pill ai-neutral") if timestamp else html.Span(""),
                ]),
            ]),
            html.Div(style={"textAlign": "right"}, children=[
                html.P("Powered by", style={"color": "#556688", "fontSize": "10px", "margin": "0", "fontFamily": "Space Mono, monospace", "letterSpacing": "1px"}),
                html.P("claude-sonnet-4-6", style={"color": "#9B66E0", "fontSize": "12px", "margin": "4px 0 0 0", "fontFamily": "Space Mono, monospace", "fontWeight": "700"}),
            ]),
        ]),

        # Loading wrapper
        dcc.Loading(type="circle", color="#9B66E0", children=[
            html.Div(id="ai-analysis-output", children=parse_sections(raw_text))
        ]),

        # Disclaimer
        html.P(
            "⚠ AI-generated analysis is for informational purposes only and does not constitute financial advice. Always conduct your own due diligence.",
            style={"color": "#334466", "fontFamily": "Space Mono, monospace", "fontSize": "10px",
                   "marginTop": "16px", "textAlign": "center", "letterSpacing": "0.5px"}
        )
    ])


# AI Analysis callback — runs analysis, stores result, redirects to AI tab
@app.callback(
    Output("ai-analysis-text-store", "data"),
    Output("main-tabs", "value"),
    Input("ai-analysis-btn", "n_clicks"),
    State("price-data-store", "data"),
    State("period-select", "value"),
    State("layer-select", "value"),
    prevent_initial_call=True
)
def run_ai_analysis(n_clicks, data_json, period, selected_layer):
    if not data_json or not n_clicks:
        return no_update, no_update

    df = pd.read_json(StringIO(data_json)).set_index("Date")
    df.index = pd.to_datetime(df.index)

    if selected_layer == "ALL":
        layer_summary = {}
        for layer_key in AI_STACK:
            idx = compute_layer_index(df, layer_key)
            if not idx.empty:
                perf = ((idx.iloc[-1] - idx.iloc[0]) / idx.iloc[0]) * 100
                if "SPY" in df.columns:
                    spy = df["SPY"].dropna()
                    spy_perf = ((spy.iloc[-1] - spy.iloc[0]) / spy.iloc[0]) * 100
                    layer_summary[layer_key] = {"return_pct": round(perf, 1), "vs_sp500": round(perf - spy_perf, 1)}
                else:
                    layer_summary[layer_key] = {"return_pct": round(perf, 1)}
        analysis = get_portfolio_analysis(json.dumps(layer_summary, indent=2), period)
    else:
        layer_data = AI_STACK[selected_layer]
        tickers = [t for t in layer_data["companies"] if t in df.columns]
        stats = get_current_stats(df, tickers)
        if stats.empty:
            analysis = "No data available for this layer."
        else:
            stats_json = stats[["Ticker", "Name", "Price", "1D %", "Period %"]].to_json(orient="records", indent=2)
            analysis = get_ai_analysis(stats_json, selected_layer, period)

    store_data = {
        "text": analysis,
        "scope": selected_layer,
        "period": period,
        "timestamp": datetime.now().strftime("%b %d, %Y  %H:%M")
    }

    # Return analysis data + switch to AI tab automatically
    return store_data, "ai"

# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║        AI STACK BENCHMARK DASHBOARD                          ║
╠══════════════════════════════════════════════════════════════╣
║  Fetching initial market data...                             ║
║  Dashboard will open at: http://127.0.0.1:8050               ║
║                                                              ║
║  Features:                                                   ║
║  • 7 AI Stack Layers + Power/Energy                          ║
║  • 100+ stocks across all layers                             ║
║  • Equal-weighted layer index benchmarking                   ║
║  • S&P 500 / NASDAQ / Semiconductor ETF comparison           ║
║  • Claude AI layer analysis (requires ANTHROPIC_API_KEY)     ║
║  • Auto-refreshes every 5 minutes                            ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(debug=False, port=8050, host="127.0.0.1")
