# Agentic Economy — Trust & Verification Layer Dashboard

A comprehensive Dash web application for analyzing trust layer companies in the agentic economy, powered by real-time market data (yfinance) and AI-driven insights (Anthropic Claude API).

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Dash](https://img.shields.io/badge/Dash-2.14+-green) ![License](https://img.shields.io/badge/License-MIT-purple)

---

## 📋 Features

- **8 Trust Layer Tiers**: Comprehensive taxonomy of AI governance, security, identity, and observability companies
- **Real-time Market Data**: Live stock prices, performance metrics, and financial data via yfinance
- **Multiple Visualization Modes**:
  - Overview with benchmark comparison (SPY, QQQ, SOXX)
  - Layer-specific performance charts
  - Correlation heatmaps
  - Scatter plot analysis (Risk vs. Return)
  - Top movers dashboard
  - Fundamental financials table
  
- **AI-Powered Analysis**: Claude Sonnet generates deep insights on selected layers
- **Interactive Controls**:
  - Time period selection (1D, 5D, 1M, 3M, 6M, 1Y, YTD)
  - Layer selection for targeted analysis
  - Benchmark overlay options
  
- **Auto-Refresh**: Fetches fresh market data every 5 minutes

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Anthropic API key (free tier available at [console.anthropic.com](https://console.anthropic.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd agentic_trust_dashboard
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your Anthropic API key**
   ```bash
   export ANTHROPIC_API_KEY="sk-your-key-here"
   ```
   
   Or create a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY="sk-your-key-here"
   ```

5. **Run the dashboard**
   ```bash
   python agentic_trust_dashboard.py
   ```
   
   Dashboard opens at: **http://127.0.0.1:8051**

---

## 🌐 Deploy to Render

### What You Need
- **GitHub repository** (with your code pushed)
- **Render account** ([render.com](https://render.com))
- **Anthropic API key**

### Required Files
Your repo should include:
- `agentic_trust_dashboard.py` — Main app
- `requirements.txt` — Python dependencies ✓ Included
- `Procfile` — Deployment configuration ✓ Included

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add dashboard and deployment files"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repo
   - Select the repo and branch

3. **Configure the Service**
   - **Name**: `agentic-trust-dashboard` (or your choice)
   - **Root Directory**: `/` (or leave blank)
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn agentic_trust_dashboard:app --bind 0.0.0.0:$PORT`

4. **Add Environment Variable**
   - Under "Environment" → "Add Environment Variable"
   - **Key**: `ANTHROPIC_API_KEY`
   - **Value**: Paste your Anthropic API key (from [console.anthropic.com](https://console.anthropic.com/))

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Your app will be live at: `https://<your-service-name>.onrender.com`

### Deployment Details
- **Instance Type**: Use Free tier for testing; upgrade to Paid for production
- **Auto-Redeploy**: Enable auto-deploy on GitHub push
- **Health Checks**: Render automatically monitors uptime
- **Logs**: View real-time logs in the Render dashboard

---

## 📊 Trust Layer Taxonomy

### T1 – AI Governance & Policy
IBM, ServiceNow, Salesforce, SAP, Microsoft — regulatory compliance and AI lifecycle management.

### T2 – AI Observability & Monitoring
Datadog, Dynatrace, Snowflake, Palantir, MongoDB — production health, drift, and anomaly detection.

### T3 – Agent Identity & IAM
**HIGHEST-CONVICTION TIER** — Okta, SailPoint, CyberArk, CrowdStrike, Palo Alto, Microsoft, others — identity and access for AI agents and non-human identities.

### T4 – AI Security & Red-Teaming
Palo Alto Networks, CrowdStrike, Cisco, Check Point, Cloudflare, Fortinet — offensive/defensive AI security.

### T5 – Cloud & Agent Orchestration
Microsoft Azure, Amazon AWS, Alphabet GCP, ServiceNow, Salesforce — hyperscaler infrastructure and deployment platforms.

### T6 – Enterprise Trust Incumbents
Salesforce, IBM, Snowflake, Datadog — large incumbents with embedded AI trust modules.

### T7 – Biometric & Human Verification
Clear Secure, Mitek Systems — biometric liveness and deepfake defense.

### T8 – Vertical Agent Trust
Thomson Reuters, RELX, Meta, Oracle — industry-specific agentic workflows and trust frameworks.

---

## 🔧 Configuration

### Environment Variables
| Variable | Default | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | (none) | Yes, for AI analysis |
| `PORT` | 8051 | No |

### Customization
Edit the dashboard by modifying:
- **`TRUST_STACK`** (line 74) — Add/remove companies or layers
- **`STYLE`** (line 327) — Change colors and layout
- **`BENCH_COLORS`** (line 938) — Customize benchmark visualization

---

## 🐛 Troubleshooting

### AI Analysis Button Not Working
✓ **FIXED in v2** — Previous issue where button would disable after first click has been resolved.

**If still encountering issues:**
1. Check that `ANTHROPIC_API_KEY` is set correctly
2. Look for error messages in the browser console (F12)
3. Check Render logs: `Logs` tab in your Render dashboard
4. Verify your API key has sufficient credits at [console.anthropic.com](https://console.anthropic.com/usage)

### "Fetching market data..." Appears
- Yfinance may be rate-limited. Wait 30 seconds for retry.
- Check your internet connection.

### High memory usage or slow performance
- Reduce the number of stocks in `TRUST_STACK` for your use case
- Increase cache duration (modify refresh timer in `app.layout`)

---

## 📚 API Documentation

### Market Data (yfinance)
Fetches real-time and historical OHLCV data for all tickers in the trust layers.

### AI Analysis (Anthropic Claude Sonnet)
Generates contextual insights on portfolio performance, tier comparisons, and investment theses. Supports:
- Layer-specific analysis (single tier)
- Cross-layer analysis (ALL)
- Time-period contextualization (1D to 1Y)

---

## 💡 Usage Tips

1. **Deep Dive into a Layer**: Select a specific tier from "Layer Select" dropdown and click "AI Analysis" for expert commentary
2. **Watch Movers**: Switch to "Top Movers" tab to identify fastest-gaining/losing stocks daily
3. **Correlation Analysis**: Use the heatmap to find stocks that move together
4. **Benchmark Overlay**: Compare your portfolio vs. SPY, QQQ, SOXX simultaneously
5. **Export Data**: All charts support download as PNG via Plotly menu (camera icon)

---

## 📈 Data Sources

- **Stock Prices**: yfinance (powered by Yahoo Finance)
- **Fundamentals**: Company filings and Visible Alpha consensus estimates
- **AI Insights**: Anthropic Claude Sonnet API
- **Benchmarks**: SPY (S&P 500), QQQ (Nasdaq 100), SOXX (Semiconductor ETF), SMH (Semiconductor Mega Cap), CIBR (Cybersecurity ETF)

---

## 🤝 Contributing

Have ideas for new trust layers, companies, or visualizations? Open an issue or submit a pull request!

---

## 📄 License

MIT License — See LICENSE file for details.

---

## ⚖️ Disclaimer

**Not financial advice.** This dashboard is for educational and research purposes only. Past performance does not guarantee future results. Always conduct your own due diligence before making investment decisions. Consult a financial advisor.

---

## 📞 Support

- **Issues**: GitHub Issues
- **API Help**: [Anthropic Docs](https://docs.anthropic.com)
- **yfinance**: [GitHub](https://github.com/ranaroussi/yfinance)
- **Dash**: [Plotly Dash Docs](https://dash.plotly.com)

---

**Last Updated**: February 2026 | **Python 3.10+** | **Dash 2.14+**
