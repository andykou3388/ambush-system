from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.models.screener import ScreenerRequest, ScreenerResponse, ZoneType, StockItem

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])

# 模擬股票數據（實際應用中應該從數據庫或緩存獲取）
mock_stocks = [
    StockItem(
        symbol="2330.TW",
        name="台積電",
        price=580.0,
        change_pct=2.5,
        zone=ZoneType.BUY,
        score=95.5,
        ma10=560.0,
        ma30=540.0
    ),
    StockItem(
        symbol="2317.TW",
        name="鴻海",
        price=85.0,
        change_pct=-1.2,
        zone=ZoneType.HOLD,
        score=78.0,
        ma10=88.0,
        ma30=90.0
    ),
    StockItem(
        symbol="2454.TW",
        name="聯發科",
        price=1200.0,
        change_pct=5.0,
        zone=ZoneType.BUY,
        score=92.0,
        ma10=1150.0,
        ma30=1100.0
    ),
    StockItem(
        symbol="1301.TW",
        name="台塑",
        price=110.0,
        change_pct=0.8,
        zone=ZoneType.HOLD,
        score=65.0,
        ma10=108.0,
        ma30=105.0
    ),
    StockItem(
        symbol="2880.TW",
        name="國巨",
        price=250.0,
        change_pct=-3.0,
        zone=ZoneType.SELL,
        score=45.0,
        ma10=260.0,
        ma30=270.0
    ),
    StockItem(
        symbol="2303.TW",
        name="光寶科",
        price=180.0,
        change_pct=1.5,
        zone=ZoneType.BUY,
        score=88.0,
        ma10=175.0,
        ma30=170.0
    ),
    StockItem(
        symbol="2327.TW",
        name="華碩",
        price=320.0,
        change_pct=-0.5,
        zone=ZoneType.HOLD,
        score=72.0,
        ma10=325.0,
        ma30=330.0
    ),
    StockItem(
        symbol="2357.TW",
        name="晶圓廠",
        price=95.0,
        change_pct=2.0,
        zone=ZoneType.BUY,
        score=85.0,
        ma10=92.0,
        ma30=90.0
    ),
    StockItem(
        symbol="2881.TW",
        name="茂矽",
        price=150.0,
        change_pct=-1.0,
        zone=ZoneType.HOLD,
        score=68.0,
        ma10=155.0,
        ma30=160.0
    ),
    StockItem(
        symbol="2344.TW",
        name="騰訊",
        price=350.0,
        change_pct=3.5,
        zone=ZoneType.BUY,
        score=90.0,
        ma10=340.0,
        ma30=330.0
    ),
]

@router.get("/stocks", response_model=ScreenerResponse)
async def screen_stocks(
    zone: Optional[str] = Query(None, description="區域過濾"),
    min_price: Optional[float] = Query(None, description="最低價格"),
    max_price: Optional[float] = Query(None, description="最高價格"),
    min_volume: Optional[float] = Query(None, description="最低成交量"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
):
    """
    篩選股票
    
    根據指定的過濾條件篩選股票，支援分頁查詢。
    """
    # 過濾邏輯
    filtered_stocks = mock_stocks.copy()
    
    # 區域過濾
    if zone:
        zone_enum = ZoneType(zone)
        filtered_stocks = [stock for stock in filtered_stocks if stock.zone == zone_enum]
    
    # 價格過濾
    if min_price is not None:
        filtered_stocks = [stock for stock in filtered_stocks if stock.price >= min_price]
    
    if max_price is not None:
        filtered_stocks = [stock for stock in filtered_stocks if stock.price <= max_price]
    
    # 成交量過濾
    if min_volume is not None:
        # 這裡假設成交量與價格成正比，實際應用中會有真實的成交量數據
        filtered_stocks = [stock for stock in filtered_stocks if stock.price >= min_volume]
    
    # 排序
    sort_field = "score"  # 默認按分數排序
    sort_order = "desc"  # 默認降序
    
    # 如果有數據才進行排序
    if filtered_stocks:
        if hasattr(filtered_stocks[0], sort_field):
            sorted_stocks = sorted(
                filtered_stocks,
                key=lambda x: getattr(x, sort_field),
                reverse=(sort_order == "desc")
            )
        else:
            sorted_stocks = filtered_stocks
    else:
        sorted_stocks = filtered_stocks
    
    # 分頁處理
    total = len(sorted_stocks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_stocks = sorted_stocks[start_idx:end_idx]
    
    return ScreenerResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=paginated_stocks
    )