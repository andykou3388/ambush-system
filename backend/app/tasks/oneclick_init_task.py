"""
一次性初始化所有任務
用於快速執行所有重要的數據獲取和分析任務
注意：此任務會直接調用函數，而不是通過 Celery 發送子任務，
因為 Celery 不允許在任務內部同步等待另一個任務的結果。
"""
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import talib
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
                hist = ticker.history(period="2y", interval="1wk")

                if hist.empty:
                    logger.warning(f"{symbol} 無週線數據")
                    failed_symbols.append(symbol)
                    continue

                # 使用 TA-Lib 計算 MA10、MA30 和 Volume MA5
                close_array = hist["Close"].values.astype(float)
                volume_array = hist["Volume"].values.astype(float)
                ma10_all = talib.MA(close_array, timeperiod=10) if len(close_array) >= 10 else None
                ma30_all = talib.MA(close_array, timeperiod=30) if len(close_array) >= 30 else None
                vol_ma5_all = talib.MA(volume_array, timeperiod=5) if len(volume_array) >= 5 else None

                # 計算 change_pct（漲跌幅），第一筆為 None
                prev_close = None

                bars_saved = 0
                for i, (trade_date, row) in enumerate(hist.iterrows()):
                    # 安全取得 volume，處理 NaN 和各種類型
                    raw_vol = row.get("Volume", 0)
                    try:
                        if pd.isna(raw_vol):
                            volume = 0
                        else:
                            volume = int(float(raw_vol))
                    except (ValueError, TypeError):
                        volume = 0

                    # 計算成交金額 amount = close * volume
                    current_close = float(row["Close"])
                    amount = int(round(current_close * volume)) if volume > 0 else 0

                    # 安全取得 MA 值（TA-Lib 前 N-1 筆為 NaN）
                    ma10_val = None
                    ma30_val = None
                    if ma10_all is not None and i < len(ma10_all) and not np.isnan(ma10_all[i]):
                        ma10_val = round(float(ma10_all[i]), 4)
                    if ma30_all is not None and i < len(ma30_all) and not np.isnan(ma30_all[i]):
                        ma30_val = round(float(ma30_all[i]), 4)

                    # 安全取得 Volume MA5 值
                    vol_ma5_val = None
                    if vol_ma5_all is not None and i < len(vol_ma5_all) and not np.isnan(vol_ma5_all[i]):
                        vol_ma5_val = round(float(vol_ma5_all[i]), 4)

                    # 計算 change_pct（漲跌幅 %）
                    change_pct = None
                    if prev_close is not None and prev_close != 0:
                        change_pct = round((current_close - prev_close) / prev_close * 100, 2)
                    prev_close = current_close

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
                        "amount": amount,
                        "change_pct": change_pct,
                        "ma10_w": ma10_val,
                        "ma30_w": ma30_val,
                        "volume_ma5_w": vol_ma5_val,
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
                            "amount": bar_data["amount"],
                            "change_pct": bar_data["change_pct"],
                            "ma10_w": bar_data["ma10_w"],
                            "ma30_w": bar_data["ma30_w"],
                            "volume_ma5_w": bar_data["volume_ma5_w"],
                            "created_at": bar_data["created_at"],
                        },
                    )
                    db.execute(stmt)
                    bars_saved += 1

                success_count += 1
                # 取得最新一筆的 MA 值用於返回結果
                latest_ma10 = None
                latest_ma30 = None
                if ma10_all is not None and not np.isnan(ma10_all[-1]):
                    latest_ma10 = round(float(ma10_all[-1]), 2)
                if ma30_all is not None and not np.isnan(ma30_all[-1]):
                    latest_ma30 = round(float(ma30_all[-1]), 2)
                print(f"成功獲取 {symbol} 的 {bars_saved} 筆週線數據 (MA10={latest_ma10}, MA30={latest_ma30})")
                logger.info(f"成功獲取 {symbol} 的 {bars_saved} 筆週線數據 (MA10={latest_ma10}, MA30={latest_ma30})")

            except Exception as e:
                print(f"獲取 {symbol} 週線數據失敗: {e}")
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
        # 精選港股列表（包含更多有價值的股票）
        stock_codes = [
                        "0700.HK", "9988.HK", "3690.HK", "1024.HK", "9618.HK", "9888.HK", "1810.HK", "2518.HK", "2018.HK", "0268.HK",
                        "0981.HK", "1347.HK", "6809.HK", "shturl.", "3750.HK", "shturl.", "shturl.", "2382.HK", "shturl.", "0889.HK",
                        "0005.HK", "0939.HK", "1398.HK", "2388.HK", "2628.HK", "1299.HK", "3968.HK", "2318.HK", "2601.HK", "6030.HK",
                        "shturl.", "0023.HK", "0026.HK", "0027.HK", "0028.HK", "0999.HK", "1066.HK", "1336.HK", "1428.HK", "1551.HK",
                        "0016.HK", "0017.HK", "0083.HK", "0101.HK", "0688.HK", "1109.HK", "1209.HK", "1918.HK", "0035.HK", "0059.HK",
                        "0960.HK", "1030.HK", "shturl.", "1383.HK", "1520.HK", "1777.HK", "2007.HK", "2103.HK", "shturl.", "2899.HK",
                        "1928.HK", "6862.HK", "0699.HK", "0166.HK", "0241.HK", "0321.HK", "0332.HK", "0388.HK", "0519.HK", "0851.HK",
                        "0857.HK", "shturl.", "1051.HK", "1117.HK", "1288.HK", "1313.HK", "0288.HK", "1211.HK", "9992.HK", "1371.HK",
                        "0151.HK", "1099.HK", "1177.HK", "1548.HK", "1801.HK", "2126.HK", "2162.HK", "2359.HK", "shturl.", "3332.HK",
                        "6618.HK", "6998.HK", "0952.HK", "1251.HK", "1302.HK", "1530.HK", "1666.HK", "2269.HK", "0386.HK", "0883.HK",
                        "0702.HK", "6000.HK", "shturl.", "1088.HK", "1898.HK", "shturl.", "3475.HK", "0351.HK", "0389.HK", "0508.HK",
                        "0512.HK", "0520.HK", "0535.HK", "0358.HK", "0585.HK", "1133.HK", "1818.HK", "2799.HK", "0267.HK", "0177.HK",
                        "0941.HK", "2618.HK", "1616.HK", "1728.HK", "1888.HK", "2008.HK", "shturl.", "2238.HK", "2338.HK", "2438.HK",
                        "2538.HK", "2638.HK", "2738.HK", "2938.HK", "shturl.", "0003.HK", "shturl.", "0010.HK", "3138.HK", "3238.HK",
                        "3338.HK", "3438.HK", "3538.HK", "3638.HK", "3738.HK", "3838.HK", "4038.HK", "4138.HK", "0001.HK"
                    ]
                
        # 2. 執行股票基本面數據獲取（直接調用函數）
        logger.info("正在獲取股票基本面數據...")
        result1 = _fetch_stock_fundamentals_impl(stock_codes)
        logger.info(f"✅ 股票基本面數據獲取完成: {result1}")
        
        # 3. 從 YFinance 獲取週線 K 線數據並寫入 StockBar 表（新增步驟）
        logger.info("正在獲取週線 K 線數據...")
        result_weekly = _fetch_weekly_bars_impl(stock_codes)
        logger.info(f"✅ 週線 K 線數據獲取完成: {result_weekly}")
        
        # # 4. 執行週線技術指標計算（直接調用函數）
        # logger.info("正在計算週線技術指標...")
        # result2 = _calculate_weekly_indicators_impl("HK")
        # logger.info(f"✅ 週線技術指標計算完成: {result2}")
        
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
