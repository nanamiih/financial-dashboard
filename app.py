import streamlit as st
import pandas as pd
from financial_risk import get_company_data

st.set_page_config(page_title="Financial Risk Dashboard", page_icon="📊", layout="wide")
st.title("Company Financial Risk Dashboard")
st.caption("Data source: StockAnalysis.com (Real-time scraping)")

# User input
symbol = st.text_input("Enter company ticker (e.g., AA, AAPL, TSLA, RIO)").strip().upper()

if symbol:
    with st.spinner("Fetching data..."):
        df, period = get_company_data(symbol)

    if df is not None and not df.empty:
        st.success(f"✅ {symbol} financial data retrieved ({period.upper()})")

        # Show entire table
        st.dataframe(df, use_container_width=True)

        # Safely extract and display key metrics if available
        cols = list(df.columns)
        
        # Helper function: pick latest or 2nd latest valid value
        def get_latest_value(column):
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if len(series) == 0:
                return None
            elif len(series) == 1:
                return series.iloc[0]
            else:
                # take the first value (newest) instead of last
                return series.iloc[0]  # or use .iloc[1] if you want 2nd newest

        # Display metrics
        if "Debt / Equity Ratio" in cols:
            val = get_latest_value("Debt / Equity Ratio")
            if val is not None:
                st.metric("Debt / Equity Ratio", f"{val:.2f}")

        if "Inventory Turnover" in cols:
            val = get_latest_value("Inventory Turnover")
            if val is not None:
                st.metric("Inventory Turnover", f"{val:.2f}")

        if "Free Cash Flow (Millions)" in cols:
            val = get_latest_value("Free Cash Flow (Millions)")
            if val is not None:
                st.metric("Free Cash Flow (M)", f"${val:,.0f}")

    else:
        st.error("❌ No financial data found. Please check if the ticker symbol is correct.")
else:
    st.info("Please enter a company ticker to start.")


