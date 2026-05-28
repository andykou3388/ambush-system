from fastapi import APIRouter, HTTPException
from app.models.stock_detail import StockDetailResponse
from app.indicators.ta_lib_calculator import TALibCalculator
from app.engine.rule_engine import RuleEngine
from app.classifier.zone_classifier import ThreeZoneClassifier
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/v1/stocks", tags=["stock_detail"])

# 模擬股票數據（實際應用中應該從數據庫或緩存獲取）
mock_stocks = [
    {"symbol": "2330.TW", "name": "台積電4", "price": 580.0, "change_pct": 2.5, "volume": 1000000, "market_cap": 1000000000000, "pe_ratio": 15.0},
    {"symbol": "2317.TW", "name": "鴻海", "price": 85.0, "change_pct": -1.2, "volume": 800000, "market_cap": 500000000000, "pe_ratio": 12.0},
    {"symbol": "2454.TW", "name": "聯發科", "price": 1200.0, "change_pct": 5.0, "volume": 1200000, "market_cap": 800000000000, "pe_ratio": 20.0},
    {"symbol": "1301.TW", "name": "台塑", "price": 110.0, "change_pct": 0.8, "volume": 900000, "market_cap": 400000000000, "pe_ratio": 10.0},
    {"symbol": "2880.TW", "name": "國巨", "price": 250.0, "change_pct": -3.0, "volume": 700000, "market_cap": 300000000000, "pe_ratio": 18.0},
    {"symbol": "2303.TW", "name": "光寶科", "price": 180.0, "change_pct": 1.5, "volume": 600000, "market_cap": 250000000000, "pe_ratio": 14.0},
    {"symbol": "2327.TW", "name": "華碩", "price": 320.0, "change_pct": -0.5, "volume": 500000, "market_cap": 200000000000, "pe_ratio": 16.0},
    {"symbol": "2357.TW", "name": "晶圓廠", "price": 95.0, "change_pct": 2.0, "volume": 400000, "market_cap": 150000000000, "pe_ratio": 8.0},
    {"symbol": "2881.TW", "name": "茂矽", "price": 150.0, "change_pct": -1.0, "volume": 300000, "market_cap": 100000000000, "pe_ratio": 11.0},
    {"symbol": "2344.TW", "name": "騰訊", "price": 350.0, "change_pct": 3.5, "volume": 1100000, "market_cap": 700000000000, "pe_ratio": 25.0},
]

@router.get("/{symbol}", response_model=StockDetailResponse)
async def get_stock_detail(symbol: str):
    """
    獲取個股詳情
    
    返回指定股票的完整資訊，包括技術指標、規則檢核結果、三區分類等。
    """
    # 查找股票
    stock = next((s for s in mock_stocks if s["symbol"] == symbol), None)
    if not stock:
        raise HTTPException(status_code=404, detail=f"股票 {symbol} 不存在")
    
    # 1. 計算技術指標
    ta_calc = TALibCalculator()
    
    # 模擬歷史價格數據（實際應用中應該從數據庫獲取）
    # 這邊假設我們有100天的歷史數據
    days = 100
    close_prices = np.random.uniform(stock["price"] * 0.95, stock["price"] * 1.05, days)
    close_series = pd.Series(close_prices)
    
    # 計算 MA10 和 MA30
    ma10 = ta_calc.calculate_ma10(close_series)
    ma30 = ta_calc.calculate_ma30(close_series)
    
    # 計算 MA10/MA30 比值
    ma10_ma30_ratio = None
    if ma10 is not None and ma30 is not None and len(ma30) > 0 and ma30.iloc[-1] != 0:
        ma10_ma30_ratio = ma10.iloc[-1] / ma30.iloc[-1]
    
    # 2. 執行規則引擎檢核
    rule_engine = RuleEngine()
    
    # 準備規則引擎輸入數據
    rule_input = {
        "code": stock["symbol"],
        "datetime": "2026-05-27",
        "close": stock["price"],
        "ma10": ma10.iloc[-1] if ma10 is not None and len(ma10) > 0 else 0,
        "ma30": ma30.iloc[-1] if ma30 is not None and len(ma30) > 0 else 0,
        "volume": stock["volume"],
        "pe": stock["pe_ratio"] if stock["pe_ratio"] else 0,
        "market_cap": stock["market_cap"],
        "debt_ratio": 0.3,
        "insider_buy": True,
        "analyst_cover": 4.5,
        "week_high": stock["price"] * 1.1,
        "week_low": stock["price"] * 0.9
    }
    
    # 執行規則引擎
    rule_result = rule_engine.run(pd.DataFrame([rule_input]))
    rule_output = rule_result.iloc[0].to_dict() if not rule_result.empty else {}
    
    # 3. 三區分類
    zone_classifier = ThreeZoneClassifier()
    zone_result = zone_classifier.classify_stock(rule_output)
    
    # 4. 組裝響應數據
    response = StockDetailResponse(
        symbol=stock["symbol"],
        name=stock["name"],
        price=stock["price"],
        change_pct=stock["change_pct"],
        volume=stock["volume"],
        market_cap=stock["market_cap"],
        pe_ratio=stock["pe_ratio"],
        technical_indicators={
            "ma10": ma10.iloc[-1] if ma10 is not None and len(ma10) > 0 else None,
            "ma30": ma30.iloc[-1] if ma30 is not None and len(ma30) > 0 else None,
            "ma10_ma30_ratio": ma10_ma30_ratio
        },
        zone_info={
            "zone": zone_result["zone"],
            "confidence": zone_result["confidence"],
            "explanation": zone_result["explanation"]
        },
        rules=[
            {
                "layer": 1,
                "rule_name": "趨勢規則",
                "passed": rule_output.get("rule1_trend", {}).get("long", False),
                "description": "價格趨勢分析",
                "details": str(rule_output.get("rule1_trend", {}))
            },
            {
                "layer": 2,
                "rule_name": "成交量規則",
                "passed": rule_output.get("rule2_volume_break", False),
                "description": "成交量異常放量",
                "details": ""
            },
            {
                "layer": 3,
                "rule_name": "買點規則",
                "passed": rule_output.get("rule3_buy_point", False),
                "description": "低風險買點",
                "details": ""
            },
            {
                "layer": 4,
                "rule_name": "估值規則",
                "passed": rule_output.get("rule4_valuation", False),
                "description": "價格與估值分析",
                "details": ""
            },
            {
                "layer": 5,
                "rule_name": "基本面規則",
                "passed": rule_output.get("rule5_fundamental", False),
                "description": "基本面條件",
                "details": ""
            }
        ],
        updated_at="2026-05-27T00:00:00Z"
    )
    
    return response

# 新增：用於獲取股票詳細信息的API，返回更完整的數據格式
@router.get("/{symbol}/detail", response_model=StockDetailResponse)
async def get_stock_detailed_info(symbol: str):
    """
    獲取個股詳細資訊（包含更多前端需要的字段）
    """
    # 查找股票
    stock = next((s for s in mock_stocks if s["symbol"] == symbol), None)
    if not stock:
        raise HTTPException(status_code=404, detail=f"股票 {symbol} 不存在")
    
    # 1. 計算技術指標
    ta_calc = TALibCalculator()
    
    # 模擬歷史價格數據（實際應用中應該從數據庫獲取）
    # 這邊假設我們有100天的歷史數據
    days = 100
    close_prices = np.random.uniform(stock["price"] * 0.95, stock["price"] * 1.05, days)
    close_series = pd.Series(close_prices)
    
    # 計算 MA10 和 MA30
    ma10 = ta_calc.calculate_ma10(close_series)
    ma30 = ta_calc.calculate_ma30(close_series)
    
    # 計算 MA10/MA30 比值
    ma10_ma30_ratio = None
    if ma10 is not None and ma30 is not None and len(ma30) > 0 and ma30.iloc[-1] != 0:
        ma10_ma30_ratio = ma10.iloc[-1] / ma30.iloc[-1]
    
    # 2. 執行規則引擎檢核
    rule_engine = RuleEngine()
    
    # 準備規則引擎輸入數據
    rule_input = {
        "code": stock["symbol"],
        "datetime": "2026-05-27",
        "close": stock["price"],
        "ma10": ma10.iloc[-1] if ma10 is not None and len(ma10) > 0 else 0,
        "ma30": ma30.iloc[-1] if ma30 is not None and len(ma30) > 0 else 0,
        "volume": stock["volume"],
        "pe": stock["pe_ratio"] if stock["pe_ratio"] else 0,
        "market_cap": stock["market_cap"],
        "debt_ratio": 0.3,
        "insider_buy": True,
        "analyst_cover": 4.5,
        "week_high": stock["price"] * 1.1,
        "week_low": stock["price"] * 0.9
    }
    
    # 執行規則引擎
    rule_result = rule_engine.run(pd.DataFrame([rule_input]))
    rule_output = rule_result.iloc[0].to_dict() if not rule_result.empty else {}
    
    # 3. 三區分類
    zone_classifier = ThreeZoneClassifier()
    zone_result = zone_classifier.classify_stock(rule_output)
    
    # 4. 組裝響應數據
    response = StockDetailResponse(
        symbol=stock["symbol"],
        name=stock["name"],
        price=stock["price"],
        change_pct=stock["change_pct"],
        volume=stock["volume"],
        market_cap=stock["market_cap"],
        pe_ratio=stock["pe_ratio"],
        technical_indicators={
            "ma10": ma10.iloc[-1] if ma10 is not None and len(ma10) > 0 else None,
            "ma30": ma30.iloc[-1] if ma30 is not None and len(ma30) > 0 else None,
            "ma10_ma30_ratio": ma10_ma30_ratio
        },
        zone_info={
            "zone": zone_result["zone"],
            "confidence": zone_result["confidence"],
            "explanation": zone_result["explanation"]
        },
        rules=[
            {
                "layer": 1,
                "rule_name": "趨勢規則",
                "passed": rule_output.get("rule1_trend", {}).get("long", False),
                "description": "價格趨勢分析",
                "details": str(rule_output.get("rule1_trend", {}))
            },
            {
                "layer": 2,
                "rule_name": "成交量規則",
                "passed": rule_output.get("rule2_volume_break", False),
                "description": "成交量異常放量",
                "details": ""
            },
            {
                "layer": 3,
                "rule_name": "買點規則",
                "passed": rule_output.get("rule3_buy_point", False),
                "description": "低風險買點",
                "details": ""
            },
            {
                "layer": 4,
                "rule_name": "估值規則",
                "passed": rule_output.get("rule4_valuation", False),
                "description": "價格與估值分析",
                "details": ""
            },
            {
                "layer": 5,
                "rule_name": "基本面規則",
                "passed": rule_output.get("rule5_fundamental", False),
                "description": "基本面條件",
                "details": ""
            }
        ],
        updated_at="2026-05-27T00:00:00Z"
    )
    
    return response
