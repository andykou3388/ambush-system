"""
任務輔助函數
提供週期性任務所需的各種輔助功能 - 使用 SQLAlchemy ORM 操作資料庫
"""
import logging
from typing import List, Dict, Any, Optional

from app.database import SessionLocal
from app.models.stock_bar import StockBar
from app.models.stock_fundamental import StockFundamental
from app.models.stock_signal_log import StockSignalLog
from app.engine.rule_engine import RuleEngine
from classifier.zone_classifier import ThreeZoneClassifier

logger = logging.getLogger(__name__)


def get_stock_list(market: str) -> List[str]:
    """
    從 stock_bar 獲取指定市場的股票列表

    Args:
        market: 市場代碼 ('TW' 或 'US')

    Returns:
        股票代碼列表
    """
    logger.info(f"從資料庫獲取 {market} 市場的股票列表")
    db = SessionLocal()
    try:
        stocks = (
            db.query(StockBar.code)
            .filter(StockBar.market == market)
            .distinct()
            .all()
        )
        result = [s.code for s in stocks]
        logger.info(f"找到 {len(result)} 隻股票")
        return result
    except Exception as e:
        logger.error(f"獲取股票列表失敗: {e}")
        return []
    finally:
        db.close()


def calculate_indicators(symbol: str) -> Dict[str, Any]:
    """
    計算技術指標並更新 stock_bar

    Args:
        symbol: 股票代碼

    Returns:
        技術指標數據
    """
    logger.info(f"計算 {symbol} 的技術指標")
    db = SessionLocal()
    try:
        # 讀取最近 60 筆週線數據
        bars = (
            db.query(StockBar)
            .filter(StockBar.code == symbol)
            .order_by(StockBar.trade_date.desc())
            .limit(60)
            .all()
        )

        if not bars:
            logger.warning(f"{symbol} 無歷史數據")
            return {"symbol": symbol, "status": "no_data"}

        # 計算 MA10, MA30, Volume MA5
        closes = [float(b.close) for b in bars if b.close]
        volumes = [b.volume or 0 for b in bars]

        if len(closes) >= 10:
            ma10 = sum(closes[:10]) / 10
        else:
            ma10 = closes[0] if closes else 0

        if len(closes) >= 30:
            ma30 = sum(closes[:30]) / 30
        else:
            ma30 = closes[0] if closes else 0

        if len(volumes) >= 5:
            vol_ma5 = sum(volumes[:5]) / 5
        else:
            vol_ma5 = volumes[0] if volumes else 0

        # 更新最新一筆的 MA 值
        latest_bar = bars[0]
        latest_bar.ma10_w = ma10
        latest_bar.ma30_w = ma30
        latest_bar.volume_ma5_w = vol_ma5

        db.commit()
        logger.info(f"{symbol} 技術指標計算完成: MA10={ma10:.2f}, MA30={ma30:.2f}")

        return {
            "symbol": symbol,
            "ma10": ma10,
            "ma30": ma30,
            "volume_ma5": vol_ma5,
            "status": "success",
        }
    except Exception as e:
        db.rollback()
        logger.error(f"計算 {symbol} 技術指標失敗: {e}")
        return {"symbol": symbol, "status": "error", "error": str(e)}
    finally:
        db.close()


def run_rule_engine(symbol: str) -> Dict[str, Any]:
    """
    執行規則引擎

    Args:
        symbol: 股票代碼

    Returns:
        規則引擎結果
    """
    logger.info(f"執行 {symbol} 的規則引擎")
    db = SessionLocal()
    try:
        # 讀取最新行情
        bar = (
            db.query(StockBar)
            .filter(StockBar.code == symbol)
            .order_by(StockBar.trade_date.desc())
            .first()
        )

        if not bar:
            logger.warning(f"{symbol} 無行情數據")
            return {"symbol": symbol, "status": "no_data"}

        # 讀取最新基本面
        fund = (
            db.query(StockFundamental)
            .filter(StockFundamental.code == symbol)
            .order_by(StockFundamental.report_date.desc())
            .first()
        )

        # 執行規則引擎
        engine = RuleEngine()
        result = engine.run_from_db(bar, fund)

        logger.info(f"{symbol} 規則引擎結果: {result.get('label', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"執行 {symbol} 規則引擎失敗: {e}")
        return {"symbol": symbol, "status": "error", "error": str(e)}
    finally:
        db.close()


def classify_stock(symbol: str) -> Dict[str, Any]:
    """
    執行三區分類並寫入 stock_signal_log

    Args:
        symbol: 股票代碼

    Returns:
        三區分類結果
    """
    logger.info(f"對 {symbol} 執行三區分類")
    db = SessionLocal()
    try:
        # 讀取最新行情
        bar = (
            db.query(StockBar)
            .filter(StockBar.code == symbol)
            .order_by(StockBar.trade_date.desc())
            .first()
        )

        if not bar:
            logger.warning(f"{symbol} 無行情數據")
            return {"symbol": symbol, "zone": "unknown", "status": "no_data"}

        # 讀取最新基本面
        fund = (
            db.query(StockFundamental)
            .filter(StockFundamental.code == symbol)
            .order_by(StockFundamental.report_date.desc())
            .first()
        )

        # 執行規則引擎
        engine = RuleEngine()
        rule_result = engine.run_from_db(bar, fund)

        # 執行三區分類
        classifier = ThreeZoneClassifier()
        result = classifier.classify_stock(rule_result)

        # 將規則引擎的 label 映射為三區分類
        label = rule_result.get("label", "观望")
        zone_map = {
            "上升交易（买点）": "UPTREND",
            "潜在实力股（观察）": "POTENTIAL",
            "下跌参考（警示）": "DOWNTREND",
            "观望": "POTENTIAL",
        }
        zone = zone_map.get(label, "POTENTIAL")

        # 計算信心度（根據規則通過數量）
        rules_passed = sum([
            1 if rule_result.get("rule1_trend", {}).get("long") else 0,
            1 if rule_result.get("rule2_volume_break") else 0,
            1 if rule_result.get("rule3_buy_point") else 0,
            1 if rule_result.get("rule4_valuation") else 0,
            1 if rule_result.get("rule5_fundamental") else 0,
        ])
        confidence = round(rules_passed / 5, 2)

        # 寫入 stock_signal_log
        signal = StockSignalLog(
            code=symbol,
            market=bar.market,
            trade_date=bar.trade_date,
            zone=zone,
            confidence=confidence,
            trigger_rules=rule_result,
            reason=f"{bar.name or symbol} - {zone} 區域，信心度 {confidence:.0%}",
            engine_version="V2.2",
        )
        db.add(signal)
        db.commit()

        logger.info(f"{symbol} 分類完成: {zone} (信心度: {confidence:.0%})")

        return {
            "symbol": symbol,
            "zone": zone,
            "confidence": confidence,
            "rules_passed": rules_passed,
            "status": "success",
        }
    except Exception as e:
        db.rollback()
        logger.error(f"分類 {symbol} 失敗: {e}")
        return {"symbol": symbol, "status": "error", "error": str(e)}
    finally:
        db.close()


def generate_report(results: List[Dict], market: str) -> str:
    """
    生成分析報告

    Args:
        results: 分析結果列表
        market: 市場代碼

    Returns:
        報告文件路徑或狀態
    """
    logger.info(f"生成 {market} 市場的分析報告，共 {len(results)} 隻股票")

    report_content = f"""
週分析報告 - {market} 市場
========================

總計分析股票數量: {len(results)}
生成時間: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

分析結果摘要:
"""

    for result in results:
        report_content += f"- {result.get('symbol', 'unknown')}: {result.get('zone', 'unknown')} (信心度: {result.get('confidence', 0):.2f})\n"

    # 保存報告到文件
    report_path = f"reports/weekly_analysis_{market}_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.txt"

    try:
        import os
        os.makedirs('reports', exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"報告已保存至: {report_path}")
    except Exception as e:
        logger.error(f"保存報告失敗: {e}")
        raise

    return report_path


def validate_market(market: str) -> bool:
    """
    驗證市場代碼

    Args:
        market: 市場代碼

    Returns:
        是否有效
    """
    valid_markets = ['TW', 'US']
    return market in valid_markets


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    獲取任務執行狀態

    Args:
        task_id: 任務ID

    Returns:
        任務狀態信息
    """
    # 這裡應該實現任務狀態查詢邏輯
    # 通常會從 Redis 或其他後端存儲中獲取
    return {
        'task_id': task_id,
        'status': 'completed',
        'result': 'success'
    }