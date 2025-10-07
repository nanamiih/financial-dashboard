import streamlit as st
import pandas as pd
from financial_risk import get_company_data  # 從你的爬蟲程式匯入函數

st.set_page_config(page_title="Financial Risk Dashboard", page_icon="📊", layout="wide")
st.title("📊 Company Financial Risk Dashboard (No API)")
st.caption("資料來源：StockAnalysis.com（即時爬取）")

# 使用者輸入公司代號
symbol = st.text_input("輸入公司代號（例如：AA, AAPL, TSLA, RIO）").strip().upper()

if symbol:
    with st.spinner("抓取資料中..."):
        df, period = get_company_data(symbol)

    if df is not None and not df.empty:
        st.success(f"✅ {symbol} 財報資料 ({period.upper()})")
        st.dataframe(df, use_container_width=True)

        # 簡單展示幾個指標
        if "Debt / Equity Ratio" in df.columns:
            st.metric("Debt / Equity Ratio", round(df.iloc[-1]['Debt / Equity Ratio'], 2))
        if "Inventory Turnover" in df.columns:
            st.metric("Inventory Turnover", round(df.iloc[-1]['Inventory Turnover'], 2))
        if "Free Cash Flow (Millions)" in df.columns:
            st.metric("Free Cash Flow (M)", f"${df.iloc[-1]['Free Cash Flow (Millions)']:.0f}")
    else:
        st.error("❌ 找不到公司資料，請確認代號是否正確。")
else:
    st.info("請輸入公司代號開始查詢。")
