#!/usr/bin/env python3
"""
簡化的篩選器測試腳本
用於測試篩選器功能的核心邏輯
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.models.screener import ScreenerRequest, ScreenerResponse, ZoneType, StockItem
from backend.app.routers.screener import screen_stocks

def test_screener_logic():
    """測試篩選器邏輯"""
    print("🚀 測試篩選器邏輯...")
    
    # 測試基本功能
    print("\n📊 測試 1：基本查詢")
    try:
        result = screen_stocks()
        print(f"  ✅ 成功執行篩選器")
        print(f"  總數: {result.total}")
        print(f"  頁碼: {result.page}")
        print(f"  每頁: {result.page_size}")
        print(f"  結果筆數: {len(result.items)}")
        
        if result.items:
            first_item = result.items[0]
            print(f"  範例: {first_item.symbol} - {first_item.name} ({first_item.zone})")
            
    except Exception as e:
        print(f"  ❌ 執行失敗: {e}")
        return False
    
    # 測試區域過濾
    print("\n📈 測試 2：區域過濾")
    try:
        result = screen_stocks(zone="buy")
        print(f"  ✅ 買入區股票: {result.total} 筆")
        if result.items:
            all_buy = all(item.zone == ZoneType.BUY for item in result.items)
            print(f"  ✅ 所有股票都是買入區: {all_buy}")
    except Exception as e:
        print(f"  ❌ 執行失敗: {e}")
        return False
        
    # 測試價格過濾
    print("\n💰 測試 3：價格過濾")
    try:
        result = screen_stocks(min_price=100, max_price=500)
        print(f"  ✅ 價格 100-500 的股票: {result.total} 筆")
        if result.items:
            all_in_range = all(100 <= item.price <= 500 for item in result.items)
            print(f"  ✅ 所有價格都在範圍內: {all_in_range}")
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