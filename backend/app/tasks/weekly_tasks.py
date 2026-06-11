"""
每週任務模組
負責週五收盤後的技術指標計算、規則引擎執行與通知發送
V2.0 優化：使用 stock_fundamental_latest 緩存表進行基本面查詢
V2.0 增強：技術指標計算時過濾 NaN/Inf，避免下游 JSON 序列化失敗
"""
import logging
import math
from typing import List

from celery import shared_task
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from app.database import SessionLocal
from app.models.stock_bar import StockBar
from app.models.stock_fundamental_latest import StockFundamentalLatest
from app.models.stock_signal_log import StockSignalLog
from app.models.user_notification_config import UserNotificationConfig
from app.engine.rule_engine import RuleEngine
from classifier.zone_classifier import ThreeZoneClassifier

logger = logging.getLogger(__name__)


def _finite_or_none(v):
    """過濾 NaN/Inf，僅保留有限值，否則回傳 None"""
    if v is None:
        return None
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (ValueError, TypeError):
        return None


def _calculate_weekly_indicators_impl(market: str = "HK"):
    """
    計算指定市場所有股票的週線技術指標（非 Celery 任務版本）
    供 Celery 任務和一次性初始化任務直接調用
    
    Args:
        market: 市場代碼，預設 'TW'
    """
    logger.info(f"開始計算 {market} 市場的週線技術指標")
    market = (market or "").upper()
    db = SessionLocal()
    try:
        # 獲取所有股票代碼（大小寫無關）
        stocks = db.query(StockBar.code).filter(
            func.upper(StockBar.market) == market
        ).distinct().all()
        
        codes = [s.code for s in stocks]
        logger.info(f"需要計算 {len(codes)} 隻股票的技術指標")
        
        results = []
        for code in codes:
            try:
                # 讀取最近 60 筆週線數據（包含所有分區表）
                # 使用原生SQL查詢所有分區表，確保涵蓋所有年份
                from sqlalchemy import text
                sql_query = text("""
                    SELECT id, code, name, market, trade_date, freq, open, high, low, close, volume, 
                           change_pct, ma10_w, ma30_w, volume_ma5_w, created_at 
                    FROM stock_bar 
                    WHERE code = :code 
                    ORDER BY trade_date DESC 
                    LIMIT 60
                """)
                bars = db.execute(sql_query, {"code": code}).fetchall()
                
                # 轉換為 StockBar 對象以便處理
                bars = [StockBar(**row._asdict()) for row in bars]
                
                if not bars:
                    continue
                
                closes = [float(b.close) for b in bars if b.close]
                volumes = [b.volume or 0 for b in bars]
                
                if not closes:
                    continue
                
                # 計算 MA10, MA30, Volume MA5
                ma10 = sum(closes[:10]) / 10 if len(closes) >= 10 else closes[-1]
                ma30 = sum(closes[:30]) / 30 if len(closes) >= 30 else closes[-1]
                vol_ma5 = sum(volumes[:5]) / 5 if len(volumes) >= 5 else volumes[-1] if volumes else 0

                # 過濾 NaN/Inf，僅寫入有限值
                ma10 = _finite_or_none(ma10)
                ma30 = _finite_or_none(ma30)
                vol_ma5 = _finite_or_none(vol_ma5)

                # 更新最新一筆
                latest_bar = bars[0]
                latest_bar.ma10_w = ma10
                latest_bar.ma30_w = ma30
                latest_bar.volume_ma5_w = vol_ma5
                
                results.append({
                    "code": code,
                    "ma10": round(ma10, 2) if ma10 is not None else None,
                    "ma30": round(ma30, 2) if ma30 is not None else None,
                    "status": "success",
                })
                
            except Exception as e:
                logger.error(f"計算 {code} 技術指標失敗: {e}")
                results.append({"code": code, "status": "error", "error": str(e)})
        
        db.commit()
        logger.info(f"技術指標計算完成，成功 {sum(1 for r in results if r['status'] == 'success')}/{len(results)}")
        return {"status": "success", "market": market, "results": results}
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def calculate_weekly_indicators(self, market: str = "TW"):
    """
    計算指定市場所有股票的週線技術指標
    
    Args:
        market: 市場代碼，預設 'TW'
    """
    try:
        return _calculate_weekly_indicators_impl(market)
    except Exception as exc:
        logger.error(f"計算技術指標失敗: {exc}")
        raise self.retry(exc=exc)


def _run_weekly_rule_engine_impl(market: str = "TW"):
    """
    執行每週規則引擎，生成選股信號（非 Celery 任務版本）
    供 Celery 任務和一次性初始化任務直接調用
    
    Args:
        market: 市場代碼，預設 'TW'
    """
    logger.info(f"開始執行 {market} 市場的規則引擎")
    market = (market or "").upper()
    db = SessionLocal()
    try:
        # 獲取所有股票代碼（大小寫無關）
        stocks = db.query(StockBar.code).filter(
            func.upper(StockBar.market) == market
        ).distinct().all()
        
        codes = [s.code for s in stocks]
        #codes = ['0001.HK', '0002.HK', '0003.HK']  # 測試用，實際使用時請註釋掉這行
        logger.info(f"需要執行 {len(codes)} 隻股票的規則引擎")
        
        engine = RuleEngine()
        classifier = ThreeZoneClassifier()
        results = []
        
        for code in codes:
            try:
                # 讀取最新行情（包含所有分區表）
                # 使用原生SQL查詢所有分區表，確保涵蓋所有年份
                from sqlalchemy import text
                sql_query = text("""
                    SELECT id, code, name, market, trade_date, freq, open, high, low, close, volume, 
                           change_pct, ma10_w, ma30_w, volume_ma5_w, created_at 
                    FROM stock_bar 
                    WHERE code = :code 
                    ORDER BY trade_date DESC 
                    LIMIT 1
                """)
                bar_result = db.execute(sql_query, {"code": code}).fetchone()
                
                if not bar_result:
                    continue
                
                # 轉換為 StockBar 對象
                bar = StockBar(**bar_result._asdict())
   
                # 讀取最新基本面（使用 latest 緩存表）
                fund = db.query(StockFundamentalLatest).filter(
                    StockFundamentalLatest.code == code
                ).first()
                
                # 執行規則引擎
                rule_result = engine.run_from_db(bar, fund)
           
                # 執行三區分類
                # 規則引擎標籤 → 三區對應：
                #   UPTREND   : 上升交易（买点）— 強勢買入信號
                #   POTENTIAL : 潛在实力股（观察）/ 觀望 — 持有或觀察（靠信心度區分）
                #   DOWNTREND : 下跌参考（警示）— 風險警示
                label = rule_result.get("label", "觀望")
                zone_map = {
                    "上升交易（买点）": "UPTREND",
                    "潜在实力股（观察）": "POTENTIAL",
                    "下跌参考（警示）": "DOWNTREND",
                    "觀望": "POTENTIAL",
                }
                zone = zone_map.get(label, "POTENTIAL")
                
                # 計算信心度
                rules_passed = sum([
                    1 if rule_result.get("rule1_trend", {}).get("long") else 0,
                    1 if rule_result.get("rule2_volume_break") else 0,
                    1 if rule_result.get("rule3_buy_point") else 0,
                    1 if rule_result.get("rule4_valuation") else 0,
                    1 if rule_result.get("rule5_fundamental") else 0,
                ])
                confidence = round(rules_passed / 5, 2)
                
                # 寫入信號（使用 UPSERT 避免唯一約束衝突）
                signal_data = {
                    "code": code,
                    "market": market,
                    "trade_date": bar.trade_date,
                    "zone": zone,
                    "confidence": confidence,
                    "trigger_rules": rule_result,
                    "reason": f"{bar.name or code} - {zone} 區域，信心度 {confidence:.0%}",
                    "engine_version": "V2.2",
                }
                stmt = insert(StockSignalLog).values(**signal_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["code", "trade_date"],
                    set_={
                        "zone": zone,
                        "confidence": confidence,
                        "trigger_rules": rule_result,
                        "reason": f"{bar.name or code} - {zone} 區域，信心度 {confidence:.0%}",
                        "engine_version": "V2.2",
                    }
                )
                db.execute(stmt)
                
                results.append({
                    "code": code,
                    "zone": zone,
                    "confidence": confidence,
                    "status": "success",
                })
                
            except Exception as e:
                logger.error(f"執行 {code} 規則引擎失敗: {e}")
                results.append({"code": code, "status": "error", "error": str(e)})
        
        db.commit()
        
        # 統計結果
        zones = {}
        for r in results:
            if r["status"] == "success":
                zone = r["zone"]
                zones[zone] = zones.get(zone, 0) + 1
        
        logger.info(f"規則引擎執行完成: {zones}")
        return {
            "status": "success",
            "market": market,
            "total": len(results),
            "zone_summary": zones,
            "results": results,
        }
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def run_weekly_rule_engine(self, market: str = "TW"):
    """
    執行每週規則引擎，生成選股信號
    
    Args:
        market: 市場代碼，預設 'TW'
    """
    try:
        return _run_weekly_rule_engine_impl(market)
    except Exception as exc:
        logger.error(f"執行規則引擎失敗: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def send_weekly_notifications(self, market: str = "TW"):
    """
    發送每週選股通知
    
    Args:
        market: 市場代碼，預設 'TW'
    """
    try:
        logger.info(f"開始發送 {market} 市場的每週通知")
        db = SessionLocal()
        try:
            # 獲取用戶通知配置
            configs = db.query(UserNotificationConfig).filter(
                UserNotificationConfig.is_active == True
            ).all()
            
            if not configs:
                logger.info("無活躍通知配置")
                return {"status": "no_active_configs"}
            
            # 獲取最新信號
            from sqlalchemy import desc
            latest_signals = db.query(StockSignalLog).filter(
                StockSignalLog.market == market
            ).order_by(desc(StockSignalLog.trade_date)).limit(50).all()
            
            # 按用戶配置發送通知
            notifications_sent = 0
            for config in configs:
                # 過濾用戶感興趣的區域
                user_signals = [
                    s for s in latest_signals
                    if s.zone in config.zone_filter
                    and s.confidence >= config.min_confidence
                ]
                
                if user_signals:
                    # TODO: 實際發送通知（APP推送/企微/郵件）
                    logger.info(
                        f"用戶 {config.user_id} 通過 {config.channel} "
                        f"收到 {len(user_signals)} 條通知"
                    )
                    notifications_sent += 1
            
            logger.info(f"通知發送完成，共 {notifications_sent} 位用戶")
            return {
                "status": "success",
                "market": market,
                "notifications_sent": notifications_sent,
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"發送通知失敗: {exc}")
        raise self.retry(exc=exc)
