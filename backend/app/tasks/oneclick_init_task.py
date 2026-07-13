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
        
        # 1. 從 monitored_stocks 表讀取股票代碼列表（無資料則用預設種子清單）
        from app.utils.stock_utils import get_tracked_stock_codes
        stock_codes = get_tracked_stock_codes()
        logger.info(f"取得 {len(stock_codes)} 隻股票代碼")
                
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
