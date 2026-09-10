# Apex Institutional Data Analytics & Financial Data Dashboard 🏛️📈

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6%2B-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)

An institutional-grade **Data Analytics & Financial Data Dashboard Web Application** that enables users to input any company name or stock ticker (e.g., *Apple*, *Nvidia*, *Tesla*, *Microsoft*, *Tata Motors*, *Reliance*, *AAPL*, *NVDA*, *TSLA*) to automatically retrieve real-time financial metrics, execute multi-stage financial models, perform stochastic risk simulations, and analyze custom dataset analytics.

---

## 🌟 Key Features & Financial Modeling Suite

1. **Smart Company Search Engine**:
   - Searches Yahoo Finance endpoints to dynamically resolve company names into stock ticker symbols.
   - Includes real-time quotes, Market Cap, Trailing & Forward P/E, Beta (5Y), Enterprise Value, and Free Cash Flow Yield.

2. **Multi-Model Financial Suite**:
   - 📑 **3-Statement Linking Model**: Historical Income Statement, Balance Sheet, and Cash Flow Statement.
   - 📈 **5-Year DCF Valuation & 2D Sensitivity Matrix**: Projections, WACC discount rate slider, perpetual terminal growth rate ($g$), Fair Value per share calculation, and interactive **2D Sensitivity Matrix Heatmap** (WACC vs Perpetual Terminal Growth Rate).
   - 💼 **Leveraged Buyout (LBO) Sponsor Returns Model**: Entry/Exit EV multiples, sponsor debt leverage slider, holding period, EBITDA CAGR, Sponsor Equity Check, MoIC multiple, Sponsor Net IRR %, and target hurdle status evaluation (&ge;20% IRR).
   - 🤝 **Pro-Forma M&A Accretion / Dilution Engine**: Standalone Buyer & Target metrics, cash/equity consideration split, pre-tax synergies, interest expenses, pro-forma net income, pro-forma EPS, and accretion/dilution %.
   - 🔍 **DuPont ROE Analysis Breakdown**: Decomposes Return on Equity into Net Margin × Asset Turnover × Financial Equity Multiplier.
   - 🎲 **Monte Carlo Valuation & Risk Simulator**: 1,000+ stochastic iterations using Gaussian normal distribution (Box-Muller transform), calculating Value at Risk (VaR 5th percentile) and 95th percentile upside.
   - ⚡ **Black-Scholes Options Pricing & Option Greeks**: European Call/Put premiums, Days to Expiration, Implied Volatility slider, and Delta, Gamma, Vega, Theta Greeks.
   - 🔬 **Institutional Financial Ratio Diagnostics**: Multi-category breakdown for Valuation, Profitability, Solvency, and Return metrics.

3. **Data Analytics & AutoML Studio**:
   - Upload custom CSV data or analyze company financial series.
   - Data Quality Diagnostics (Completeness %, IQR Outlier detection).
   - Interactive Pearson Correlation Heatmap.
   - Automated Feature Importance Ranking chart.

---

## 📁 Repository Structure

```
.
├── index.html                  # Standalone Web Application UI (HTML5 + Glassmorphism)
├── styles.css                  # Custom Design System (CSS3 HSL tokens & animations)
├── app.js                      # Financial Modeling Algorithms & Charting Engine
├── app.py                      # Master Streamlit Python Web Application
├── financial_studio.py         # Institutional Financial Modeling Engine (Python)
├── analytics_app.py            # Data Analytics & AutoML Workbench (Python)
├── WA_Fn-UseC_-Telco-Churn.csv # Sample Benchmark Dataset
└── README.md                   # Project Documentation
```

---

## 🚀 Getting Started

### Option 1: Standalone Browser Web App
Open `index.html` directly in any modern web browser, or run a local HTTP server:
```bash
python -m http.server 8000
```
Then navigate to: `http://localhost:8000/index.html`

### Option 2: Streamlit Master Python App
Install requirements and launch the Streamlit app:
```bash
pip install streamlit pandas numpy plotly yfinance scipy scikit-learn requests
streamlit run app.py
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
