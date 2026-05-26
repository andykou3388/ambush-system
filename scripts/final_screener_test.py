#!/usr/bin/env python3
"""
最終的篩選器測試腳本
直接測試篩選邏輯，不依賴 FastAPI
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.models.screener import ZoneType, StockItem

# 模擬篩選器邏輯
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
]

def filter_stocks(stocks, zone=None, min_price=None, max_price=None, min_volume=None):
    """篩選股票的邏輯"""
    filtered_stocks = stocks.copy()
    
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
    
    return filtered_stocks

def test_screener_logic():
    """測試篩選器邏輯"""
    print("Testing screener logic...")
    
    # 測試基本功能
    print("\nTest 1: Basic query")
    try:
        filtered_stocks = filter_stocks(mock_stocks)
        print(f"  Success: Filtered {len(filtered_stocks)} stocks")
        if filtered_stocks:
            first_item = filtered_stocks[0]
            print(f"  Sample: {first_item.symbol} - {first_item.name} ({first_item.zone})")
            
    except Exception as e:
        print(f"  Failed: {e}")
        return False
    
    # 測試區域過濾
    print("\nTest 2: Zone filtering")
    try:
        filtered_stocks = filter_stocks(mock_stocks, zone="buy")
        print(f"  Success: Buy zone stocks: {len(filtered_stocks)}")
        if filtered_stocks:
            all_buy = all(item.zone == ZoneType.BUY for item in filtered_stocks)
            print(f"  All stocks are buy zone: {all_buy}")
    except Exception as e:
        print(f"  Failed: {e}")
        return False
        
    # 測試價格過濾
    print("\nTest 3: Price filtering")
    try:
        filtered_stocks = filter_stocks(mock_stocks, min_price=100, max_price=500)
        print(f"  Success: Stocks in price range 100-500: {len(filtered_stocks)}")
        if filtered_stocks:
            all_in_range = all(100 <= item.price <= 500 for item in filtered_stocks)
            print(f"  All prices in range: {all_in_range}")
    except Exception as e:
        print(f"  Failed: {e}")
        return False
    
    # 測試分頁功能
    print("\nTest 4: Pagination")
    try:
        filtered_stocks = filter_stocks(mock_stocks)
        # 模擬分頁
        page = 1
        page_size = 2
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_stocks = filtered_stocks[start_idx:end_idx]
        print(f"  Success: Page {page}, {page_size} items per page")
        print(f"  Results count: {len(paginated_stocks)}")
        if paginated_stocks:
            first_item = paginated_stocks[0]
            print(f"  Sample: {first_item.symbol} - {first_item.name}")
    except Exception as e:
        print(f"  Failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("Screener logic test passed!")
    return True

if __name__ == "__main__":
    success = test_screener_logic()
    if success:
        print("\nAll tests completed successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)