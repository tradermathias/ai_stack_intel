"""
╔══════════════════════════════════════════════════════════════════════╗
║        AGENTIC ECONOMY — TRUST & VERIFICATION LAYER DASHBOARD        ║
║        Powered by yfinance + Anthropic API (Claude)                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  SETUP:                                                              ║
║    pip install yfinance pandas plotly dash dash-bootstrap-components ║
║                anthropic                                             ║
║    export ANTHROPIC_API_KEY="your-key-here"                          ║
║    python agentic_trust_dashboard.py                                 ║
║  Then open: http://127.0.0.1:8051                                    ║
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
# API KEY SETUP
# ──────────────────────────────────────────────────────────────────────────────

def load_api_key():
    """Load Anthropic API key from env, .env file, or prompt the user."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key and key.startswith("sk-"):
        print(f"✓ Anthropic API key loaded from environment variable.")
        return key

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

    print("\n" + "="*60)
    print("  ANTHROPIC API KEY NOT FOUND")
    print("  Get your key at: https://console.anthropic.com/")
    print("="*60)
    key = input("  Paste your Anthropic API key (or press Enter to skip): ").strip()
    if key.startswith("sk-"):
        os.environ["ANTHROPIC_API_KEY"] = key
        env_file.write_text(f'ANTHROPIC_API_KEY="{key}"\n')
        print(f"  ✓ Key saved to {env_file} — won't ask again.")
        return key
    else:
        print("  ⚠ No valid key entered. AI Analysis will be disabled.")
        return ""

ANTHROPIC_API_KEY = load_api_key()

# ──────────────────────────────────────────────────────────────────────────────
# TRUST LAYER UNIVERSE  — 8 tiers from the Agentic Economy Master Dashboard
# ──────────────────────────────────────────────────────────────────────────────

TRUST_STACK = {
    "T1 – AI Governance & Policy": {
        "color": "#1F4E79",
        "light": "#4E9FD9",
        "description": "Platforms governing the AI model lifecycle: policy, compliance, audit, EU AI Act / NIST RMF. The regulatory command-center for enterprise AI programs.",
        "companies": {
            "IBM":  {"name": "IBM (OpenPages + Watson Gov)",     "cap": "Large"},
            "NOW":  {"name": "ServiceNow (AI Workflow Gov)",     "cap": "Large"},
            "CRM":  {"name": "Salesforce (Einstein Trust Layer)","cap": "Large"},
            "SAP":  {"name": "SAP (AI Governance & Compliance)", "cap": "Large"},
            "MSFT": {"name": "Microsoft (Responsible AI + Purview)", "cap": "Large"},
        }
    },
    "T2 – AI Observability & Monitoring": {
        "color": "#0D6B5E",
        "light": "#3DB8A5",
        "description": "Production monitoring for AI/LLM systems: drift, hallucination, bias, latency, cost anomalies, and agentic trace analysis. The operational health layer.",
        "companies": {
            "DDOG":  {"name": "Datadog (LLM Observability + Arize investor)", "cap": "Large"},
            "DT":    {"name": "Dynatrace (AI-observability platform)",         "cap": "Large"},
            "SNOW":  {"name": "Snowflake (TruEra acquisition + Cortex AI)",    "cap": "Large"},
            "PLTR":  {"name": "Palantir (AIP model monitoring)",               "cap": "Large"},
            "MDB":   {"name": "MongoDB (AI data layer + observability)",        "cap": "Mid"},
        }
    },
    "T3 – Agent Identity & IAM": {
        "color": "#5C1A8C",
        "light": "#A855F7",
        "description": "Identity and access management for AI agents and non-human identities. Just-in-time credentials, agent-to-agent auth, secrets management, NHI governance. Highest-conviction tier.",
        "companies": {
            "OKTA":  {"name": "Okta (AI Agents IAM — FY27 rollout)",       "cap": "Large"},
            "SAIL":  {"name": "SailPoint (Agent Identity Security)",        "cap": "Mid"},
            "CYBR":  {"name": "CyberArk (Privileged access for agents)",    "cap": "Large"},
            "CRWD":  {"name": "CrowdStrike (Falcon Agentic Identity)",      "cap": "Large"},
            "PANW":  {"name": "Palo Alto Networks (Identity as perimeter)", "cap": "Large"},
            "MSFT":  {"name": "Microsoft Entra (Cross-App agent auth)",     "cap": "Large"},
            "YOU":   {"name": "Clear Secure (Biometric human counterproof)","cap": "Mid"},
            "MITK":  {"name": "Mitek Systems (Liveness + deepfake defense)","cap": "Small"},
        }
    },
    "T4 – AI Security & Red-Teaming": {
        "color": "#8C1A1A",
        "light": "#EF4444",
        "description": "Offensive and defensive AI security: prompt injection detection, model supply chain integrity, adversarial testing, and AI-specific threat intelligence.",
        "companies": {
            "PANW":  {"name": "Palo Alto Networks (AI Access Security)",    "cap": "Large"},
            "CRWD":  {"name": "CrowdStrike (AI model protection + Falcon)", "cap": "Large"},
            "CSCO":  {"name": "Cisco (acquired Robust Intelligence 2024)",  "cap": "Large"},
            "CHKP":  {"name": "Check Point (acquired Astrix — NHI sec)",    "cap": "Large"},
            "NET":   {"name": "Cloudflare (AI Gateway + Zero Trust)",       "cap": "Large"},
            "FTNT":  {"name": "Fortinet (AI-powered network security)",     "cap": "Large"},
        }
    },
    "T5 – Cloud & Agent Orchestration": {
        "color": "#374891",
        "light": "#6B83D4",
        "description": "Hyperscalers and enterprise platforms hosting, orchestrating, and managing AI agent deployments. The deployment fabric of the agentic economy.",
        "companies": {
            "MSFT":  {"name": "Microsoft Azure (Copilot Studio + AutoGen)", "cap": "Large"},
            "AMZN":  {"name": "Amazon AWS (Bedrock multi-agent framework)", "cap": "Large"},
            "GOOGL": {"name": "Alphabet GCP (Vertex AI + SynthID)",         "cap": "Large"},
            "NOW":   {"name": "ServiceNow (Vancouver agentic workflows)",   "cap": "Large"},
            "CRM":   {"name": "Salesforce (Agentforce platform)",           "cap": "Large"},
        }
    },
    "T6 – Enterprise Trust Incumbents": {
        "color": "#1A5C2E",
        "light": "#4ADE80",
        "description": "Large public companies with embedded AI trust modules in their existing platforms. Distribution moats enable cross-sell of trust capabilities to large installed bases.",
        "companies": {
            "CRM":   {"name": "Salesforce (Einstein Trust Layer leader)",   "cap": "Large"},
            "IBM":   {"name": "IBM (OpenPages AI governance)",              "cap": "Large"},
            "SNOW":  {"name": "Snowflake (TruEra + data governance)",       "cap": "Large"},
            "NOW":   {"name": "ServiceNow (AI audit workflows)",            "cap": "Large"},
            "DDOG":  {"name": "Datadog (AI security + LLM monitoring)",     "cap": "Large"},
            "MSFT":  {"name": "Microsoft (Responsible AI + Entra)",         "cap": "Large"},
        }
    },
    "T7 – Biometric & Human Verification": {
        "color": "#7A5C00",
        "light": "#F59E0B",
        "description": "Physical and behavioral biometrics as the human counterproof to bodiless AI agents. Liveness detection, deepfake defense, and identity proofing for high-stakes agent interactions.",
        "companies": {
            "YOU":   {"name": "Clear Secure (Face/iris biometric auth)",    "cap": "Mid"},
            "MITK":  {"name": "Mitek Systems (Liveness + mobile ID)",       "cap": "Small"},
            "IDEX":  {"name": "IDEX Biometrics (Fingerprint sensor tech)",  "cap": "Small"},
            "ACXP":  {"name": "Acuity Corp (Digital identity verification)","cap": "Small"},
        }
    },
    "T8 – Vertical Agent Trust (Legal, Finance, Data)": {
        "color": "#5C3A8C",
        "light": "#C084FC",
        "description": "Companies building AI agents for high-trust professional verticals — legal, finance, data — where governance, accuracy, and auditability are non-negotiable.",
        "companies": {
            "TRI":   {"name": "Thomson Reuters (CoCounsel legal agent)",    "cap": "Large"},
            "RELX":  {"name": "RELX / LexisNexis (Protégé legal agents)",   "cap": "Large"},
            "META":  {"name": "Meta (Llama Guard open-source safety layer)","cap": "Large"},
            "ORCL":  {"name": "Oracle (AI data governance + audit)",        "cap": "Large"},
            "WDAY":  {"name": "Workday (AI governance for HR/finance)",     "cap": "Large"},
        }
    },
}

# ── Benchmark indices — SPY + QQQ + SOXX (Semiconductor/AI proxy) ────────────
BENCHMARKS = {
    "SPY":  "S&P 500",
    "QQQ":  "NASDAQ 100",
    "SOXX": "iShares Semiconductor ETF",
    "SMH":  "VanEck Semiconductor ETF",
    "CIBR": "First Trust Cybersecurity ETF",
}

# ──────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ──────────────────────────────────────────────────────────────────────────────

def get_all_tickers():
    tickers = set()
    for layer_data in TRUST_STACK.values():
        tickers.update(layer_data["companies"].keys())
    tickers.update(BENCHMARKS.keys())
    return list(tickers)

def fetch_price_data(period="1y"):
    """Fetch historical price data for all tickers."""
    all_tickers = get_all_tickers()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching {len(all_tickers)} tickers...")
    end = datetime.today()
    period_map = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "3y": 1095, "5y": 1825}
    days = period_map.get(period, 365)
    start = end - timedelta(days=days)
    try:
        raw = yf.download(
            tickers=all_tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetched: {prices.shape[1]} tickers, {len(prices)} days")
        return prices
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def compute_normalized_returns(prices):
    return (prices / prices.iloc[0]) * 100

def compute_layer_index(prices, layer_key):
    """Equal-weighted index for a given trust layer."""
    tickers = [t for t in TRUST_STACK[layer_key]["companies"].keys() if t in prices.columns]
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
        current    = series.iloc[-1]
        prev_close = series.iloc[-2]
        start      = series.iloc[0]
        pct_1d     = ((current - prev_close) / prev_close) * 100
        pct_period = ((current - start) / start) * 100

        name = ticker
        for layer_data in TRUST_STACK.values():
            if ticker in layer_data["companies"]:
                name = layer_data["companies"][ticker]["name"]
                break
        if ticker in BENCHMARKS:
            name = BENCHMARKS[ticker]

        stats.append({
            "Ticker":    ticker,
            "Name":      name,
            "Price":     round(current, 2),
            "1D %":      round(pct_1d, 2),
            "Period %":  round(pct_period, 2),
            "52W High":  round(series.rolling(252).max().iloc[-1], 2) if len(series) >= 252 else round(series.max(), 2),
            "52W Low":   round(series.rolling(252).min().iloc[-1], 2) if len(series) >= 252 else round(series.min(), 2),
        })
    return pd.DataFrame(stats).sort_values("Period %", ascending=False)

# ──────────────────────────────────────────────────────────────────────────────
# ANTHROPIC AI ANALYSIS — trust-layer-specific prompts
# ──────────────────────────────────────────────────────────────────────────────

def get_ai_analysis(layer_stats_json: str, layer_name: str, period: str) -> str:
    """Use Claude to analyze trust layer performance data."""
    api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ No Anthropic API key found.\n\nRestart and paste your key when prompted.\nGet one at: https://console.anthropic.com/"
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a portfolio manager specializing in enterprise AI trust, security, and governance equities — the "trust and verification layer" of the agentic economy.

Analyze the following stock performance data for the **{layer_name}** tier of the AI Trust & Verification stack over a **{period}** lookback period.

Performance Data (JSON):
{layer_stats_json}

Provide a concise analysis covering:
1. **Key Outperformers**: Which 2-3 stocks stand out and what trust-layer dynamics drove their performance?
2. **Laggards**: Which 1-2 stocks underperformed and likely why?
3. **Layer Thesis**: Is this layer gaining or losing enterprise adoption momentum relative to the broader AI stack?
4. **Notable Signal**: One actionable observation for investors watching the trust and verification layer
5. **Risk Factor**: The single biggest risk to continued performance — platform consolidation, regulatory shift, or open-source commoditization?

Keep it under 320 words. Be specific, use the performance numbers, and frame everything in terms of the agentic economy thesis: as AI agents proliferate, every deployment needs governance, identity, observability, and security."""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"Analysis unavailable: {str(e)}"

def get_portfolio_analysis(all_layer_returns: str, period: str) -> str:
    """Claude cross-layer portfolio analysis for the full trust stack."""
    api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ No Anthropic API key found.\n\nRestart and paste your key when prompted.\nGet one at: https://console.anthropic.com/"
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a senior portfolio manager building an investment thesis around the AI Trust & Verification layer of the agentic economy.

Context: 91% of enterprises are deploying AI agents but only 10% have a governance strategy. The trust layer — governance, observability, agent identity, and AI security — is the largest unmet demand in enterprise software today.

Below is equal-weighted index performance for each tier of the Trust & Verification stack over **{period}**:

{all_layer_returns}

Provide a strategic cross-tier analysis:
1. **Stack Flow**: Where is capital rotating within the trust stack? Which tiers are leading?
2. **Leading vs. Lagging Tiers**: Which tiers are beating or lagging SPY? What does that signal?
3. **Investment Positioning**: For a new investor in the agentic economy trust thesis, which 2 tiers offer the best risk/reward today?
4. **Adoption Signal**: What does the relative performance of Identity (T3) vs. Governance (T1) tell us about where enterprises are prioritizing trust spending?
5. **Contrarian Opportunity**: Is there a tier being overlooked that deserves attention given the agent proliferation tailwind?

Be specific, cite the numbers, under 420 words."""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"Analysis unavailable: {str(e)}"

# ──────────────────────────────────────────────────────────────────────────────
# DASH APP
# ──────────────────────────────────────────────────────────────────────────────

try:
    import dash_bootstrap_components as dbc
    HAS_DBC = True
except ImportError:
    HAS_DBC = False

app = Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap",
        dbc.themes.DARKLY if HAS_DBC else ""
    ] if HAS_DBC else [
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap"
    ],
    title="Agentic Trust Layer Dashboard",
    suppress_callback_exceptions=True,
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * { box-sizing: border-box; }
            body { margin: 0; padding: 0; background: #07091A; font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif; }
            ::-webkit-scrollbar { width: 5px; }
            ::-webkit-scrollbar-track { background: #07091A; }
            ::-webkit-scrollbar-thumb { background: #2D1B6E; border-radius: 10px; }

            /* ── Dropdowns — Dash 4.0 + legacy compatible ── */
            .Select-control, .dash-dropdown .Select-control {
                background-color: #1A1A3E !important; border: 1px solid #3D3B6E !important;
                border-radius: 6px !important; box-shadow: none !important; min-height: 36px !important;
            }
            .Select-value-label, .Select--single .Select-value .Select-value-label,
            .dash-dropdown .Select-value-label,
            .dash-dropdown .Select--single > .Select-control .Select-value .Select-value-label {
                color: #FFFFFF !important; font-family: "Inter", sans-serif !important;
                font-size: 13px !important; font-weight: 500 !important; line-height: 34px !important;
            }
            .Select-placeholder { color: #7C83A0 !important; font-size: 13px !important; line-height: 34px !important; }
            .Select-input > input { color: #FFFFFF !important; font-family: "Inter", sans-serif !important; font-size: 13px !important; background: transparent !important; }
            .Select-menu-outer {
                background-color: #1A1A3E !important; border: 1px solid #3D3B6E !important;
                border-radius: 6px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
                z-index: 9999 !important; margin-top: 4px !important;
            }
            .Select-option { background-color: #1A1A3E !important; color: #C4B5FD !important; font-size: 13px !important; padding: 9px 14px !important; }
            .Select-option:hover, .Select-option.is-focused { background-color: #2D1B6E !important; color: #FFFFFF !important; }
            .Select-option.is-selected { background-color: #4C1D95 !important; color: #FFFFFF !important; font-weight: 600 !important; }
            .Select-arrow-zone .Select-arrow { border-top-color: #A78BFA !important; }
            .Select-clear-zone { color: #7C83A0 !important; }
            /* Dash 4.0 react-select overrides */
            .dash-dropdown .dropdown { background: #1A1A3E !important; }
            .VirtualizedSelectOption { background-color: #1A1A3E !important; color: #C4B5FD !important; }
            .VirtualizedSelectFocusedOption { background-color: #2D1B6E !important; color: #FFFFFF !important; }
            .VirtualizedSelectSelectedOption { background-color: #4C1D95 !important; }

            /* ── Global font ── */
            .dash-tab, button, label, p, h1, h2, h3, span, td, th {
                font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif !important;
            }

            /* ── Data tables ── */
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                background-color: #0D1030 !important; color: #E2E8F0 !important;
                border-color: #2D1B6E !important; font-family: "DM Mono", monospace !important; font-size: 12px !important;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                background-color: #0A0C22 !important; color: #A78BFA !important;
                border-color: #2D1B6E !important; font-size: 11px !important; font-weight: 600 !important;
                letter-spacing: 0.8px; text-transform: uppercase;
            }

            /* ── Trust layer accent glow on hover ── */
            .trust-card:hover { border-color: #6D28D9 !important; transition: border-color 0.2s ease; }

            /* ── AI section cards ── */
            .ai-section-card { animation: fadeUp 0.35s ease forwards; opacity: 0; }
            .ai-section-card:nth-child(1) { animation-delay: 0.05s; }
            .ai-section-card:nth-child(2) { animation-delay: 0.10s; }
            .ai-section-card:nth-child(3) { animation-delay: 0.15s; }
            .ai-section-card:nth-child(4) { animation-delay: 0.20s; }
            .ai-section-card:nth-child(5) { animation-delay: 0.25s; }
            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(10px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            .ai-pill { display: inline-flex; align-items: center; padding: 3px 12px; border-radius: 20px; font-size: 11px; font-weight: 500; letter-spacing: 0.3px; margin: 2px 4px 2px 0; }
            .ai-pill-purple { background: rgba(139,92,246,0.15); color: #A78BFA; border: 1px solid rgba(139,92,246,0.3); }
            .ai-pill-blue   { background: rgba(59,130,246,0.12); color: #60A5FA; border: 1px solid rgba(59,130,246,0.25); }
            .ai-pill-green  { background: rgba(34,197,94,0.12);  color: #4ADE80; border: 1px solid rgba(34,197,94,0.25); }
            .ai-pill-red    { background: rgba(239,68,68,0.12);  color: #F87171; border: 1px solid rgba(239,68,68,0.25); }
            .ai-pill-amber  { background: rgba(245,158,11,0.12); color: #FCD34D; border: 1px solid rgba(245,158,11,0.25); }
            .ticker-tag { display: inline; color: #A78BFA; font-family: "DM Mono", monospace; font-size: 12px; font-weight: 500; }
            .pct-pos { color: #4ADE80; font-weight: 600; font-family: "DM Mono", monospace; }
            .pct-neg { color: #F87171; font-weight: 600; font-family: "DM Mono", monospace; }
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

# ── Tier badge colors for the header accent stripe ───────────────────────────
TIER_COLORS = {k: v["light"] for k, v in TRUST_STACK.items()}

# ── Styles ───────────────────────────────────────────────────────────────────
STYLE = {
    "page": {
        "background": "#07091A",
        "minHeight": "100vh",
        "fontFamily": "'Inter', sans-serif",
        "color": "#E8EDF5",
    },
    "header": {
        "background": "linear-gradient(135deg, #0D0B2A 0%, #130E3A 50%, #0D0B2A 100%)",
        "borderBottom": "1px solid #2D1B6E",
        "padding": "20px 32px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
    },
    "header_badge": {
        "background": "linear-gradient(135deg, #4C1D95, #7C3AED)",
        "borderRadius": "4px",
        "padding": "3px 10px",
        "fontSize": "9px",
        "fontWeight": "700",
        "letterSpacing": "1.5px",
        "color": "white",
        "textTransform": "uppercase",
        "marginLeft": "10px",
        "verticalAlign": "middle",
    },
    "title": {
        "fontWeight": "800",
        "fontSize": "21px",
        "color": "#FFFFFF",
        "letterSpacing": "2px",
        "textTransform": "uppercase",
        "margin": "0",
    },
    "subtitle": {
        "fontFamily": "'DM Mono', monospace",
        "fontSize": "11px",
        "color": "#7C3AED",
        "letterSpacing": "1px",
        "margin": "4px 0 0 0",
    },
    "body": {"padding": "24px 32px"},
    "card": {
        "background": "#0D1030",
        "border": "1px solid #1E1B4B",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "20px",
    },
    "card_title": {
        "fontWeight": "700",
        "fontSize": "13px",
        "color": "#7C3AED",
        "letterSpacing": "2px",
        "textTransform": "uppercase",
        "marginBottom": "16px",
    },
    "btn_primary": {
        "background": "linear-gradient(135deg, #1E1B4B, #3730A3)",
        "border": "none",
        "borderRadius": "4px",
        "color": "white",
        "padding": "8px 20px",
        "fontWeight": "700",
        "fontSize": "12px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "cursor": "pointer",
    },
    "btn_ai": {
        "background": "linear-gradient(135deg, #4C1D95, #7C3AED)",
        "border": "none",
        "borderRadius": "4px",
        "color": "white",
        "padding": "8px 20px",
        "fontWeight": "700",
        "fontSize": "12px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "cursor": "pointer",
        "marginLeft": "8px",
    },
    "ai_box": {
        "background": "#0A0C22",
        "border": "1px solid #4C1D95",
        "borderLeft": "3px solid #7C3AED",
        "borderRadius": "4px",
        "padding": "16px",
        "fontFamily": "'DM Mono', monospace",
        "fontSize": "12px",
        "color": "#C4B5FD",
        "lineHeight": "1.7",
        "whiteSpace": "pre-wrap",
        "marginTop": "12px",
    },
    "metric_card": {
        "background": "#0A0C22",
        "border": "1px solid #1E1B4B",
        "borderRadius": "6px",
        "padding": "16px",
        "textAlign": "center",
    },
    "metric_value": {
        "fontFamily": "'DM Mono', monospace",
        "fontSize": "24px",
        "fontWeight": "700",
        "color": "#FFFFFF",
        "margin": "0",
    },
    "metric_label": {
        "fontSize": "10px",
        "color": "#7C3AED",
        "letterSpacing": "1.5px",
        "textTransform": "uppercase",
        "margin": "4px 0 0 0",
    },
    "tab": {
        "background": "transparent",
        "border": "none",
        "color": "#6B7AA0",
        "padding": "10px 20px",
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
        "color": "#A78BFA",
        "padding": "10px 20px",
        "fontWeight": "700",
        "fontSize": "11px",
        "letterSpacing": "1px",
        "textTransform": "uppercase",
        "borderBottom": "2px solid #7C3AED",
    },
}

# ── Layout ───────────────────────────────────────────────────────────────────

layer_options = [{"label": k, "value": k} for k in TRUST_STACK.keys()]
period_options = [
    {"label": "3 Months", "value": "3mo"},
    {"label": "6 Months", "value": "6mo"},
    {"label": "1 Year",   "value": "1y"},
    {"label": "2 Years",  "value": "2y"},
    {"label": "3 Years",  "value": "3y"},
    {"label": "5 Years",  "value": "5y"},
]

app.layout = html.Div(style=STYLE["page"], children=[

    # ── Header ──
    html.Div(style=STYLE["header"], children=[
        html.Div([
            html.H1([
                "AGENTIC TRUST LAYER",
                html.Span("BENCHMARK", style=STYLE["header_badge"]),
            ], style=STYLE["title"]),
            html.P(
                "AI Governance · Identity · Observability · Security  •  Powered by Claude",
                style=STYLE["subtitle"]
            ),
        ]),
        html.Div([
            html.Span(id="last-updated", style={
                "fontFamily": "'DM Mono', monospace",
                "fontSize": "11px",
                "color": "#7C3AED",
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
                        style={"width": "160px", "fontSize": "12px"},
                    )
                ]),
                html.Div([
                    html.Label("VIEW TIER", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    dcc.Dropdown(
                        id="layer-select",
                        options=[{"label": "All Tiers (Full Stack)", "value": "ALL"}] + layer_options,
                        value="ALL",
                        clearable=False,
                        style={"width": "320px", "fontSize": "12px"},
                    )
                ]),
                html.Div([
                    html.Label("\u00a0", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    html.Button("↻ REFRESH DATA", id="refresh-btn", n_clicks=0, style=STYLE["btn_primary"]),
                    html.Button("✦ AI ANALYSIS",  id="ai-analysis-btn", n_clicks=0, style=STYLE["btn_ai"]),
                ], style={"marginTop": "2px"}),
                html.Div([
                    html.Label("COMPARE TO", style={**STYLE["metric_label"], "display": "block", "marginBottom": "6px"}),
                    dcc.Checklist(
                        id="benchmark-select",
                        options=[{"label": f"  {v}", "value": k} for k, v in BENCHMARKS.items()],
                        value=["SPY", "QQQ", "SOXX", "SMH", "CIBR"],
                        style={"fontFamily": "DM Mono, monospace", "fontSize": "11px", "color": "#FFFFFF"},
                        inputStyle={"marginRight": "4px"},
                        labelStyle={"marginRight": "16px", "display": "inline-block", "color": "#FFFFFF"},
                    )
                ]),
            ])
        ])
    ]),

    # ── Data stores ──
    dcc.Store(id="price-data-store"),
    dcc.Store(id="ai-analysis-text-store"),
    dcc.Store(id="ai-btn-state"),
    dcc.Interval(id="auto-refresh", interval=300_000, n_intervals=0),

    # ── Main Content ──
    html.Div(style=STYLE["body"], children=[

        # Summary metrics row
        html.Div(id="summary-metrics", style={"marginBottom": "20px"}),

        # Tabs
        dcc.Tabs(id="main-tabs", value="overview", style={"marginBottom": "4px"}, children=[
            dcc.Tab(label="TIER OVERVIEW",       value="overview",  style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="PERFORMANCE CHART",   value="perf",      style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="HEAT MAP",            value="heat",      style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="COMPANY DRILL-DOWN",  value="drilldown", style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="CROSS-TIER SCATTER",  value="scatter",   style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="TOP MOVERS",          value="movers",    style=STYLE["tab"], selected_style=STYLE["tab_selected"]),
            dcc.Tab(label="✦ AI ANALYSIS",       value="ai",
                style={**STYLE["tab"], "color": "#7C3AED"},
                selected_style={**STYLE["tab_selected"], "color": "#C4B5FD", "borderBottom": "2px solid #7C3AED"}),
            dcc.Tab(label="◈ FUNDAMENTALS",       value="fundamentals",
                style={**STYLE["tab"], "color": "#22D3EE"},
                selected_style={**STYLE["tab_selected"], "color": "#67E8F9", "borderBottom": "2px solid #22D3EE"}),
        ]),

        html.Div(id="tab-content"),
        dcc.Loading(
            id="ai-loading",
            target_components={"tab-content": "children"},
            overlay_style={"visibility": "visible", "opacity": 0.4,
                           "backgroundColor": "#07091A"},
            color="#7C3AED",
            type="circle",
        ),
    ]),
])

# ── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    Output("price-data-store", "data"),
    Output("last-updated", "children"),
    Input("refresh-btn", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
    Input("period-select", "value"),
    prevent_initial_call=False,
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
        return html.P("Loading data...", style={"color": "#7C3AED", "fontFamily": "DM Mono"})

    df = pd.read_json(StringIO(data_json)).set_index("Date")
    df.index = pd.to_datetime(df.index)

    layers_to_show = list(TRUST_STACK.keys()) if selected_layer == "ALL" else [selected_layer]
    metrics = []

    for layer_key in layers_to_show[:8]:
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        perf = ((idx.iloc[-1] - idx.iloc[0]) / idx.iloc[0]) * 100
        light = TRUST_STACK[layer_key]["light"]
        sign  = "+" if perf >= 0 else ""
        perf_color = "#4ADE80" if perf >= 0 else "#F87171"
        short = layer_key.split("–")[0].strip() if "–" in layer_key else layer_key[:8]
        metrics.append(
            html.Div(style={
                **STYLE["metric_card"],
                "borderTop": f"3px solid {light}",
                "flex": "1", "minWidth": "115px",
            }, children=[
                html.P(f"{sign}{perf:.1f}%", style={**STYLE["metric_value"], "color": perf_color}),
                html.P(short,               style={**STYLE["metric_label"], "color": light}),
            ])
        )

    # Separate benchmark tiles into their own row below tiers
    bm_map = {
        "SPY":  ("#94A3B8", "S&P 500"),
        "QQQ":  ("#FBBF24", "NASDAQ 100"),
        "SOXX": ("#22D3EE", "SOX Semis"),
        "SMH":  ("#FB923C", "VanEck Semi"),
        "CIBR": ("#F472B6", "Cybersecurity"),
    }
    bm_tiles = []
    for ticker, (color, label) in bm_map.items():
        if ticker in df.columns:
            s    = df[ticker].dropna()
            perf = ((s.iloc[-1] - s.iloc[0]) / s.iloc[0]) * 100
            sign = "+" if perf >= 0 else ""
            bm_tiles.append(
                html.Div(style={
                    **STYLE["metric_card"],
                    "borderTop": f"3px solid {color}",
                    "flex": "1", "minWidth": "115px",
                }, children=[
                    html.P(f"{sign}{perf:.1f}%", style={**STYLE["metric_value"], "color": "#AABBCC", "fontSize": "20px"}),
                    html.P(label, style={**STYLE["metric_label"], "color": color}),
                ])
            )

    return html.Div([
        html.Div(metrics,   style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "10px"}),
        html.Div(bm_tiles,  style={"display": "flex", "gap": "10px", "flexWrap": "wrap"}),
    ])

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
            "color": "#7C3AED", "fontFamily": "DM Mono, monospace",
        })

    df = pd.read_json(StringIO(data_json)).set_index("Date")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    if tab == "overview":   return render_overview(df, period, benchmarks)
    elif tab == "perf":     return render_performance_chart(df, period, selected_layer, benchmarks)
    elif tab == "heat":     return render_heatmap(df)
    elif tab == "drilldown":return render_drilldown(df, selected_layer)
    elif tab == "scatter":  return render_scatter(df)
    elif tab == "movers":   return render_movers(df)
    elif tab == "fundamentals": return render_fundamentals(df)
    return html.Div("Select a tab")

@app.callback(
    Output("ai-analysis-text-store", "data"),
    Output("ai-btn-state", "data"),
    Input("ai-analysis-btn", "n_clicks"),
    State("price-data-store", "data"),
    State("period-select", "value"),
    State("layer-select", "value"),
    prevent_initial_call=True,
)
def run_ai_analysis(n_clicks, data_json, period, selected_layer):
    if not data_json or not n_clicks:
        return no_update, no_update

    try:
        df = pd.read_json(StringIO(data_json)).set_index("Date")
        df.index = pd.to_datetime(df.index)

        if selected_layer == "ALL":
            layer_summary = {}
            spy_perf = None
            if "SPY" in df.columns:
                spy = df["SPY"].dropna()
                spy_perf = ((spy.iloc[-1] - spy.iloc[0]) / spy.iloc[0]) * 100
            for layer_key in TRUST_STACK:
                idx = compute_layer_index(df, layer_key)
                if not idx.empty:
                    perf = ((idx.iloc[-1] - idx.iloc[0]) / idx.iloc[0]) * 100
                    entry = {"return_pct": round(perf, 1)}
                    if spy_perf is not None:
                        entry["vs_sp500"] = round(perf - spy_perf, 1)
                    layer_summary[layer_key] = entry
            analysis = get_portfolio_analysis(json.dumps(layer_summary, indent=2), period)
        else:
            layer_data = TRUST_STACK[selected_layer]
            tickers    = [t for t in layer_data["companies"] if t in df.columns]
            stats      = get_current_stats(df, tickers)
            if stats.empty:
                analysis = "No data available for this tier."
            else:
                stats_json = stats[["Ticker", "Name", "Price", "1D %", "Period %"]].to_json(orient="records", indent=2)
                analysis   = get_ai_analysis(stats_json, selected_layer, period)

        store = {
            "text":      analysis,
            "scope":     selected_layer,
            "period":    period,
            "timestamp": datetime.now().strftime("%b %d, %Y  %H:%M"),
        }
        return store, "done"
    except Exception as e:
        store = {
            "text":      f"Analysis error: {str(e)}\n\nCheck that your ANTHROPIC_API_KEY is set correctly.",
            "scope":     selected_layer,
            "period":    period,
            "timestamp": datetime.now().strftime("%b %d, %Y  %H:%M"),
        }
        return store, "done"


@app.callback(
    Output("main-tabs", "value"),
    Input("ai-analysis-text-store", "data"),
    prevent_initial_call=True,
)
def switch_to_ai_tab(store_data):
    """Automatically switch to AI tab once analysis is ready."""
    if store_data and store_data.get("text"):
        return "ai"
    return no_update

@app.callback(
    Output("ai-analysis-btn", "children"),
    Output("ai-analysis-btn", "disabled"),
    Output("ai-analysis-btn", "style"),
    Input("ai-analysis-btn", "n_clicks"),
    Input("ai-btn-state", "data"),
    prevent_initial_call=True,
)
def update_ai_btn(n_clicks, btn_state):
    """Show loading state while AI analysis is running."""
    from dash import ctx
    if ctx.triggered_id == "ai-analysis-btn":
        return "⟳ ANALYZING...", True, {**STYLE["btn_ai"], "opacity": "0.6", "cursor": "not-allowed"}
    return "✦ AI ANALYSIS", False, STYLE["btn_ai"]

# ── Chart helpers ─────────────────────────────────────────────────────────────

def make_fig(fig):
    fig.update_layout(
        paper_bgcolor="#07091A",
        plot_bgcolor="#0D1030",
        font=dict(family="DM Mono, monospace", color="#C4B5FD", size=11),
        xaxis=dict(gridcolor="#1E1B4B", linecolor="#2D1B6E"),
        yaxis=dict(gridcolor="#1E1B4B", linecolor="#2D1B6E"),
        legend=dict(bgcolor="#0A0C22", bordercolor="#2D1B6E", borderwidth=1),
        margin=dict(l=60, r=30, t=50, b=50),
        hoverlabel=dict(
            bgcolor="#0A0C22", bordercolor="#2D1B6E",
            font=dict(family="DM Mono, monospace", size=11, color="#E8EDF5"),
        ),
    )
    return fig

BENCH_COLORS = {"SPY": "#94A3B8", "QQQ": "#FBBF24", "SOXX": "#22D3EE", "SMH": "#FB923C", "CIBR": "#F472B6"}
BENCH_DASH   = {"SPY": "dash", "QQQ": "dot", "SOXX": "dashdot", "SMH": "longdash", "CIBR": "longdashdot"}

# ── Tab renderers ─────────────────────────────────────────────────────────────

def render_overview(df, period, benchmarks):
    fig = go.Figure()

    for bm in (benchmarks or []):
        if bm in df.columns:
            s    = df[bm].dropna()
            norm = (s / s.iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm.values,
                name=BENCHMARKS[bm],
                line=dict(color=BENCH_COLORS.get(bm, "#999"), width=2,
                          dash=BENCH_DASH.get(bm, "dash")),
                opacity=0.85,
            ))

    for layer_key, layer_data in TRUST_STACK.items():
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        short = layer_key.split("–")[1].strip() if "–" in layer_key else layer_key
        fig.add_trace(go.Scatter(
            x=idx.index, y=idx.values,
            name=short,
            line=dict(color=layer_data["light"], width=2.2),
            hovertemplate=f"<b>{layer_key}</b><br>%{{x|%b %d, %Y}}<br>Index: %{{y:.1f}}<extra></extra>",
        ))

    fig.add_hline(y=100, line_color="#2D1B6E", line_dash="dot", line_width=1)
    fig.update_layout(
        title=dict(text="TRUST LAYER TIER INDICES — Equal-Weighted (Base=100)", font=dict(size=13, color="#A78BFA")),
        yaxis_title="Normalized Return (Base=100)",
        height=500, hovermode="x unified",
    )
    make_fig(fig)

    rows = []
    for layer_key, layer_data in TRUST_STACK.items():
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        perf    = ((idx.iloc[-1] - idx.iloc[0]) / idx.iloc[0]) * 100
        n_co    = len([t for t in layer_data["companies"] if t in df.columns])
        spy_perf = None
        if "SPY" in df.columns:
            spy      = df["SPY"].dropna()
            spy_perf = ((spy.iloc[-1] - spy.iloc[0]) / spy.iloc[0]) * 100
        alpha   = perf - spy_perf if spy_perf is not None else None
        rows.append({"Layer": layer_key, "perf": perf, "n": n_co, "alpha": alpha})

    rows.sort(key=lambda x: x["perf"], reverse=True)

    table_rows = []
    for row in rows:
        pc   = "#4ADE80" if row["perf"] >= 0 else "#F87171"
        sign = "+" if row["perf"] >= 0 else ""
        if row["alpha"] is not None:
            ac   = "#4ADE80" if row["alpha"] >= 0 else "#F87171"
            asign = "+" if row["alpha"] >= 0 else ""
            alpha_td = html.Td(
                f"{asign}{row['alpha']:.1f}%",
                style={"padding": "10px 14px", "borderBottom": "1px solid #1E1B4B", "color": ac,
                       "fontFamily": "DM Mono", "textAlign": "right", "fontSize": "12px"},
            )
        else:
            alpha_td = html.Td("—", style={"padding": "10px 14px", "borderBottom": "1px solid #1E1B4B", "color": "#334155", "textAlign": "right"})

        table_rows.append(html.Tr([
            html.Td(row["Layer"], style={"padding": "10px 14px", "borderBottom": "1px solid #1E1B4B", "color": "#C4B5FD"}),
            html.Td(f"{sign}{row['perf']:.1f}%", style={"padding": "10px 14px", "borderBottom": "1px solid #1E1B4B", "color": pc, "fontFamily": "DM Mono", "fontWeight": "700", "textAlign": "right"}),
            html.Td(str(row["n"]), style={"padding": "10px 14px", "borderBottom": "1px solid #1E1B4B", "color": "#6B7AA0", "textAlign": "center"}),
            alpha_td,
            html.Td("↑ OUTPERFORM" if row["perf"] > 0 else "↓ UNDERPERFORM", style={"padding": "10px 14px", "borderBottom": "1px solid #1E1B4B", "color": pc, "fontSize": "11px"}),
        ]))

    th = {"padding": "10px 14px", "color": "#7C3AED", "fontSize": "11px", "letterSpacing": "1px",
          "textAlign": "left", "borderBottom": "2px solid #2D1B6E", "textTransform": "uppercase"}
    table = html.Table([
        html.Thead(html.Tr([
            html.Th("TIER",           style=th),
            html.Th("RETURN",         style={**th, "textAlign": "right"}),
            html.Th("# STOCKS",       style={**th, "textAlign": "center"}),
            html.Th("ALPHA vs SPY",   style={**th, "textAlign": "right"}),
            html.Th("STATUS",         style=th),
        ])),
        html.Tbody(table_rows),
    ], style={"width": "100%", "borderCollapse": "collapse", "fontFamily": "DM Mono, monospace", "fontSize": "12px"})

    return html.Div(style=STYLE["card"], children=[
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.P("TIER PERFORMANCE SUMMARY (vs. SPY / QQQ / SOXX Benchmarks)", style={**STYLE["card_title"], "marginTop": "20px"}),
        table,
    ])


def render_performance_chart(df, period, selected_layer, benchmarks):
    fig = go.Figure()
    for bm in (benchmarks or []):
        if bm in df.columns:
            s = df[bm].dropna()
            norm = (s / s.iloc[0]) * 100
            fig.add_trace(go.Scatter(x=norm.index, y=norm.values, name=BENCHMARKS[bm],
                line=dict(color=BENCH_COLORS.get(bm, "#999"), width=2,
                          dash=BENCH_DASH.get(bm, "dash")), opacity=0.85))

    layers = TRUST_STACK.items() if selected_layer == "ALL" else [(selected_layer, TRUST_STACK[selected_layer])]

    seen_perf = set()
    for layer_key, layer_data in layers:
        for ticker, info in layer_data["companies"].items():
            if ticker in seen_perf:
                continue
            seen_perf.add(ticker)
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if series.empty:
                continue
            norm = (series / series.iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm.values,
                name=f"{ticker} – {info['name'][:30]}",
                line=dict(width=1.5),
                opacity=0.85,
                hovertemplate=f"<b>{ticker}</b><br>%{{x|%b %d, %Y}}<br>Normalized: %{{y:.1f}}<extra></extra>",
            ))

    fig.add_hline(y=100, line_color="#2D1B6E", line_dash="dot")
    fig.update_layout(
        title=dict(text="NORMALIZED PRICE PERFORMANCE (Base=100 at period start)", font=dict(size=13, color="#A78BFA")),
        height=560, hovermode="x unified", yaxis_title="Normalized Price (Base = 100)",
    )
    make_fig(fig)
    return html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": True})])


def render_heatmap(df):
    monthly_returns = {}
    for layer_key in TRUST_STACK:
        idx = compute_layer_index(df, layer_key)
        if idx.empty:
            continue
        monthly = idx.resample("ME").last().pct_change().dropna() * 100
        monthly_returns[layer_key] = monthly

    if not monthly_returns:
        return html.Div("Insufficient data for heatmap.")

    combined = pd.DataFrame(monthly_returns).T
    combined.columns = [str(c)[:7] for c in combined.columns]
    short_names = [k.split("–")[1].strip()[:20] if "–" in k else k[:20] for k in combined.index]

    fig = go.Figure(data=go.Heatmap(
        z=combined.values, x=list(combined.columns), y=short_names,
        colorscale=[
            [0, "#7F1D1D"], [0.35, "#1E1B4B"], [0.5, "#0D1030"],
            [0.65, "#14532D"], [1, "#16A34A"],
        ],
        zmid=0,
        text=[[f"{v:.1f}%" for v in row] for row in combined.values],
        texttemplate="%{text}",
        textfont={"size": 10, "family": "DM Mono, monospace"},
        colorbar=dict(
            title="Monthly %",
            tickfont=dict(color="#C4B5FD", size=10),
            title_font=dict(color="#7C3AED", size=11),
        ),
    ))
    fig.update_layout(
        title=dict(text="MONTHLY RETURN HEATMAP BY TRUST TIER", font=dict(size=13, color="#A78BFA")),
        height=400,
    )
    make_fig(fig)
    return html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": False})])


def render_drilldown(df, selected_layer):
    if selected_layer == "ALL":
        selected_layer = list(TRUST_STACK.keys())[0]
    layer_data = TRUST_STACK[selected_layer]
    tickers    = [t for t in layer_data["companies"] if t in df.columns]
    stats      = get_current_stats(df, tickers)
    if stats.empty:
        return html.Div("No data available.")

    colors = ["#4ADE80" if v >= 0 else "#F87171" for v in stats["Period %"]]

    fig = go.Figure(go.Bar(
        x=stats["Ticker"], y=stats["Period %"],
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in stats["Period %"]],
        textposition="outside",
        textfont=dict(family="DM Mono, monospace", size=10),
        hovertemplate="<b>%{x}</b><br>Return: %{y:.2f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="#2D1B6E", line_width=1)
    fig.update_layout(
        title=dict(text=f"{selected_layer} — Individual Stock Performance", font=dict(size=13, color="#A78BFA")),
        height=380, yaxis_title="Period Return %", showlegend=False,
    )
    make_fig(fig)

    table_rows = []
    for _, row in stats.iterrows():
        color  = "#4ADE80" if row["Period %"] >= 0 else "#F87171"
        d_color= "#4ADE80" if row["1D %"] >= 0 else "#F87171"
        table_rows.append(html.Tr([
            html.Td(row["Ticker"], style={"padding": "9px 14px", "color": "#A78BFA", "fontWeight": "700", "borderBottom": "1px solid #1A1840"}),
            html.Td(row["Name"][:36], style={"padding": "9px 14px", "color": "#C4B5FD", "borderBottom": "1px solid #1A1840", "fontSize": "11px"}),
            html.Td(f"${row['Price']:,.2f}", style={"padding": "9px 14px", "color": "#E8EDF5", "fontFamily": "DM Mono", "borderBottom": "1px solid #1A1840", "textAlign": "right"}),
            html.Td(f"{'+' if row['1D %'] >= 0 else ''}{row['1D %']:.2f}%", style={"padding": "9px 14px", "color": d_color, "fontFamily": "DM Mono", "borderBottom": "1px solid #1A1840", "textAlign": "right"}),
            html.Td(f"{'+' if row['Period %'] >= 0 else ''}{row['Period %']:.1f}%", style={"padding": "9px 14px", "color": color, "fontFamily": "DM Mono", "fontWeight": "700", "borderBottom": "1px solid #1A1840", "textAlign": "right"}),
            html.Td(f"${row['52W High']:,.2f}", style={"padding": "9px 14px", "color": "#6B7AA0", "fontFamily": "DM Mono", "borderBottom": "1px solid #1A1840", "textAlign": "right", "fontSize": "11px"}),
            html.Td(f"${row['52W Low']:,.2f}",  style={"padding": "9px 14px", "color": "#6B7AA0", "fontFamily": "DM Mono", "borderBottom": "1px solid #1A1840", "textAlign": "right", "fontSize": "11px"}),
        ]))

    th = {"padding": "10px 14px", "color": "#7C3AED", "fontSize": "10px", "letterSpacing": "1px",
          "textAlign": "left", "borderBottom": "2px solid #2D1B6E", "textTransform": "uppercase"}
    table = html.Table([
        html.Thead(html.Tr([
            html.Th("Ticker",   style=th), html.Th("Name",    style=th),
            html.Th("Price",    style={**th, "textAlign": "right"}),
            html.Th("1D %",     style={**th, "textAlign": "right"}),
            html.Th("Period %", style={**th, "textAlign": "right"}),
            html.Th("52W High", style={**th, "textAlign": "right"}),
            html.Th("52W Low",  style={**th, "textAlign": "right"}),
        ])),
        html.Tbody(table_rows),
    ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "12px", "fontFamily": "DM Mono, monospace"})

    return html.Div(style=STYLE["card"], children=[
        html.P(layer_data["description"], style={"color": "#6B7AA0", "fontFamily": "DM Mono, monospace", "fontSize": "11px", "marginBottom": "16px"}),
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.P("DETAILED METRICS", style={**STYLE["card_title"], "marginTop": "20px"}),
        table,
    ])


def render_scatter(df):
    seen = set()
    all_tickers = []
    for layer_key, layer_data in TRUST_STACK.items():
        for t in layer_data["companies"]:
            if t not in seen:
                seen.add(t)
                all_tickers.append((t, layer_key, layer_data["light"]))

    stats_data = []
    for ticker, layer, color in all_tickers:
        if ticker not in df.columns:
            continue
        series = df[ticker].dropna()
        if len(series) < 5:
            continue
        period_ret = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
        d_ret      = ((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]) * 100
        stats_data.append({
            "ticker": ticker,
            "layer":  layer.split("–")[1].strip()[:18] if "–" in layer else layer[:18],
            "1d": d_ret, "period": period_ret, "color": color,
        })

    if not stats_data:
        return html.Div("No data.")

    sdf = pd.DataFrame(stats_data)
    fig = px.scatter(
        sdf, x="period", y="1d",
        color="layer", text="ticker",
        hover_data={"ticker": True, "layer": True, "1d": ":.2f", "period": ":.1f"},
        labels={"period": "Period Return %", "1d": "1-Day Return %", "layer": "Tier"},
        title="CROSS-TIER SCATTER: Period Return vs. 1-Day Momentum — Trust Layer Universe",
        color_discrete_sequence=[v["light"] for v in TRUST_STACK.values()],
    )
    fig.update_traces(textposition="top center", textfont=dict(size=8, family="DM Mono, monospace"))
    fig.add_vline(x=0, line_color="#2D1B6E", line_dash="dot")
    fig.add_hline(y=0, line_color="#2D1B6E", line_dash="dot")
    fig.update_layout(height=560)
    make_fig(fig)
    fig.update_layout(title=dict(font=dict(size=13, color="#A78BFA")))
    return html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": True})])


def render_movers(df):
    seen = set()
    all_stats = []
    for layer_key, layer_data in TRUST_STACK.items():
        for ticker in layer_data["companies"]:
            if ticker in seen:
                continue
            seen.add(ticker)
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if len(series) < 2:
                continue
            perf   = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
            d_perf = ((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]) * 100
            all_stats.append({
                "Ticker":  ticker,
                "Name":    layer_data["companies"][ticker]["name"],
                "Tier":    layer_key.split("–")[1].strip()[:16] if "–" in layer_key else layer_key[:16],
                "Period %": perf,
                "1D %":     d_perf,
                "Color":    layer_data["light"],
            })

    if not all_stats:
        return html.Div("No data.")

    sdf  = pd.DataFrame(all_stats).sort_values("Period %", ascending=False)
    top10 = sdf.head(10)
    bot10 = sdf.tail(10).sort_values("Period %")

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("TOP 10 GAINERS", "BOTTOM 10 LAGGARDS"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(go.Bar(
        x=top10["Period %"], y=top10["Ticker"], orientation="h",
        marker_color=top10["Color"].tolist(),
        text=[f"+{v:.1f}%" for v in top10["Period %"]],
        textposition="outside", textfont=dict(size=10, family="DM Mono"),
        name="Gainers",
        hovertemplate="<b>%{y}</b><br>Return: %{x:.1f}%<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=bot10["Period %"], y=bot10["Ticker"], orientation="h",
        marker_color="#F87171",
        text=[f"{v:.1f}%" for v in bot10["Period %"]],
        textposition="outside", textfont=dict(size=10, family="DM Mono"),
        name="Laggards",
        hovertemplate="<b>%{y}</b><br>Return: %{x:.1f}%<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(height=460, showlegend=False)
    fig.update_xaxes(gridcolor="#1E1B4B", linecolor="#2D1B6E")
    fig.update_yaxes(gridcolor="#1E1B4B", linecolor="#2D1B6E")
    make_fig(fig)
    for ann in fig.layout.annotations:
        ann.font.color = "#A78BFA"
        ann.font.size  = 12

    top5_1d = sdf.nlargest(5, "1D %")
    bot5_1d = sdf.nsmallest(5, "1D %")

    def mini_table(data, title, color):
        rows = []
        for _, r in data.iterrows():
            rows.append(html.Tr([
                html.Td(r["Ticker"], style={"padding": "8px 12px", "color": "#A78BFA", "fontWeight": "700", "borderBottom": "1px solid #1A1840", "fontSize": "12px"}),
                html.Td(r["Name"][:24], style={"padding": "8px 12px", "color": "#C4B5FD", "borderBottom": "1px solid #1A1840", "fontSize": "11px"}),
                html.Td(f"{'+' if r['1D %'] >= 0 else ''}{r['1D %']:.2f}%", style={"padding": "8px 12px", "color": color, "fontFamily": "DM Mono", "fontWeight": "700", "borderBottom": "1px solid #1A1840", "fontSize": "12px", "textAlign": "right"}),
            ]))
        return html.Div([
            html.P(title, style={**STYLE["card_title"], "color": color}),
            html.Table([html.Tbody(rows)], style={"width": "100%", "borderCollapse": "collapse"}),
        ])

    return html.Div([
        html.Div(style=STYLE["card"], children=[dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        html.Div(style={"display": "flex", "gap": "16px"}, children=[
            html.Div(style={**STYLE["card"], "flex": "1"}, children=[mini_table(top5_1d, "TODAY'S TOP MOVERS", "#4ADE80")]),
            html.Div(style={**STYLE["card"], "flex": "1"}, children=[mini_table(bot5_1d, "TODAY'S BIGGEST DROPS", "#F87171")]),
        ]),
    ])


# ── AI Analysis Tab ───────────────────────────────────────────────────────────

def render_ai_tab(ai_text_data, selected_layer, period):
    import re

    if not ai_text_data:
        return html.Div(style={**STYLE["card"], "textAlign": "center", "padding": "72px 40px"}, children=[
            html.Div(style={
                "width": "64px", "height": "64px", "borderRadius": "50%",
                "background": "rgba(124,58,237,0.12)", "border": "1px solid rgba(124,58,237,0.3)",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "margin": "0 auto 20px auto", "fontSize": "28px",
            }, children="✦"),
            html.P("No analysis yet", style={
                "fontWeight": "600", "fontSize": "18px", "color": "#E2E8F0",
                "margin": "0 0 10px 0", "letterSpacing": "-0.3px",
            }),
            html.P("Select a time period and tier above, then click  ✦ AI ANALYSIS  to generate a Claude-powered trust layer report.",
                style={"color": "#475569", "fontSize": "14px", "lineHeight": "1.7",
                       "maxWidth": "440px", "margin": "0 auto", "fontWeight": "400"}),
        ])

    raw_text   = ai_text_data.get("text", "")
    scope      = ai_text_data.get("scope", selected_layer)
    period_lbl = ai_text_data.get("period", period)
    timestamp  = ai_text_data.get("timestamp", "")

    def clean_text(text):
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.M)
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    SKIP_WORDS = {
        "AI","THE","AND","FOR","BUT","NOT","WITH","THIS","FROM","THAT","HAVE","WILL","ARE","ITS",
        "WAS","HAS","ALL","NEW","ONE","TWO","CAN","MAY","TOP","KEY","LOW","HIGH","OVER","NEXT",
        "LAST","EACH","YEAR","THAN","ALSO","INTO","VERY","EVEN","JUST","MOST","ONLY","SUCH",
        "BOTH","MORE","LESS","LONG","TERM","NEAR","RISK","WELL","BEEN","THEY","THEM","FULL",
        "HALF","WIDE","DEEP","BIG","DUE","SET","LED","YET","VS","EX","US","EU","GDP","EPS",
        "PE","YOY","QOQ","CEO","CFO","CTO","IPO","ETF","SaaS","IAM","PAM","NHI","GRC",
    }

    def highlight_inline(text):
        text = re.sub(
            r'([+\-]?\d+\.?\d*%)',
            lambda m: (f'<span class="pct-pos">{m.group(1)}</span>'
                       if not m.group(1).startswith("-")
                       else f'<span class="pct-neg">{m.group(1)}</span>'),
            text,
        )
        text = re.sub(
            r'\b([A-Z]{2,5})\b(?![a-z])',
            lambda m: (f'<span class="ticker-tag">{m.group(1)}</span>'
                       if m.group(1) not in SKIP_WORDS else m.group(1)),
            text,
        )
        return text

    def parse_sections(text):
        text = clean_text(text)
        pattern = re.compile(
            r'^\d+\.\s+([^\n:]+?)(?::\s*|\n)(.*?)(?=^\d+\.\s+|\Z)',
            re.MULTILINE | re.DOTALL,
        )
        matches = pattern.findall(text)

        section_cfg = {
            "Key Outperformers":       ("#4ADE80", "#052E16", "#166534", "↑"),
            "Laggards":                ("#F87171", "#1C0A0A", "#7F1D1D", "↓"),
            "Layer Thesis":            ("#60A5FA", "#0C1A2E", "#1E40AF", "◈"),
            "Stack Flow":              ("#60A5FA", "#0C1A2E", "#1E40AF", "⟳"),
            "Notable Signal":          ("#FCD34D", "#1C1200", "#78350F", "◆"),
            "Investment Positioning":  ("#34D399", "#061A14", "#065F46", "$"),
            "Risk Factor":             ("#F87171", "#1C0A0A", "#7F1D1D", "⚠"),
            "Macro Signal":            ("#C084FC", "#160B2C", "#6B21A8", "≈"),
            "Contrarian Opportunity":  ("#FCD34D", "#1C1200", "#78350F", "◎"),
            "Leading vs. Lagging":     ("#60A5FA", "#0C1A2E", "#1E40AF", "↕"),
            "Adoption Signal":         ("#A78BFA", "#1A0D35", "#4C1D95", "◎"),
        }
        default_cfg = ("#94A3B8", "#0F172A", "#334155", "·")

        cards = []
        if matches:
            for title, content in matches:
                title   = clean_text(title.strip())
                content = clean_text(content.strip())
                accent, bg, border, icon = section_cfg.get(title, default_cfg)
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                para_els = [
                    dcc.Markdown(
                        highlight_inline(p),
                        dangerously_allow_html=True,
                        style={"fontSize": "14px", "lineHeight": "1.75", "color": "#CBD5E1",
                               "marginBottom": "8px", "fontWeight": "400"},
                    )
                    for p in paragraphs
                ]
                cards.append(html.Div(
                    className="ai-section-card",
                    style={"background": bg, "border": f"1px solid {border}",
                           "borderLeft": f"3px solid {accent}", "borderRadius": "10px",
                           "padding": "20px 24px", "marginBottom": "10px"},
                    children=[
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "14px"}, children=[
                            html.Span(icon, style={"fontSize": "13px", "color": accent, "width": "24px", "height": "24px",
                                                   "display": "inline-flex", "alignItems": "center", "justifyContent": "center",
                                                   "background": "rgba(255,255,255,0.06)", "borderRadius": "6px", "flexShrink": "0"}),
                            html.Span(title, style={"fontWeight": "600", "fontSize": "13px", "color": accent, "letterSpacing": "0.1px"}),
                        ]),
                        html.Div(para_els),
                    ],
                ))
        else:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for p in paragraphs:
                cards.append(dcc.Markdown(
                    highlight_inline(p),
                    dangerously_allow_html=True,
                    style={"fontSize": "14px", "lineHeight": "1.75", "color": "#CBD5E1", "marginBottom": "14px"},
                ))
        return cards

    period_map     = {"3mo": "3 Months", "6mo": "6 Months", "1y": "1 Year",
                      "2y": "2 Years",   "3y": "3 Years",   "5y": "5 Years"}
    scope_label    = scope if scope != "ALL" else "All Tiers — Full Trust Stack"
    period_display = period_map.get(period_lbl, period_lbl)

    return html.Div([
        html.Div(style={
            "background": "linear-gradient(135deg, #0F0A1F 0%, #1A0D35 60%, #0F0A1F 100%)",
            "border": "1px solid rgba(124,58,237,0.25)", "borderRadius": "12px",
            "padding": "28px 32px", "marginBottom": "16px",
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "flex-start", "flexWrap": "wrap", "gap": "16px",
        }, children=[
            html.Div([
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "12px"}, children=[
                    html.Div(style={"width": "36px", "height": "36px",
                                    "background": "rgba(124,58,237,0.2)", "border": "1px solid rgba(124,58,237,0.4)",
                                    "borderRadius": "10px", "display": "flex", "alignItems": "center",
                                    "justifyContent": "center", "fontSize": "16px", "color": "#A78BFA"},
                             children="✦"),
                    html.Div([
                        html.Span("Trust Layer Analysis Report", style={"fontWeight": "700", "fontSize": "20px",
                                                                          "color": "#F1F5F9", "letterSpacing": "-0.5px", "display": "block"}),
                        html.Span("Powered by Claude — Agentic Economy Thesis", style={"fontSize": "12px", "color": "#7C3AED", "fontWeight": "500"}),
                    ]),
                ]),
                html.Div(style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}, children=[
                    html.Span(scope_label,    className="ai-pill ai-pill-purple"),
                    html.Span(period_display, className="ai-pill ai-pill-blue"),
                    html.Span(f"Generated {timestamp}", className="ai-pill ai-pill-blue") if timestamp else html.Span(""),
                ]),
            ]),
            html.Div(style={"background": "rgba(255,255,255,0.04)", "border": "1px solid rgba(255,255,255,0.08)",
                            "borderRadius": "8px", "padding": "12px 16px", "textAlign": "right"}, children=[
                html.Span("Model", style={"display": "block", "color": "#475569", "fontSize": "10px",
                                          "fontWeight": "500", "letterSpacing": "0.5px",
                                          "textTransform": "uppercase", "marginBottom": "4px"}),
                html.Span("claude-sonnet-4-6", style={"color": "#A78BFA", "fontSize": "13px",
                                                       "fontWeight": "600", "fontFamily": "DM Mono, monospace"}),
            ]),
        ]),

        html.Div(id="ai-analysis-output", children=parse_sections(raw_text)),

        html.Div(style={"marginTop": "20px", "padding": "14px 20px",
                        "background": "rgba(255,255,255,0.02)", "border": "1px solid rgba(255,255,255,0.06)",
                        "borderRadius": "8px", "display": "flex", "alignItems": "center", "gap": "10px"}, children=[
            html.Span("ⓘ", style={"color": "#334155", "fontSize": "16px", "flexShrink": "0"}),
            html.Span("AI-generated analysis is for informational purposes only and does not constitute financial advice. Always conduct your own due diligence.",
                      style={"color": "#334155", "fontSize": "11px", "lineHeight": "1.5", "fontWeight": "400"}),
        ]),
    ])


# ──────────────────────────────────────────────────────────────────────────────
# FUNDAMENTALS DATA  — consensus estimates + trust-layer relevance scoring
# Sources: company filings, Visible Alpha consensus, Wall Street consensus (Feb 2026)
# ──────────────────────────────────────────────────────────────────────────────

FUNDAMENTALS = {
    # ticker: {name, tier, relevance, rev_growth, gross_margin, nrr, ev_ntm_rev, ma_flag, ma_note, notes}
    "CRWD": {"name": "CrowdStrike",       "tier": "T3/T4", "relevance": "HIGHEST",
              "rev_growth": 25.0, "gross_margin": 77.5, "nrr": 124, "ev_ntm_rev": 22.0,
              "ma_flag": False, "ma_note": "",
              "notes": "Falcon Identity + agentic threat intel; NHI workloads expanding"},
    "OKTA": {"name": "Okta",              "tier": "T3",    "relevance": "HIGHEST",
              "rev_growth": 13.0, "gross_margin": 76.0, "nrr": 110, "ev_ntm_rev": 8.5,
              "ma_flag": True,  "ma_note": "Potential acqui-hire or acqui-target speculation",
              "notes": "Agent identity FY27 roadmap; Auth0 integration maturing"},
    "CYBR": {"name": "CyberArk",          "tier": "T3",    "relevance": "HIGHEST",
              "rev_growth": 30.0, "gross_margin": 78.0, "nrr": 122, "ev_ntm_rev": 14.0,
              "ma_flag": False, "ma_note": "",
              "notes": "Privileged access + secrets mgmt for AI agents; fastest NHI growth"},
    "PANW": {"name": "Palo Alto Networks", "tier": "T3/T4", "relevance": "HIGHEST",
              "rev_growth": 14.0, "gross_margin": 74.5, "nrr": 115, "ev_ntm_rev": 13.0,
              "ma_flag": True,  "ma_note": "Active M&A — acquired Talon, Dig, IBM QRadar assets",
              "notes": "AI Security Posture Mgmt (AI-SPM); platformization driving NRR expansion"},
    "NET":  {"name": "Cloudflare",         "tier": "T4",    "relevance": "HIGH",
              "rev_growth": 27.0, "gross_margin": 77.5, "nrr": 118, "ev_ntm_rev": 18.0,
              "ma_flag": False, "ma_note": "",
              "notes": "AI Gateway for agent traffic; Zero Trust + Workers AI convergence"},
    "DDOG": {"name": "Datadog",            "tier": "T2/T6", "relevance": "HIGH",
              "rev_growth": 24.0, "gross_margin": 80.5, "nrr": 116, "ev_ntm_rev": 17.5,
              "ma_flag": True,  "ma_note": "Invested in Arize AI; M&A appetite for LLM observability",
              "notes": "LLM Observability product GA; AI spend monitoring expanding"},
    "SNOW": {"name": "Snowflake",          "tier": "T2/T6", "relevance": "HIGH",
              "rev_growth": 29.0, "gross_margin": 67.0, "nrr": 127, "ev_ntm_rev": 14.0,
              "ma_flag": True,  "ma_note": "Acquired TruEra (model observability)",
              "notes": "Cortex AI + TruEra = data + model governance on single platform"},
    "DT":   {"name": "Dynatrace",          "tier": "T2",    "relevance": "HIGH",
              "rev_growth": 19.0, "gross_margin": 80.0, "nrr": 113, "ev_ntm_rev": 9.0,
              "ma_flag": False, "ma_note": "",
              "notes": "Davis AI engine extended to LLM observability; strong EMEA enterprise"},
    "SAIL": {"name": "SailPoint",          "tier": "T3",    "relevance": "HIGHEST",
              "rev_growth": 20.0, "gross_margin": 71.0, "nrr": 118, "ev_ntm_rev": 10.5,
              "ma_flag": False, "ma_note": "",
              "notes": "Pure-play non-human identity governance; newly public FY25"},
    "PLTR": {"name": "Palantir",           "tier": "T2",    "relevance": "HIGH",
              "rev_growth": 28.0, "gross_margin": 79.0, "nrr": 108, "ev_ntm_rev": 35.0,
              "ma_flag": False, "ma_note": "",
              "notes": "AIP model monitoring + governance; high EV/Rev reflects AI sentiment premium"},
    "NOW":  {"name": "ServiceNow",         "tier": "T1/T5/T6", "relevance": "HIGH",
              "rev_growth": 22.0, "gross_margin": 79.5, "nrr": 120, "ev_ntm_rev": 16.0,
              "ma_flag": True,  "ma_note": "Acquired multiple AI workflow assets in FY25",
              "notes": "Vancouver agentic workflows; AI Governance Studio in beta"},
    "CRM":  {"name": "Salesforce",         "tier": "T1/T5/T6", "relevance": "HIGH",
              "rev_growth": 9.0,  "gross_margin": 76.0, "nrr": 108, "ev_ntm_rev": 7.5,
              "ma_flag": False, "ma_note": "",
              "notes": "Agentforce platform + Einstein Trust Layer; $3B+ agent ARR target"},
    "IBM":  {"name": "IBM",                "tier": "T1/T6", "relevance": "HIGH",
              "rev_growth": 3.0,  "gross_margin": 55.0, "nrr": None, "ev_ntm_rev": 3.5,
              "ma_flag": True,  "ma_note": "Acquired Apptio, HashiCorp; active portfolio reshaping",
              "notes": "OpenPages GRC + Watson Governance; Hybrid cloud AI governance"},
    "CSCO": {"name": "Cisco",              "tier": "T4",    "relevance": "HIGH",
              "rev_growth": 1.0,  "gross_margin": 63.5, "nrr": None, "ev_ntm_rev": 4.5,
              "ma_flag": True,  "ma_note": "Acquired Robust Intelligence, Splunk ($28B)",
              "notes": "Robust Intelligence acquisition = AI red-teaming capability"},
    "CHKP": {"name": "Check Point",        "tier": "T4",    "relevance": "HIGH",
              "rev_growth": 7.0,  "gross_margin": 86.0, "nrr": None, "ev_ntm_rev": 6.5,
              "ma_flag": True,  "ma_note": "Acquired Astrix Security (NHI governance)",
              "notes": "Astrix = machine-to-machine identity; Infinity platform expanding"},
    "FTNT": {"name": "Fortinet",           "tier": "T4",    "relevance": "HIGH",
              "rev_growth": 12.0, "gross_margin": 75.5, "nrr": None, "ev_ntm_rev": 8.0,
              "ma_flag": False, "ma_note": "",
              "notes": "FortiAI threat detection; enterprise SASE + AI security convergence"},
    "MSFT": {"name": "Microsoft",          "tier": "T1/T3/T5/T6", "relevance": "HIGHEST",
              "rev_growth": 16.0, "gross_margin": 70.0, "nrr": None, "ev_ntm_rev": 12.0,
              "ma_flag": True,  "ma_note": "Active AI acquisitions; Activision integration",
              "notes": "Entra cross-app agent auth + Purview governance; Azure OpenAI platform"},
    "AMZN": {"name": "Amazon",             "tier": "T5",    "relevance": "HIGH",
              "rev_growth": 11.0, "gross_margin": 47.5, "nrr": None, "ev_ntm_rev": 3.5,
              "ma_flag": False, "ma_note": "",
              "notes": "Bedrock multi-agent + AWS IAM for AI; Guardrails product"},
    "GOOGL": {"name": "Alphabet",          "tier": "T5",    "relevance": "HIGH",
               "rev_growth": 13.0, "gross_margin": 58.0, "nrr": None, "ev_ntm_rev": 6.5,
               "ma_flag": False, "ma_note": "",
               "notes": "Vertex AI + SynthID watermarking; Workspace AI governance"},
    "TRI":  {"name": "Thomson Reuters",    "tier": "T8",    "relevance": "HIGHEST",
              "rev_growth": 8.0,  "gross_margin": 60.0, "nrr": None, "ev_ntm_rev": 7.0,
              "ma_flag": False, "ma_note": "",
              "notes": "CoCounsel legal AI agent; hallucination-zero mandate for legal"},
    "RELX": {"name": "RELX / LexisNexis",  "tier": "T8",    "relevance": "HIGHEST",
              "rev_growth": 9.0,  "gross_margin": 62.0, "nrr": None, "ev_ntm_rev": 6.0,
              "ma_flag": False, "ma_note": "",
              "notes": "Protégé legal AI with citation verification; risk analytics AI"},
    "ORCL": {"name": "Oracle",             "tier": "T8",    "relevance": "HIGH",
              "rev_growth": 12.0, "gross_margin": 71.0, "nrr": None, "ev_ntm_rev": 8.5,
              "ma_flag": True,  "ma_note": "Cerner integration; cloud ERP M&A opportunistic",
              "notes": "AI data governance + audit trails; Fusion ERP AI agents"},
    "WDAY": {"name": "Workday",            "tier": "T8",    "relevance": "HIGH",
              "rev_growth": 15.0, "gross_margin": 74.0, "nrr": 105, "ev_ntm_rev": 8.5,
              "ma_flag": False, "ma_note": "",
              "notes": "AI governance for HR/Finance; Skills Cloud + AI-native workflows"},
    "YOU":  {"name": "Clear Secure",       "tier": "T3/T7", "relevance": "HIGH",
              "rev_growth": 14.0, "gross_margin": 55.0, "nrr": None, "ev_ntm_rev": 3.5,
              "ma_flag": False, "ma_note": "",
              "notes": "Biometric human counterproof; airport + stadium expansion"},
    "MITK": {"name": "Mitek Systems",      "tier": "T3/T7", "relevance": "HIGH",
              "rev_growth": 8.0,  "gross_margin": 68.0, "nrr": None, "ev_ntm_rev": 2.5,
              "ma_flag": False, "ma_note": "",
              "notes": "Liveness detection + deepfake defense for banking/fintech"},
    "MDB":  {"name": "MongoDB",            "tier": "T2",    "relevance": "HIGH",
              "rev_growth": 22.0, "gross_margin": 70.5, "nrr": 118, "ev_ntm_rev": 10.0,
              "ma_flag": False, "ma_note": "",
              "notes": "Atlas Vector Search + AI data layer; agent memory store"},
    "SAP":  {"name": "SAP",                "tier": "T1",    "relevance": "HIGH",
              "rev_growth": 10.0, "gross_margin": 72.0, "nrr": None, "ev_ntm_rev": 6.5,
              "ma_flag": False, "ma_note": "",
              "notes": "AI Governance & Compliance module; 300M+ enterprise user base"},
    "META": {"name": "Meta",               "tier": "T8",    "relevance": "HIGH",
              "rev_growth": 19.0, "gross_margin": 81.0, "nrr": None, "ev_ntm_rev": 8.5,
              "ma_flag": False, "ma_note": "",
              "notes": "Llama Guard open-source safety layer; Responsible AI tooling"},
}

RELEVANCE_ORDER = {"HIGHEST": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def render_fundamentals(df):
    """Fundamentals tab: grouped by tier, filterable by relevance, key metrics table."""
    import re

    # ── Header + filter controls ──────────────────────────────────────────────
    header = html.Div(style={
        "background": "linear-gradient(135deg, #051A2E 0%, #0A1E3A 100%)",
        "border": "1px solid rgba(34,211,238,0.25)", "borderRadius": "10px",
        "padding": "20px 24px", "marginBottom": "16px",
        "display": "flex", "justifyContent": "space-between", "flexWrap": "wrap", "gap": "12px",
    }, children=[
        html.Div([
            html.Span("◈ TRUST LAYER FUNDAMENTALS", style={
                "fontWeight": "700", "fontSize": "16px", "color": "#67E8F9",
                "letterSpacing": "1px", "display": "block", "marginBottom": "4px",
            }),
            html.Span("Revenue Growth · Gross Margin · NRR · EV/NTM Revenue · M&A Flags — filtered to HIGH/HIGHEST trust-layer relevance",
                      style={"color": "#64748B", "fontSize": "11px"}),
        ]),
        html.Div(style={"display": "flex", "gap": "8px", "alignItems": "center"}, children=[
            html.Span("Showing:", style={"color": "#64748B", "fontSize": "11px"}),
            html.Span("HIGH + HIGHEST relevance", style={
                "background": "rgba(34,211,238,0.1)", "border": "1px solid rgba(34,211,238,0.3)",
                "borderRadius": "20px", "padding": "3px 12px",
                "color": "#22D3EE", "fontSize": "11px", "fontWeight": "600",
            }),
        ]),
    ])

    # ── Build rows, filtered to HIGH/HIGHEST, grouped by tier ────────────────
    by_tier = {}
    for ticker, fd in FUNDAMENTALS.items():
        if fd["relevance"] not in ("HIGH", "HIGHEST"):
            continue
        tier = fd["tier"]
        by_tier.setdefault(tier, []).append((ticker, fd))

    # Sort tiers
    def tier_sort_key(t):
        m = re.match(r"T(\d+)", t)
        return int(m.group(1)) if m else 99
    sorted_tiers = sorted(by_tier.keys(), key=tier_sort_key)

    th_style = {
        "padding": "9px 12px", "color": "#22D3EE", "fontSize": "10px",
        "letterSpacing": "1px", "textAlign": "left",
        "borderBottom": "2px solid #0E3A50", "textTransform": "uppercase",
        "fontWeight": "700", "whiteSpace": "nowrap",
    }

    blocks = []
    for tier in sorted_tiers:
        items = sorted(by_tier[tier], key=lambda x: RELEVANCE_ORDER.get(x[1]["relevance"], 9))
        tier_label = tier  # e.g. "T3" or "T3/T4"

        # Map tier label to color from TRUST_STACK
        tier_color = "#22D3EE"
        for k, v in TRUST_STACK.items():
            if k.startswith(f"T{tier.replace('T','')[0]}"):
                tier_color = v["light"]
                tier_label = k
                break

        rows = []
        for ticker, fd in items:
            # Pull price performance from df
            period_pct = None
            d_pct = None
            if ticker in df.columns:
                s = df[ticker].dropna()
                if len(s) >= 2:
                    period_pct = ((s.iloc[-1] - s.iloc[0]) / s.iloc[0]) * 100
                    d_pct = ((s.iloc[-1] - s.iloc[-2]) / s.iloc[-2]) * 100

            rel_badge_color = "#22D3EE" if fd["relevance"] == "HIGHEST" else "#60A5FA"
            rel_bg = "rgba(34,211,238,0.1)" if fd["relevance"] == "HIGHEST" else "rgba(96,165,250,0.1)"
            rel_border = "rgba(34,211,238,0.3)" if fd["relevance"] == "HIGHEST" else "rgba(96,165,250,0.3)"

            def fmt_pct(v, plus=True):
                if v is None: return "—"
                s = f"+{v:.1f}%" if v >= 0 and plus else f"{v:.1f}%"
                return s

            rev_color = "#4ADE80" if fd["rev_growth"] >= 20 else "#FCD34D" if fd["rev_growth"] >= 10 else "#F87171"
            gm_color  = "#4ADE80" if fd["gross_margin"] >= 75 else "#FCD34D" if fd["gross_margin"] >= 60 else "#F87171"
            nrr_val   = f"{fd['nrr']}%" if fd["nrr"] else "N/A"
            nrr_color = "#4ADE80" if fd["nrr"] and fd["nrr"] >= 120 else "#FCD34D" if fd["nrr"] and fd["nrr"] >= 110 else "#94A3B8"
            ev_color  = "#F87171" if fd["ev_ntm_rev"] > 20 else "#FCD34D" if fd["ev_ntm_rev"] > 10 else "#4ADE80"
            price_color = "#4ADE80" if period_pct and period_pct >= 0 else "#F87171"

            rows.append(html.Tr([
                # Ticker + name
                html.Td([
                    html.Span(ticker, style={"color": "#A78BFA", "fontWeight": "700", "fontFamily": "DM Mono", "fontSize": "13px"}),
                    html.Br(),
                    html.Span(fd["name"], style={"color": "#64748B", "fontSize": "10px"}),
                ], style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "whiteSpace": "nowrap"}),
                # Relevance badge
                html.Td(
                    html.Span(fd["relevance"], style={
                        "background": rel_bg, "border": f"1px solid {rel_border}",
                        "borderRadius": "20px", "padding": "2px 8px",
                        "color": rel_badge_color, "fontSize": "10px", "fontWeight": "600",
                    }),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "textAlign": "center"},
                ),
                # Revenue Growth YoY
                html.Td(
                    html.Span(f"{fd['rev_growth']:+.0f}%", style={"color": rev_color, "fontFamily": "DM Mono", "fontWeight": "700", "fontSize": "13px"}),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "textAlign": "right"},
                ),
                # Gross Margin
                html.Td(
                    html.Span(f"{fd['gross_margin']:.0f}%", style={"color": gm_color, "fontFamily": "DM Mono", "fontSize": "13px"}),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "textAlign": "right"},
                ),
                # NRR
                html.Td(
                    html.Span(nrr_val, style={"color": nrr_color, "fontFamily": "DM Mono", "fontSize": "13px"}),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "textAlign": "right"},
                ),
                # EV/NTM Revenue
                html.Td(
                    html.Span(f"{fd['ev_ntm_rev']:.1f}x", style={"color": ev_color, "fontFamily": "DM Mono", "fontSize": "13px"}),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "textAlign": "right"},
                ),
                # M&A Flag
                html.Td([
                    html.Span("◆ M&A", style={
                        "background": "rgba(251,191,36,0.1)", "border": "1px solid rgba(251,191,36,0.3)",
                        "borderRadius": "4px", "padding": "2px 6px",
                        "color": "#FBBF24", "fontSize": "10px", "fontWeight": "600",
                    }) if fd["ma_flag"] else html.Span("—", style={"color": "#334155"}),
                    html.Br() if fd["ma_note"] else html.Span(""),
                    html.Span(fd["ma_note"][:36] if fd["ma_note"] else "", style={"color": "#475569", "fontSize": "9px", "lineHeight": "1.3"}),
                ], style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50"}),
                # Price performance
                html.Td(
                    html.Span(fmt_pct(period_pct), style={"color": price_color, "fontFamily": "DM Mono", "fontWeight": "700", "fontSize": "13px"}),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "textAlign": "right"},
                ),
                # Notes
                html.Td(
                    html.Span(fd["notes"], style={"color": "#64748B", "fontSize": "10px", "lineHeight": "1.4"}),
                    style={"padding": "10px 12px", "borderBottom": "1px solid #0E3A50", "maxWidth": "220px"},
                ),
            ]))

        table = html.Table([
            html.Thead(html.Tr([
                html.Th("COMPANY",        style=th_style),
                html.Th("RELEVANCE",      style={**th_style, "textAlign": "center"}),
                html.Th("REV GROWTH",     style={**th_style, "textAlign": "right"}),
                html.Th("GROSS MARGIN",   style={**th_style, "textAlign": "right"}),
                html.Th("NRR",            style={**th_style, "textAlign": "right"}),
                html.Th("EV/NTM REV",     style={**th_style, "textAlign": "right"}),
                html.Th("M&A FLAG",       style=th_style),
                html.Th("PERIOD PERF",    style={**th_style, "textAlign": "right"}),
                html.Th("THESIS NOTE",    style=th_style),
            ])),
            html.Tbody(rows),
        ], style={"width": "100%", "borderCollapse": "collapse", "fontFamily": "Inter, sans-serif"})

        blocks.append(html.Div(style={
            **STYLE["card"],
            "borderTop": f"3px solid {tier_color}",
            "padding": "0", "overflow": "hidden",
        }, children=[
            html.Div(style={
                "padding": "14px 20px",
                "borderBottom": "1px solid #0E3A50",
                "background": "rgba(0,0,0,0.2)",
                "display": "flex", "alignItems": "center", "gap": "12px",
            }, children=[
                html.Span(tier_label, style={"color": tier_color, "fontWeight": "700", "fontSize": "13px", "letterSpacing": "0.5px"}),
                html.Span(f"{len(items)} companies", style={"color": "#475569", "fontSize": "11px"}),
            ]),
            html.Div(style={"overflowX": "auto"}, children=[table]),
        ]))

    # ── Color legend ──────────────────────────────────────────────────────────
    legend = html.Div(style={
        "display": "flex", "gap": "20px", "flexWrap": "wrap",
        "padding": "14px 20px",
        "background": "rgba(0,0,0,0.2)", "border": "1px solid #1E1B4B",
        "borderRadius": "8px", "marginBottom": "16px",
    }, children=[
        html.Span("Color key:", style={"color": "#475569", "fontSize": "11px", "fontWeight": "600"}),
        html.Span("■ Green = strong (≥20% rev growth / ≥75% GM / ≥120 NRR / <10x EV)", style={"color": "#4ADE80", "fontSize": "11px"}),
        html.Span("■ Amber = moderate", style={"color": "#FCD34D", "fontSize": "11px"}),
        html.Span("■ Red = watch", style={"color": "#F87171", "fontSize": "11px"}),
        html.Span("◆ M&A = active acquirer or rumored target", style={"color": "#FBBF24", "fontSize": "11px"}),
        html.Span("NRR = Net Revenue Retention (SaaS only)", style={"color": "#64748B", "fontSize": "11px"}),
    ])

    footnote = html.Div(style={
        "marginTop": "16px", "padding": "12px 16px",
        "background": "rgba(0,0,0,0.2)", "border": "1px solid #1E1B4B",
        "borderRadius": "8px",
    }, children=[
        html.Span("ⓘ  Data sourced from Visible Alpha consensus, company filings, and Wall Street sell-side estimates (Feb 2026). "
                  "EV/NTM Revenue multiples are approximate and change daily. NRR shown for SaaS companies only. "
                  "Not financial advice — conduct your own due diligence.",
                  style={"color": "#334155", "fontSize": "10px", "lineHeight": "1.5"}),
    ])

    return html.Div([header, legend] + blocks + [footnote])

# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║     AGENTIC ECONOMY — TRUST & VERIFICATION LAYER DASHBOARD   ║
╠══════════════════════════════════════════════════════════════╣
║  Fetching initial market data...                             ║
║  Dashboard will open at: http://127.0.0.1:8051               ║
║                                                              ║
║  Trust Layer Tiers:                                          ║
║  T1 – AI Governance & Policy        (IBM, NOW, CRM, SAP)     ║
║  T2 – AI Observability & Monitoring (DDOG, DT, SNOW, PLTR)   ║
║  T3 – Agent Identity & IAM          (OKTA, SAIL, CYBR, CRWD) ║
║  T4 – AI Security & Red-Teaming     (PANW, CRWD, CSCO, NET)  ║
║  T5 – Cloud & Agent Orchestration   (MSFT, AMZN, GOOG, NOW)  ║
║  T6 – Enterprise Trust Incumbents   (CRM, IBM, SNOW, DDOG)   ║
║  T7 – Biometric & Human Verif.      (YOU, MITK, IDEX)        ║
║  T8 – Vertical Agent Trust          (TRI, RELX, META, ORCL)  ║
║                                                              ║
║  Benchmarks: S&P 500 (SPY), NASDAQ 100 (QQQ), Sox Semi (SOXX)║
║  Auto-refreshes every 5 minutes                              ║
║  Claude AI analysis requires ANTHROPIC_API_KEY               ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(debug=False, port=8051, host="127.0.0.1")
