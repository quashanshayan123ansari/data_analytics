import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from scipy.stats import norm
import requests

st.set_page_config(page_title="Apex Financial Modeling Suite", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background: #11141d;
        border: 1px solid #1e293b;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .metric-sub { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
    .metric-num { font-size: 24px; font-weight: 700; color: #38bdf8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Apex Institutional Modeling & Valuation Suite")
st.caption("Live 3-Statement Linking, Multi-Stage DCF, M&A Accretion/Dilution, LBO Sponsor Returns & Derivatives Engine.")

# --- SMART SEARCH ENGINE (Resolves Company Name -> Ticker) ---
def search_ticker(query: str):
    """Searches Yahoo Finance API to convert company name or text into ticker symbol."""
    if not query or not query.strip():
        return "AAPL", "Apple Inc."
    
    clean_q = query.strip()
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={clean_q}&quotesCount=5"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5).json()
        quotes = r.get("quotes", [])
        if quotes:
            # Pick first valid equity/ETF
            for q in quotes:
                if "symbol" in q:
                    return q["symbol"], q.get("shortname", q["symbol"])
            return quotes[0]["symbol"], quotes[0].get("shortname", quotes[0]["symbol"])
    except Exception:
        pass
    return clean_q.upper(), clean_q.upper()

# --- SIDEBAR SEARCH ---
search_query = st.sidebar.text_input(
    "Search Company Name or Ticker:", 
    value="Apple",
    placeholder="e.g. Nvidia, Tesla, Microsoft, Tata Motors, AAPL"
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
    hist = stock.history(period="1mo")
    return info, income, balance, cashflow, hist

with st.spinner(f"Aggregating regulatory filings and market quotes for {company_display_name}..."):
    try:
        info, income_stmt, balance_stmt, cashflow_stmt, price_hist = fetch_financial_data(resolved_ticker)
    except Exception as e:
        st.error(f"Could not load data for {resolved_ticker}: {e}")
        st.stop()

# --- SAFE PARAMETER EXTRACTION ---
current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
if not current_price and not price_hist.empty:
    current_price = float(price_hist['Close'].iloc[-1])
current_price = float(current_price or 100.0)

market_cap = info.get("marketCap") or (current_price * info.get("sharesOutstanding", 1e8))
shares_out = info.get("sharesOutstanding") or (market_cap / current_price if current_price > 0 else 1e8)
trailing_pe = info.get("trailingPE", "N/A")
beta = float(info.get("beta") or 1.0)
enterprise_val = info.get("enterpriseValue") or market_cap

# Top KPIs
k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(f'<div class="metric-card"><div class="metric-sub">Market Price</div><div class="metric-num">${current_price:,.2f}</div></div>', unsafe_allow_html=True)
k2.markdown(f'<div class="metric-card"><div class="metric-sub">Market Cap</div><div class="metric-num">${market_cap / 1e9:,.2f}B</div></div>', unsafe_allow_html=True)
k3.markdown(f'<div class="metric-card"><div class="metric-sub">Trailing P/E</div><div class="metric-num">{trailing_pe if isinstance(trailing_pe, str) else round(trailing_pe, 2)}</div></div>', unsafe_allow_html=True)
k4.markdown(f'<div class="metric-card"><div class="metric-sub">Beta (5Y)</div><div class="metric-num">{beta:.2f}</div></div>', unsafe_allow_html=True)
k5.markdown(f'<div class="metric-card"><div class="metric-sub">Enterprise Value</div><div class="metric-num">${enterprise_val / 1e9:,.2f}B</div></div>', unsafe_allow_html=True)

# Tabs
tab_stmt, tab_dcf, tab_lbo, tab_ma, tab_options, tab_ratios = st.tabs([
    "📑 3-Statement Model", 
    "📈 Discounted Cash Flow (DCF)", 
    "💼 Leveraged Buyout (LBO)", 
    "🤝 M&A Accretion/Dilution", 
    "🎲 Black-Scholes Options",
    "🔬 Financial Ratio Suite"
])

# ----------------- 1. THREE-STATEMENT MODEL -----------------
with tab_stmt:
    st.subheader(f"Historical Filings ({company_display_name})")
    stmt_choice = st.radio("Statement:", ["Income Statement", "Balance Sheet", "Cash Flow Statement"], horizontal=True)
    
    active_df = income_stmt if stmt_choice == "Income Statement" else (balance_stmt if stmt_choice == "Balance Sheet" else cashflow_stmt)
    if not active_df.empty:
        clean_df = active_df.copy().applymap(lambda x: f"${x/1e6:,.2f}M" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
        st.dataframe(clean_df, width='stretch')
    else:
        st.warning("Statement line items unavailable for this company.")

# ----------------- 2. DCF VALUATION & SENSITIVITY -----------------
with tab_dcf:
    st.subheader("Interactive 5-Year DCF Model")
    
    try:
        baseline_fcf = float(cashflow_stmt.loc['Operating Cash Flow'].iloc[0] - abs(cashflow_stmt.loc['Capital Expenditure'].iloc[0]))
    except Exception:
        baseline_fcf = float(info.get("freeCashflow") or (market_cap * 0.04))

    col_dcf1, col_dcf2, col_dcf3 = st.columns(3)
    with col_dcf1:
        rev_growth = st.slider("FCF Growth Rate (%)", 0.0, 40.0, 8.0, 0.5) / 100
    with col_dcf2:
        wacc = st.slider("Discount Rate / WACC (%)", 5.0, 18.0, 9.0, 0.25) / 100
    with col_dcf3:
        terminal_growth = st.slider("Perpetual Terminal Growth (g) (%)", 1.0, 5.0, 2.5, 0.1) / 100

    projected_fcf = [baseline_fcf * ((1 + rev_growth) ** i) for i in range(1, 6)]
    pv_fcf = [fcf / ((1 + wacc) ** i) for i, fcf in enumerate(projected_fcf, 1)]

    tv = (projected_fcf[-1] * (1 + terminal_growth)) / max(0.001, (wacc - terminal_growth))
    pv_tv = tv / ((1 + wacc) ** 5)
    ev = sum(pv_fcf) + pv_tv

    total_cash = info.get("totalCash") or 0
    total_debt = info.get("totalDebt") or 0
    equity_val = max(1.0, ev + total_cash - total_debt)
    fair_value = equity_val / max(1.0, shares_out)

    # Safe Delta Calculation (guards against zero division)
    delta_pct = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0.0

    dcf_res1, dcf_res2, dcf_res3 = st.columns(3)
    dcf_res1.metric("Calculated Enterprise Value", f"${ev / 1e9:,.2f}B")
    dcf_res2.metric("Fair Value per Share", f"${fair_value:,.2f}", delta=f"{delta_pct:+.1f}% vs Market")
    dcf_res3.metric("Terminal Value PV", f"${pv_tv / 1e9:,.2f}B")

    # Sensitivity Heatmap
    st.markdown("#### 2D Sensitivity Matrix (WACC vs Terminal Growth)")
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
    fig_heat = px.imshow(sens_df, text_auto=".2f", color_continuous_scale="RdYlGn", template="plotly_dark")
    st.plotly_chart(fig_heat, width='stretch')

# ----------------- 3. LEVERAGED BUYOUT (LBO) -----------------
with tab_lbo:
    st.subheader("Private Equity Sponsor LBO Returns")
    ebitda = float(info.get("ebitda") or (market_cap * 0.08))
    
    lbo1, lbo2, lbo3 = st.columns(3)
    with lbo1:
        entry_mult = st.number_input("Entry Multiple (EV/EBITDA)", 4.0, 35.0, 11.0)
        exit_mult = st.number_input("Exit Multiple (EV/EBITDA)", 4.0, 35.0, 12.0)
    with lbo2:
        leverage = st.slider("Debt Leverage (% Entry EV)", 20.0, 85.0, 60.0) / 100
        horizon = st.slider("Holding Period (Years)", 3, 7, 5)
    with lbo3:
        ebitda_growth = st.slider("EBITDA CAGR (%)", 0.0, 20.0, 6.0) / 100

    entry_val = ebitda * entry_mult
    debt_in = entry_val * leverage
    equity_in = max(1.0, entry_val - debt_in)

    exit_ebitda_val = ebitda * ((1 + ebitda_growth) ** horizon)
    exit_val = exit_ebitda_val * exit_mult
    debt_out = debt_in * max(0.0, 1.0 - (0.06 * horizon))
    equity_out = max(0.0, exit_val - debt_out)

    moic = equity_out / equity_in
    irr = ((moic) ** (1 / horizon)) - 1 if moic > 0 else -1.0

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Sponsor Equity Check", f"${equity_in / 1e9:.2f}B")
    r2.metric("Exit Equity Value", f"${equity_out / 1e9:.2f}B")
    r3.metric("MoIC Multiple", f"{moic:.2f}x")
    r4.metric("Sponsor IRR", f"{irr:.1%}", delta="Attractive" if irr >= 0.20 else "Sub-Target")

# ----------------- 4. M&A ACCRETION / DILUTION -----------------
with tab_ma:
    st.subheader("Pro-Forma M&A Accretion / Dilution Engine")
    acq_net_inc = float(info.get("netIncomeToCommon") or (market_cap * 0.05))
    acq_eps = acq_net_inc / max(1.0, shares_out)

    ma1, ma2 = st.columns(2)
    with ma1:
        st.write(f"Standalone EPS: **${acq_eps:.2f}**")
        target_val = st.number_input("Target Purchase EV ($B)", 0.5, 200.0, 8.0) * 1e9
        target_ni = st.number_input("Target Net Income ($M)", 10.0, 15000.0, 500.0) * 1e6
    with ma2:
        eq_pct = st.slider("Equity Consideration (%)", 0, 100, 30) / 100
        synergies = st.number_input("Pre-Tax Synergies ($M)", 0.0, 2000.0, 100.0) * 1e6

    new_shares = (target_val * eq_pct) / max(0.1, current_price)
    interest_exp = (target_val * (1 - eq_pct) * 0.055) * (1 - 0.21)
    pro_forma_ni = acq_net_inc + target_ni + (synergies * (1 - 0.21)) - interest_exp
    pro_forma_eps = pro_forma_ni / (shares_out + new_shares)
    accretion = ((pro_forma_eps - acq_eps) / acq_eps) * 100 if acq_eps != 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Combined EPS", f"${pro_forma_eps:.2f}")
    c2.metric("Accretion / (Dilution)", f"{accretion:+.2f}%", delta="Accretive" if accretion > 0 else "Dilutive")
    c3.metric("Shares Issued", f"{new_shares / 1e6:,.1f}M")

# ----------------- 5. BLACK-SCHOLES OPTIONS -----------------
with tab_options:
    st.subheader("Derivatives Pricing & Volatility Payoffs")
    s1, s2, s3 = st.columns(3)
    with s1:
        strike_val = st.number_input("Strike ($)", 1.0, 10000.0, float(round(current_price, 0)))
    with s2:
        dte = st.slider("Days to Expiration", 1, 365, 45)
    with s3:
        iv = st.slider("Implied Volatility (%)", 5, 120, 28) / 100

    T_yrs = dte / 365.0
    d1 = (np.log(current_price / strike_val) + (0.045 + 0.5 * iv ** 2) * T_yrs) / (iv * np.sqrt(T_yrs))
    d2 = d1 - iv * np.sqrt(T_yrs)
    c_px = current_price * norm.cdf(d1) - strike_val * np.exp(-0.045 * T_yrs) * norm.cdf(d2)
    p_px = strike_val * np.exp(-0.045 * T_yrs) * norm.cdf(-d2) - current_price * norm.cdf(-d1)

    op1, op2, op3 = st.columns(3)
    op1.metric("Call Premium", f"${c_px:.2f}")
    op2.metric("Put Premium", f"${p_px:.2f}")
    op3.metric("Call Delta (Δ)", f"{norm.cdf(d1):.3f}")

# ----------------- 6. RATIO SUITE -----------------
with tab_ratios:
    st.subheader(f"Financial Diagnostics & Key Ratios ({company_display_name})")
    ratio_records = [
        {"Metric": "Trailing P/E", "Value": str(trailing_pe)},
        {"Metric": "Price to Book (P/B)", "Value": f"{info.get('priceToBook', 'N/A')}"},
        {"Metric": "Profit Margins", "Value": f"{(info.get('profitMargins') or 0):.2%}"},
        {"Metric": "Operating Margins", "Value": f"{(info.get('operatingMargins') or 0):.2%}"},
        {"Metric": "Return on Equity (ROE)", "Value": f"{(info.get('returnOnEquity') or 0):.2%}"},
        {"Metric": "Total Debt / EBITDA", "Value": f"{(total_debt / max(1.0, info.get('ebitda') or 1e9)):.2f}x"}
    ]
    st.dataframe(pd.DataFrame(ratio_records), width='stretch')