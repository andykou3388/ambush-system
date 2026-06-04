# One-Click 初始化所有 Celery 任務

## 功能說明

`oneclick_init_data` 是一個一次性初始化所有 Celery 任務的功能，用於快速執行所有重要的數據獲取和分析任務。

## 使用方法

### 1. 手動觸發任務

```bash
# 在後端容器中執行（假設您已經進入了後端容器）
# 注意：任務名稱是 app.tasks.oneclick_init_task.oneclick_init_data
# 因為任務定義在 oneclick_init_task.py 文件中
celery -A app.celery_app.celery_app call app.tasks.oneclick_init_task.oneclick_init_data

# 如果您在主機上執行，需要先進入後端容器
# docker exec -it <backend_container_name> bash
# 然後執行上面的命令
```

### 2. 程式碼中調用

```python
from app.celery_app import celery_app

# 觸發一次性初始化
celery_app.send_task('app.tasks.oneclick_init_data')
```

### 3. API 接口觸發

可以在 API 端點中添加調用此任務的路由：

```python
from fastapi import APIRouter
from app.celery_app import celery_app

router = APIRouter()

@router.post("/init-all-tasks")
async def init_all_tasks():
    task = celery_app.send_task('app.tasks.oneclick_init_data')
    return {"task_id": task.id, "message": "任務已啟動"}
```

## 執行的任務順序

1. **股票基本面數據獲取** - 獲取指定股票的基本面數據
2. **週線技術指標計算** - 計算技術指標（MA10, MA30, Volume MA5）
3. **規則引擎分析** - 執行選股規則引擎
4. **每日分鐘線數據校驗** - 校驗分鐘線數據完整性

## 配置說明

預設使用的股票代碼：
- 2330.TW (台積電)
- 2317.TW (鴻海)
- 2454.TW (聯發科)

實際應用中，您可能需要修改程式碼以從資料庫動態獲取股票列表。

## 日誌輸出

任務執行期間會輸出詳細的日誌信息，包括：
- 開始執行各項任務
- 任務完成狀態
- 最終執行結果

## 注意事項

- 此任務可能需要較長時間執行（約5-10分鐘）
- 建議在系統負載較低時執行
- 確保所有依賴服務（資料庫、Redis等）都已正常運行