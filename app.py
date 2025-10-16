import streamlit as st
import pandas as pd
from financial_risk import get_company_data, get_scores

st.set_page_config(page_title="Financial Risk Dashboard", page_icon="📊", layout="wide")
st.title("📊 Multi-Company Financial Risk Dashboard (No API)")
st.caption("Data source: StockAnalysis.com – Real-time scraping")

# -----------------------------
# User input (allow multiple tickers)
# -----------------------------
tickers_input = st.text_input(
    "Enter company tickers separated by commas (e.g., AA, RIO, NHYDY, OSL:NHY)"
).strip()

if tickers_input:
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
else:
    tickers = []

# -----------------------------
# Helper to get the latest value
# -----------------------------
def get_latest_value(df, column):
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) == 0:
        return None
    return series.iloc[0]

# -----------------------------
# Main loop for each company
# -----------------------------
for symbol in tickers:
    st.divider()
    st.subheader(f"🏢 {symbol}")

    with st.spinner(f"Fetching data for {symbol}..."):
        df, period = get_company_data(symbol)
        z, f = get_scores(symbol)

    if df is None or df.empty:
        st.error(f"❌ No data found for {symbol}")
        continue

    # --- Basic financial metrics ---
    st.success(f"✅ {symbol} financial data retrieved")
    st.dataframe(df, use_container_width=True)
    cols = list(df.columns)

    # Show key metrics
    metrics = []
    if "Debt / Equity Ratio" in cols:
        val = get_latest_value(df, "Debt / Equity Ratio")
        if val is not None:
            metrics.append(("Debt / Equity Ratio", f"{val:.2f}"))
    if "Current Ratio" in cols:
        val = get_latest_value(df, "Current Ratio")
        if val is not None:
            metrics.append(("Current Ratio", f"{val:.2f}"))
    if "Inventory Turnover" in cols:
        val = get_latest_value(df, "Inventory Turnover")
        if val is not None:
            metrics.append(("Inventory Turnover", f"{val:.2f}"))
    if "Free Cash Flow (Millions)" in cols:
        val = get_latest_value(df, "Free Cash Flow (Millions)")
        if val is not None:
            metrics.append(("Free Cash Flow (M)", f"${val:,.0f}"))
    if "Earnings per Share (Diluted)" in cols:
        val = get_latest_value(df, "Earnings per Share (Diluted)")
        if val is not None:
            metrics.append(("EPS (Diluted)", f"{val:.2f}"))

    # Display as columns
    if metrics:
        kcols = st.columns(len(metrics))
        for (label, value), col in zip(metrics, kcols):
            col.metric(label, value)

    # --- Company scores (Altman Z & Piotroski F) ---
    if z or f:
        st.subheader("📊 Company Scores")
        score_cols = st.columns(2)
        if z:
            z = float(z)
            color = "🔴" if z < 1.8 else "🟠" if z < 3 else "🟢"
            score_cols[0].metric(f"{color} Altman Z-Score", f"{z:.2f}")
        if f:
            score_cols[1].metric("📘 Piotroski F-Score", f"{f}")
        st.caption("Z < 1.8 → high bankruptcy risk ; 1.8–3 = moderate ; > 3 = safe.")
