import pandas as pd
import requests
from io import StringIO

# 🧭 顯示完整 DataFrame
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# 🎯 目標財務指標
TARGET_KEYWORDS = {
    "Debt": "Debt / Equity Ratio",
    "Free Cash Flow": "Free Cash Flow (Millions)",
    "Net Income": "Net Income (Millions)",
    "EBITDA": "EBITDA",
    "Inventory Turnover": "Inventory Turnover"
}


# -------------------------------------------------------
# 抓取指定公司在不同報表頁面的資料
# -------------------------------------------------------
def fetch_table(symbol, page):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # 判斷網址結構（國際股票有前綴）
    if ":" in symbol:
        exchange, code = symbol.split(":")
        base_url = f"https://stockanalysis.com/quote/{exchange.lower()}/{code.lower()}/financials"
    else:
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/financials"

    # 嘗試不同的報表頻率
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
# 組合多個表格並抽取關鍵財務指標
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
        print(f"⚠️ 沒找到 {symbol} 的財報資料。")
        return None, None

    print(f"\n📅 使用的報表頻率：{detected_period.upper()}")
    combined = pd.concat(dfs, ignore_index=True)

    # 🎯 根據關鍵字模糊比對
    selected_rows = pd.DataFrame()
    for keyword, label in TARGET_KEYWORDS.items():
        match = combined[combined.iloc[:, 0].astype(str).str.contains(keyword, case=False, na=False)]
        if not match.empty:
            match.iloc[0, 0] = label
            selected_rows = pd.concat([selected_rows, match.head(1)])
        else:
            print(f"⚠️ Not found on site: {label}")

    # 🧾 轉橫向
    selected_rows = selected_rows.set_index(selected_rows.columns[0]).T

    # 🧮 若有 Inventory Turnover，自動新增 Days Working Capital = 365 / turnover
    if "Inventory Turnover" in selected_rows.columns:
        inv_turn = pd.to_numeric(selected_rows["Inventory Turnover"], errors="coerce")
        selected_rows["Days Working Capital (calculated)"] = (365 / inv_turn).round(2)

    print(f"✅ Extracted {len(selected_rows.columns)} metrics.")
    return selected_rows, detected_period


# -------------------------------------------------------
# 主執行區：可連續查詢多家公司
# -------------------------------------------------------
print("💡 輸入公司代號查財務指標，例如 AA, AAPL, TSLA")
print("輸入 q 或 exit 離開程式\n")

while True:
    company = input("請輸入公司代號：").strip().upper()
    if company in ["Q", "EXIT"]:
        print("👋 離開程式，再見！")
        break

    df, period = get_company_data(company)
    if df is not None:
        print(f"\n📊 {company} ({period.upper()}) Summary:\n")
        print(df.head(6))
        print("\n" + "-" * 80 + "\n")
