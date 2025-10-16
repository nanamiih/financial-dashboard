import streamlit as st
import pandas as pd
from financial_risk import get_company_data, get_scores

st.set_page_config(page_title="Financial Risk Dashboard", page_icon="📊", layout="wide")
st.title("📊 Company Financial Risk Dashboard (No API)")
st.caption("Data source: StockAnalysis.com (Real-time scraping)")

symbol = st.text_input("Enter company ticker (e.g., AA, RIO, OSL:NHY)").strip().upper()

if symbol:
    with st.spinner("Fetching data..."):
        df, period = get_company_data(symbol)
        z, f = get_scores(symbol)

    if df is not None and not df.empty:
        st.success(f"✅ {symbol} financial data retrieved")
        st.dataframe(df, use_container_width=True)

        cols = list(df.columns)

        # Helper function
        def get_latest_value(column):
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if len(series) == 0:
                return None
            return series.iloc[0]  # newest

        # Display key metrics
        if "Debt / Equity Ratio" in cols:
            val = get_latest_value("Debt / Equity Ratio")
            if val is not None:
                st.metric("Debt / Equity Ratio", f"{val:.2f}")

        if "Current Ratio" in cols:
            val = get_latest_value("Current Ratio")
            if val is not None:
                st.metric("Current Ratio", f"{val:.2f}")

        if "Inventory Turnover" in cols:
            val = get_latest_value("Inventory Turnover")
            if val is not None:
                st.metric("Inventory Turnover", f"{val:.2f}")

        if "Free Cash Flow (Millions)" in cols:
            val = get_latest_value("Free Cash Flow (Millions)")
            if val is not None:
                st.metric("Free Cash Flow (M)", f"${val:,.0f}")

        if "Earnings per Share (Diluted)" in cols:
            val = get_latest_value("Earnings per Share (Diluted)")
            if val is not None:
                st.metric("EPS (Diluted)", f"{val:.2f}")

        # Show Z-Score and F-Score
        if z or f:
            st.subheader("📊 Company Risk Scores")
            score_cols = st.columns(2)
            if z:
                z = float(z)
                color = "🔴" if z < 1.8 else "🟠" if z < 3 else "🟢"
                score_cols[0].metric(f"{color} Altman Z-Score", f"{z:.2f}")
            if f:
                score_cols[1].metric("📘 Piotroski F-Score", f"{f}")
            st.caption("Z < 1.8 → high bankruptcy risk; 1.8–3 = moderate; >3 = safe.")
    else:
        st.error("❌ No financial data found. Please check the ticker symbol.")
else:
    st.info("Please enter a company ticker to start.")
