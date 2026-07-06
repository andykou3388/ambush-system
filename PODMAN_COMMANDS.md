# Ambush System - Podman Compose 完整指令清單

## 📌 服務管理命令

### 啟動/停止服務

```bash
# 啟動所有服務（後台運行）
podman compose up -d

# 停止所有服務
podman compose down

# 重啟所有服務
podman compose restart

# 查看服務狀態
podman compose ps

# 刪除容器並清理數據
podman compose down -v
```

### 日誌查看

```bash
# 查看所有服務日誌
podman compose logs

# 查看特定服務日誌
podman compose logs backend
podman compose logs db
podman compose logs redis
podman compose logs celery_worker
podman compose logs celery_beat

# 實時追蹤日誌
podman compose logs -f backend
podman compose logs -f celery_worker
```

---

## 🔧 進入容器執行命令

### 進入 Shell

```bash
# 進入 backend 容器 bash
podman compose exec backend bash

# 進入 db 容器
podman compose exec db bash

# 進入 redis 容器
podman compose exec redis redis-cli
```

---

## 🗄️ 資料庫操作

### PostgreSQL 連接

```bash
# 進入 psql
podman compose exec db psql -U dev_user -d ambush_dev

# 查看表列表
podman compose exec db psql -U dev_user -d ambush_dev -c "\dt"

# 查詢股票池
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT * FROM stock_pool;"

# 查詢最新信號
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT * FROM stock_signal_log ORDER BY trade_date DESC LIMIT 10;"

# 清空數據庫（警告：會刪除所有數據！）
podman compose exec db psql -U dev_user -d ambush_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO dev_user;"
```

### 備份與還原

```bash
# 備份數據庫到本地
podman compose exec db pg_dump -U dev_user ambush_dev > db_backup.sql

# 從本地恢復數據庫
podman compose exec db psql -U dev_user ambush_dev < db_backup.sql
```

---

## ⏰ Celery 任務執行

### 查看註冊的任務

```bash
# 查看 Celery 註冊的所有任務
podman compose exec backend celery -A app.celery_app inspect registered

# 查看當前運行的 worker
podman compose exec backend celery -A app.celery_app inspect active

# 查看 worker 統計信息
podman compose exec backend celery -A app.celery_app inspect stats
```

### 手動執行單一任務

```bash
# 進入 backend 容器
podman compose exec backend bash

# 1. 獲取基本面數據（測試用 3 檔股票）
python -c "from app.tasks.stock_fundamental_tasks import fetch_stock_fundamentals; result = fetch_stock_fundamentals(['2330.TW']); print(result)"

# 2. 每日分鐘線校驗
python -c "from app.tasks.minute_data_tasks import daily_minute_validation; result = daily_minute_validation(); print(result)"

# 3. 計算週線技術指標
python -c "from app.tasks.weekly_tasks import calculate_weekly_indicators; result = calculate_weekly_indicators('HK'); print(result)"

# 4. 執行規則引擎
python -c "from app.tasks.weekly_tasks import run_weekly_rule_engine; result = run_weekly_rule_engine('HK'); print(result)"

# 5. 發送每週通知
python -c "from app.tasks.weekly_tasks import send_weekly_notifications; result = send_weekly_notifications('HK'); print(result)"

# 6. 獲取盤中分鐘線數據
python -c "from app.tasks.minute_data_tasks import fetch_intraday_minute_data; result = fetch_intraday_minute_data(); print(result)"

# 7. 檢查止損條件
python -c "from app.tasks.minute_data_tasks import check_all_stop_loss; result = check_all_stop_loss(); print(result)"

# 8. 清理舊數據
python -c "from app.tasks.minute_data_tasks import cleanup_old_minute_data; result = cleanup_old_minute_data(30); print(result)"

# 9. 一次性初始化全部數據
python -c "from app.tasks.oneclick_init_task import oneclick_init_data; result = oneclick_init_data(); print(result)"
```

### 使用 Celery 命令執行任務

```bash
# 進入 backend 容器
podman compose exec backend bash

# 通過 Celery 執行基本面任務
celery -A app.celery_app call app.tasks.stock_fundamental_tasks.fetch_stock_fundamentals('[\"2330.TW\"]')

# 通過 Celery 執行週線指標計算
celery -A app.celery_app call app.tasks.weekly_tasks.calculate_weekly_indicators('HK')

# 通過 Celery 執行規則引擎
celery -A app.celery_app call app.tasks.weekly_tasks.run_weekly_rule_engine('HK')
```

---

## 🚀 啟動 Celery Worker

### 啟動 Worker（不同佇列）

```bash
# 進入 backend 容器
podman compose exec backend bash

# 啟動基本面隊列 worker
celery -A app.celery_app worker -Q fundamental -l info

# 啟動週線隊列 worker
celery -A app.celery_app worker -Q weekly -l info

# 啟動分鐘數據隊列 worker
celery -A app.celery_app worker -Q minute_data -l info

# 啟動維護隊列 worker
celery -A app.celery_app worker -Q maintenance -l info

# 啟動通知隊列 worker
celery -A app.celery_app worker -Q notification -l info
```

### 啟動 Celery Beat（排程調度）

```bash
# 進入 backend 容器
podman compose exec backend bash

# 啟動 Beat 排程器
celery -A app.celery_app beat --loglevel=info --scheduler celery.schedules:scheduler

# 或多行啟動所有服務
podman compose up -d celery_worker celery_beat
```

---

## 🧪 快速測試指令集

### 測試腳本一：基礎數據驗證

```bash
#!/bin/bash
# test_basic.sh

echo "=== 測試基礎數據 ==="

# 測試基本面數據
echo "1. 測試基本面數據..."
podman compose exec backend python -c "from app.tasks.stock_fundamental_tasks import fetch_stock_fundamentals; result = fetch_stock_fundamentals(['2330.TW']); print(result)"

# 測試每日校驗
echo "2. 測試每日校驗..."
podman compose exec backend python -c "from app.tasks.minute_data_tasks import daily_minute_validation; result = daily_minute_validation(); print(result)"

echo "基本測試完成"
```

### 測試腳本二：週線數據完整流程

```bash
#!/bin/bash
# test_weekly.sh

echo "=== 測試週線數據完整流程 ==="

# 1. 計算技術指標
echo "1. 計算技術指標..."
podman compose exec backend python -c "from app.tasks.weekly_tasks import calculate_weekly_indicators; result = calculate_weekly_indicators('HK'); print(result)"

# 2. 執行規則引擎
echo "2. 執行規則引擎..."
podman compose exec backend python -c "from app.tasks.weekly_tasks import run_weekly_rule_engine; result = run_weekly_rule_engine('HK'); print(result)"

# 3. 發送通知
echo "3. 發送通知..."
podman compose exec backend python -c "from app.tasks.weekly_tasks import send_weekly_notifications; result = send_weekly_notifications('HK'); print(result)"

echo "週線測試完成"
```

### 測試腳本三：止損系統驗證

```bash
#!/bin/bash
# test_stop_loss.sh

echo "=== 測試止損系統 ==="

# 獲取分鐘線數據
echo "1. 獲取分鐘線數據..."
podman compose exec backend python -c "from app.tasks.minute_data_tasks import fetch_intraday_minute_data; result = fetch_intraday_minute_data(); print(result)"

# 檢查止損條件
echo "2. 檢查止損條件..."
podman compose exec backend python -c "from app.tasks.minute_data_tasks import check_all_stop_loss; result = check_all_stop_loss(); print(result)"

echo "止損系統測試完成"
```

---

## 📊 監控視圖

### 查看數據庫統計

```bash
# 查看股票池數量
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT COUNT(*) as total_stocks FROM stock_pool;"

# 查看信號統計
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT zone, COUNT(*) as count FROM stock_signal_log GROUP BY zone;"

# 查看活躍部位
podman compose exec db psql -U dev_user -d ambush_dev -c "SELECT COUNT(*) as active_positions FROM ram_stop_loss WHERE is_active = true;"
```

### 查看 Redis 數據

```bash
# 進入 redis
podman compose exec redis redis-cli

# 查看所有 key
KEYS *

# 查看特定 key 的值
GET your_key_name

# 查看庫存大小
INFO keyspace
```

---

## 🔄 常見故障排除

### 重置整個系統

```bash
# 完全停止並清除所有數據
podman compose down -v

# 重新創建所有容器
podman compose up -d

# 等待服務就緒
sleep 10

# 重新初始化數據
podman compose exec backend python -c "from app.tasks.oneclick_init_task import oneclick_init_data; result = oneclick_init_data(); print(result)"
```

### 重置資料庫

```bash
# 重置 PostgreSQL 資料庫
podman compose exec db psql -U dev_user -d ambush_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO dev_user;"

# 重新初始化
podman compose exec backend python -c "from app.tasks.oneclick_init_task import oneclick_init_data; result = oneclick_init_data(); print(result)"
```

---

## 📋 預設環境變數

```bash
BACKEND_PORT=8000
FRONTEND_PORT=3000
DB_PORT=5432
REDIS_PORT=6379

DATABASE_URL=postgresql://dev_user:dev_pass_123@db:5432/ambush_dev
REDIS_URL=redis://redis:6379
```

---

## 📅 定時任務時間表

| 任務 | 頻率 | 時間 | 描述 |
|------|------|------|------|
| fetch-daily-fundamentals | 週一至五 | 14:00 | 獲取基本面數據 |
| daily-minute-validation | 週一至五 | 15:00 | 每日校驗 |
| intraday-minute-data-fetch | 每分鐘 | 持續 | 獲取分鐘線數據 |
| intraday-stop-loss-check | 每分鐘 | 持續 | 止損檢查 |
| weekly-calculate-indicators | 週五 | 14:30 | 計算週線指標 |
| weekly-run-rule-engine | 週五 | 15:00 | 執行規則引擎 |
| weekly-send-notifications | 週五 | 16:00 | 發送通知 |
| cleanup-old-minute-data | 週日 | 03:00 | 清理舊數據 |

---

生成時間：2026-07-06