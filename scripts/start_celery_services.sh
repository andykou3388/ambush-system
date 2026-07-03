#!/bin/bash
# RAM-13: Celery 止損檢查任務 - 啟動腳本
# 使用方式：bash scripts/start_celery_services.sh

set -e

echo "=============================================="
echo "RAM-13: Celery 止損檢查任務 - 啟動腳本"
echo "開始時間：$(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# 檢查是否在專案根目錄
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 錯誤：未在 docker-compose.yml 所在目錄執行"
    echo "請切換到專案根目錄後再執行此腳本"
    exit 1
fi

# 步驟 1: 啟動所有依賴服務
echo ""
echo "【步驟 1】啟動 Redis 和 PostgreSQL..."
podman compose up -d redis db

# 等待資料庫啟動
echo "等待資料庫初始化中... (約 10 秒)"
sleep 10

# 步驟 2: 啟動 Celery Worker
echo ""
echo "【步驟 2】啟動 Celery Worker..."
podman compose up -d celery_worker

# 等待 Worker 啟動
echo "等待 Worker 啟動中... (約 5 秒)"
sleep 5

# 步驟 3: 啟動 Celery Beat
echo ""
echo "【步驟 3】啟動 Celery Beat..."
podman compose up -d celery_beat

# 等待 Beat 啟動
echo "等待 Beat 啟動中... (約 5 秒)"
sleep 5

# 步驟 4: 顯示容器狀態
echo ""
echo "【步驟 4】容器狀態檢查"
echo "----------------------------------------------"
podman ps --filter "name=celery" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 步驟 5: 測試連線
echo ""
echo "【步驟 5】Celery 連線測試"
echo "----------------------------------------------"
cd backend && python -c "
from app.celery_app import celery_app
try:
    result = celery_app.control.ping(timeout=5)
    print(f'✅ Celery Worker 回應：{result}')
except Exception as e:
    print(f'❌ Celery 連接失敗：{e}')
" 2>/dev/null || echo "請先確認 Python 虛擬環境已激活"

cd ..

# 步驟 6: 顯示日誌（最後 20 行）
echo ""
echo "【步驟 6】最新日誌（各容器最後 20 行）"
echo "=============================================="
echo ""
echo "--- Celery Worker 日誌 ---"
podman logs celery_worker --tail 20

echo ""
echo "--- Celery Beat 日誌 ---"
podman logs celery_beat --tail 20

echo ""
echo "=============================================="
echo "✅ 啟動完成！"
echo "=============================================="
echo ""
echo "後續操作命令:"
echo "  查看 Worker 日誌：podman logs -f celery_worker"
echo "  查看 Beat 日誌：podman logs -f celery_beat"
echo "  停止服務：podman compose down"
echo "  重啟服務：podman compose restart celery_worker celery_beat"
echo ""
echo "結束時間：$(date '+%Y-%m-%d %H:%M:%S')"