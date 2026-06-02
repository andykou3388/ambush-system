#!/usr/bin/env python3
"""
測試股票基本面數據獲取功能
使用方式：
    python scripts/test_fundamental_fetch.py
"""
import sys
import os
import json

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tasks.stock_fundamental_tasks import (
    fetch_stock_fundamentals,
    fetch_single_stock_fundamental,
)


def test_single_stock():
    """測試獲取單一股票基本面數據"""
    print("=" * 60)
    print("測試 1: 獲取單一股票基本面數據")
    print("=" * 60)
    
    symbol = "0005.HK"  # 匯豐控股
    print(f"正在獲取 {symbol} 的基本面數據...")
    
    try:
        result = fetch_single_stock_fundamental.delay(symbol)
        print(f"任務已啟動，ID: {result.id}")
        
        # 等待結果
        task_result = result.get(timeout=30)
        print(f"✅ 成功獲取 {symbol} 的數據:")
        print(json.dumps(task_result, indent=2, default=str))
        return True
    except Exception as e:
        print(f"❌ 獲取 {symbol} 數據失敗: {e}")
        return False


def test_batch_stocks():
    """測試批量獲取股票基本面數據"""
    print("\n" + "=" * 60)
    print("測試 2: 批量獲取股票基本面數據")
    print("=" * 60)
    
    # 測試用的小批量股票
    test_symbols = ["0005.HK", "9988.HK", "0700.HK"]
    print(f"正在獲取 {len(test_symbols)} 隻股票的基本面數據: {test_symbols}")
    
    try:
        result = fetch_stock_fundamentals.delay(test_symbols)
        print(f"任務已啟動，ID: {result.id}")
        
        # 等待結果
        task_result = result.get(timeout=120)
        print(f"✅ 批量獲取完成:")
        print(json.dumps(task_result, indent=2, default=str))
        return True
    except Exception as e:
        print(f"❌ 批量獲取失敗: {e}")
        return False


def test_hsi_constituents():
    """測試獲取恒生指數成份股基本面數據"""
    print("\n" + "=" * 60)
    print("測試 3: 獲取恒生指數成份股基本面數據")
    print("=" * 60)
    
    hsi_stocks = [
        "0005.HK", "9988.HK", "0700.HK", "1299.HK", "0939.HK",
        "1398.HK", "1810.HK", "0941.HK", "0388.HK", "0883.HK",
        "3690.HK", "2318.HK", "1211.HK", "3988.HK", "0981.HK",
        "9999.HK", "0857.HK", "2899.HK", "2628.HK", "0016.HK",
        "9618.HK", "3968.HK", "0001.HK", "2388.HK", "0669.HK",
        "1088.HK", "0175.HK", "1801.HK", "9888.HK", "1024.HK",
    ]
    
    print(f"正在獲取 {len(hsi_stocks)} 隻恒生成份股的基本面數據...")
    print("注意: 這可能需要幾分鐘時間")
    
    try:
        result = fetch_stock_fundamentals.delay(hsi_stocks)
        print(f"任務已啟動，ID: {result.id}")
        
        # 等待結果（可能需要較長時間）
        task_result = result.get(timeout=600)
        print(f"✅ 恒生成份股數據獲取完成:")
        print(json.dumps(task_result, indent=2, default=str))
        return True
    except Exception as e:
        print(f"❌ 恒生成份股數據獲取失敗: {e}")
        return False


if __name__ == "__main__":
    print("🚀 開始測試股票基本面數據獲取功能")
    print()
    
    # 執行測試
    test_single_stock()
    test_batch_stocks()
    
    # 詢問是否要測試完整的恒生成份股
    print("\n" + "=" * 60)
    print("提示: 測試 3 (恒生成份股) 需要較長時間")
    print("可以通過 API 端點手動觸發:")
    print("  POST /api/v1/stock-fundamental/fetch-batch")
    print("  Body: {\"stock_codes\": [\"0005.HK\", \"9988.HK\", ...]}")
    print("=" * 60)
