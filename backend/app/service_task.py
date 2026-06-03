"""
週期性分析任務
實現週五收盤後的完整分析流程
V2.0 優化：使用 stock_fundamental_latest 緩存表進行基本面查詢
"""
from celery import shared_task
from celery.utils.log import get_task_logger
import logging
from .tasks_helper import get_stock_list, calculate_indicators, run_rule_engine, classify_stock, generate_report

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def run_weekly_analysis(self, market='TW'):
    """
    週五收盤後執行完整分析流程
    
    Args:
        market: 市場代碼 ('TW' 或 'US')
    """
    logger.info(f"🚀 開始執行 {market} 市場週分析")

    try:
        # 步驟 1：獲取股票列表
        logger.info("步驟 1/4：獲取股票列表")
        symbols = get_stock_list(market)
        logger.info(f"  獲取 {len(symbols)} 隻股票")

        # 步驟 2：計算技術指標
        logger.info("步驟 2/4：計算技術指標")
        for symbol in symbols:
            calculate_indicators(symbol)

        # 步驟 3：執行規則引擎
        logger.info("步驟 3/4：執行規則引擎")
        for symbol in symbols:
            run_rule_engine(symbol)

        # 步驟 4：三區分類
        logger.info("步驟 4/4：執行三區分類")
        results = []
        for symbol in symbols:
            result = classify_stock(symbol)
            results.append(result)

        # 生成報告
        generate_report(results, market)

        logger.info(f"✅ {market} 市場週分析完成")
        return {'status': 'success', 'market': market, 'count': len(symbols)}

    except Exception as exc:
        logger.error(f"❌ 分析失敗: {exc}")
        raise self.retry(exc=exc)
