"""
股票相關共用工具函式
提供 get_tracked_stock_codes() 供多個 task 模組共用
"""
import logging

logger = logging.getLogger(__name__)

# 種子清單：資料庫無資料時使用此預設清單進行 bootstrap
DEFAULT_SEED_CODES = [
    # 台股
    "2330.TW", "2317.TW", "2454.TW", "2308.TW",
    "1301.TW", "2881.TW", "2882.TW", "1101.TW",
    # 美股
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    # 港股
    "0700.HK", "9988.HK", "3690.HK", "9618.HK",
]


def get_tracked_stock_codes() -> list:
    """
    從 monitored_stocks 表讀取需要定期抓取基本面的股票清單。
    若資料庫無資料，則回傳預設種子清單以便系統 bootstrap。

    Returns:
        list: 股票代碼列表，例如 ['2330.TW', '0700.HK', 'AAPL']
    """
    try:
        from app.database import SessionLocal
        from app.models.monitored_stock import MonitoredStock

        db = SessionLocal()
        try:
            rows = (
                db.query(MonitoredStock.code)
                .filter(MonitoredStock.is_active == True)
                .all()
            )
            codes = [row.code for row in rows if row.code]

            if not codes:
                logger.info("monitored_stocks 表無資料，使用預設種子清單")
                codes = DEFAULT_SEED_CODES.copy()

            logger.info(f"取得 {len(codes)} 隻待監控股票")
            return codes

        finally:
            db.close()

    except Exception as e:
        logger.error(f"讀取股票清單失敗：{e}，使用預設清單")
        return DEFAULT_SEED_CODES.copy()