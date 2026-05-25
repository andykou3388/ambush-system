"""
CORE-02 规则引擎 V1 验证脚本

用法：
    python scripts/check_rules.py              # 使用模拟数据
    python scripts/check_rules.py --real-data   # 使用 yfinance 真实数据
"""
import sys
import argparse

sys.path.append("backend")

import pandas as pd
import numpy as np
from engine.rule_engine import RuleEngine


def load_mock_data() -> pd.DataFrame:
    """加载10只模拟测试标的"""
    data = [
        # code, close, ma10, ma30, volume, pe, market_cap, debt_ratio, insider_buy, analyst_cover
        ["000001", 8.5, 8.2, 7.8, 50000, 9, 40e9, 0.5, 1, 0],
        ["000002", 12, 11.5, 13, 20000, 15, 60e9, 0.7, 0, 1],
        ["000003", 5.5, 5.7, 6.0, 15000, 8, 20e9, 0.45, 1, 0],
        ["000004", 18, 17, 16, 80000, 12, 80e9, 0.65, 0, 1],
        ["000005", 7.2, 7.1, 6.9, 45000, 7, 30e9, 0.4, 1, 0],
        ["000006", 9.5, 9.8, 10, 25000, 11, 55e9, 0.62, 0, 1],
        ["000007", 6.8, 6.7, 6.5, 60000, 8, 25e9, 0.42, 1, 0],
        ["000008", 22, 20, 19, 70000, 18, 120e9, 0.7, 0, 1],
        ["000009", 4.9, 4.8, 4.7, 38000, 6, 15e9, 0.38, 1, 0],
        ["000010", 14, 13.5, 14.2, 32000, 9, 48e9, 0.55, 1, 0],
    ]

    df = pd.DataFrame(
        data,
        columns=[
            "code",
            "close",
            "ma10",
            "ma30",
            "volume",
            "pe",
            "market_cap",
            "debt_ratio",
            "insider_buy",
            "analyst_cover",
        ],
    )
    return df


def load_real_data() -> pd.DataFrame:
    """使用 yfinance 加载真实数据"""
    try:
        import yfinance as yf
    except ImportError:
        print("[ERROR] 请先安装 yfinance: pip install yfinance")
        sys.exit(1)

    # 测试标的列表（台股/港股/美股示例）
    symbols = ["2330.TW", "2317.TW", "2454.TW", "AAPL", "MSFT"]
    all_data = []

    for symbol in symbols:
        print(f"  正在获取 {symbol} 数据...")
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")

        if hist.empty:
            print(f"  [WARN] {symbol} 无数据，跳过")
            continue

        # 计算技术指标
        hist["ma10"] = hist["Close"].rolling(10).mean()
        hist["ma30"] = hist["Close"].rolling(30).mean()
        hist["code"] = symbol
        hist["datetime"] = hist.index.strftime("%Y-%m-%d")

        # 取最新一行数据
        latest = hist.iloc[-1:].copy()
        latest = latest.rename(
            columns={
                "Close": "close",
                "Volume": "volume",
            }
        )

        # 模拟基本面数据（真实场景应从数据库获取）
        latest["pe"] = 12
        latest["market_cap"] = 100e9
        latest["debt_ratio"] = 0.5
        latest["insider_buy"] = 1
        latest["analyst_cover"] = 0

        all_data.append(
            latest[
                [
                    "code",
                    "datetime",
                    "close",
                    "ma10",
                    "ma30",
                    "volume",
                    "pe",
                    "market_cap",
                    "debt_ratio",
                    "insider_buy",
                    "analyst_cover",
                ]
            ]
        )

    if not all_data:
        print("[ERROR] 无法获取任何真实数据")
        sys.exit(1)

    return pd.concat(all_data, ignore_index=True)


def print_results(results: pd.DataFrame):
    """打印规则引擎执行结果"""
    print("\n" + "=" * 80)
    print("规则引擎 V1 执行结果")
    print("=" * 80)

    for _, row in results.iterrows():
        print(f"\n标的: {row['code']}")
        print(f"  收盘价: {row['close']:.2f}")
        print(f"  MA10: {row['ma10']:.2f}")
        print(f"  MA30: {row['ma30']:.2f}")
        print(f"  成交量: {row['volume']:.0f}")

        r1 = row["rule1_trend"]
        print(f"  第1层(趋势): long={r1['long']}, strong={r1['strong']}, "
              f"short={r1['short']}, weak={r1['weak']}")
        print(f"  第2层(成交量突破): {row['rule2_volume_break']}")
        print(f"  第3层(低风险买点): {row['rule3_buy_point']}")
        print(f"  第4层(价格估值): {row['rule4_valuation']}")
        print(f"  第5层(基本面): {row['rule5_fundamental']}")
        print(f"  >>> 最终分类: {row['label']}")

    print("\n" + "=" * 80)
    print("结果统计:")
    print(results["label"].value_counts().to_string())
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="规则引擎 V1 验证脚本")
    parser.add_argument(
        "--real-data",
        action="store_true",
        help="使用 yfinance 真实数据（默认使用模拟数据）",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("CORE-02 规则引擎 V1 验证")
    print("=" * 50)

    # 加载数据
    if args.real_data:
        print("\n[INFO] 使用 yfinance 真实数据...")
        df = load_real_data()
    else:
        print("\n[INFO] 使用模拟数据（10只测试标的）...")
        df = load_mock_data()

    print(f"\n[INFO] 共 {len(df)} 只标的")

    # 执行规则引擎
    print("\n[INFO] 初始化规则引擎...")
    engine = RuleEngine()

    print("[INFO] 执行5层规则...")
    results = engine.run(df)

    # 打印结果
    print_results(results)


if __name__ == "__main__":
    main()