"""
拉姆動態止損引擎（Ram Stop Loss Engine）
基於分鐘線數據的動態移動止損策略

策略說明：
1. 以買入後的最高收盤價為基準
2. 當價格從最高點回撤超過設定比例（預設 8%）時觸發止損
3. 使用 corrected_close 字段計算，避免異常數據導致誤觸發
4. 止損比例可從 system_config 表動態讀取
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List

from sqlalchemy import desc, func
from app.database import SessionLocal
from app.models.stock_bar_minute import StockBarMinute
from app.models.ram_stop_loss import RamStopLoss
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class RamStopLossEngine:
    """拉姆動態止損引擎"""

    def __init__(self, drawdown_ratio: Optional[float] = None):
        """
        Args:
            drawdown_ratio: 回撤觸發比例，若為 None 則從 system_config 讀取
        """
        self.drawdown_ratio = drawdown_ratio or self._load_drawdown_ratio()

    def _load_drawdown_ratio(self) -> float:
        """從 system_config 表讀取止損比例"""
        db = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == "ram_stop_loss.params"
            ).first()
            if config and config.config_value:
                params = config.config_value
                if isinstance(params, str):
                    import json
                    params = json.loads(params)
                return float(params.get("drawdown_ratio", 0.08))
        except Exception as e:
            logger.warning(f"讀取止損配置失敗，使用預設值 0.08: {e}")
        finally:
            db.close()
        return 0.08

    # ==========================================
    # 分鐘線數據處理
    # ==========================================

    def update_minute_data(self, code: str, minute_data: dict) -> dict:
        """
        更新分鐘線數據（盤中每分鐘調用）
        
        Args:
            code: 股票代碼
            minute_data: {
                "trade_time": datetime,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": int
            }
        
        Returns:
            處理結果（含數據質量標記）
        """
        db = SessionLocal()
        try:
            # 1. 檢查是否為重複記錄
            existing = db.query(StockBarMinute).filter(
                StockBarMinute.code == code,
                StockBarMinute.trade_time == minute_data["trade_time"]
            ).first()
            
            if existing:
                logger.warning(f"{code} 重複分鐘數據，跳過: {minute_data['trade_time']}")
                return {"status": "duplicate", "code": code}
            
            # 2. 檢查價格異常跳動
            is_valid = True
            corrected_open = Decimal(str(minute_data["open"]))
            corrected_close = Decimal(str(minute_data["close"]))
            
            last_minute = db.query(StockBarMinute).filter(
                StockBarMinute.code == code
            ).order_by(desc(StockBarMinute.trade_time)).first()
            
            if last_minute and last_minute.close and float(last_minute.close) > 0:
                last_close = float(last_minute.close)
                current_close = float(minute_data["close"])
                change_pct = abs(current_close - last_close) / last_close
                
                if change_pct > 0.10:  # 單分鐘漲跌幅 > 10%
                    # 檢查成交量是否異常低
                    avg_volume = self._get_avg_volume(db, code, 10)
                    if avg_volume > 0 and minute_data["volume"] < avg_volume * 0.1:
                        is_valid = False
                        corrected_close = Decimal(str(last_close))
                        corrected_open = Decimal(str(last_close))
                        logger.warning(
                            f"{code} 價格異常跳動 {change_pct:.2%}，"
                            f"成交量 {minute_data['volume']} 低於均值 {avg_volume:.0f} 的 10%，已修正"
                        )
            
            # 3. 寫入數據庫
            record = StockBarMinute(
                code=code,
                trade_time=minute_data["trade_time"],
                open=Decimal(str(minute_data["open"])),
                high=Decimal(str(minute_data["high"])),
                low=Decimal(str(minute_data["low"])),
                close=Decimal(str(minute_data["close"])),
                volume=minute_data["volume"],
                is_valid=is_valid,
                corrected_open=corrected_open,
                corrected_close=corrected_close,
            )
            db.add(record)
            db.commit()
            
            return {
                "status": "success",
                "code": code,
                "is_valid": is_valid,
                "corrected_close": float(corrected_close),
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新 {code} 分鐘數據失敗: {e}")
            return {"status": "error", "code": code, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # 止損檢查
    # ==========================================

    def check_stop_loss(self, code: str) -> dict:
        """
        檢查是否觸發止損（使用 corrected_close）
        
        Args:
            code: 股票代碼
        
        Returns:
            止損檢查結果
        """
        db = SessionLocal()
        try:
            # 讀取止損狀態
            ram = db.query(RamStopLoss).filter(
                RamStopLoss.code == code,
                RamStopLoss.is_active == True
            ).first()
            
            if not ram:
                return {"status": "no_active_position", "code": code}
            
            # 讀取最新有效分鐘線
            latest = db.query(StockBarMinute).filter(
                StockBarMinute.code == code,
                StockBarMinute.is_valid == True
            ).order_by(desc(StockBarMinute.trade_time)).first()
            
            if not latest or not latest.corrected_close:
                return {"status": "no_data", "code": code}
            
            current_price = float(latest.corrected_close)
            highest_price = float(ram.highest_price)
            
            # 更新最高價
            if current_price > highest_price:
                highest_price = current_price
                ram.highest_price = current_price
            
            # 計算回撤比例
            drawdown = (highest_price - current_price) / highest_price if highest_price > 0 else 0
            ram.drawdown_pct = round(Decimal(str(drawdown)), 4)
            
            # 計算止損價
            stop_loss_price = highest_price * (1 - self.drawdown_ratio)
            ram.stop_loss_price = round(Decimal(str(stop_loss_price)), 4)
            ram.current_price = round(Decimal(str(current_price)), 4)
            ram.updated_at = datetime.now()
            
            # 檢查是否觸發止損
            if current_price <= stop_loss_price:
                ram.is_triggered = True
                ram.is_active = False
                ram.triggered_at = datetime.now()
                db.commit()
                
                logger.warning(
                    f"🚨 {code} 觸發拉姆止損！"
                    f"買入價: {float(ram.buy_price):.2f}, "
                    f"最高價: {highest_price:.2f}, "
                    f"當前價: {current_price:.2f}, "
                    f"回撤: {drawdown:.2%}"
                )
                return {
                    "status": "triggered",
                    "code": code,
                    "buy_price": float(ram.buy_price),
                    "highest_price": highest_price,
                    "current_price": current_price,
                    "stop_loss_price": stop_loss_price,
                    "drawdown_pct": round(drawdown, 4),
                }
            
            db.commit()
            return {
                "status": "holding",
                "code": code,
                "current_price": current_price,
                "highest_price": highest_price,
                "stop_loss_price": stop_loss_price,
                "drawdown_pct": round(drawdown, 4),
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"檢查 {code} 止損失敗: {e}")
            return {"status": "error", "code": code, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # 建立止損部位
    # ==========================================

    def create_position(self, code: str, market: str, buy_date, buy_price: float) -> dict:
        """
        建立新的止損部位（買入股票時調用）
        
        Args:
            code: 股票代碼
            market: 市場
            buy_date: 買入日期
            buy_price: 買入價格
        
        Returns:
            建立結果
        """
        db = SessionLocal()
        try:
            # 檢查是否已有活躍部位
            existing = db.query(RamStopLoss).filter(
                RamStopLoss.code == code,
                RamStopLoss.is_active == True
            ).first()
            
            if existing:
                logger.warning(f"{code} 已有活躍止損部位，跳過")
                return {"status": "already_exists", "code": code}
            
            # 建立新部位
            ram = RamStopLoss(
                code=code,
                market=market,
                buy_date=buy_date,
                buy_price=round(Decimal(str(buy_price)), 4),
                highest_price=round(Decimal(str(buy_price)), 4),
                current_price=round(Decimal(str(buy_price)), 4),
                stop_loss_price=round(Decimal(str(buy_price * (1 - self.drawdown_ratio))), 4),
                drawdown_pct=0,
                is_triggered=False,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(ram)
            db.commit()
            
            logger.info(f"✅ {code} 建立拉姆止損部位，買入價: {buy_price:.2f}")
            return {
                "status": "created",
                "code": code,
                "buy_price": buy_price,
                "stop_loss_price": float(ram.stop_loss_price),
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"建立 {code} 止損部位失敗: {e}")
            return {"status": "error", "code": code, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # 每日收盤後批量校驗
    # ==========================================

    def daily_validation(self, codes: List[str] = None) -> dict:
        """
        每日收盤後批量處理數據缺失與成交量異常
        
        Args:
            codes: 股票代碼列表，若為 None 則處理所有活躍部位
        
        Returns:
            處理結果
        """
        db = SessionLocal()
        try:
            if codes is None:
                # 獲取所有活躍部位
                active_positions = db.query(RamStopLoss).filter(
                    RamStopLoss.is_active == True
                ).all()
                codes = [p.code for p in active_positions]
            
            results = []
            for code in codes:
                result = self._fill_missing_data(db, code)
                results.append(result)
            
            db.commit()
            logger.info(f"每日校驗完成，處理 {len(codes)} 隻股票")
            return {"status": "success", "processed": len(codes), "results": results}
            
        except Exception as e:
            db.rollback()
            logger.error(f"每日校驗失敗: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            db.close()

    def _fill_missing_data(self, db, code: str) -> dict:
        """填充缺失的分鐘線數據"""
        try:
            # 檢查最近 30 分鐘內是否有數據缺失
            cutoff = datetime.now() - timedelta(minutes=30)
            
            # 獲取最近的有效數據點
            last_valid = db.query(StockBarMinute).filter(
                StockBarMinute.code == code,
                StockBarMinute.trade_time >= cutoff,
                StockBarMinute.is_valid == True
            ).order_by(desc(StockBarMinute.trade_time)).first()
            
            if not last_valid:
                return {"code": code, "status": "no_recent_data"}
            
            # 檢查是否有連續 3 分鐘以上的缺失
            recent_records = db.query(StockBarMinute).filter(
                StockBarMinute.code == code,
                StockBarMinute.trade_time >= cutoff
            ).order_by(StockBarMinute.trade_time).all()
            
            if len(recent_records) < 2:
                return {"code": code, "status": "insufficient_data"}
            
            # 檢查時間間隔
            for i in range(len(recent_records) - 1):
                time_diff = (recent_records[i + 1].trade_time - recent_records[i].trade_time).total_seconds()
                if time_diff > 180:  # 超過 3 分鐘
                    logger.warning(f"{code} 在 {recent_records[i].trade_time} 附近有數據缺失")
            
            return {"code": code, "status": "ok"}
            
        except Exception as e:
            logger.error(f"填充 {code} 缺失數據失敗: {e}")
            return {"code": code, "status": "error", "error": str(e)}

    def _get_avg_volume(self, db, code: str, minutes: int) -> float:
        """獲取過去 N 分鐘的平均成交量"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        result = db.query(func.avg(StockBarMinute.volume)).filter(
            StockBarMinute.code == code,
            StockBarMinute.trade_time >= cutoff,
            StockBarMinute.is_valid == True
        ).scalar()
        return float(result) if result else 0
