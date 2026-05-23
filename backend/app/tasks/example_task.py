"""
範例 Celery 任務
這個文件展示了如何創建可被 Celery Worker 執行的任務
"""

from celery import current_task
from ..celery_app import celery_app

@celery_app.task(bind=True)
def example_task(self, name: str, count: int = 1):
    """
    一個簡單的範例任務
    
    Args:
        name: 任務名稱
        count: 迴圈次數
        
    Returns:
        任務結果字串
    """
    try:
        # 模擬工作
        print(f"開始執行任務: {name}")
        
        # 模擬處理過程
        for i in range(count):
            print(f"處理項目 {i+1}/{count}")
            # 模擬耗時操作
            import time
            time.sleep(0.1)
        
        print("任務完成")
        return f"任務 '{name}' 完成，處理了 {count} 個項目"
        
    except Exception as exc:
        print(f"任務失敗: {exc}")
        raise exc

# 額外提供一個不需要返回結果的任務版本
@celery_app.task
def simple_task(message: str):
    """
    簡單任務 - 不需要結果回傳
    """
    try:
        print(f"執行簡單任務: {message}")
        # 模擬工作
        import time
        time.sleep(1)
        print("簡單任務完成")
        return f"簡單任務 '{message}' 完成"
    except Exception as exc:
        print(f"簡單任務失敗: {exc}")
        raise exc
