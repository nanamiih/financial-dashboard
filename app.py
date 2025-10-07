import streamlit as st
import pandas as pd
from financial_risk import get_company_data

st.set_page_config(page_title="Financial Risk Dashboard", page_icon="📊", layout="wide")
st.title("📊 Company Financial Risk Dashboard (No API)")
st.caption("資料來源：StockAnalysis.com（即時爬取）")

symbol = st.text_input("輸入公司代號（例如：AA, AAPL, TSLA, RIO）").strip().upper()

if symbol:
    with st.spinner("抓取資料中..."):
        df, period = get_company_data(symbol)

    if df is not None and not df.empty:
        st.success(f"✅ {symbol} 財報資料 ({period.upper()})")

        # 顯示整張表格（保證不報錯）
        st.dataframe(df, use_container_width=True)

        # 如果資料方向正確，再安全取出指標
        cols = list(df.columns)
        if "Debt / Equity Ratio" in cols:
            val = pd.to_numeric(df["Debt / Equity Ratio"], errors="coerce").dropna().iloc[-1]
            st.metric("Debt / Equity Ratio", f"{val:.2f}")
        if "Inventory Turnover" in cols:
            val = pd.to_numeric(df["Inventory Turnover"], errors="coerce").dropna().iloc[-1]
            st.metric("Inventory Turnover", f"{val:.2f}")
        if "Free Cash Flow (Millions)" in cols:
            val = pd.to_numeric(df["Free Cash Flow (Millions)"], errors="coerce").dropna().iloc[-1]
            st.metric("Free Cash Flow (M)", f"${val:,.0f}")
    else:
        st.error("❌ 找不到公司資料，請確認代號是否正確。")
else:
    st.info("請輸入公司代號開始查詢。")
