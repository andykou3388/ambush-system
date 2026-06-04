"""
任務模組初始化
用於註冊所有 Celery 任務
"""
# 導入所有任務模組以確保被註冊
from . import oneclick_init_task
from . import stock_fundamental_tasks
from . import minute_data_tasks
from . import weekly_tasks