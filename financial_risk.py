import pandas as pd
import requests
import re
from io import StringIO
import datetime

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

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
# 抓取財報表格
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
    return None, None


# -------------------------------------------------------
# 主函數：整理成第一張圖那樣的格式
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

    # ---- 抓出目標指標 ----
    selected_rows = pd.DataFrame()
    for keyword, label in TARGET_KEYWORDS.items():
        match = combined[combined.iloc[:, 0].astype(str).str.contains(keyword, case=False, na=False)]
        if not match.empty:
            match.iloc[0, 0] = label
            selected_rows = pd.concat([selected_rows, match.head(1)])
        else:
            print(f"⚠️ Not found on site: {label}")

    df = selected_rows.set_index(selected_rows.columns[0]).T
    df.reset_index(inplace=True)

    # ---- 日期欄修正 ----
    if "level_1" in df.columns:
        df.rename(columns={"level_1": "Date"}, inplace=True)
    elif "index" in df.columns:
        df.rename(columns={"index": "Date"}, inplace=True)
    else:
        df.insert(0, "Date", [f"Q{i+1}" for i in range(len(df))])

    # ---- 抽出最後日期 ----
    def extract_last_date(text):
        if isinstance(text, str):
            match = re.findall(r"[A-Za-z]{3}\s\d{1,2},\s\d{4}", text)
            if match:
                return match[-1]
        return text

    df["Date"] = df["Date"].astype(str).apply(extract_last_date)

    # ---- 統一季度結束日期 ----
    def normalize_quarter(date_str):
        if isinstance(date_str, str):
            if "Mar" in date_str:
                year = re.findall(r"\d{4}", date_str)[-1]
                return f"Mar 31 {year}"
            elif "Jun" in date_str:
                year = re.findall(r"\d{4}", date_str)[-1]
                return f"Jun 30 {year}"
            elif "Sep" in date_str:
                year = re.findall(r"\d{4}", date_str)[-1]
                return f"Sep 30 {year}"
            elif "Dec" in date_str:
                year = re.findall(r"\d{4}", date_str)[-1]
                return f"Dec 31 {year}"
            elif re.search(r"\d{4}", date_str):
                return re.findall(r"\d{4}", date_str)[-1]
        return date_str

    df["Date"] = df["Date"].apply(normalize_quarter)

    # ---- 排序季度 ----
    df["ParsedDate"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["ParsedDate"])
    df = df.drop_duplicates(subset=["ParsedDate"])
    df = df.sort_values("ParsedDate", ascending=False).head(7)
    df.drop(columns=["ParsedDate"], inplace=True)

    # ---- 插入今天日期當 Current ----
    today = datetime.datetime.today().strftime("%b %d %Y")
    today_col = pd.DataFrame({"Date": [today]}, index=[0])
    df = pd.concat([today_col, df], ignore_index=True)

    # ---- 建立欄位名稱 (Current, Q2 2025, ...) ----
    periods = ["Current", "Q2 2025", "Q1 2025", "Q4 2024", "Q3 2024", "Q2 2024", "Q1 2024"]
    df["Period"] = periods[: len(df)]

    # ---- Pivot成橫向結構 ----
    df_final = df.set_index("Period").T
    df_final.reset_index(inplace=True)
    df_final.rename(columns={"index": "Metric"}, inplace=True)

    print(f"✅ Formatted table in wide layout with metrics vertical and periods horizontal.")
    return df_final, detected_period


# -------------------------------------------------------
# 抓取 Z-score / F-score
# -------------------------------------------------------
def get_scores(symbol):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    if ":" in symbol:
        exchange, code = symbol.split(":")
        base_url = f"https://stockanalysis.com/quote/{exchange.lower()}/{code.lower()}/statistics/"
    else:
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/statistics/"

    try:
        r = requests.get(base_url, headers=headers, timeout=30)
        r.raise_for_status()
        html = r.text

        z_match = re.search(r"Altman\s*Z-Score.*?(\d+\.\d+)", html, re.IGNORECASE | re.DOTALL)
        f_match = re.search(r"Piotroski\s*F-Score.*?(\d+)", html, re.IGNORECASE | re.DOTALL)

        z_score = float(z_match.group(1)) if z_match else None
        f_score = int(f_match.group(1)) if f_match else None

        print(f"🔍 [DEBUG] {symbol} → Z={z_score}, F={f_score}")
        return z_score, f_score

    except Exception as e:
        print(f"⚠️ Failed to fetch scores for {symbol}: {e}")
        return None, None


# -------------------------------------------------------
# 🚀 測試
# -------------------------------------------------------
if __name__ == "__main__":
    symbol = "OSL:NHY"
    df, freq = get_company_data(symbol)
    print(df)

    z, f = get_scores(symbol)
    print(f"\nZ-Score: {z}, F-Score: {f}")

    filename = f"financial_table_{symbol.replace(':','_')}.csv"
    df.to_csv(filename, index=False)
    print(f"📁 Saved: {filename}")
