"""
分鐘線數據任務模組
負責盤中分鐘線數據獲取、止損檢查、每日校驗與數據清理
V2.0 新增：拉姆止損專用分鐘線數據處理
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

import yfinance as yf
from celery import shared_task
from app.database import SessionLocal
from app.models.ram_stop_loss import RamStopLoss
from app.models.stock_bar_minute import StockBarMinute
from app.engine.ram_stop_loss import RamStopLossEngine

logger = logging.getLogger(__name__)


def _fetch_yfinance_minute(code: str) -> List[Dict]:
    """
    從 yfinance 獲取股票最近 5 分鐘的分鐘線數據

    Args:
        code: 股票代碼（如 2330.TW, 0700.HK）

    Returns:
        list[dict]: 每筆包含 {
            "trade_time": datetime,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int
        }
        或空 list（無法獲取時）
    """
    try:
        ticker = yf.Ticker(code)
        # 獲取當日分鐘線數據（最近 1 天，間隔 1 分鐘）
        df = ticker.history(period="1d", interval="1m")

        if df.empty:
            logger.warning(f"{code} yfinance 回傳空資料，可能非交易時段")
            return []

        # 取最近 5 筆，確保不漏掉任何一分鐘
        recent = df.tail(5)

        return [
            {
                "trade_time": idx.to_pydatetime(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            }
            for idx, row in recent.iterrows()
        ]

    except Exception as e:
        logger.error(f"從 yfinance 獲取 {code} 分鐘線數據失敗: {e}")
        return []


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
        active_positions = db.query(RamStopLoss).filter(
            RamStopLoss.is_active == True
        ).all()
        
        if not active_positions:
            logger.info("無活躍部位，跳過分鐘線數據獲取")
            return {"status": "no_active_positions"}
        
        codes = [p.code for p in active_positions]
        logger.info(f"需要獲取 {len(codes)} 隻股票的分鐘線數據：{codes}")
        
        results = []
        for code in codes:
            try:
                # 從 yfinance 獲取最近 5 分鐘的分鐘線數據
                minute_data_list = _fetch_yfinance_minute(code)
                if minute_data_list:
                    code_results = []
                    for minute_data in minute_data_list:
                        result = engine.update_minute_data(code, minute_data)
                        code_results.append(result)
                    results.append({
                        "code": code,
                        "status": "success",
                        "records": len(code_results),
                    })
                else:
                    logger.warning(f"{code} 無法獲取分鐘線數據（可能非交易時段）")
                    results.append({"code": code, "status": "no_data"})
                
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


def _fetch_yfinance_full_day(code: str) -> List[Dict]:
    """
    從 yfinance 獲取股票當日所有分鐘線數據（收盤後補全用）

    Args:
        code: 股票代碼（如 2330.TW, 0700.HK）

    Returns:
        list[dict]: 每筆包含 {
            "trade_time": datetime,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int
        }
        或空 list（無法獲取時）
    """
    try:
        ticker = yf.Ticker(code)
        df = ticker.history(period="1d", interval="1m")

        if df.empty:
            logger.warning(f"{code} yfinance 回傳空資料，可能非交易時段")
            return []

        return [
            {
                "trade_time": idx.to_pydatetime(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            }
            for idx, row in df.iterrows()
        ]

    except Exception as e:
        logger.error(f"從 yfinance 獲取 {code} 全日分鐘線數據失敗: {e}")
        return []


def _daily_minute_backfill_impl():
    """
    每日收盤後補全當日所有分鐘線數據（非 Celery 任務版本）
    供 Celery 任務和一次性初始化任務直接調用
    """
    logger.info("開始補全日分鐘線數據")
    engine = RamStopLossEngine()

    db = SessionLocal()
    try:
        # 獲取所有活躍部位
        active_positions = db.query(RamStopLoss).filter(
            RamStopLoss.is_active == True
        ).all()

        if not active_positions:
            logger.info("無活躍部位，跳過補全")
            return {"status": "no_active_positions"}

        codes = [p.code for p in active_positions]
        logger.info(f"需要補全 {len(codes)} 隻股票的分鐘線數據：{codes}")

        results = []
        for code in codes:
            try:
                # 拉取當日所有分鐘線
                all_minutes = _fetch_yfinance_full_day(code)
                if not all_minutes:
                    logger.warning(f"{code} 無法獲取全日分鐘線數據")
                    results.append({"code": code, "status": "no_data"})
                    continue

                # 逐筆寫入（duplicate 檢查會自動跳過已存在的）
                written = 0
                skipped = 0
                for minute_data in all_minutes:
                    result = engine.update_minute_data(code, minute_data)
                    if result.get("status") == "success":
                        written += 1
                    elif result.get("status") == "duplicate":
                        skipped += 1

                logger.info(f"{code} 補全完成: 寫入 {written} 筆, 跳過 {skipped} 筆")
                results.append({
                    "code": code,
                    "status": "success",
                    "written": written,
                    "skipped": skipped,
                })

            except Exception as e:
                logger.error(f"補全 {code} 分鐘線數據失敗: {e}")
                results.append({"code": code, "status": "error", "error": str(e)})

        return {
            "status": "success",
            "total": len(codes),
            "results": results,
        }

    finally:
        db.close()


def _daily_minute_validation_impl():
    """
    每日收盤後先補全數據，再檢查缺失與異常（非 Celery 任務版本）
    供 Celery 任務和一次性初始化任務直接調用
    """
    logger.info("開始每日分鐘線數據補全與校驗")

    # 第一步：補全當日所有分鐘線數據
    backfill_result = _daily_minute_backfill_impl()
    logger.info(f"補全結果: {backfill_result}")

    # 第二步：檢查數據缺失與異常
    engine = RamStopLossEngine()
    validation_result = engine.daily_validation()

    logger.info(f"每日校驗完成: {validation_result}")
    return {
        "backfill": backfill_result,
        "validation": validation_result,
    }


@shared_task(bind=True, max_retries=1)
def daily_minute_validation(self):
    """
    每日收盤後補全當日分鐘線數據並檢查缺失與異常
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
