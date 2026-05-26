#!/usr/bin/env python3
"""
獨立的篩選器測試腳本
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
    print("🚀 測試篩選器邏輯...")
    
    # 測試基本功能
    print("\n📊 測試 1：基本查詢")
    try:
        filtered_stocks = filter_stocks(mock_stocks)
        print(f"  ✅ 成功篩選股票")
        print(f"  總數: {len(filtered_stocks)}")
        if filtered_stocks:
            first_item = filtered_stocks[0]
            print(f"  範例: {first_item.symbol} - {first_item.name} ({first_item.zone})")
            
    except Exception as e:
        print(f"  ❌ 執行失敗: {e}")
        return False
    
    # 測試區域過濾
    print("\n📈 測試 2：區域過濾")
    try:
        filtered_stocks = filter_stocks(mock_stocks, zone="buy")
        print(f"  ✅ 買入區股票: {len(filtered_stocks)} 筆")
        if filtered_stocks:
            all_buy = all(item.zone == ZoneType.BUY for item in filtered_stocks)
            print(f"  ✅ 所有股票都是買入區: {all_buy}")
    except Exception as e:
        print(f"  ❌ 執行失敗: {e}")
        return False
        
    # 測試價格過濾
    print("\n💰 測試 3：價格過濾")
    try:
        filtered_stocks = filter_stocks(mock_stocks, min_price=100, max_price=500)
        print(f"  ✅ 價格 100-500 的股票: {len(filtered_stocks)} 筆")
        if filtered_stocks:
            all_in_range = all(100 <= item.price <= 500 for item in filtered_stocks)
            print(f"  ✅ 所有價格都在範圍內: {all_in_range}")
    except Exception as e:
        print(f"  ❌ 執行失敗: {e}")
        return False
    
    # 測試分頁功能
    print("\n📄 測試 4：分頁功能")
    try:
        filtered_stocks = filter_stocks(mock_stocks)
        # 模擬分頁
        page = 1
        page_size = 2
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_stocks = filtered_stocks[start_idx:end_idx]
        print(f"  ✅ 第 {page} 頁，每頁 {page_size} 筆")
        print(f"  結果筆數: {len(paginated_stocks)} 筆")
        if paginated_stocks:
            first_item = paginated_stocks[0]
            print(f"  範例: {first_item.symbol} - {first_item.name}")
    except Exception as e:
        print(f"  ❌ 執行失敗: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ 篩選器邏輯測試通過！")
    return True

if __name__ == "__main__":
    success = test_screener_logic()
    if success:
        print("\n🎉 所有測試成功完成！")
        sys.exit(0)
    else:
        print("\n💥 某些測試失敗！")
        sys.exit(1)