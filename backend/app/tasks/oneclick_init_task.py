"""
一次性初始化所有任務
用於快速執行所有重要的數據獲取和分析任務
注意：此任務會直接調用函數，而不是通過 Celery 發送子任務，
因為 Celery 不允許在任務內部同步等待另一個任務的結果。
"""
from celery import shared_task
from celery.utils.log import get_task_logger

from app.tasks.stock_fundamental_tasks import _fetch_stock_fundamentals_impl
from app.tasks.weekly_tasks import (
    _fetch_weekly_bars_impl,
    _run_weekly_rule_engine_impl
)
from app.tasks.minute_data_tasks import _daily_minute_validation_impl

logger = get_task_logger(__name__)


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
                        "0700.HK", "9988.HK", 
                        "3690.HK", "1024.HK", "9618.HK", "9888.HK", "1810.HK", "2518.HK", "2018.HK", "0268.HK",
                        "0981.HK", "1347.HK", "6809.HK",  "3750.HK",   "2382.HK",  "0889.HK",
                        "0005.HK", "0939.HK", "1398.HK", "2388.HK", "2628.HK", "1299.HK", "3968.HK", "2318.HK", "2601.HK", "6030.HK",
                        "0023.HK", "0026.HK", "0027.HK", "0028.HK", "0999.HK", "1066.HK", "1336.HK", "1428.HK", "1551.HK",
                        "0016.HK", "0017.HK", "0083.HK", "0101.HK", "0688.HK", "1109.HK", "1209.HK", "1918.HK", "0035.HK", "0059.HK",
                        "0960.HK", "1030.HK",  "1383.HK", "1520.HK", "1777.HK", "2007.HK", "2103.HK",  "2899.HK",
                        "1928.HK", "6862.HK", "0699.HK", "0166.HK", "0241.HK", "0321.HK", "0332.HK", "0388.HK", "0519.HK", "0851.HK",
                        "0857.HK",  "1051.HK", "1117.HK", "1288.HK", "1313.HK", "0288.HK", "1211.HK", "9992.HK", "1371.HK",
                        "0151.HK", "1099.HK", "1177.HK", "1548.HK", "1801.HK", "2126.HK", "2162.HK", "2359.HK",  "3332.HK",
                        "6618.HK", "6998.HK", "0952.HK", "1251.HK", "1302.HK", "1530.HK", "1666.HK", "2269.HK", "0386.HK", "0883.HK",
                        "0702.HK", "6000.HK",  "1088.HK", "1898.HK",  "3475.HK", "0351.HK", "0389.HK", "0508.HK",
                        "0512.HK", "0520.HK", "0535.HK", "0358.HK", "0585.HK", "1133.HK", "1818.HK", "2799.HK", "0267.HK", "0177.HK",
                        "0941.HK", "2618.HK", "1616.HK", "1728.HK", "1888.HK", "2008.HK",  "2238.HK", "2338.HK", "2438.HK",
                        "2538.HK", "2638.HK", "2738.HK", "2938.HK",  "0003.HK",  "0010.HK", "3138.HK", "3238.HK",
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
        
        # 4. 執行規則引擎分析（直接調用函數）
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
