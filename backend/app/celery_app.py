"""
Celery 應用配置
V2.0 優化：加入拉姆止損分鐘線任務與每日校驗任務
"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "ambush_system",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Taipei",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,
)

# ==========================================
# 定時任務配置
# ==========================================
celery_app.conf.beat_schedule = {
    # ========== 每日任務 ==========
    "fetch-daily-fundamentals": {
        "task": "app.tasks.stock_fundamental_tasks.fetch_stock_fundamentals",
        "schedule": crontab(hour="14", minute="0", day_of_week="1-5"),
        "args": [["2330.TW", "2317.TW", "2454.TW"]],  # 實際使用時從 DB 讀取
        "options": {"queue": "fundamental"},
    },
    "daily-minute-data-validation": {
        "task": "app.tasks.minute_data_tasks.daily_minute_validation",
        "schedule": crontab(hour="15", minute="0", day_of_week="1-5"),
        "options": {"queue": "minute_data"},
    },
    "cleanup-old-minute-data": {
        "task": "app.tasks.minute_data_tasks.cleanup_old_minute_data",
        "schedule": crontab(hour="3", minute="0", day_of_week="0"),
        "options": {"queue": "maintenance"},
    },
    # ========== 每週任務（週五） ==========
    "weekly-run-rule-engine": {
        "task": "app.tasks.weekly_tasks.run_weekly_rule_engine",
        "schedule": crontab(hour="15", minute="0", day_of_week="5"),
        "options": {"queue": "weekly"},
    },
    "weekly-send-notifications": {
        "task": "app.tasks.weekly_tasks.send_weekly_notifications",
        "schedule": crontab(hour="16", minute="0", day_of_week="5"),
        "options": {"queue": "notification"},
    },
    # ========== 盤中分鐘任務（每分鐘執行） ==========
    "intraday-minute-data-fetch": {
        "task": "app.tasks.minute_data_tasks.fetch_intraday_minute_data",
        "schedule": crontab(minute="*"),
        "options": {"queue": "minute_data"},
    },
    "intraday-stop-loss-check": {
        "task": "app.tasks.minute_data_tasks.check_all_stop_loss",
        "schedule": crontab(minute="*"),
        "options": {"queue": "minute_data"},
    },
}

# 自動發現任務
celery_app.autodiscover_tasks(["app.tasks"])

# ==========================================
# 手動導入任務模組（確保任務被註冊）
# ==========================================
import app.tasks.stock_fundamental_tasks
import app.tasks.minute_data_tasks
import app.tasks.weekly_tasks
import app.tasks.oneclick_init_task
