"""
分鐘線數據任務模組
負責盤中分鐘線數據獲取、止損檢查、每日校驗與數據清理
V2.0 新增：拉姆止損專用分鐘線數據處理
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from celery import shared_task
from app.database import SessionLocal
from app.models.ram_stop_loss import RamStopLoss
from app.models.stock_bar_minute import StockBarMinute
from app.engine.ram_stop_loss import RamStopLossEngine

logger = logging.getLogger(__name__)


def _fetch_intraday_minute_data_impl():
    """
    盤中每分鐘獲取所有活躍部位的分鐘線數據（非 Celery 版本）
    供開發和調試直接調用
    
    Returns:
        dict: 執行結果，包含狀態、總數和結果列表
    """
    logger.info("開始獲取盤中分鐘線數據 [直接調用]")
    engine = RamStopLossEngine()
    
    db = SessionLocal()
    try:
        # 獲取所有活躍部位
        # active_positions = db.query(RamStopLoss).filter(
        #     RamStopLoss.is_active == True
        # ).all()
        
        active_positions = ['0700.HK', '9988.HK']  # TODO: 從資料庫獲取活躍部位，這裡為示範
        
        if not active_positions:
            logger.info("無活躍部位，跳過分鐘線數據獲取")
            return {"status": "no_active_positions"}
        
        codes = [p.code for p in active_positions]
        logger.info(f"需要獲取 {len(codes)} 隻股票的分鐘線數據：{codes}")
        
        results = []
        for code in codes:
            try:
                # TODO: 從 yfinance 或券商 API 獲取實際分鐘線數據
                # 此處為示範，實際使用時需替換為真實數據源
                # minute_data = get_minute_data_from_yfinance(code)
                # result = engine.update_minute_data(code, minute_data)
                # results.append(result)
                
                logger.info(f"{code} 分鐘線數據獲取（待接入真實數據源）")
                results.append({"code": code, "status": "pending_data_source"})
                
            except Exception as e:
                logger.error(f"獲取 {code} 分鐘線數據失敗：{e}")
                results.append({"code": code, "status": "error", "error": str(e)})
        
        return {
            "status": "success",
            "total": len(codes),
            "results": results,
        }
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=1)
def fetch_intraday_minute_data(self):
    """
    盤中每分鐘獲取所有活躍部位的分鐘線數據
    
    注意：實際分鐘線數據應從 yfinance 或券商 API 獲取，
    此處為框架示範，實際使用時需接入真實數據源
    """
    try:
        return _fetch_intraday_minute_data_impl()
    except Exception as exc:
        logger.error(f"獲取分鐘線數據失敗：{exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def check_all_stop_loss(self):
    """
    盤中每分鐘檢查所有活躍部位是否觸發止損
    """
    try:
        logger.info("開始檢查所有活躍部位止損")
        engine = RamStopLossEngine()
        
        db = SessionLocal()
        try:
            active_positions = db.query(RamStopLoss).filter(
                RamStopLoss.is_active == True
            ).all()
            
            if not active_positions:
                logger.info("無活躍部位，跳過止損檢查")
                return {"status": "no_active_positions"}
            
            triggered = []
            for position in active_positions:
                result = engine.check_stop_loss(position.code)
                if result.get("status") == "triggered":
                    triggered.append(result)
                    logger.warning(
                        f"🚨 止損觸發: {position.code}, "
                        f"買入價: {result['buy_price']:.2f}, "
                        f"當前價: {result['current_price']:.2f}"
                    )
            
            return {
                "status": "success",
                "total": len(active_positions),
                "triggered": len(triggered),
                "triggered_details": triggered,
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"止損檢查失敗: {exc}")
        raise self.retry(exc=exc)


def _daily_minute_validation_impl():
    """
    每日收盤後批量處理數據缺失與成交量異常（非 Celery 任務版本）
    供 Celery 任務和一次性初始化任務直接調用
    """
    logger.info("開始每日分鐘線數據校驗")
    engine = RamStopLossEngine()
    result = engine.daily_validation()
    
    logger.info(f"每日校驗完成: {result}")
    return result


@shared_task(bind=True, max_retries=1)
def daily_minute_validation(self):
    """
    每日收盤後批量處理數據缺失與成交量異常
    """
    try:
        return _daily_minute_validation_impl()
    except Exception as exc:
        logger.error(f"每日校驗失敗: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def cleanup_old_minute_data(self, days: int = 30):
    """
    清理超過指定天數的分鐘線數據
    
    Args:
        days: 保留天數，預設 30 天
    """
    try:
        cutoff = datetime.now() - timedelta(days=days)
        logger.info(f"開始清理 {cutoff} 之前的分鐘線數據")
        
        db = SessionLocal()
        try:
            deleted = db.query(StockBarMinute).filter(
                StockBarMinute.trade_time < cutoff
            ).delete()
            db.commit()
            
            logger.info(f"清理完成，刪除 {deleted} 條舊數據")
            return {"status": "success", "deleted": deleted}
            
        except Exception as e:
            db.rollback()
            logger.error(f"清理失敗: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"清理任務失敗: {exc}")
        raise self.retry(exc=exc)
