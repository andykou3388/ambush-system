"""
通用股票基本面數據獲取任務
從 YFinance 獲取股票基本面數據並保存到 stock_fundamental 表
"""
from celery import shared_task
from yfinance import Ticker
from datetime import datetime
import time
import logging
from sqlalchemy.dialects.postgresql import insert
from app.database import SessionLocal
from app.models.stock_fundamental import StockFundamental

logger = logging.getLogger(__name__)


def save_to_database(data_list: list):
    """
    批量保存基本面數據到資料庫（使用 UPSERT 避免唯一約束衝突）
    
    Args:
        data_list: 基本面數據列表
    """
    db = SessionLocal()
    try:
        for data in data_list:
            stmt = insert(StockFundamental).values(**data)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_code_report",
                set_={
                    "pe_ttm": data["pe_ttm"],
                    "eps_ttm": data["eps_ttm"],
                    "float_shares": data["float_shares"],
                    "debt_ratio": data["debt_ratio"],
                    "insider_net_buy_3m": data["insider_net_buy_3m"],
                    "updated_at": data["updated_at"],
                },
            )
            db.execute(stmt)
        db.commit()
        logger.info(f"批量保存 {len(data_list)} 條基本面數據")
    except Exception as e:
        db.rollback()
        logger.error(f"保存數據失敗: {e}")
        raise
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_stock_fundamentals(self, stock_codes: list):
    """
    批量獲取股票基本面數據的通用任務
    
    Args:
        stock_codes: 股票代碼列表，例如 ['0005.HK', '9988.HK', '0700.HK']
        
    Returns:
        dict: 包含處理結果的字典
    """
    try:
        logger.info(f"開始獲取 {len(stock_codes)} 隻股票的基本面數據")
        
        batch_fundamental_data = []
        failed_symbols = []
        success_count = 0
        
        # 分批處理避免過於頻繁的 API 請求
        batch_size = 5
        total_batches = (len(stock_codes) + batch_size - 1) // batch_size
        
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i : i + batch_size]
            current_batch = i // batch_size + 1
            logger.info(f"處理批次 {current_batch}/{total_batches}: {batch}")
            
            for symbol in batch:
                try:
                    # 添加延遲避免過於頻繁的 API 請求
                    time.sleep(0.5)
                    
                    ticker = Ticker(symbol)
                    info = ticker.info
                    
                    # 提取基本面數據
                    # 注意：YFinance 的 debtToEquity 返回的是百分比值（如 140.542），
                    # 需要轉換為小數（如 1.40542）以符合資料庫 NUMERIC(6,4) 的精度
                    debt_to_equity = info.get("debtToEquity")
                    if debt_to_equity is not None:
                        debt_to_equity = round(debt_to_equity / 100, 4)
                    
                    fundamental_data = {
                        "code": symbol,
                        "market": symbol.split(".")[-1] if "." in symbol else "HK",
                        "report_date": datetime.now().date(),
                        "pe_ttm": info.get("trailingPE"),
                        "eps_ttm": info.get("trailingEps"),
                        "float_shares": info.get("floatShares"),
                        "debt_ratio": debt_to_equity,
                        "insider_net_buy_3m": info.get("insiderTransactions"),
                        "updated_at": datetime.now(),
                    }
                    
                    batch_fundamental_data.append(fundamental_data)
                    success_count += 1
                    logger.info(f"成功獲取 {symbol} 的基本面數據")
                    
                except Exception as e:
                    logger.error(f"獲取 {symbol} 數據失敗: {e}")
                    failed_symbols.append(symbol)
                    continue
            
            # 每批次後稍作休息
            time.sleep(2)
        
        # 保存數據到資料庫
        if batch_fundamental_data:
            save_to_database(batch_fundamental_data)
            logger.info(f"成功保存 {len(batch_fundamental_data)} 條數據到資料庫")
        
        if failed_symbols:
            logger.warning(f"有 {len(failed_symbols)} 隻股票獲取失敗: {failed_symbols}")
        
        return {
            "status": "success",
            "total": len(stock_codes),
            "success": success_count,
            "failed": len(failed_symbols),
            "failed_symbols": failed_symbols,
        }
        
    except Exception as exc:
        logger.error(f"獲取股票數據失敗: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def fetch_single_stock_fundamental(self, symbol: str):
    """
    獲取單一股票基本面數據
    
    Args:
        symbol: 股票代碼，例如 '0005.HK'
        
    Returns:
        dict: 股票基本面數據
    """
    try:
        logger.info(f"獲取單一股票 {symbol} 的基本面數據")
        ticker = Ticker(symbol)
        info = ticker.info
        
        # 注意：YFinance 的 debtToEquity 返回的是百分比值（如 140.542），
        # 需要轉換為小數（如 1.40542）以符合資料庫 NUMERIC(6,4) 的精度
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None:
            debt_to_equity = round(debt_to_equity / 100, 4)
        
        fundamental_data = {
            "code": symbol,
            "market": symbol.split(".")[-1] if "." in symbol else "HK",
            "report_date": datetime.now().date(),
            "pe_ttm": info.get("trailingPE"),
            "eps_ttm": info.get("trailingEps"),
            "float_shares": info.get("floatShares"),
            "debt_ratio": debt_to_equity,
            "insider_net_buy_3m": info.get("insiderTransactions"),
            "updated_at": datetime.now(),
        }
        
        save_to_database([fundamental_data])
        logger.info(f"成功獲取並保存 {symbol} 的基本面數據")
        return fundamental_data
        
    except Exception as exc:
        logger.error(f"獲取 {symbol} 數據失敗: {exc}")
        raise self.retry(exc=exc)
