"""
一次性初始化所有任務
用於快速執行所有重要的數據獲取和分析任務
注意：此任務會直接調用函數，而不是通過 Celery 發送子任務，
因為 Celery 不允許在任務內部同步等待另一個任務的結果。
"""
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models.stock_bar import StockBar
from app.tasks.stock_fundamental_tasks import _fetch_stock_fundamentals_impl
from app.tasks.weekly_tasks import _calculate_weekly_indicators_impl, _run_weekly_rule_engine_impl
from app.tasks.minute_data_tasks import _daily_minute_validation_impl

logger = get_task_logger(__name__)


def _fetch_weekly_bars_impl(stock_codes: list):
    """
    從 YFinance 批量獲取週線 K 線數據並寫入 StockBar 表（非 Celery 任務版本）
    供 oneclick_init_data 直接調用

    Args:
        stock_codes: 股票代碼列表，例如 ['0001.HK', '0700.HK']
    """
    logger.info(f"開始獲取 {len(stock_codes)} 隻股票的週線 K 線數據")
    db = SessionLocal()
    try:
        success_count = 0
        failed_symbols = []

        for symbol in stock_codes:
            try:
                time.sleep(0.5)  # 避免請求過於頻繁

                # 判斷市場
                if "." in symbol:
                    suffix = symbol.split(".")[-1]
                    if suffix == "TW":
                        market = "TW"
                    elif suffix == "HK":
                        market = "HK"
                    else:
                        market = suffix
                else:
                    market = "US"

                # 下載近 1 年的週線數據
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y", interval="1wk")

                if hist.empty:
                    logger.warning(f"{symbol} 無週線數據")
                    failed_symbols.append(symbol)
                    continue

                bars_saved = 0
                for trade_date, row in hist.iterrows():
                    # 安全取得 volume，處理 NaN 和各種類型
                    raw_vol = row.get("Volume", 0)
                    try:
                        if pd.isna(raw_vol):
                            volume = 0
                        else:
                            volume = int(float(raw_vol))
                    except (ValueError, TypeError):
                        volume = 0

                    # 使用 UTC 時間避免時區問題
                    now_utc = datetime.now(timezone.utc)

                    bar_data = {
                        "code": symbol,
                        "market": market,
                        "trade_date": trade_date.date(),
                        "freq": "W",
                        "open": round(float(row["Open"]), 4),
                        "high": round(float(row["High"]), 4),
                        "low": round(float(row["Low"]), 4),
                        "close": round(float(row["Close"]), 4),
                        "volume": volume,
                        "created_at": now_utc,
                    }

                    stmt = insert(StockBar).values(**bar_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["code", "trade_date"],
                        set_={
                            "open": bar_data["open"],
                            "high": bar_data["high"],
                            "low": bar_data["low"],
                            "close": bar_data["close"],
                            "volume": bar_data["volume"],
                            "created_at": bar_data["created_at"],
                        },
                    )
                    db.execute(stmt)
                    bars_saved += 1

                success_count += 1
                logger.info(f"成功獲取 {symbol} 的 {bars_saved} 筆週線數據")

            except Exception as e:
                logger.error(f"獲取 {symbol} 週線數據失敗: {e}", exc_info=True)
                failed_symbols.append(symbol)
                continue

        db.commit()
        logger.info(f"週線數據獲取完成，成功 {success_count}/{len(stock_codes)} 隻股票")
        return {
            "status": "success",
            "total": len(stock_codes),
            "success": success_count,
            "failed": len(failed_symbols),
            "failed_symbols": failed_symbols,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"批量獲取週線數據失敗: {e}", exc_info=True)
        raise
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def oneclick_init_data(self):
    """
    一次性初始化所有 Celery 任務
    直接調用函數執行所有重要的數據獲取和分析任務
    """
    try:
        logger.info("🚀 開始一次性初始化所有任務")
        
        # 1. 獲取股票代碼列表（這裡使用硬編碼的示例，實際應用中可能需要從資料庫獲取）
        # TOP 500 港股 乾淨版（無 shturl、無錯、可直接用於 oneclick_init_data）
        stock_codes = [
            # 1 - 100
            "0001.HK",
            # "0003.HK", "0005.HK", "0006.HK", "0012.HK",
            # "0016.HK", "0017.HK", "0019.HK", "0027.HK", "0066.HK",
            # "0083.HK", "0101.HK", "0151.HK", "0241.HK", "0268.HK",
            # "0288.HK", "0291.HK", "0322.HK", "0358.HK", "0386.HK",
            # "0388.HK", "0494.HK", "0596.HK", "0669.HK", "0688.HK",
            # "0700.HK", "0728.HK", "0762.HK", "0788.HK", "0823.HK",
            # "0836.HK", "0857.HK", "0883.HK", "0939.HK", "0941.HK",
            # "0960.HK", "0966.HK", "0981.HK", "0983.HK", "0992.HK",
            # "0998.HK", "1038.HK", "1044.HK", "1088.HK", "1093.HK",
            # "1100.HK", "1109.HK", "1128.HK", "1137.HK", "1157.HK",

            # # 101 - 200
            # "1177.HK", "1186.HK", "1211.HK", "1288.HK", "1299.HK",
            # "1336.HK", "1339.HK", "1359.HK", "1398.HK", "1458.HK",
            # "1516.HK", "1528.HK", "1595.HK", "1658.HK", "1688.HK",
            # "1772.HK", "1776.HK", "1787.HK", "1797.HK", "1800.HK",
            # "1810.HK", "1833.HK", "1876.HK", "1898.HK", "1919.HK",
            # "1928.HK", "1929.HK", "1952.HK", "1988.HK", "2007.HK",
            # "2015.HK", "2018.HK", "2020.HK", "2066.HK", "2196.HK",
            # "2238.HK", "2282.HK", "2313.HK", "2318.HK", "2319.HK",
            # "2328.HK", "2333.HK", "2382.HK", "2386.HK", "2399.HK",
            # "2400.HK", "2518.HK", "2588.HK", "2600.HK", "2601.HK",

            # # 201 - 300
            # "2611.HK", "2628.HK", "2666.HK", "2678.HK", "2688.HK",
            # "2696.HK", "2700.HK", "2727.HK", "2800.HK", "2822.HK",
            # "2823.HK", "2828.HK", "2866.HK", "2876.HK", "2877.HK",
            # "2883.HK", "2899.HK", "2901.HK", "2910.HK", "2914.HK",
            # "2938.HK", "3333.HK", "3458.HK", "3500.HK", "3606.HK",
            # "3608.HK", "3618.HK", "3690.HK", "3692.HK", "3698.HK",
            # "3759.HK", "3799.HK", "3833.HK", "3866.HK", "3888.HK",
            # "3898.HK", "3908.HK", "3933.HK", "3948.HK", "3958.HK",
            # "3968.HK", "3983.HK", "3988.HK", "3993.HK", "6000.HK",
            # "6011.HK", "4359.HK", "4608.HK", "4689.HK", "4708.HK",

            # # 301 - 400
            # "4888.HK", "5200.HK", "5858.HK", "6018.HK", "6078.HK",
            # "6098.HK", "6186.HK", "6188.HK", "6200.HK", "6399.HK",
            # "6500.HK", "6600.HK", "6618.HK", "6686.HK", "6690.HK",
            # "6699.HK", "6789.HK", "6806.HK", "6811.HK", "6826.HK",
            # "6837.HK", "6855.HK", "6862.HK", "6869.HK", "6881.HK",
            # "6882.HK", "6885.HK", "6888.HK", "6899.HK", "6900.HK",
            # "6908.HK", "6918.HK", "6928.HK", "6933.HK", "6958.HK",
            # "6966.HK", "6976.HK", "6978.HK", "6988.HK", "6998.HK",
            # "6999.HK", "7000.HK", "7200.HK", "7800.HK", "7888.HK",
            # "7999.HK", "8033.HK", "8083.HK", "8176.HK", "8233.HK",

            # # 401 - 500
            # "8300.HK", "8366.HK", "8411.HK", "8422.HK", "8477.HK",
            # "8500.HK", "8566.HK", "8622.HK", "8668.HK", "8788.HK",
            # "8888.HK", "9009.HK", "9147.HK", "9399.HK", "9618.HK",
            # "9626.HK", "9633.HK", "9666.HK", "9688.HK", "9698.HK",
            # "9707.HK", "9818.HK", "9866.HK", "9888.HK", "9898.HK",
            # "9900.HK", "9918.HK", "9988.HK"
        ]
                
        # 2. 執行股票基本面數據獲取（直接調用函數）
        logger.info("正在獲取股票基本面數據...")
        result1 = _fetch_stock_fundamentals_impl(stock_codes)
        logger.info(f"✅ 股票基本面數據獲取完成: {result1}")
        
        # 3. 從 YFinance 獲取週線 K 線數據並寫入 StockBar 表（新增步驟）
        logger.info("正在獲取週線 K 線數據...")
        result_weekly = _fetch_weekly_bars_impl(stock_codes)
        logger.info(f"✅ 週線 K 線數據獲取完成: {result_weekly}")
        
        # 4. 執行週線技術指標計算（直接調用函數）
        logger.info("正在計算週線技術指標...")
        result2 = _calculate_weekly_indicators_impl("HK")
        logger.info(f"✅ 週線技術指標計算完成: {result2}")
        
        # 5. 執行規則引擎分析（直接調用函數）
        logger.info("正在執行規則引擎分析...")
        result3 = _run_weekly_rule_engine_impl("HK")
        logger.info(f"✅ 規則引擎分析完成: {result3}")
        
        # 6. 執行每日分鐘線數據校驗（直接調用函數）
        logger.info("正在執行每日分鐘線數據校驗...")
        result4 = _daily_minute_validation_impl()
        logger.info(f"✅ 每日分鐘線數據校驗完成: {result4}")
        
        logger.info("🎉 所有任務初始化完成")
        return {
            "status": "success",
            "message": "所有任務初始化完成",
            "tasks": ["fundamentals", "weekly_bars", "indicators", "rule_engine", "minute_validation"]
        }
        
    except Exception as exc:
        logger.error(f"❌ 一次性初始化任務失敗: {exc}")
        raise self.retry(exc=exc)
