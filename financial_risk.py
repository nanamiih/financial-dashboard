import pandas as pd
import requests
import re
import json
from io import StringIO

# Display full DataFrame
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# Target financial metrics
TARGET_KEYWORDS = {
    "Debt": "Debt / Equity Ratio",
    "EPS (Diluted)": "Earnings per Share (Diluted)",
    "Diluted EPS": "Earnings per Share (Diluted)",
    "EPS Diluted": "Earnings per Share (Diluted)",
    "Earnings per Share (Diluted)": "Earnings per Share (Diluted)",
    "Current Ratio": "Current Ratio",
    "EBITDA": "EBITDA",
    "Inventory Turnover": "Inventory Turnover",
    "Free Cash Flow": "Free Cash Flow (Millions)",
    "Net Income": "Net Income (Millions)"
}

# -------------------------------------------------------
# Fetch data table from StockAnalysis for a specific company and financial page
# -------------------------------------------------------
def fetch_table(symbol, page):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    if ":" in symbol:
        exchange, code = symbol.split(":")
        base_url = f"https://stockanalysis.com/quote/{exchange.lower()}/{code.lower()}/financials"
    else:
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/financials"

    periods = ["quarterly", "semi-annual", "annual"]
    collected, first_period = [], None

    for period in periods:
        url = f"{base_url}/{page}/?p={period}" if page else f"{base_url}/?p={period}"
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            tables = pd.read_html(StringIO(r.text))
            if tables and not tables[0].empty:
                if first_period is None:
                    first_period = period
                collected.append(tables[0])
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}")

    if collected:
        return pd.concat(collected, ignore_index=True), first_period

    print(f"❌ All periods failed for {symbol}.")
    return None, None


# -------------------------------------------------------
# Combine multiple tables and extract target metrics
# -------------------------------------------------------
def get_company_data(symbol):
    pages = ["ratios", "cash-flow-statement", "balance-sheet", "income-statement", "statistics", ""]
    dfs, detected_period = [], None

    for page in pages:
        df, period = fetch_table(symbol, page)
        if df is not None:
            dfs.append(df)
            if detected_period is None:
                detected_period = period

    if not dfs:
        print(f"⚠️ No financial data found for {symbol}.")
        return None, None

    print(f"\n📅 Reporting frequency used: {detected_period.upper()}")
    combined = pd.concat(dfs, ignore_index=True)

    # Debug: check fetched items
    print("✅ Combined table fetched. Preview of first 50 items:")
    print(combined.iloc[:, 0].dropna().astype(str).head(50).to_list())

    selected_rows = pd.DataFrame()
    for keyword, label in TARGET_KEYWORDS.items():
        match = combined[combined.iloc[:, 0].astype(str).str.contains(keyword, case=False, na=False)]
        if not match.empty:
            match.iloc[0, 0] = label
            selected_rows = pd.concat([selected_rows, match.head(1)])
        else:
            print(f"⚠️ Not found on site: {label}")

    selected_rows = selected_rows.set_index(selected_rows.columns[0]).T
    print(f"✅ Extracted {len(selected_rows.columns)} metrics.")
    return selected_rows, detected_period


# -------------------------------------------------------
# Extra: fetch Altman Z-Score and Piotroski F-Score
# -------------------------------------------------------
import re
import requests
from io import StringIO
import pandas as pd

def get_scores(symbol):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/statistics/"
    try:
        r = requests.get(base_url, headers=headers, timeout=30)
        r.raise_for_status()
        html = r.text

        # 使用正則直接找出分數
        z_match = re.search(r"Altman Z-Score[^0-9]*([\d.]+)", html)
        f_match = re.search(r"Piotroski F-Score[^0-9]*([\d.]+)", html)

        z_score = float(z_match.group(1)) if z_match else None
        f_score = float(f_match.group(1)) if f_match else None
        return z_score, f_score

    except Exception as e:
        print(f"⚠️ Failed to fetch scores for {symbol}: {e}")
        return None, None





