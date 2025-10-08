import pandas as pd
import requests
from io import StringIO

# Display full DataFrame
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# Target financial metrics
TARGET_KEYWORDS = {
    "Debt": "Debt / Equity Ratio",
    "Free Cash Flow": "Free Cash Flow (Millions)",
    "Net Income": "Net Income (Millions)",
    "EBITDA": "EBITDA",
    "Inventory Turnover": "Inventory Turnover"
}

# -------------------------------------------------------
# Fetch data table from StockAnalysis for a specific company and financial page
# -------------------------------------------------------
def fetch_table(symbol, page):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Determine URL structure (some international stocks have prefixes)
    if ":" in symbol:
        exchange, code = symbol.split(":")
        base_url = f"https://stockanalysis.com/quote/{exchange.lower()}/{code.lower()}/financials"
    else:
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/financials"

    # Try different reporting periods
    periods = ["quarterly", "semi-annual", "annual"]

    for period in periods:
        url = f"{base_url}/{page}/?p={period}" if page else f"{base_url}/?p={period}"
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            tables = pd.read_html(StringIO(r.text))
            if tables and not tables[0].empty:
                print(f"✅ Got table from {url}")
                return tables[0], period
            else:
                print(f"⚠️ No data found on {url}, trying next period...")
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}")

    print(f"❌ All periods failed for {symbol}.")
    return None, None


# -------------------------------------------------------
# Combine multiple tables and extract target financial metrics
# -------------------------------------------------------
def get_company_data(symbol):
    pages = ["ratios", "cash-flow-statement", "balance-sheet", ""]
    dfs = []
    detected_period = None

    for page in pages:
        df, period = fetch_table(symbol, page)
        if df is not None:
            dfs.append(df)
            if detected_period is None:
                detected_period = period

    if not dfs:
        print(f"⚠️ No financial data found for {symbol}.")
        return None, None

    print(f"\n Reporting frequency used: {detected_period.upper()}")
    combined = pd.concat(dfs, ignore_index=True)

    #  Fuzzy match target keywords
    selected_rows = pd.DataFrame()
    for keyword, label in TARGET_KEYWORDS.items():
        match = combined[combined.iloc[:, 0].astype(str).str.contains(keyword, case=False, na=False)]
        if not match.empty:
            match.iloc[0, 0] = label
            selected_rows = pd.concat([selected_rows, match.head(1)])
        else:
            print(f"⚠️ Not found on site: {label}")

    # Transpose the table
    selected_rows = selected_rows.set_index(selected_rows.columns[0]).T

    # If Inventory Turnover exists, calculate Days Working Capital = 365 / turnover
    if "Inventory Turnover" in selected_rows.columns:
        inv_turn = pd.to_numeric(selected_rows["Inventory Turnover"], errors="coerce")
        selected_rows["Days Working Capital (calculated)"] = (365 / inv_turn).round(2)

    print(f"✅ Extracted {len(selected_rows.columns)} metrics.")
    return selected_rows, detected_period


# -------------------------------------------------------
# CLI mode (disabled when running on Streamlit)
# -------------------------------------------------------
# print("💡 Enter a company ticker to get financial metrics, e.g., AA, AAPL, TSLA")
# print("Type q or exit to quit.\n")

# while True:
#     company = input("Enter company ticker: ").strip().upper()
#     if company in ["Q", "EXIT"]:
#         print("👋 Exiting program. Goodbye!")
#         break
#
#     df, period = get_company_data(company)
#     if df is not None:
#         print(f"\n📊 {company} ({period.upper()}) Summary:\n")
#         print(df.head(5))
#         print("\n" + "-" * 80 + "\n")

