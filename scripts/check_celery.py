#!/usr/bin/env python3
"""
Celery 任務驗證腳本
用於測試和驗證 Celery 定時任務功能
"""

import sys
import os

# 將當前目錄添加到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

try:
    # 導入 Celery 應用和任務
    from app.celery_app import celery_app
    from app.service_task import run_weekly_analysis
    
    def test_celery_connection():
        """測試 Celery 連接"""
        print("🚀 測試 Celery 連接...")
        print("=" * 50)
        
        try:
            # 測試 1：檢查 Redis 連接
            print("\n📊 測試 1：檢查 Celery 連接")
            conn = celery_app.connection()
            conn.connect()
            print("  ✅ Redis 連接成功")
            conn.close()
            
            # 測試 2：獲取 Celery 狀態
            print("\n📋 測試 2：獲取 Celery 狀態")
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            if active_tasks:
                print(f"  📋 活躍任務: {len(active_tasks)} 個")
                for worker, tasks in active_tasks.items():
                    print(f"    {worker}: {len(tasks)} 個任務")
            else:
                print("  📋 當前無活躍任務")
                
            # 測試 3：獲取定時任務配置
            print("\n⏰ 測試 3：檢查定時任務配置")
            if hasattr(celery_app.conf, 'beat_schedule') and celery_app.conf.beat_schedule:
                print("  📋 定時任務配置:")
                for task_name, task_config in celery_app.conf.beat_schedule.items():
                    print(f"    - {task_name}: {task_config['task']}")
                    schedule = task_config.get('schedule', 'N/A')
                    print(f"      調度: {schedule}")
            else:
                print("  ⚠️  無定時任務配置")
                
            return True
            
        except Exception as e:
            print(f"  ❌ 連接測試失敗: {e}")
            return False

    def test_manual_task_execution():
        """手動觸發任務測試"""
        print("\n📈 測試 4：手動觸發分析任務")
        
        try:
            # 測試台股任務
            print("  執行台股任務...")
            result_tw = run_weekly_analysis.delay(market='TW')
            print(f"  台股任務 ID: {result_tw.id}")
            print(f"  任務狀態: {result_tw.status}")
            
            # 測試美股任務
            print("  執行美股任務...")
            result_us = run_weekly_analysis.delay(market='US')
            print(f"  美股任務 ID: {result_us.id}")
            print(f"  任務狀態: {result_us.status}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 任務執行測試失敗: {e}")
            return False

    def test_task_functions():
        """測試任務相關函數"""
        print("\n🔧 測試 5：任務函數測試")
        
        try:
            # 測試股票列表獲取
            from app.tasks_helper import get_stock_list
            tw_stocks = get_stock_list('TW')
            us_stocks = get_stock_list('US')
            print(f"  📋 台股股票數量: {len(tw_stocks)}")
            print(f"  📋 美股股票數量: {len(us_stocks)}")
            
            # 測試其他函數
            from app.tasks_helper import calculate_indicators, classify_stock
            indicators = calculate_indicators('2330.TW')
            classification = classify_stock('2330.TW')
            print(f"  📊 技術指標計算成功")
            print(f"  📊 三區分類成功")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 函數測試失敗: {e}")
            return False

    def main():
        """主函數"""
        print("🔍 Celery 任務驗證腳本")
        print("=" * 50)
        
        success = True
        
        # 執行所有測試
        success &= test_celery_connection()
        success &= test_manual_task_execution()
        success &= test_task_functions()
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 所有測試通過！Celery 配置正常")
            return 0
        else:
            print("❌ 部分測試失敗")
            return 1

    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"模塊導入錯誤: {e}")
    print("請確保項目結構正確且 Python 路徑設置正確")
    sys.exit(1)
