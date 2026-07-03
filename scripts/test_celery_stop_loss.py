#!/usr/bin/env python3
"""
Celery 止損檢查任務測試腳本
用於驗證 RAM-13 功能是否正常運作
"""
import sys
import time
from datetime import datetime

# 添加專案根目錄到 Python path
sys.path.insert(0, '.')

from app.celery_app import celery_app
from app.tasks.minute_data_tasks import check_all_stop_loss, fetch_intraday_minute_data
from app.database import SessionLocal
from app.models.ram_stop_loss import RamStopLoss


def test_celery_connection():
    """測試 Celery 連接是否成功"""
    print("=" * 60)
    print("步驟 1: 測試 Celery 連接")
    print("=" * 60)
    
    try:
        # 測試 Redis 連接
        result = celery_app.control.ping(timeout=5)
        print(f"✅ Celery Worker 回應：{result}")
        
        # 列出所有已註冊的任務
        registered_tasks = list(celery_app.tasks.keys())
        stop_loss_tasks = [t for t in registered_tasks if 'stop_loss' in t or 'minute' in t]
        print(f"\n相關 Tasks 已註冊 ({len(stop_loss_tasks)}個):")
        for task in stop_loss_tasks:
            print(f"  - {task}")
        
        return True
    except Exception as e:
        print(f"❌ Celery 連接失敗：{e}")
        return False


def test_check_task_directly():
    """直接執行止損檢查任務（非 Celery）"""
    print("\n" + "=" * 60)
    print("步驟 2: 直接執行止損檢查任務")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        try:
            # 查詢活躍部位
            active_positions = db.query(RamStopLoss).filter(
                RamStopLoss.is_active == True
            ).all()
            
            print(f"\n找到 {len(active_positions)} 個活躍部位:")
            
            for position in active_positions[:5]:  # 只顯示前 5 個
                print(f"  - {position.code}: "
                      f"買入價={float(position.buy_price) if position.buy_price else 'N/A'}, "
                      f"當前價={float(position.current_price)}, "
                      f"止損價={float(position.stop_loss_price)}, "
                      f"最高價={float(position.highest_price)}, "
                      f"回撤={float(position.drawdown_pct):.2f}%")
            
            if len(active_positions) > 5:
                print(f"  ... 還有 {len(active_positions) - 5} 個部位")
            
            # 執行止損檢查
            print("\n執行止損檢查...")
            from app.engine.ram_stop_loss import RamStopLossEngine
            engine = RamStopLossEngine()
            
            triggered_count = 0
            for position in active_positions:
                result = engine.check_stop_loss(position.code)
                if result.get("status") == "triggered":
                    triggered_count += 1
                    print(f"  ⚠️ {position.code} 觸發止損！")
            
            print(f"\n✅ 檢查完成：{triggered_count} 個部位觸發止損")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 止損檢查失敗：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_task_execution():
    """通過 Celery 執行任務"""
    print("\n" + "=" * 60)
    print("步驟 3: 透過 Celery 執行止損檢查任務")
    print("=" * 60)
    
    try:
        # 執行 Celery 任務
        print("提交任務到 Celery Worker...")
        result = check_all_stop_loss.delay()
        
        # 等待結果（最多 30 秒）
        print("等待任務執行中...")
        final_result = result.get(timeout=30)
        
        print(f"\n✅ 任務執行結果:")
        print(f"  狀態：{final_result.get('status')}")
        print(f"  總計：{final_result.get('total', 'N/A')} 個部位")
        print(f"  觸發：{final_result.get('triggered', 0)} 個")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery 任務執行失敗：{e}")
        print("這可能表示 Celery Worker 尚未啟動，請先執行 podman compose up -d")
        return False


def show_beat_schedule():
    """顯示定時任務配置"""
    print("\n" + "=" * 60)
    print("步驟 4: Celery Beat 定時任務配置")
    print("=" * 60)
    
    beat_schedule = celery_app.conf.beat_schedule
    
    print(f"\n共配置 {len(beat_schedule)} 個定時任務:\n")
    
    for name, config in beat_schedule.items():
        schedule = config.get('schedule', 'N/A')
        task = config.get('task', 'N/A')
        options = config.get('options', {})
        queue = options.get('queue', 'default')
        
        # 格式化時間表
        if hasattr(schedule, 'hour'):
            time_str = f"{schedule.hour}:{schedule.minute}"
        else:
            time_str = str(schedule)
        
        print(f"  {time_str} | {queue:15s} | {name}")
        print(f"         → 任務：{task}")


def main():
    """主測試流程"""
    print("\n" + "#" * 60)
    print("# RAM-13 Celery 止損檢查任務測試")
    print("# 開始時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("#" * 60)
    
    results = []
    
    # 步驟 1: 測試 Celery 連接
    results.append(("Celery 連接", test_celery_connection()))
    
    # 步驟 2: 直接執行任務
    results.append(("直接執行", test_check_task_directly()))
    
    # 步驟 3: Celery 任務執行
    results.append(("Celery 任務", test_celery_task_execution()))
    
    # 步驟 4: 顯示 Beat 配置
    show_beat_schedule()
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有測試通過！RAM-13 功能正常運作")
    else:
        print("⚠️ 部分測試失敗，請檢查以下項目:")
        print("  1. 確認 Redis 容器正在運行：podman ps | grep redis")
        print("  2. 確認 Celery Worker 正在運行：podman ps | grep worker")
        print("  3. 確認 Celery Beat 正在運行：podman ps | grep beat")
        print("  4. 查看日誌：podman logs celery_worker")
        print("  5. 查看日誌：podman logs celery_beat")
    print("=" * 60)
    
    # 結束時間
    print(f"\n結束時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())