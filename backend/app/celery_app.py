from celery import Celery

# 使用環境變數配置 Redis 連接
# 在 Docker 環境中，Redis 服務名稱為 "redis"
redis_url = "redis://redis:6379/0"

# 創建 Celery 實例
celery_app = Celery(
    "ambush_system",
    broker=redis_url,
    backend=redis_url,  # 使用 Redis 作為結果後端
    include=['app.tasks.example_task']  # 直接指定任務模組
)

# 配置 Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
