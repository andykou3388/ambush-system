"""
測試盤中分鐘線數據獲取任務
使用方法一：直接調用實現函數
"""
import sys
import os

# 檢測是否在 Docker/Podman 容器內運行
if os.path.exists('/app'):
    # 容器環境：backend 目錄在 /app
    sys.path.insert(0, '/app')
else:
    # 本地環境：相對於 scripts 目錄
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.tasks.minute_data_tasks import _fetch_intraday_minute_data_impl


def main():
    print("=" * 60)
    print("測試盤中分鐘線數據獲取任務")
    print("=" * 60)
    
    # 直接調用實現函數
    result = _fetch_intraday_minute_data_impl()
    
    print("\n" + "=" * 60)
    print("執行結果")
    print("=" * 60)
    print(f"狀態：{result.get('status')}")
    print(f"總數：{result.get('total')}")
    
    if 'results' in result:
        print(f"\n結果列表:")
        for r in result['results']:
            print(f"  - {r['code']}: {r['status']}")
    
    if result.get('status') == 'no_active_positions':
        print("\n提示：資料庫中沒有活躍部位，請先插入測試數據")
    
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    main()