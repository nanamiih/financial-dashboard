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


def get_scores(symbol):
    """
    Fetch Altman Z-Score and Piotroski F-Score from StockAnalysis statistics page.
    This method parses the embedded JSON (window.__DATA__) instead of HTML tables.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = f"https://stockanalysis.com/stocks/{symbol.lower()}/statistics/"
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()

        # 🔍 在 HTML 裡找到內嵌 JSON 區塊
        match = re.search(r"window\.__DATA__\s*=\s*(\{.*?\});", r.text)
        if not match:
            print(f"⚠️ No JSON data found for {symbol}")
            return None, None

        # 載入 JSON
        data = json.loads(match.group(1))

        # 從 JSON 抓出統計數據
        stats = data.get("statistics", {})
        z = stats.get("AltmanZScore")
        f = stats.get("PiotroskiFScore")

        if z is None and f is None:
            print(f"⚠️ Scores not found in JSON for {symbol}")
        else:
            print(f"✅ {symbol} → Z={z}, F={f}")

        return z, f

    except Exception as e:
        print(f"⚠️ Failed to fetch scores for {symbol}: {e}")
        return None, None









