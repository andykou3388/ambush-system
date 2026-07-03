# RAM-13: Celery 止損檢查任務串接文件

## 任務概述

**任務 ID**: RAM-13  
**任務名稱**: Celery 止損檢查任務串接  
**完成日期**: $(date '+%Y-%m-%d')  

本任務旨在整合 Celery 後台任務系統，實現自動化的止損監控功能。

---

## 新增檔案清單

| 檔案路徑 | 說明 | 狀態 |
|---------|------|------|
| `docker-compose.yml` (修改) | 新增 Celery Beat 服務定義 | ✅ 已完成 |
| `scripts/test_celery_stop_loss.py` | 止損檢查任務測試腳本 | ✅ 已完成 |
| `scripts/start_celery_services.sh` | Celery 服務啟動腳本 | ✅ 已完成 |
| `docs/celery_stop_loss_task.md` | 任務實施文件 | ✅ 已完成 |

---

## 原有系統檢視

以下模組在任務前已存在並繼續運作：

### 核心組件

1. **Celery App 配置** (`backend/app/celery_app.py`)
   - Redis Broker: `redis://redis:6379/0`
   - Redis Backend: `redis://redis:6379/1`
   - 時區設定：Asia/Taipei
   - 任務超時：30 分鐘

2. **定時任務配置** (`backend/app/celery_app.py:32-77`)
   
   ```python
   celery_app.conf.beat_schedule = {
       # 每分鐘執行
       "intraday-stop-loss-check": {
           "task": "app.tasks.minute_data_tasks.check_all_stop_loss",
           "schedule": crontab(minute="*"),
       },
       # 每日校驗
       "daily-minute-data-validation": {
           "task": "app.tasks.minute_data_tasks.daily_minute_validation",
           "schedule": crontab(hour="15", minute="0", day_of_week="1-5"),
       },
       # 其他週期性任務...
   }
   ```

3. **止損檢查任務** (`backend/app/tasks/minute_data_tasks.py:87-129`)
   
   ```python
   @shared_task(bind=True, max_retries=1)
   def check_all_stop_loss(self):
       """盤中每分鐘檢查所有活躍部位是否觸發止損"""
   ```

4. **止損引擎** (`backend/app/engine/ram_stop_loss.py`)
   - `check_stop_loss()`: 單一股票止損檢查
   - `create_position()`: 建立止損部位
   - `activate_stop_loss()`: 啟用止損監控
   - `daily_validation()`: 每日數據校驗

5. **數據模型** (`backend/app/models/ram_stop_loss.py`)
   
   ```python
   class RamStopLoss(Base):
       __tablename__ = "ram_stop_loss"
       
       id, code, name, market
       status, buy_date, buy_price
       highest_price, current_price, lowest_price
       stop_loss_price, drawdown_pct
       is_triggered, triggered_at, is_active
       created_at, updated_at
   ```

---

## 本次新增內容

### 1. Celery Beat 容器定義

在 `docker-compose.yml` 中新增：

```yaml
celery_beat:
  build:
    context: ./backend
    dockerfile: Dockerfile
  env_file:
    - .env
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
    - DEBUG=${DEBUG:-true}
  volumes:
    - ./backend/app:/app/app
    - ./backend/engine:/app/app/engine
    - ./backend/classifier:/app/app/engine
    - /app/__pycache__
    - /app/.pytest_cache
  command: celery -A app.celery_app beat --loglevel=info --scheduler celery.schedules:scheduler
  depends_on:
    redis:
      condition: service_started
    celery_worker:
      condition: service_started
  networks:
    - ambush-network
```

---

### 2. 測試腳本 (`scripts/test_celery_stop_loss.py`)

#### 功能特點

- ✅ Celery Worker 連線測試
- ✅ 列出已註冊的 Tasks
- ✅ 直接執行止損檢查（非 Celery）
- ✅ 透過 Celery 執行任務
- ✅ 顯示定時任務配置

#### 使用方式

```bash
# 確保虛擬環境已激活
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate.bat  # Windows

# 執行測試
python scripts/test_celery_stop_loss.py
```

#### 預期輸出

```
#############################################################
# RAM-13 Celery 止損檢查任務測試
# 開始時間：2026-07-03 14:30:00
#############################################################

============================================================
步驟 1: 測試 Celery 連接
============================================================
✅ Celery Worker 回應：[{'received': '...', 'localtime': '...'}]

相關 Tasks 已註冊 (X 個):
  - app.tasks.minute_data_tasks.check_all_stop_loss
  - app.tasks.minute_data_tasks.fetch_intraday_minute_data
  ...
```

---

### 3. 啟動腳本 (`scripts/start_celery_services.sh`)

#### 功能特點

- ✅ 自動啟動 Redis 和 PostgreSQL
- ✅ 依序啟動 Celery Worker 和 Beat
- ✅ 容器狀態檢查
- ✅ 連線測試
- ✅ 日誌輸出

#### 使用方式

```bash
bash scripts/start_celery_services.sh
```

#### 自動化流程

```
┌─────────────────┐
│  步驟 1         │
│  Redis + DB     │
└────────┬────────┘
         │ (等待 10 秒)
         ▼
┌─────────────────┐
│  步驟 2         │
│  Celery Worker  │
└────────┬────────┘
         │ (等待 5 秒)
         ▼
┌─────────────────┐
│  步驟 3         │
│  Celery Beat    │
└────────┬────────┘
         │ (等待 5 秒)
         ▼
┌─────────────────┐
│  步驟 4-6       │
│  狀態檢查 &     │
│  日誌輸出       │
└─────────────────┘
```

---

## 執行流程圖

```
┌──────────────┐
│ Celery Beat  │  (每分鐘)
└──────┬───────┘
       │ crontab(minute="*")
       ▼
┌───────────────────┐
│ check_all_stop_   │
│ loss  task        │
└──────┬────────────┘
       │
       ▼
┌───────────────────┐
│ RamStopLossEngine │
│ .check_stop_loss  │
└──────┬────────────┘
       │
       ▼
┌───────────────────┐
│ 查詢最新分鐘線    │
│ 計算回撤比例      │
│ 檢查止損條件      │
└──────┬────────────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│ 未觸發      │  │ 已觸發      │
│ 更新數據    │  │ 標記為止損  │
│ 保持監控    │  │ 發送通知    │
└─────────────┘  └─────────────┘
```

---

## 部署注意事項

### 環境要求

| 項目 | 版本 | 必要性 |
|------|------|--------|
| Podman | >= 4.0 | 必需 |
| Redis | 6-alpine | 必需 |
| PostgreSQL | 13 | 必需 |
| Python | 3.10+ | 必需 |
| Celery | 5.2.7 | 必需 |

### 依賴服務

```
docker-compose.yml 服務依賴關係：

celery_beat → redis (started)
             → celery_worker (started)

celery_worker → db (healthy)
               → redis (started)
```

### 日誌位置

- **Worker 日誌**: `podman logs celery_worker`
- **Beat 日誌**: `podman logs celery_beat`
- **實時追蹤**: `podman logs -f celery_worker`

---

## 故障排除

### 問題 1: Celery Worker 無法連線

```bash
# 檢查 Redis 是否運行
podman ps | grep redis

# 測試 Redis 連線
podman exec -it redis redis-cli ping

# 重新啟動 Redis
podman compose restart redis
```

### 問題 2: Celery Beat 未觸發任務

```bash
# 查看 Beat 日誌
podman logs celery_beat

# 確認任務已註冊
podman exec celery_worker celery -A app.celery_app inspect registered

# 重啟 Beat
podman compose restart celery_beat
```

### 問題 3: 任務執行失敗

```bash
# 查看 Worker 錯誤日誌
podman logs celery_worker | grep ERROR

# 手動執行任務測試
cd backend
python -c "from app.tasks.minute_data_tasks import check_all_stop_loss; print(check_all_stop_loss.run())"
```

### 問題 4: 資料庫連線失敗

```bash
# 檢查資料庫狀態
podman ps | grep db

# 測試 PostgreSQL 連線
podman exec -it db psql -U dev_user -d ambush_dev -c "SELECT 1"
```

---

## 性能優化建議

### 1. 調整 Worker 數量

如需處理更多同時請求，可增加 Worker 實例：

```bash
podman-compose up -d --scale celery_worker=3
```

### 2. 調整預取數量

在 `celery_app.py` 中調整：

```python
celery_app.conf.update(
    worker_prefetch_multiplier=4,  # 預設為 1
)
```

### 3. 增加執行時間限制

對於大量數據處理任務：

```python
celery_app.conf.update(
    task_time_limit=60 * 60,  # 1 小時
)
```

---

## 監控與警報

### Prometheus 指標

Celery 自動暴露以下指標：

- `celery_task_runtime_sum`: 任務執行時間總和
- `celery_task_success_total`: 成功任務數
- `celery_task_failure_total`: 失敗任務數

访问 Grafana Dashboard (http://localhost:3001) 查看視覺化儀表板。

### 日誌分級

```
INFO: 一般執行日誌
WARNING: 警告事件（如價格異常）
ERROR: 錯誤事件
CRITICAL: 嚴重錯誤
```

---

## 維護計畫

### 每日維護

```bash
# 檢查服務狀態
podman ps | grep celery

# 查看昨日執行統計
podman logs celery_worker | grep "止損檢查完成"
```

### 每週維護

```bash
# 重啟 Celery 服務（可選）
podman compose restart celery_worker celery_beat

# 檢查日誌大小
du -sh /var/lib/docker/containers/*celery*
```

---

## 相關文件

| 文件 | 說明 |
|------|------|
| `docs/api_data_flow.md` | API 資料流程 |
| `docs/integration_plan.md` | 整合計畫 |
| `backend/app/celery_app.py` | Celery 配置 |
| `backend/app/tasks/minute_data_tasks.py` | 分鐘線任務 |
| `backend/app/engine/ram_stop_loss.py` | 止損引擎 |

---

## 變更記錄

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2026-07-03 | v1.0 | 初始實施，新增 Celery Beat 容器 |
| 2026-07-03 | v1.0 | 建立測試腳本與啟動腳本 |

---

**本文檔由 RAM-13 任務團隊維護**