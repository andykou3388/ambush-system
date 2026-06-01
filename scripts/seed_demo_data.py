"""
模擬資料寫入腳本
在開發環境中寫入模擬資料，讓前端可以先看到效果

使用方式：
    podman compose exec backend python scripts/seed_demo_data.py
"""
import sys
import os
from datetime import date, timedelta
import random

# 加入專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, check_db_connection, init_db
from app.models.stock_bar import StockBar
from app.models.stock_fundamental import StockFundamental
from app.models.stock_signal_log import StockSignalLog


# 模擬股票資料
DEMO_STOCKS = [
    {"code": "2330.TW", "name": "台積電", "market": "TW", "close": 585.0, "ma10_w": 575.0, "ma30_w": 560.0, "volume_ma5_w": 35000, "zone": "UPTREND", "confidence": 0.85, "pe": 18.5, "eps": 31.62, "float_shares": 25930000000},
    {"code": "2317.TW", "name": "鴻海", "market": "TW", "close": 145.0, "ma10_w": 140.0, "ma30_w": 135.0, "volume_ma5_w": 28000, "zone": "UPTREND", "confidence": 0.78, "pe": 12.3, "eps": 11.79, "float_shares": 13860000000},
    {"code": "2454.TW", "name": "聯發科", "market": "TW", "close": 880.0, "ma10_w": 850.0, "ma30_w": 820.0, "volume_ma5_w": 15000, "zone": "POTENTIAL", "confidence": 0.62, "pe": 22.1, "eps": 39.82, "float_shares": 15980000000},
    {"code": "2303.TW", "name": "聯電", "market": "TW", "close": 52.0, "ma10_w": 50.5, "ma30_w": 48.0, "volume_ma5_w": 45000, "zone": "POTENTIAL", "confidence": 0.55, "pe": 10.8, "eps": 4.81, "float_shares": 12420000000},
    {"code": "2308.TW", "name": "台達電", "market": "TW", "close": 320.0, "ma10_w": 310.0, "ma30_w": 295.0, "volume_ma5_w": 12000, "zone": "UPTREND", "confidence": 0.72, "pe": 25.4, "eps": 12.60, "float_shares": 25980000000},
    {"code": "1301.TW", "name": "台塑", "market": "TW", "close": 72.0, "ma10_w": 74.0, "ma30_w": 76.0, "volume_ma5_w": 18000, "zone": "DOWNTREND", "confidence": 0.35, "pe": 15.2, "eps": 4.74, "float_shares": 6360000000},
    {"code": "2880.TW", "name": "國巨", "market": "TW", "close": 580.0, "ma10_w": 590.0, "ma30_w": 610.0, "volume_ma5_w": 8000, "zone": "DOWNTREND", "confidence": 0.30, "pe": 20.5, "eps": 28.29, "float_shares": 4200000000},
    {"code": "2327.TW", "name": "華碩", "market": "TW", "close": 380.0, "ma10_w": 375.0, "ma30_w": 365.0, "volume_ma5_w": 6000, "zone": "POTENTIAL", "confidence": 0.58, "pe": 14.8, "eps": 25.68, "float_shares": 7420000000},
    {"code": "2881.TW", "name": "富邦金", "market": "TW", "close": 68.0, "ma10_w": 66.5, "ma30_w": 65.0, "volume_ma5_w": 22000, "zone": "UPTREND", "confidence": 0.68, "pe": 11.2, "eps": 6.07, "float_shares": 10240000000},
    {"code": "2344.TW", "name": "華邦電", "market": "TW", "close": 26.0, "ma10_w": 25.0, "ma30_w": 24.5, "volume_ma5_w": 35000, "zone": "POTENTIAL", "confidence": 0.52, "pe": 35.0, "eps": 0.74, "float_shares": 3980000000},
    {"code": "AAPL", "name": "Apple", "market": "US", "close": 190.0, "ma10_w": 185.0, "ma30_w": 178.0, "volume_ma5_w": 55000, "zone": "UPTREND", "confidence": 0.82, "pe": 28.5, "eps": 6.67, "float_shares": 15500000000},
    {"code": "MSFT", "name": "Microsoft", "market": "US", "close": 420.0, "ma10_w": 410.0, "ma30_w": 395.0, "volume_ma5_w": 25000, "zone": "UPTREND", "confidence": 0.80, "pe": 35.2, "eps": 11.93, "float_shares": 7430000000},
    {"code": "GOOGL", "name": "Alphabet", "market": "US", "close": 175.0, "ma10_w": 170.0, "ma30_w": 165.0, "volume_ma5_w": 20000, "zone": "POTENTIAL", "confidence": 0.60, "pe": 25.8, "eps": 6.78, "float_shares": 12400000000},
    {"code": "AMZN", "name": "Amazon", "market": "US", "close": 185.0, "ma10_w": 180.0, "ma30_w": 175.0, "volume_ma5_w": 40000, "zone": "UPTREND", "confidence": 0.75, "pe": 42.0, "eps": 4.40, "float_shares": 10400000000},
    {"code": "TSLA", "name": "Tesla", "market": "US", "close": 240.0, "ma10_w": 250.0, "ma30_w": 260.0, "volume_ma5_w": 80000, "zone": "DOWNTREND", "confidence": 0.28, "pe": 55.0, "eps": 4.36, "float_shares": 3180000000},
]


def seed_data():
    """寫入模擬資料到資料庫"""
    # 檢查資料庫連線
    if not check_db_connection():
        print("❌ 無法連線到資料庫，請確認容器已啟動")
        return False

    # 初始化資料表（如果尚未建立）
    print("🗄️ 初始化資料表...")
    init_db()
    print("✅ 資料表初始化完成")

    db = SessionLocal()
    try:
        # 使用上週五的日期作為交易日
        trade_date = date(2026, 5, 29)

        print(f"📅 交易日: {trade_date}")
        print(f"📊 準備寫入 {len(DEMO_STOCKS)} 隻股票的模擬資料...")

        for s in DEMO_STOCKS:
            # 計算漲跌幅（隨機 +/- 2%）
            change_pct = round(random.uniform(-2.0, 3.0), 2)

            # 1. 寫入 stock_bar
            bar = StockBar(
                code=s["code"],
                name=s["name"],
                market=s["market"],
                trade_date=trade_date,
                freq="W",
                close=s["close"],
                change_pct=change_pct,
                ma10_w=s["ma10_w"],
                ma30_w=s["ma30_w"],
                volume_ma5_w=s["volume_ma5_w"],
            )
            db.add(bar)

            # 2. 寫入 stock_fundamental
            fund = StockFundamental(
                code=s["code"],
                market=s["market"],
                report_date=trade_date,
                pe_ttm=s["pe"],
                eps_ttm=s["eps"],
                float_shares=s["float_shares"],
            )
            db.add(fund)

            # 3. 寫入 stock_signal_log
            signal = StockSignalLog(
                code=s["code"],
                market=s["market"],
                trade_date=trade_date,
                zone=s["zone"],
                confidence=s["confidence"],
                trigger_rules={
                    "rule1_trend": {"long": s["zone"] == "UPTREND", "strong": s["confidence"] > 0.7},
                    "rule2_volume": s["volume_ma5_w"] > 10000,
                    "rule3_buy_point": s["zone"] in ("UPTREND", "POTENTIAL"),
                    "rule4_valuation": s["pe"] < 30,
                    "rule5_fundamental": s["eps"] > 0,
                },
                reason=f"{s['name']} - {s['zone']} 區域，信心度 {s['confidence']:.0%}",
                engine_version="V2.2",
            )
            db.add(signal)

            print(f"  ✅ {s['code']} {s['name']:6s} | {s['zone']:10s} | 信心: {s['confidence']:.0%} | 收盤: {s['close']}")

        db.commit()
        print(f"\n🎉 成功寫入 {len(DEMO_STOCKS)} 隻股票的模擬資料！")
        print("💡 現在可以啟動前端查看效果了")
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ 寫入失敗: {e}")
        return False
    finally:
        db.close()


def clear_demo_data():
    """清除模擬資料"""
    db = SessionLocal()
    try:
        trade_date = date(2026, 5, 29)
        
        deleted_bar = db.query(StockBar).filter(StockBar.trade_date == trade_date).delete()
        deleted_fund = db.query(StockFundamental).filter(StockFundamental.report_date == trade_date).delete()
        deleted_signal = db.query(StockSignalLog).filter(StockSignalLog.trade_date == trade_date).delete()
        
        db.commit()
        print(f"🗑️ 已清除 {deleted_bar} 筆行情、{deleted_fund} 筆基本面、{deleted_signal} 筆信號")
    except Exception as e:
        db.rollback()
        print(f"❌ 清除失敗: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="模擬資料管理")
    parser.add_argument("action", nargs="?", default="seed", choices=["seed", "clear"],
                        help="seed=寫入資料, clear=清除資料")
    
    args = parser.parse_args()
    
    if args.action == "seed":
        seed_data()
    elif args.action == "clear":
        confirm = input("確定要清除所有模擬資料？(y/N): ")
        if confirm.lower() == "y":
            clear_demo_data()
        else:
            print("已取消")