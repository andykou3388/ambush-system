from celery import Celery
from celery.schedules import crontab

# 使用環境變數配置 Redis 連接
# 在 Docker 環境中，Redis 服務名稱為 "redis"
redis_url = "redis://redis:6379/0"

# 創建 Celery 實例
celery_app = Celery(
    "ambush_system",
    broker=redis_url,
    backend=redis_url,  # 使用 Redis 作為結果後端
    include=[
        'app.tasks.example_task',
        'app.tasks.stock_fundamental_tasks',
        'app.service_task',
    ]  # 包含任務模組
)

# 配置 Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=False,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分鐘超時
    task_soft_time_limit=25 * 60,  # 25分鐘軟超時
)

# 定時任務配置
celery_app.conf.beat_schedule = {
    # 週五台北時間 13:30 執行（台股收盤後）
    'run-weekly-analysis-tw': {
        'task': 'app.service_task.run_weekly_analysis',
        'schedule': crontab(
            hour=13, minute=30, 
            day_of_week=5  # 週五
        ),
        'kwargs': {'market': 'TW'}
    },
    # 週五台北時間 16:00 執行（美股收盤後）
    'run-weekly-analysis-us': {
        'task': 'app.service_task.run_weekly_analysis',
        'schedule': crontab(
            hour=16, minute=0, 
            day_of_week=5  # 週五
        ),
        'kwargs': {'market': 'US'}
    },
}
