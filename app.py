import streamlit as st
import pandas as pd
from io import BytesIO
from financial_risk import get_company_data, get_scores

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Financial Risk Dashboard", page_icon="📊", layout="wide")
st.title("Company Financial Risk Dashboard (No API)")
st.caption("Data source: StockAnalysis.com (Real-time scraping)")

# -------------------------------
# User Input
# -------------------------------
symbol = st.text_input("Enter company ticker (e.g., AA, RIO, OSL:NHY)").strip().upper()

# -------------------------------
# Main Logic
# -------------------------------
if symbol:
    with st.spinner("Fetching data..."):
        df, period = get_company_data(symbol)
        z, f = get_scores(symbol)

    if df is not None and not df.empty:
        st.success(f"✅ {symbol} financial data retrieved")
        st.dataframe(df, use_container_width=True)

        cols = list(df.columns)

        # Helper: get latest value
        def get_latest_value(column):
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if len(series) == 0:
                return None
            return series.iloc[0]

        # Display Key Metrics
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

        # Display Scores
        if z or f:
            st.subheader("Company Risk Scores")
            score_cols = st.columns(2)
            if z:
                z = float(z)
                color = "🔴" if z < 1.8 else "🟠" if z < 3 else "🟢"
                score_cols[0].metric(f"{color} Altman Z-Score", f"{z:.2f}")
            if f:
                score_cols[1].metric("📘 Piotroski F-Score", f"{f}")
            st.caption("Z < 1.8 → high bankruptcy risk; 1.8–3 = moderate; >3 = safe.")

        # =====================================================
        # ✅ EXPORT ONE EXCEL FILE (Financials + Scores)
        # =====================================================
        # Reset index and rename first column as Date
        df_reset = df.reset_index()
        if df_reset.columns[0] != "Date":
            df_reset.rename(columns={df_reset.columns[0]: "Date"}, inplace=True)

        # One-row scores table
        score_df = pd.DataFrame({
            "Ticker": [symbol],
            "Altman Z-Score": [z if z else None],
            "Piotroski F-Score": [f if f else None],
            "Exported At": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")]
        })

        # Export to single Excel buffer
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_reset.to_excel(writer, sheet_name=f"{symbol}_financials", index=False)
            score_df.to_excel(writer, sheet_name="Scores", index=False)
        excel_buffer.seek(0)

        # Streamlit download button
        st.download_button(
            label="📊 Download Excel (Financials + Scores)",
            data=excel_buffer,
            file_name=f"{symbol}_financials.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("✅ Excel file ready — load it directly into Power BI!")

    else:
        st.error("❌ No financial data found. Please check the ticker symbol.")
else:
    st.info("Please enter a company ticker to start.")
