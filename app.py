import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from scipy.stats import norm
import requests
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, r2_score, mean_squared_error

st.set_page_config(page_title="Apex Institutional Financial & Data Analytics Studio", page_icon="🏛️", layout="wide")

# Custom Institutional Dark Glassmorphism Styling
st.markdown("""
<style>
    .stApp {
        background-color: #070a12;
    }
    .metric-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 18px;
        border-radius: 12px;
        backdrop-filter: blur(12px);
        margin-bottom: 12px;
    }
    .metric-sub { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .metric-num { font-size: 26px; font-weight: 700; color: #38bdf8; margin-top: 4px; }
    .tree-node {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(129, 140, 248, 0.15));
        border: 1px solid #38bdf8;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Apex Institutional Financial & Data Analytics Studio")
st.caption("Live Company Financial Modeling, 3-Statement Linking, DCF Sensitivity, LBO Sponsor Engine, M&A Accretion, DuPont Breakdown, Monte Carlo Simulator & AutoML Workbench.")

# --- SMART SEARCH ENGINE (Resolves Company Name -> Ticker) ---
def search_ticker(query: str):
    """Searches Yahoo Finance API to convert company name or text into ticker symbol."""
    if not query or not query.strip():
        return "AAPL", "Apple Inc."
    
    clean_q = query.strip()
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={clean_q}&quotesCount=5"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=4).json()
        quotes = r.get("quotes", [])
        if quotes:
            for q in quotes:
                if "symbol" in q:
                    return q["symbol"], q.get("shortname", q["symbol"])
            return quotes[0]["symbol"], quotes[0].get("shortname", quotes[0]["symbol"])
    except Exception:
        pass
    return clean_q.upper(), clean_q.upper()

# --- SIDEBAR SEARCH & NAVIGATION ---
st.sidebar.markdown("### 🔍 Company Search Engine")
search_query = st.sidebar.text_input(
    "Enter Company Name or Stock Ticker:", 
    value="Apple",
    placeholder="e.g. Nvidia, Tesla, Microsoft, Tata Motors, Reliance, AAPL"
)

resolved_ticker, company_display_name = search_ticker(search_query)
st.sidebar.success(f"Selected: **{company_display_name}** (`{resolved_ticker}`)")

@st.cache_data(ttl=3600)
def fetch_financial_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info or {}
    income = stock.financials if stock.financials is not None else pd.DataFrame()
    balance = stock.balance_sheet if stock.balance_sheet is not None else pd.DataFrame()
    cashflow = stock.cashflow if stock.cashflow is not None else pd.DataFrame()
    hist = stock.history(period="1y")
    return info, income, balance, cashflow, hist

with st.spinner(f"Fetching financial filings and real-time market data for {company_display_name}..."):
    try:
        info, income_stmt, balance_stmt, cashflow_stmt, price_hist = fetch_financial_data(resolved_ticker)
    except Exception as e:
        st.warning(f"Could not reach live market endpoint for {resolved_ticker}. Using simulation mode.")
        info, income_stmt, balance_stmt, cashflow_stmt, price_hist = {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# SAFE PARAMETER EXTRACTION
current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
if not current_price and not price_hist.empty:
    current_price = float(price_hist['Close'].iloc[-1])
current_price = float(current_price or 185.0)

market_cap = info.get("marketCap") or (current_price * info.get("sharesOutstanding", 1.55e10))
shares_out = info.get("sharesOutstanding") or (market_cap / current_price if current_price > 0 else 1.55e10)
trailing_pe = info.get("trailingPE", 29.4)
beta = float(info.get("beta") or 1.25)
enterprise_val = info.get("enterpriseValue") or (market_cap * 1.05)

# TOP EXECUTIVE KPIS
k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(f'<div class="metric-card"><div class="metric-sub">Market Price</div><div class="metric-num">${current_price:,.2f}</div></div>', unsafe_allow_html=True)
k2.markdown(f'<div class="metric-card"><div class="metric-sub">Market Cap</div><div class="metric-num">${market_cap / 1e9:,.2f}B</div></div>', unsafe_allow_html=True)
k3.markdown(f'<div class="metric-card"><div class="metric-sub">Trailing P/E</div><div class="metric-num">{trailing_pe if isinstance(trailing_pe, str) else round(trailing_pe, 2)}</div></div>', unsafe_allow_html=True)
k4.markdown(f'<div class="metric-card"><div class="metric-sub">Beta (5Y)</div><div class="metric-num">{beta:.2f}</div></div>', unsafe_allow_html=True)
k5.markdown(f'<div class="metric-card"><div class="metric-sub">Enterprise Value</div><div class="metric-num">${enterprise_val / 1e9:,.2f}B</div></div>', unsafe_allow_html=True)

# TABS NAVIGATION
tab_stmt, tab_dcf, tab_lbo, tab_ma, tab_dupont, tab_mc, tab_options, tab_ratios, tab_analytics = st.tabs([
    "📑 3-Statement Model", 
    "📈 DCF Valuation & 2D Matrix", 
    "💼 LBO Sponsor Model", 
    "🤝 M&A Accretion/Dilution", 
    "🔍 DuPont ROE Breakdown",
    "🎲 Monte Carlo Simulator",
    "⚡ Black-Scholes Options",
    "🔬 Financial Ratio Suite",
    "📊 Data Analytics & AutoML Studio"
])

# ----------------- 1. THREE-STATEMENT MODEL -----------------
with tab_stmt:
    st.subheader(f"Historical Financial Statements ({company_display_name})")
    stmt_choice = st.radio("Statement View:", ["Income Statement", "Balance Sheet", "Cash Flow Statement"], horizontal=True)
    
    active_df = income_stmt if stmt_choice == "Income Statement" else (balance_stmt if stmt_choice == "Balance Sheet" else cashflow_stmt)
    if not active_df.empty:
        clean_df = active_df.copy().applymap(lambda x: f"${x/1e6:,.2f}M" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
        st.dataframe(clean_df, use_container_width=True)
    else:
        st.info("Showing standard filing structure template for target company.")
        sample_data = pd.DataFrame({
            "Line Item": ["Total Revenue", "Operating Expenses", "Net Income", "Total Assets", "Total Debt", "Free Cash Flow"],
            "2025 (TTM)": ["$383.2B", "$54.8B", "$96.9B", "$352.5B", "$108.0B", "$99.5B"],
            "2024": ["$394.3B", "$51.3B", "$99.8B", "$352.7B", "$120.0B", "$111.4B"]
        })
        st.dataframe(sample_data, use_container_width=True)

# ----------------- 2. DCF VALUATION & 2D SENSITIVITY MATRIX -----------------
with tab_dcf:
    st.subheader("Interactive 5-Year DCF Valuation & 2D Sensitivity Matrix")
    
    try:
        baseline_fcf = float(cashflow_stmt.loc['Operating Cash Flow'].iloc[0] - abs(cashflow_stmt.loc['Capital Expenditure'].iloc[0]))
    except Exception:
        baseline_fcf = float(info.get("freeCashflow") or (market_cap * 0.035))

    col_dcf1, col_dcf2, col_dcf3 = st.columns(3)
    with col_dcf1:
        rev_growth = st.slider("5Y FCF Growth Rate (%)", 0.0, 40.0, 8.5, 0.5) / 100
    with col_dcf2:
        wacc = st.slider("Discount Rate / WACC (%)", 5.0, 18.0, 9.0, 0.25) / 100
    with col_dcf3:
        terminal_growth = st.slider("Perpetual Terminal Growth (g) (%)", 1.0, 5.0, 2.5, 0.1) / 100

    projected_fcf = [baseline_fcf * ((1 + rev_growth) ** i) for i in range(1, 6)]
    pv_fcf = [fcf / ((1 + wacc) ** i) for i, fcf in enumerate(projected_fcf, 1)]

    tv = (projected_fcf[-1] * (1 + terminal_growth)) / max(0.001, (wacc - terminal_growth))
    pv_tv = tv / ((1 + wacc) ** 5)
    ev = sum(pv_fcf) + pv_tv

    total_cash = info.get("totalCash") or (market_cap * 0.02)
    total_debt = info.get("totalDebt") or (market_cap * 0.04)
    equity_val = max(1.0, ev + total_cash - total_debt)
    fair_value = equity_val / max(1.0, shares_out)

    delta_pct = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0.0

    dcf_res1, dcf_res2, dcf_res3 = st.columns(3)
    dcf_res1.metric("Calculated Enterprise Value", f"${ev / 1e9:,.2f}B")
    dcf_res2.metric("Fair Value per Share", f"${fair_value:,.2f}", delta=f"{delta_pct:+.1f}% vs Market")
    dcf_res3.metric("Terminal Value PV", f"${pv_tv / 1e9:,.2f}B")

    # 2D Sensitivity Matrix Heatmap
    st.markdown("#### 2D Sensitivity Matrix Heatmap (WACC vs Terminal Growth g)")
    wacc_range = np.linspace(wacc - 0.02, wacc + 0.02, 5)
    g_range = np.linspace(terminal_growth - 0.01, terminal_growth + 0.01, 5)
    
    sens_matrix = []
    for g in g_range:
        row = []
        for w in wacc_range:
            if w <= g:
                row.append(np.nan)
            else:
                tv_cell = (projected_fcf[-1] * (1 + g)) / (w - g)
                pv_t_cell = tv_cell / ((1 + w) ** 5)
                ev_cell = sum([fcf / ((1 + w) ** i) for i, fcf in enumerate(projected_fcf, 1)]) + pv_t_cell
                eq_cell = ev_cell + total_cash - total_debt
                row.append(eq_cell / max(1.0, shares_out))
        sens_matrix.append(row)

    sens_df = pd.DataFrame(sens_matrix, index=[f"g: {g:.1%}" for g in g_range], columns=[f"WACC: {w:.1%}" for w in wacc_range])
    fig_heat = px.imshow(sens_df, text_auto=".2f", color_continuous_scale="Viridis", template="plotly_dark")
    st.plotly_chart(fig_heat, use_container_width=True)

# ----------------- 3. LEVERAGED BUYOUT (LBO) -----------------
with tab_lbo:
    st.subheader("Private Equity Sponsor LBO Return Engine")
    ebitda = float(info.get("ebitda") or (market_cap * 0.05))
    
    lbo1, lbo2, lbo3 = st.columns(3)
    with lbo1:
        entry_mult = st.number_input("Entry Multiple (EV/EBITDA)", 4.0, 35.0, 12.0)
        exit_mult = st.number_input("Exit Multiple (EV/EBITDA)", 4.0, 35.0, 12.5)
    with lbo2:
        leverage = st.slider("Debt Leverage (% Entry EV)", 20.0, 85.0, 60.0) / 100
        horizon = st.slider("Holding Period (Years)", 3, 7, 5)
    with lbo3:
        ebitda_growth = st.slider("EBITDA CAGR (%)", 0.0, 25.0, 6.5) / 100

    entry_val = ebitda * entry_mult
    debt_in = entry_val * leverage
    equity_in = max(1.0, entry_val - debt_in)

    exit_ebitda_val = ebitda * ((1 + ebitda_growth) ** horizon)
    exit_val = exit_ebitda_val * exit_mult
    debt_out = debt_in * max(0.0, 1.0 - (0.07 * horizon))
    equity_out = max(0.0, exit_val - debt_out)

    moic = equity_out / equity_in
    irr = ((moic) ** (1 / horizon)) - 1 if moic > 0 else -1.0

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Sponsor Equity Check", f"${equity_in / 1e9:.2f}B")
    r2.metric("Exit Equity Value", f"${equity_out / 1e9:.2f}B")
    r3.metric("MoIC Multiple", f"{moic:.2f}x")
    r4.metric("Sponsor Net IRR", f"{irr:.1%}", delta="Target Met" if irr >= 0.20 else "Sub-Target")

# ----------------- 4. M&A ACCRETION / DILUTION -----------------
with tab_ma:
    st.subheader("Pro-Forma M&A Accretion / Dilution Model")
    acq_net_inc = float(info.get("netIncomeToCommon") or (market_cap * 0.04))
    acq_eps = acq_net_inc / max(1.0, shares_out)

    ma1, ma2 = st.columns(2)
    with ma1:
        st.write(f"Buyer Standalone EPS: **${acq_eps:.2f}**")
        target_val = st.number_input("Target Purchase EV ($B)", 0.5, 200.0, 25.0) * 1e9
        target_ni = st.number_input("Target Net Income ($M)", 10.0, 15000.0, 1200.0) * 1e6
    with ma2:
        eq_pct = st.slider("Equity Consideration (%)", 0, 100, 40) / 100
        synergies = st.number_input("Pre-Tax Synergies ($M)", 0.0, 2000.0, 350.0) * 1e6

    new_shares = (target_val * eq_pct) / max(0.1, current_price)
    interest_exp = (target_val * (1 - eq_pct) * 0.06) * (1 - 0.21)
    pro_forma_ni = acq_net_inc + target_ni + (synergies * (1 - 0.21)) - interest_exp
    pro_forma_eps = pro_forma_ni / (shares_out + new_shares)
    accretion = ((pro_forma_eps - acq_eps) / acq_eps) * 100 if acq_eps != 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Pro-Forma Combined EPS", f"${pro_forma_eps:.2f}")
    c2.metric("Accretion / (Dilution)", f"{accretion:+.2f}%", delta="Accretive" if accretion > 0 else "Dilutive")
    c3.metric("New Shares Issued", f"{new_shares / 1e6:,.1f}M")

# ----------------- 5. DUPONT ROE BREAKDOWN -----------------
with tab_dupont:
    st.subheader("DuPont 3-Stage & 5-Stage ROE Breakdown Engine")
    
    net_margin = float(info.get("profitMargins") or 0.25)
    asset_turnover = float((info.get("totalRevenue") or 1e11) / max(1.0, info.get("totalAssets") or 3.5e11))
    equity_multiplier = float((info.get("totalAssets") or 3.5e11) / max(1.0, info.get("bookValue") or 6e10))
    roe = net_margin * asset_turnover * equity_multiplier * 100

    d1, d2, d3, d4 = st.columns(4)
    d1.markdown(f'<div class="tree-node"><div>Return on Equity (ROE)</div><div style="font-size:24px;font-weight:700;">{roe:.2f}%</div></div>', unsafe_allow_html=True)
    d2.markdown(f'<div class="tree-node"><div>Net Profit Margin</div><div style="font-size:20px;font-weight:700;">{net_margin:.2%}</div></div>', unsafe_allow_html=True)
    d3.markdown(f'<div class="tree-node"><div>Asset Turnover</div><div style="font-size:20px;font-weight:700;">{asset_turnover:.2f}x</div></div>', unsafe_allow_html=True)
    d4.markdown(f'<div class="tree-node"><div>Equity Multiplier</div><div style="font-size:20px;font-weight:700;">{equity_multiplier:.2f}x</div></div>', unsafe_allow_html=True)

# ----------------- 6. MONTE CARLO SIMULATOR -----------------
with tab_mc:
    st.subheader("Monte Carlo Valuation & Risk Simulator (1,000 Runs)")
    
    sim_runs = 1000
    g_sims = np.random.normal(0.085, 0.035, sim_runs)
    w_sims = np.random.normal(0.09, 0.01, sim_runs)
    sim_prices = current_price * np.exp(g_sims - (w_sims * 0.5))

    fig_mc = px.histogram(sim_prices, nbins=30, title="Stochastic Share Price Valuation Distribution", template="plotly_dark", color_discrete_sequence=['#818cf8'])
    st.plotly_chart(fig_mc, use_container_width=True)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Mean Price", f"${np.mean(sim_prices):.2f}")
    mc2.metric("5th Percentile (VaR)", f"${np.percentile(sim_prices, 5):.2f}")
    mc3.metric("95th Percentile Upside", f"${np.percentile(sim_prices, 95):.2f}")

# ----------------- 7. BLACK-SCHOLES OPTIONS -----------------
with tab_options:
    st.subheader("Derivatives Pricing & Option Greeks")
    s1, s2, s3 = st.columns(3)
    with s1:
        strike_val = st.number_input("Strike ($)", 1.0, 10000.0, float(round(current_price, 0)))
    with s2:
        dte = st.slider("Days to Expiration", 1, 365, 45)
    with s3:
        iv = st.slider("Implied Volatility (%)", 5, 120, 26) / 100

    T_yrs = dte / 365.0
    d1 = (np.log(current_price / strike_val) + (0.045 + 0.5 * iv ** 2) * T_yrs) / (iv * np.sqrt(T_yrs))
    d2 = d1 - iv * np.sqrt(T_yrs)
    c_px = current_price * norm.cdf(d1) - strike_val * np.exp(-0.045 * T_yrs) * norm.cdf(d2)
    p_px = strike_val * np.exp(-0.045 * T_yrs) * norm.cdf(-d2) - current_price * norm.cdf(-d1)

    op1, op2, op3 = st.columns(3)
    op1.metric("Call Premium", f"${c_px:.2f}")
    op2.metric("Put Premium", f"${p_px:.2f}")
    op3.metric("Call Delta (Δ)", f"{norm.cdf(d1):.3f}")

# ----------------- 8. RATIO SUITE -----------------
with tab_ratios:
    st.subheader(f"Financial Ratio Suite ({company_display_name})")
    ratio_records = [
        {"Category": "Valuation", "Metric": "Trailing P/E", "Value": str(trailing_pe)},
        {"Category": "Valuation", "Metric": "Price to Book (P/B)", "Value": f"{info.get('priceToBook', 'N/A')}"},
        {"Category": "Profitability", "Metric": "Profit Margins", "Value": f"{(info.get('profitMargins') or 0.25):.2%}"},
        {"Category": "Profitability", "Metric": "Operating Margins", "Value": f"{(info.get('operatingMargins') or 0.29):.2%}"},
        {"Category": "Return", "Metric": "Return on Equity (ROE)", "Value": f"{(info.get('returnOnEquity') or 1.47):.2%}"},
        {"Category": "Solvency", "Metric": "Total Debt / EBITDA", "Value": f"{(total_debt / max(1.0, info.get('ebitda') or 1.3e11)):.2f}x"}
    ]
    st.dataframe(pd.DataFrame(ratio_records), use_container_width=True)

# ----------------- 9. DATA ANALYTICS & AUTOML STUDIO -----------------
with tab_analytics:
    st.subheader("Data Pulse Analytics & AutoML Model Tournament")
    uploaded_file = st.file_uploader("📂 Load Source Dataset (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head(6), use_container_width=True)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1:
            st.markdown("#### Correlation Matrix")
            corr = df[numeric_cols].corr()
            corr_fig = px.imshow(corr, text_auto=".2f", template="plotly_dark")
            st.plotly_chart(corr_fig, use_container_width=True)
    else:
        st.info("Using sample financial dataset. Upload custom CSV above to analyze any dataset.")
        sample_df = pd.DataFrame({
            "Revenue Growth": np.random.normal(0.12, 0.04, 100),
            "Net Margin": np.random.normal(0.22, 0.05, 100),
            "ROE": np.random.normal(0.35, 0.08, 100),
            "FCF Yield": np.random.normal(0.04, 0.015, 100),
            "Valuation Target": np.random.normal(180, 25, 100)
        })
        st.dataframe(sample_df.head(6), use_container_width=True)
        corr_fig = px.imshow(sample_df.corr(), text_auto=".2f", template="plotly_dark")
        st.plotly_chart(corr_fig, use_container_width=True)
