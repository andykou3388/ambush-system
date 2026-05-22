import yfinance as yf
import pandas as pd

def test_yfinance():
    """驗證 yfinance 可正常獲取數據"""
    print("🚀 測試 yfinance 數據源...")
    print("=" * 50)

    # 測試 1：獲取個股周線數據
    print("\n📊 測試 1：獲取 AAPL 周線數據")
    ticker = yf.Ticker("AAPL")
    df = ticker.history(period="6mo", interval="1wk")
    if df is not None and not df.empty:
        print(f"  ✅ 成功獲取 {len(df)} 筆周線數據")
        print(f"  最新收盤價: ${df['Close'].iloc[-1]:.2f}")
        print(f"  日期範圍: {df.index[0].date()} ~ {df.index[-1].date()}")
    else:
        print("  ❌ 獲取失敗")
        return False

    # 測試 2：獲取基本面資訊
    print("\n📋 測試 2：獲取 AAPL 基本面資訊")
    info = ticker.info
    print(f"  公司名稱: {info.get('longName', 'N/A')}")
    print(f"  市盈率 (PE): {info.get('trailingPE', 'N/A')}")
    print(f"  市值: ${info.get('marketCap', 0):,}")
    print(f"  52週高點: ${info.get('fiftyTwoWeekHigh', 'N/A')}")

    # 測試 3：批量獲取多隻股票
    print("\n📈 測試 3：批量獲取多隻股票")
    symbols = ["AAPL", "MSFT", "GOOGL"]
    for sym in symbols:
        t = yf.Ticker(sym)
        hist = t.history(period="1mo", interval="1wk")
        if not hist.empty:
            print(f"  ✅ {sym}: {len(hist)} 筆數據, 最新價 ${hist['Close'].iloc[-1]:.2f}")
        else:
            print(f"  ❌ {sym}: 獲取失敗")

    print("\n" + "=" * 50)
    print("✅ yfinance 驗證通過！")
    return True

if __name__ == "__main__":
    test_yfinance()